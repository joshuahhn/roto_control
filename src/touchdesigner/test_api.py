"""Read interface checks without a TD process."""
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest

sys.path.insert(0, str(Path(__file__).parent / 'code/py/roto_python'))
from RotoPythonExt import RotoPythonExt
from controls import Controls
from protocol import Host, sysex, digest, text13
from collection_protocol import CollectionHost


class ApiTests(unittest.TestCase):
    def single(self):
        ext = RotoPythonExt.__new__(RotoPythonExt)
        storage = {}
        ext.ownerComp = SimpleNamespace(path='/controller',fetch=lambda key,default=None:storage.get(key,default),store=lambda key,value:storage.update({key:value}))
        ext._host = Host(lambda message: None, lambda value: None, .123456789)
        ext._collection = ext._binding = None
        ext._last_error = ''
        ext._dispatching = False
        ext._publish = lambda: None
        return ext

    def collection(self):
        ext = self.single()
        ext._collection = Controls([
            dict(kind='knob', slot=2, id='speed', label='Speed', minimum=0,
                 maximum=10, value=7.123456789, on_change=lambda event: None),
            dict(kind='button', slot=8, id='reset', label='Reset', mode='pulse',
                 on_change=lambda event: None)])
        ext._host = CollectionHost(lambda message: None, ext._assign_control,
                                   list(ext._collection.specs()), 'test')
        return ext

    def test_default_value_and_detached_snapshot(self):
        ext = self.single()
        state = ext.GetControlState('Value')
        self.assertEqual(ext.GetValue(), .123456789)
        state['value'] = 9
        self.assertEqual(ext.GetValue(), .123456789)
        self.assertFalse(state['mapped'])

    def test_target_units_identity_and_suspension(self):
        ext = self.collection()
        self.assertEqual(ext.GetValue('speed'), 7.123456789)
        state = ext.GetControlState('speed')
        self.assertEqual((state['kind'],state['slot'],state['maximum']), ('knob',2,10))
        ext._collection.suspend(('knob',2), 'Target deleted')
        state = ext.GetControlState('speed')
        self.assertFalse(state['valid'])
        self.assertEqual(state['error'], 'Target deleted')
        self.assertEqual(ext.GetControlState('reset')['mode'], 'pulse')
        self.assertEqual(ext.GetValue('reset'), 0)

    def test_toggle_hardware_input_confirms_led_and_display(self):
        ext = self.single()
        sent, events = [], []
        ext._collection = Controls([dict(kind='button', slot=1, id='enabled',
            label='Enabled', mode='toggle', value=0, on_change=events.append)])
        ext._host = CollectionHost(sent.append, ext._assign_control,
                                   list(ext._collection.specs()), 'test.toggle')
        host = ext._host
        host.start(); host.receive(sysex(10,12)); host.receive(sysex(11,1,(0,)))
        target = host.controls['button',1]
        host.receive(sysex(11,11,(0,target.index,*digest(target.target_id,6),1,0,0)))
        for value, label in [(127,'On'),(0,'Off')]:
            sent.clear()
            host.receive((191,20,value))
            self.assertEqual(ext.GetValue('enabled'), float(value>0))
            self.assertEqual(sent,[(191,20,value),sysex(10,24,(1,0,*text13(label)))])
        self.assertEqual([e['value'] for e in events],[1,0])

    def ready(self, ext):
        host = ext._host
        host.start(); host.receive(sysex(10,12)); host.receive(sysex(11,1,(0,)))
        for key,target in host.controls.items():
            host.receive(sysex(11,11,(0,target.index,*digest(target.target_id,6),
                                     int(key[0]=='button'),key[1]-1,0)))

    def test_numeric_software_then_hardware_sequence_and_touch_deferral(self):
        ext = self.collection()
        sent, events = [], []
        ext._host.send = sent.append
        ext._collection.bindings['knob',2].on_change = events.append
        self.ready(ext); sent.clear()
        self.assertEqual(ext.SetValue(8,id='speed'),8)
        self.assertEqual(events,[])
        self.assertEqual([m[1] for m in sent if m[0]==191],[13,45])
        sent.clear()
        ext._host.receive((191,13,100)); ext._host.receive((191,45,0))
        self.assertAlmostEqual(ext.GetValue('speed'),10*12800/16383)
        self.assertEqual(len(events),1)
        self.assertEqual(sent,[])  # physical knob input must not echo motor CCs
        ext._host.receive((191,53,127)); sent.clear()
        ext.SetValue(2,id='speed')
        self.assertEqual(sent,[])
        ext._host.receive((191,53,0))
        self.assertEqual([m[1] for m in sent if m[0]==191],[13,45])
        self.assertEqual(len(events),1)

    def test_push_pulse_fires_on_press_only_and_confirms_release(self):
        ext = self.single()
        sent, events = [], []
        ext._collection = Controls([dict(kind='button',slot=8,id='reset',label='Reset',
            mode='pulse',button_type='push',on_change=events.append)])
        ext._host = CollectionHost(sent.append,ext._assign_control,
                                   list(ext._collection.specs()),'test.push')
        self.ready(ext); sent.clear()
        for value in [127,127,0,0,127,0]: ext._host.receive((191,27,value))
        self.assertEqual(len(events),2)
        self.assertTrue(all(e['kind']=='pulse' for e in events))
        self.assertEqual(ext.GetValue('reset'),0)
        self.assertEqual(ext.GetControlState('reset')['button_type'],'push')
        self.assertEqual([m for m in sent if m[0]==191],
                         [(191,27,127),(191,27,0),(191,27,127),(191,27,0)])
        self.assertEqual([bytes(m[9:-1]).rstrip(b'\0') for m in sent if m[0]==240],
                         [b'Trigger',b'Ready',b'Trigger',b'Ready'])
        before = list(sent); ext._host.flush_display(10)
        self.assertEqual(sent,before)

    def test_collection_software_failure_is_reported_and_isolated(self):
        ext = self.collection()
        self.ready(ext)
        with self.assertRaisesRegex(ValueError,'finite'):
            ext.SetValue(float('nan'),id='speed')
        state = ext.GetControlState('speed')
        self.assertFalse(state['valid'])
        self.assertFalse(state['mapped'])
        self.assertIn('finite',state['error'])
        self.assertTrue(ext.GetControlState('reset')['valid'])

    def test_pulse_software_learn_offer_is_not_a_business_action(self):
        ext = self.collection()
        self.ready(ext)
        self.assertFalse(ext.Offerparameter('reset'))
        with self.assertRaisesRegex(ValueError,'Pulse'):
            ext.SetValue(1,id='reset')
        self.assertTrue(ext.GetControlState('reset')['valid'])
        ext._host.receive(sysex(11,9,(1,)))
        self.assertTrue(ext.Offerparameter('reset'))
        self.assertEqual(ext.GetValue('reset'),0)

    def test_button_type_validation_is_explicit(self):
        for spec in [dict(kind='button',slot=1,id='x',mode='pulse',button_type='auto'),
                     dict(kind='knob',slot=1,id='x',button_type='push')]:
            with self.assertRaisesRegex(ValueError,'button_type'):
                Controls([dict(spec,on_change=lambda event: None)])

    def test_global_registration_fault_invalidates_all_queries(self):
        ext = self.collection()
        self.ready(ext)
        ext._fault(ValueError('Registration failed'))
        state = ext.GetControlState('speed')
        self.assertFalse(state['valid'])
        self.assertFalse(state['mapped'])
        self.assertEqual(state['error'], 'Registration failed')

    def test_inspection_lists_targets_without_inventing_callback_comp(self):
        ext = self.collection()
        states = ext.GetControlStates()
        self.assertEqual([s['id'] for s in states], ['speed', 'reset'])
        self.assertTrue(all(s['binding_type']=='callback' and s['comp']=='' for s in states))
        states[0]['value'] = 99
        self.assertNotEqual(ext.GetValue('speed'),99)
        ext = self.single()
        self.assertEqual(ext.GetControlStates()[0]['comp'],'/controller')
        self.assertEqual(ext.GetControlStates()[0]['parameter'],'Value')
        from binding import Binding
        par = SimpleNamespace(owner=SimpleNamespace(valid=True,path='/scene'),name='Speed')
        ext._binding = Binding('speed','Speed',0,10,4,parameter=par)
        self.assertEqual(ext.GetControlStates()[0]['comp'],'/scene')
        self.assertEqual(ext.GetControlStates()[0]['parameter'],'Speed')
        par.owner.valid = False
        self.assertEqual(ext.GetControlStates()[0]['comp'],'')

    def test_inspector_failure_does_not_suspend_hardware_host(self):
        ext = self.single()
        records = {}
        title = SimpleNamespace(par=SimpleNamespace(text=''))
        def fail(*args):
            raise ValueError('Invalid Inspector config')
        module = SimpleNamespace(module=SimpleNamespace(refresh=fail))
        inspector = SimpleNamespace(op=lambda name: module if name=='inspector_data' else title,
                                    store=lambda key,value: records.update({key:value}))
        ext.ownerComp.op = lambda name: inspector
        ext._publish_inspector()
        self.assertTrue(ext._host.enabled)
        self.assertEqual(records['refresh_error'],'Invalid Inspector config')
        self.assertIn('unavailable',title.par.text)

    def test_clear_learn_sends_hardware_unmap_and_isolates_control(self):
        ext = self.collection(); self.ready(ext)
        sent = []; ext._host.send = sent.append
        target=ext._host.controls[('knob',2)]
        target._parts[13]=10; target._display_dirty=target._deferred_value=True
        value=ext.GetValue('speed')
        self.assertTrue(ext.ClearLearn('speed'))
        self.assertEqual(sent,[sysex(11,14,(0,1))])
        self.assertFalse(ext.GetControlState('speed')['mapped'])
        self.assertTrue(ext.GetControlState('reset')['mapped'])
        self.assertEqual(ext.GetValue('speed'),value)
        self.assertTrue(ext.GetControlState('speed')['valid'])
        self.assertFalse(target._parts or target._display_dirty or target._deferred_value)
        before=list(sent); ext._host.flush_display(1000)
        self.assertEqual(sent,before)
        ext.ClearLearn('reset')
        self.assertEqual(sent[-1],sysex(11,14,(1,7)))
        ext._host.receive((191,27,127))
        self.assertEqual(ext.GetValue('reset'),0)

    def test_clear_learn_send_failure_keeps_mapping(self):
        ext=self.collection();self.ready(ext)
        def fail(message):
            raise RuntimeError('Transport failed')
        ext._host.send=fail
        with self.assertRaisesRegex(RuntimeError,'Transport failed'):
            ext.ClearLearn('reset')
        self.assertTrue(ext.GetControlState('reset')['mapped'])
        self.assertTrue(ext.GetControlState('reset')['valid'])

    def test_clear_learn_guards_and_single_mode(self):
        ext=self.single(); sent=[];ext._host.send=sent.append
        with self.assertRaisesRegex(ValueError,'Connect'):
            ext.ClearLearn()
        ext._host.connected=ext._host.plugin=ext._host.mapped=True
        ext._host.learning=True
        with self.assertRaisesRegex(ValueError,'Exit LEARN'):
            ext.ClearLearn()
        ext._host.learning=False;ext._host.touched=True
        with self.assertRaisesRegex(ValueError,'release'):
            ext.ClearLearn()
        ext._host.touched=False
        with self.assertRaisesRegex(ValueError,'Unknown target'):
            ext.ClearLearn('wrong')
        self.assertEqual(sent,[])
        self.assertTrue(ext.ClearLearn('Value'))
        self.assertEqual(sent,[sysex(11,14,(0,0))])
        self.assertFalse(ext._host.mapped)
        self.assertTrue(ext._host.enabled)

    def test_unknown_ids_and_missing_default_fail(self):
        with self.assertRaisesRegex(ValueError, 'Unknown target'):
            self.single().GetValue('wrong')
        with self.assertRaisesRegex(ValueError, 'Unknown target'):
            self.collection().GetValue('wrong')
        with self.assertRaisesRegex(ValueError, 'Knob 1'):
            self.collection().GetValue()


