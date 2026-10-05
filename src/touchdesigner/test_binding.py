"""Binding semantics tested without TouchDesigner or physical MIDI."""
import math
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest

sys.path.insert(0, str(Path(__file__).parent/'code/py/roto_python'))
from binding import Binding
from protocol import Host, digest, sysex


class Parameter:
    def __init__(self, value=5):
        self.owner = SimpleNamespace(valid=True)
        self.readOnly = False
        self.mode = SimpleNamespace(name='CONSTANT')
        self.val = value

    def eval(self):
        return self.val


class BindingTests(unittest.TestCase):
    def test_range_validation_and_clamping(self):
        for low, high in [(1,1),(2,1),(math.nan,10),(0,math.inf),(-1e308,1e308)]:
            with self.assertRaises(ValueError):
                Binding('speed','Speed',low,high,5)
        b = Binding('speed','Speed',0,10,5)
        self.assertEqual(b.normalized(5),0.5)
        self.assertEqual(b.from_normalized(0.25),2.5)
        self.assertEqual(b.clamp(20),10)
        with self.assertRaises(ValueError):
            b.clamp(math.nan)

    def test_integer_steps(self):
        b = Binding('steps','Steps',0,10,5,integer=True)
        self.assertEqual(b.from_normalized(0.26),3)
        with self.assertRaises(ValueError):
            Binding('steps','Steps',0,10.5,5,integer=True)

    def test_callback_only_hardware_and_changed_values(self):
        events=[]
        b=Binding('speed','Speed',0,10,5,on_change=events.append)
        b.write(7,'software')
        self.assertEqual(events,[])
        b.write(8,'hardware')
        b.write(8,'hardware')
        self.assertEqual(events,[{'id':'speed','value':8,'origin':'hardware'}])

    def test_parameter_origin_echo_and_later_external_edit(self):
        p=Parameter()
        b=Binding('speed','Speed',0,10,5,parameter=p)
        b.write(7,'hardware')
        self.assertEqual(p.eval(),7)
        self.assertFalse(b.external_changed(7))
        p.val=8
        self.assertTrue(b.external_changed(8))
        self.assertEqual(b.value,8)

    def test_batched_external_edit_is_not_discarded(self):
        p=Parameter()
        b=Binding('speed','Speed',0,10,5,parameter=p)
        b.write(7,'hardware')
        p.val=9
        self.assertTrue(b.external_changed(p.eval()))
        self.assertEqual(b.value,9)

    def test_invalid_target_stops_writes(self):
        p=Parameter()
        b=Binding('speed','Speed',0,10,5,parameter=p)
        p.owner.valid=False
        with self.assertRaises(ValueError):
            b.write(7,'hardware')
        self.assertEqual(p.val,5)
        p.owner.valid=True
        p.mode.name='EXPRESSION'
        with self.assertRaises(ValueError):
            b.write(7,'software')

    def test_callback_failure_is_visible_to_adapter(self):
        def fail(event):
            raise RuntimeError('consumer failed')
        b=Binding('speed','Speed',0,10,5,on_change=fail)
        with self.assertRaisesRegex(RuntimeError,'consumer failed'):
            b.write(7,'hardware')
        b.valid=False
        with self.assertRaisesRegex(ValueError,'suspended'):
            b.write(8,'hardware')

    def test_identity_independent_of_label_and_range_sensitive(self):
        a=Binding('speed','Speed',0,10,5)
        b=Binding('speed','Renamed',0,10,5)
        c=Binding('speed','Speed',0,20,5)
        self.assertEqual(a.wire_identity,b.wire_identity)
        self.assertNotEqual(a.wire_identity,c.wire_identity)

    def test_target_switch_rejects_old_mapping_and_returns_new_metadata(self):
        sent=[]
        h=Host(sent.append,lambda value:None)
        h.start()
        h.receive(sysex(10,12))
        h.receive(sysex(11,1,(0,)))
        h.receive(sysex(11,11,(0,0,*digest('Value',6),0,0,0)))
        b=Binding('speed','Speed',0,10,5)
        h.configure_target(b.wire_identity,b.label,0.5,
                           lambda value: str(b.from_normalized(value)))
        self.assertFalse(h.mapped)
        h.receive(sysex(11,11,(0,0,*digest('Value',6),0,0,0)))
        self.assertFalse(h.mapped)
        h.receive(sysex(11,11,(0,0,*digest(b.wire_identity,6),0,0,0)))
        self.assertTrue(h.mapped)
        self.assertEqual(sent[-4][9:15],digest(b.wire_identity,6))
        self.assertIn(b'5.0',bytes(sent[-1]))

    def test_suspended_target_ignores_mapping_and_input(self):
        sent, assigned = [], []
        h=Host(sent.append,assigned.append)
        h.start()
        h.receive(sysex(10,12))
        h.receive(sysex(11,1,(0,)))
        h.enabled=False
        before=len(sent)
        h.receive(sysex(11,11,(0,0,*digest('Value',6),0,0,0)))
        h.receive((191,12,64))
        h.receive((191,44,0))
        h.receive(sysex(11,9,(1,)))
        self.assertFalse(h.offer_parameter())
        self.assertFalse(h.mapped)
        self.assertEqual(assigned,[])
        self.assertEqual(len(sent),before)

    def test_target_switch_rejected_during_learn_or_touch(self):
        h=Host(lambda message:None,lambda value:None)
        for flag in ['learning','touched']:
            setattr(h,flag,True)
            with self.assertRaises(ValueError):
                h.configure_target('speed','Speed',0.5,str)
            self.assertEqual(h.target_id,'Value')
            setattr(h,flag,False)


if __name__=='__main__':
    unittest.main()
