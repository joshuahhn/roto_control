"""Bounded, read-only physical B1 recorder; run in an isolated TD namespace.

Start(controller) forwards real receive/dispatch unchanged. Stop(controller)
restores both instance hooks. One five-minute deadline prevents abandoned hooks;
no operators, synthetic input, target writes, saved storage or MIDI ports.
"""
from collections import deque
from pathlib import Path
from time import monotonic
import json

class ButtonAdapterProbe:
    def __init__(self, controller, phase='toggle'):
        self.controller=controller
        self.ext=controller.ext.RotoPythonExt
        self.host=self.ext._host
        self.key=('button',1)
        self.phase=phase
        self.started=monotonic()
        self.events=deque(maxlen=128)
        self.errors=deque(maxlen=8)
        self.event_count=0
        self.active=True
        self.deadline=None
        self.before=controller.GetControlCatalog()
        self.context=controller.GetLayoutContext()['key']
        target=self.host.controls[self.key]
        assert controller.State['Connected'] and controller.State['Plugin']
        assert not controller.State['Learning'] and not controller.State['Touched']
        assert target.mapped and target.button_type==phase
        self.id=self.ext._collection.bindings[self.key].id
        self.original_receive=self.host.receive
        self.original_assign=self.host.assign_control

        def receive(message,*args,**kwargs):
            raw=tuple(message)
            observed=len(raw)==3 and raw[:2]==(191,20)
            if observed:self.Event('midi',bytes=list(raw),control_only=bool(kwargs.get('control_only',args[0] if args else False)))
            return self.original_receive(message,*args,**kwargs)

        def assign(key,value):
            result=self.original_assign(key,value)
            if key==self.key:
                try:
                    state=controller.GetControlState(self.id)
                    self.Event('dispatch',input=value,value=state['value'],label=state['value_label'],error=state['error'])
                except Exception as error:self.errors.append(str(error))
            return result

        self.receive_hook=receive;self.assign_hook=assign
        self.host.receive=receive;self.host.assign_control=assign
        self.ext._button_adapter_probe=self
        self.deadline=run('args[0].Stop("deadline")',self,delayMilliSeconds=300000,delayRef=op.TDResources)
        self.Save()

    def Event(self,kind,**fields):
        if not self.active:return
        self.event_count+=1
        self.events.append(dict(time=monotonic()-self.started,kind=kind,**fields))

    def Save(self,reason='snapshot'):
        state=self.controller.GetControlState(self.id)
        events=list(self.events)
        report=dict(phase=self.phase,reason=reason,active=self.active,
            started=self.started,elapsed=monotonic()-self.started,
            expected_physical_presses=3,event_count=self.event_count,
            dropped_events=max(0,self.event_count-len(events)),events=events,
            dispatch_count=sum(e['kind']=='dispatch' for e in events),
            midi_values=[e['bytes'][2] for e in events if e['kind']=='midi'],
            before=self.before,state=state,context=self.context,
            current_context=self.controller.GetLayoutContext()['key'],
            observer_errors=list(self.errors),physical_observation='pending',
            note='Real input only. Dispatch count is evidence; physical press count, hold/release and LCD/LED require user confirmation.')
        path=Path(project.folder)/'prototypes/inspector'/('physical_button_'+self.phase+'.json')
        path.write_text(json.dumps(report,indent=2,default=str)+'\n')
        return report

    def Stop(self,reason='stopped'):
        self.active=False
        if self.host.receive is self.receive_hook:self.host.receive=self.original_receive
        if self.host.assign_control is self.assign_hook:self.host.assign_control=self.original_assign
        if getattr(self.ext,'_button_adapter_probe',None) is self:del self.ext._button_adapter_probe
        if self.deadline:
            handle=self.deadline;self.deadline=None
            if reason!='deadline':handle.kill()
        try:return self.Save(reason)
        except Exception as error:
            print('Button recorder stopped; final snapshot failed: '+str(error))

def Start(controller,phase='toggle'):
    assert phase in ('toggle','push')
    if getattr(controller.ext.RotoPythonExt,'_button_adapter_probe',None):
        raise RuntimeError('Stop the existing button recorder first')
    return ButtonAdapterProbe(controller,phase)

def Stop(controller):
    probe=getattr(controller.ext.RotoPythonExt,'_button_adapter_probe',None)
    return probe.Stop() if probe else None
