"""Isolated hardware A/B/A evidence harness; never runs inside the TD extension.

Disconnect TD first. Run with the project's MIDI-capable Python interpreter.
Commands on stdin: select A|B|EMPTY, offer, status, stop. Hardware LEARN is manual.
No timeout is treated as selection proof. Exit closes MIDI ports; reconnect TD
manually afterward. This probe stores new hardware mappings under probe-only hashes.
"""
import argparse
import json
import os
from pathlib import Path
import signal
import sys
import time
sys.path.insert(0,str(Path(__file__).parents[2]/'code/py/roto_python'))
from protocol import SysExGroup, HEADER, Host, digest, SysExCommand, text13

class Probe:
    def __init__(self, send, record):
        self.send_wire,self.record=send,record
        self.requested=None
        self.active=None
        self.locked=False
        self.learning=False
        self.touched=set()
        self.hosts={}
        for index,name in enumerate(('A','B')):
            host=Host(self.send,lambda value,i=index,n=name:self.assign(i,n,value))
            host.device_id='TD layout protocol probe v1 '+name
            host.target_id='TD layout probe parameter '+name
            host.target_label='Probe '+name
            host.plugin_name='PROBE '+name
            self.hosts[index]=host

    def assign(self,index,name,value):
        self.record("input", {"plugin":name,"value":value})
        # Match the production consumer contract: echo accepted value through the
        # host so it schedules LCD feedback while suppressing a motor MIDI echo.
        self.hosts[index].parameter_changed(value)

    def send(self,message):
        self.record('tx',list(message));self.send_wire(message)

    def announce(self):
        self.send(SysExCommand.NUM_DEVICES.message((3,)))
        self.send(SysExCommand.FIRST_DEVICE.message((0,)))
        for index,name in enumerate(('A','B','EMPTY')):
            identity=self.hosts[index].device_id if index<2 else 'TD layout protocol probe v1 EMPTY'
            self.send(SysExCommand.PLUGIN_DETAILS.message((index,*digest(identity,8),1,*text13('PROBE '+name),0,0)))
        self.send(SysExCommand.PLUGIN_DETAILS_END.message())

    def select(self,name):
        index=('A','B','EMPTY').index(name)
        if self.locked or self.learning or self.touched:
            raise ValueError('Exit LEARN, unlock and release controls before TD-origin selection')
        # Dispatch remains disabled until matching control acknowledgement.
        self.requested=index;self.active=None
        for h in self.hosts.values():
            h._clear_mapping_state();h.touched=False
        self.send(SysExCommand.DAW_SELECT_PLUGIN.message((index,0,0)))
        self.record('requested',name)

    def receive(self,message):
        message=tuple(message);self.record('rx',list(message))
        if len(message)==3 and message[0]==191 and 52<=message[1]<=59 and 0<=message[2]<128:
            if message[2]: self.touched.add(message[1])
            else: self.touched.discard(message[1])
        if message[:1]==(240,):
            if len(message)<8 or message[:5]!=HEADER or message[-1:]!=(247,) or any(type(x) is not int or not 0<=x<128 for x in message[1:-1]):
                self.record("invalid_sysex",list(message));return
            group,command,data=message[5],message[6],message[7:-1]
            identity = SysExCommand.identify(message)
            if group == SysExGroup.MIX or identity is SysExCommand.PING_DAW:
                self.active=self.requested=None;self.learning=False;self.locked=False;self.touched.clear()
                for h in self.hosts.values(): h.stop()
                self.record("session_reset",dict(group=group,command=command))
                if identity is SysExCommand.PING_DAW: self.send(SysExCommand.DAW_PING_RESP.message((1,)))
            elif identity is SysExCommand.ROTO_DAW_CONNECTED:
                self.send(SysExCommand.SET_CURRENT_TRACK_NAME.message(text13('LAYOUT PROBE')))
            elif identity in (SysExCommand.SET_PLUGIN_MODE, SysExCommand.SET_FIRST_DEVICE):
                self.announce()
                if identity is SysExCommand.SET_PLUGIN_MODE:
                    self.active=self.requested=None
                    self.learning=False;self.locked=False;self.touched.clear()
                    for h in self.hosts.values():
                        h.stop();h.connected=h.plugin=True
                    self.select('A')
            elif identity is SysExCommand.SET_PLUGIN_LOCK and len(data)==1:
                self.locked=bool(data[0]);self.record('lock',self.locked)
            elif identity is SysExCommand.SET_DEVICE_LEARN and len(data)==1:
                self.learning=bool(data[0])
                for h in self.hosts.values(): h.learning=self.learning
            elif identity is SysExCommand.ROTO_CONTROL_SELECT_DEVICE and len(data)==1 and data[0] in (0,1,2):
                self.requested=data[0];self.active=None
                for h in self.hosts.values():
                    h._clear_mapping_state();h.touched=False
                self.record('hardware_selection',data[0])
            elif identity is SysExCommand.CONTROL_MAPPED:
                h=self.hosts.get(self.requested)
                if h is not None:
                    h.receive(message)
                    if h.mapped:
                        self.active=self.requested;self.record('confirmed_control',self.active)
        elif self.active in self.hosts:
            self.hosts[self.active].receive(message)
        else: self.record('input_suspended',list(message))

    def command(self,line):
        parts=line.strip().split()
        if parts[:1]==['select'] and len(parts)==2: self.select(parts[1].upper())
        elif parts==['offer']:
            h=self.hosts.get(self.requested)
            if h is None or not h.offer_parameter(): raise ValueError('Select A/B and enable hardware LEARN first')
        elif parts==['status']:
            self.record('status',dict(requested=self.requested,confirmed=self.active,locked=self.locked,learning=self.learning))
        else: raise ValueError('Use select A|B|EMPTY, offer, status, stop')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--device',default='Roto-Control')
    parser.add_argument('--log',required=True)
    parser.add_argument('--td-disconnected',action='store_true',required=True)
    args=parser.parse_args()
    import mido
    mido.set_backend('mido.backends.rtmidi')
    if Path(args.log).exists(): raise FileExistsError(args.log)
    running=True
    def stop(*args):
        nonlocal running
        running=False
    signal.signal(signal.SIGINT,stop);signal.signal(signal.SIGTERM,stop)
    with open(args.log,'x',encoding='utf-8') as log, mido.open_input(args.device) as incoming, mido.open_output(args.device) as outgoing:
        sequence=0
        def record(kind,data):
            nonlocal sequence
            sequence+=1
            event=dict(sequence=sequence,monotonic=time.monotonic(),kind=kind,data=data)
            log.write(json.dumps(event)+'\n');log.flush()
            if kind not in ('rx','tx','input_suspended','input'): print(json.dumps(event),flush=True)
        probe=Probe(lambda message:outgoing.send(mido.Message.from_bytes(message)),record)
        probe.send(SysExCommand.DAW_STARTED.message())
        os.set_blocking(sys.stdin.fileno(),False);pending=b''
        while running:
            for _ in range(256):
                message=incoming.poll()
                if message is None: break
                probe.receive(message.bytes())
            try: chunk=os.read(sys.stdin.fileno(),65536)
            except BlockingIOError: chunk=None
            if chunk==b'': break
            if chunk:
                pending+=chunk
                while b'\n' in pending:
                    line,pending=pending.split(b'\n',1)
                    if line.strip()==b'stop': running=False;break
                    try: probe.command(line.decode('ascii'))
                    except ValueError as exc: record('rejected',str(exc))
            for host in probe.hosts.values(): host.flush_display(time.monotonic())
            time.sleep(.002)  # external process only; never proof of selection
if __name__=='__main__': main()
