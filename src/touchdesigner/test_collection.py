"""Multi-control isolation at the wire and target-adapter boundaries."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'code/py/roto_python'))
from collection_protocol import CollectionHost
from controls import Controls
from protocol import sysex, digest, text13

def pulse_feedback(slot, value):
    return [(191,19+slot,value),sysex(10,24,(1,slot-1,*text13('Trigger' if value>=64 else 'Ready')))]



class CollectionTests(unittest.TestCase):
    def setUp(self):
        self.sent, self.events, self.now = [], [], [0.0]
        specs = [dict(kind=kind, slot=slot, identity=f'{kind}{slot}', label=f'{kind}{slot}',
                      mode='value' if kind=='knob' else 'pulse' if slot==8 else 'toggle',
                      value=.5 if kind=='knob' else 0, formatter=str)
                 for kind in ('knob','button') for slot in range(1,9)]
        self.host = CollectionHost(self.sent.append, self.assign, specs, 'test', clock=lambda:self.now[0])
        self.host.start()
        self.host.receive(sysex(10,12))
        self.host.receive(sysex(11,1,(0,)))

    def assign(self,key,value):
        self.events.append((key,value))
        if self.host.controls[key].mode != 'pulse':
            self.host.parameter_changed(value,key)

    def map(self,kind,slot):
        t=self.host.controls[kind,slot]
        self.host.receive(sysex(11,11,(0,t.index,*digest(t.target_id,6),int(kind=='button'),slot-1,0)))

    def test_all_slots_recall_and_feedback_addresses(self):
        for kind in ('knob','button'):
            for slot in range(1,9):
                start=len(self.sent)
                self.map(kind,slot)
                messages=self.sent[start:]
                self.assertEqual(messages[0][7:9],(0,slot-1+(8 if kind=='button' else 0)))
                cc=[m[1] for m in messages if m[0]==191]
                self.assertEqual(cc,[11+slot,43+slot] if kind=='knob' else [19+slot])
                self.assertEqual(messages[-1][7:9],(int(kind=='button'),slot-1))
        self.assertTrue(self.host.mapped)

    def test_pulse_metadata_has_action_labels(self):
        self.map('button',8)
        details=next(m for m in reversed(self.sent) if m[0]==240 and m[5:7]==(11,10))
        self.assertEqual(details[33:46],text13('Ready'))
        self.assertEqual(details[46:59],text13('Trigger'))

    def test_native_toggle_pulse_resets_immediately_without_timer(self):
        self.map('button',8)
        self.sent.clear()
        self.host.receive((191,27,127))
        self.assertEqual(self.events,[(('button',8),1)])
        self.assertEqual(self.host.controls['button',8].value,0)
        self.host.flush_display(.21)
        self.host.flush_display(10)
        self.assertEqual(self.sent,pulse_feedback(8,0))
        self.assertEqual(len(self.events),1)

    def test_fast_latched_zero_press_is_an_action_with_immediate_reset(self):
        self.map('button',8)
        self.sent.clear()
        self.host.receive((191,27,127))
        self.now[0]=.1
        self.host.receive((191,27,0))
        self.assertEqual(self.events,[(('button',8),1),(('button',8),1)])
        self.host.flush_display(.31)
        self.assertEqual(self.sent,pulse_feedback(8,0)+pulse_feedback(8,0))

    def test_native_pulse_slots_are_independent_and_stop_suppresses_input(self):
        self.host.controls['button',2].mode='pulse'
        self.map('button',2);self.map('button',8)
        self.sent.clear()
        self.host.receive((191,21,127))
        self.now[0]=.1;self.host.receive((191,27,0))
        self.host.flush_display(1)
        self.assertEqual(self.events,[(('button',2),1),(('button',8),1)])
        self.assertEqual(self.sent,pulse_feedback(2,0)+pulse_feedback(8,0))
        self.host.stop()
        self.now[0]=2
        self.host.receive((191,27,127))
        self.assertEqual(len(self.events),2)
        self.assertEqual(self.sent,pulse_feedback(2,0)+pulse_feedback(8,0))

    def test_crossed_halves_never_mix_slots(self):
        self.map('knob',1);self.map('knob',8)
        self.host.receive((191,12,10));self.host.receive((191,51,20))
        self.assertFalse(self.events)
        self.host.receive((191,44,30));self.host.receive((191,19,40))
        self.assertEqual(self.events,[(('knob',1),(10*128+30)/16383),(('knob',8),(40*128+20)/16383)])
        self.assertEqual(self.host.echo_blocked,2)

    def test_mapping_wrong_hash_or_slot_rejected(self):
        self.host.receive(sysex(11,11,(0,0,*digest('knob1',6),0,1,0)))
        self.assertFalse(self.host.controls['knob',2].mapped)
        self.assertEqual(self.host.rejected,1)

    def test_touch_only_defers_matching_motor(self):
        self.map('knob',1);self.map('knob',2)
        self.host.receive((191,53,127));self.sent.clear()
        self.host.parameter_changed(.8,('knob',2))
        self.host.parameter_changed(.7,('knob',1))
        self.assertEqual([m[1] for m in self.sent if m[0]==191],[12,44])
        self.host.receive((191,53,0))
        self.assertEqual([m[1] for m in self.sent if m[0]==191],[12,44,13,45])

    def test_toggle_latched_values_and_repeated_pulse_presses(self):
        self.map('button',1);self.map('button',8)
        self.host.receive((191,20,127));self.host.receive((191,20,0))
        self.host.receive((191,27,127));self.host.receive((191,27,127))
        self.now[0]=.2;self.host.receive((191,27,127))
        self.assertEqual(self.events,[(('button',1),1),(('button',1),0),(('button',8),1),(('button',8),1)])
        self.assertEqual(self.host.controls['button',8].value,0)
        self.assertEqual([m for m in self.sent if m[0]==191 and m[1]==27],[(191,27,0),(191,27,0),(191,27,0)])
        self.host.receive((191,20,127));self.host.receive((191,20,127));self.host.receive((191,20,0))
        self.host.receive((191,20,127));self.host.receive((191,20,0))
        self.assertEqual(self.host.controls['button',1].value,0)

    def test_independent_learn_and_hardware_echo(self):
        self.map('knob',1)
        self.host.receive(sysex(11,9,(1,)))
        self.sent.clear()
        self.host.receive((191,12,60));self.host.receive((191,44,0))
        self.assertFalse(self.sent)
        self.host.parameter_changed(.6,('knob',2));self.host.parameter_changed(.7,('knob',2))
        self.host.parameter_changed(1,('button',1))
        self.assertEqual([m[8] for m in self.sent if m[0]==240 and m[6]==10],[1,8])

    def test_reconnect_clears_partial_pairs_and_all_mapping(self):
        self.map('knob',8);self.host.receive((191,19,42));self.host.stop()
        self.host.start();self.host.receive(sysex(10,12));self.host.receive(sysex(11,1,(0,)))
        self.map('knob',8);self.host.receive((191,51,10))
        self.assertFalse(self.events)
        self.assertFalse(self.host.mapped)

    def test_suspend_one_control_preserves_other_inputs(self):
        self.map('button',1);self.map('button',2)
        self.host.controls['button',1].enabled=False
        self.host.receive((191,20,127));self.host.receive((191,21,127))
        self.assertEqual(self.events,[(('button',2),1)])

    def test_duplicate_slots_and_invalid_modes_fail(self):
        spec=dict(kind='button',slot=1,identity='a',label='a',value=0,formatter=str,mode='toggle')
        with self.assertRaises(ValueError):CollectionHost(lambda m:None,lambda k,v:None,[spec,spec],'x')
        spec['mode']='value'
        with self.assertRaises(ValueError):CollectionHost(lambda m:None,lambda k,v:None,[spec],'x')


class AdapterTests(unittest.TestCase):
    def test_callback_ranges_and_pulse_events(self):
        events=[]
        c=Controls([dict(kind='knob',slot=8,id='speed',minimum=-10,maximum=10,value=0,on_change=events.append),
                    dict(kind='button',slot=8,id='fire',mode='pulse',on_change=events.append)])
        b=c.bindings['knob',8]
        b.write(b.from_normalized(.75),'hardware')
        c.pulse(('button',8));c.pulse(('button',8))
        self.assertEqual([e['value'] for e in events],[5,1,1])
        self.assertEqual(events[-1]['kind'],'pulse')
        self.assertEqual(c.key('speed'),('knob',8))
        with self.assertRaises(ValueError):c.key()
        c.suspend(('button',8),RuntimeError('bad'))
        with self.assertRaises(ValueError):c.pulse(('button',8))
        b.write(8,'software')
        self.assertEqual(len(events),3)

    def test_equal_valued_td_handles_are_distinct_targets(self):
        from types import SimpleNamespace
        class Parameter:
            isCustom=True
            style='Float'
            readOnly=False
            normMin=0
            normMax=10
            clampMin=clampMax=False
            mode=SimpleNamespace(name='CONSTANT')
            def __init__(self,name):
                self.name,self.label=name,name
                self.owner=SimpleNamespace(path='/demo',valid=True)
            def eval(self):return 5
            def __eq__(self,other):return isinstance(other,Parameter) and self.eval()==other.eval()
        first,second=Parameter('First'),Parameter('Second')
        self.assertEqual(first,second)
        c=Controls([dict(kind='knob',slot=1,id='a',parameter=first),dict(kind='knob',slot=2,id='b',parameter=second)])
        self.assertEqual(len(c.bindings),2)
        with self.assertRaisesRegex(ValueError,'bound twice'):
            Controls([dict(kind='knob',slot=1,id='a',parameter=first),dict(kind='knob',slot=2,id='b',parameter=first)])

    def test_duplicate_id_or_button_range_fails(self):
        specs=[dict(kind='button',slot=i,id='duplicate',on_change=lambda e:None) for i in (1,2)]
        with self.assertRaises(ValueError):Controls(specs)
        with self.assertRaises(ValueError):Controls([dict(kind='button',slot=1,id='x',maximum=10,on_change=lambda e:None)])

if __name__=='__main__':unittest.main()
