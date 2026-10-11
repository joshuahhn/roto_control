"""The probe must not imply selection completion from elapsed time."""
import unittest
from layout_protocol_probe import Probe
from protocol import digest, sysex

class LayoutProbeTests(unittest.TestCase):
    def setUp(self):
        self.sent=[];self.events=[]
        self.probe=Probe(self.sent.append,lambda kind,data:self.events.append((kind,data)))
        for host in self.probe.hosts.values(): host.connected=host.plugin=True
    def ack(self,index):
        return sysex(11,11,(0,0,*digest(self.probe.hosts[index].target_id,6),0,0,0))
    def test_recall_only_matching_parameter_routes_current(self):
        self.probe.select('A');self.probe.receive(self.ack(0));self.assertEqual(self.probe.active,0)
        self.probe.select('B');self.probe.receive(self.ack(0));self.assertIsNone(self.probe.active)
        self.probe.receive((191,12,127));self.probe.receive((191,44,127))
        self.assertFalse(any(kind=='input' for kind,data in self.events))
        self.probe.receive(self.ack(1));self.probe.receive((191,12,127));self.probe.receive((191,44,127))
        self.assertEqual([data['plugin'] for kind,data in self.events if kind=='input'],['B'])
        self.probe.select('A');self.probe.receive(self.ack(0));self.assertEqual(self.probe.active,0)
        self.assertFalse(any(message[5:7]==(11,14) for message in self.sent if message[0]==240))
    def test_empty_and_lock_rejection_atomic(self):
        self.probe.select('EMPTY');self.assertEqual(self.probe.requested,2);self.assertIsNone(self.probe.active)
        self.probe.locked=True;before=list(self.sent)
        with self.assertRaises(ValueError): self.probe.select('A')
        self.assertEqual(self.probe.requested,2);self.assertEqual(self.sent,before)
        self.probe.receive(sysex(11,7,(0,)));self.assertEqual(self.probe.requested,0)
        self.assertIsNone(self.probe.active)
    def test_malformed_and_session_reset_suspend_routing(self):
        self.probe.receive((240,0,34,3,2,11))
        self.probe.select('A');self.probe.receive(self.ack(0))
        self.probe.receive(sysex(12,1));self.assertIsNone(self.probe.active)
        self.probe.receive((191,12,127));self.probe.receive((191,44,127))
        self.assertFalse(any(kind=='input' for kind,data in self.events))
        self.assertFalse(self.probe.hosts[0].connected)
    def test_physical_touch_tracked_without_active_mapping_and_released_after_switch(self):
        self.probe.receive((191,52,127))
        with self.assertRaises(ValueError): self.probe.select('A')
        self.probe.receive(sysex(11,7,(1,)))
        self.probe.receive((191,52,0));self.probe.select('A')
        self.assertEqual(self.probe.requested,0)

    def test_mode_entry_resets_stale_session_flags_before_select(self):
        self.probe.learning=self.probe.locked=True
        self.probe.touched.add(52)
        self.probe.receive(sysex(11,1,(0,)))
        self.assertEqual(self.probe.requested,0)
        self.assertIsNone(self.probe.active)
        self.assertFalse(self.probe.learning or self.probe.locked or self.probe.touched)

    def test_input_echo_updates_lcd_without_motor_echo(self):
        self.probe.select('A');self.probe.receive(self.ack(0))
        self.sent.clear()
        self.probe.receive((191,12,64));self.probe.receive((191,44,0))
        host=self.probe.hosts[0]
        self.assertEqual(host.echo_blocked,1)
        self.assertEqual(self.sent,[])
        host.flush_display(1.0)
        self.assertEqual(len(self.sent),1)
        self.assertEqual(self.sent[0][5:7],(10,24))
        self.assertEqual(bytes(self.sent[0][9:-1]).rstrip(b'\0'),b'0.5')
        self.assertFalse(any(message[0]==191 for message in self.sent))
        self.assertEqual([data['plugin'] for kind,data in self.events if kind=='input'],['A'])