class ConfigurationTests(unittest.TestCase):
    single=ApiTests.single
    ready=ApiTests.ready
    def collection(self):
        ext=ApiTests.collection(self)
        import controls, collection_protocol
        ext.ownerComp.op=lambda name: SimpleNamespace(module=controls if name=='controls' else collection_protocol)
        return ext

    def test_edit_range_invalidates_only_changed_mapping(self):
        ext=self.collection();self.ready(ext)
        sent=[];ext._host.send=sent.append
        result=ext.ConfigureControl('speed',maximum=20)
        self.assertEqual(result['maximum'],20)
        self.assertFalse(result['mapped']);self.assertTrue(result['requires_relearn'])
        self.assertTrue(ext.GetControlState('reset')['mapped'])
        self.assertEqual(sent,[sysex(11,14,(0,1))])
        self.assertEqual(ext.GetValue('speed'),7.123456789)
        self.assertEqual(ext.ownerComp.fetch('control_overrides')['speed']['maximum'],20)

    def test_invalid_edit_has_no_side_effects(self):
        ext=self.collection();self.ready(ext)
        sent=[];ext._host.send=sent.append
        before=ext.GetControlStates()
        for changes in [dict(minimum=11),dict(maximum=float('nan')),dict(maximum=5),dict(mode='pulse')]:
            with self.assertRaises(ValueError):ext.ConfigureControl('speed',**changes)
            self.assertEqual(ext.GetControlStates(),before)
        self.assertEqual(sent,[])
        self.assertIsNone(ext.ownerComp.fetch('control_overrides'))

    def test_callback_mode_edit_and_old_identity_rejected(self):
        ext=self.collection();self.ready(ext)
        old=ext._host.controls['button',8].target_id
        ext.ConfigureControl('reset',mode='toggle')
        self.assertEqual(ext.GetControlState('reset')['mode'],'toggle')
        ext._host.receive(sysex(11,11,(0,15,*digest(old,6),1,7,0)))
        self.assertFalse(ext.GetControlState('reset')['mapped'])
        self.ready(ext)
        self.assertFalse(ext.GetControlState('reset')['requires_relearn'])

    def test_input_adapter_change_preserves_mapping_and_wire_state(self):
        ext=self.collection();self.ready(ext)
        target=ext._host.controls['button',8];target._pulse_state=127
        original_id=target.target_id;sent=[];ext._host.send=sent.append
        state=ext.ConfigureControl('reset',button_type='push')
        self.assertTrue(state['mapped']);self.assertFalse(state['requires_relearn'])
        self.assertEqual(state['mode'],'pulse');self.assertEqual(state['button_type'],'push')
        self.assertIs(ext._host.controls['button',8],target)
        self.assertEqual(target._pulse_state,127);self.assertEqual(target.target_id,original_id)
        self.assertEqual(sent,[])
        self.assertEqual(ext.ownerComp.fetch('control_overrides')['reset']['button_type'],'push')
        events=[];ext._collection.bindings['button',8].on_change=events.append
        ext._host.receive((191,27,0));self.assertEqual(events,[])
        ext._host.receive((191,27,127));self.assertEqual(len(events),1)

    def test_adapter_edit_preserves_existing_relearn_requirement(self):
        ext=self.collection();ext.ownerComp.store('needs_relearn',('reset',))
        state=ext.ConfigureControl('reset',button_type='push')
        self.assertTrue(state['requires_relearn']);self.assertFalse(state['mapped'])

    def test_clear_all_preflight_and_commands(self):
        ext=self.collection();self.ready(ext)
        sent=[];ext._host.send=sent.append
        ext._host.controls['button',8].touched=True;ext._host._sync()
        with self.assertRaises(ValueError):ext.ClearAllLearn()
        self.assertEqual(sent,[]);self.assertTrue(ext.GetControlState('speed')['mapped'])
        ext._host.controls['button',8].touched=False;ext._host._sync()
        self.assertEqual(ext.ClearAllLearn(),('speed','reset'))
        self.assertEqual(sent,[sysex(11,14,(0,1)),sysex(11,14,(1,7))])
        self.assertTrue(all(not state['mapped'] for state in ext.GetControlStates()))

if __name__ == '__main__':
    unittest.main()
