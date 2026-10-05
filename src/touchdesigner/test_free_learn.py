"""Unregistered slider -> offer -> actual hardware slot -> persistent mapping."""
from types import SimpleNamespace
import unittest
import test_assignment
import collection_protocol
import controls
from free_learn import FreeLearner
from protocol import sysex,digest

class FreeLearnTests(unittest.TestCase):
    def fixture(self):
        ext=test_assignment.AssignmentTests().fixture()
        sent=[];ext._host.send=sent.append
        ext._host.connected=ext._host.plugin=ext._host.learning=True
        old_op=ext.ownerComp.op
        inspector=SimpleNamespace(store=lambda *args:None)
        ext.ownerComp.op=lambda name:inspector if name=='inspector' else old_op(name)
        learner=FreeLearner(ext);learner.active=True;ext._free_learner=learner
        return ext,learner,sent

    def parameter(self):
        parameter=test_assignment.AssignmentTests().parameter()
        parameter.owner.name='master'
        return parameter

    def ack(self,learner,kind=0,slot=3):
        t=learner.pending['template']
        return sysex(11,11,(t.index>>7,t.index&127,*digest(t.target_id,6),kind,slot-1,0))

    def test_unregistered_parameter_is_offered_then_committed_to_hardware_slot(self):
        ext,learner,sent=self.fixture();p=self.parameter();p.val=6
        learner.changes([(p,5)])
        self.assertIsNotNone(learner.pending)
        self.assertEqual(len(sent),1);self.assertEqual(sent[0][5:7],(11,10))
        self.assertNotIn(('knob',3),ext._collection.bindings)
        packet=self.ack(learner)
        self.assertFalse(learner.receive(packet));ext._host.receive(packet)
        state=next(s for s in ext.GetControlStates() if s['slot']==3 and s['kind']=='knob')
        self.assertTrue(state['mapped']);self.assertEqual(state['parameter'],'Speed')
        self.assertEqual(ext._host.controls['knob',3].index,128)
        self.assertEqual(ext.ownerComp.fetch('parameter_assignments')[0]['index'],128)

    def test_slider_drag_does_not_offer_repeatedly_and_wrong_ack_cannot_commit(self):
        ext,learner,sent=self.fixture();p=self.parameter();p.val=6
        learner.changes([(p,5)]);p.val=7;learner.changes([(p,6)])
        self.assertEqual(len(sent),1)
        packet=list(self.ack(learner));packet[9]=(packet[9]+1)%128
        self.assertFalse(learner.receive(packet))
        self.assertIsNotNone(learner.pending)
        self.assertNotIn(('knob',3),ext._collection.bindings)

    def test_software_value_write_and_inactive_changes_do_not_offer(self):
        ext,learner,sent=self.fixture();p=self.parameter()
        # A UI assignment registers the target, then SetValue must not learn it.
        state=ext.AssignParameter('knob',3,p)
        ext.SetValue(6,id=state['id']);learner.changes([(p,5)])
        self.assertEqual(sent,[])
        learner.active=False;p.val=7;learner.changes([(p,6)])
        self.assertEqual(sent,[])

    def test_learn_mode_button_selection_is_not_a_business_pulse(self):
        ext,learner,sent=self.fixture()
        target=ext._host.controls['button',8];target.mapped=True
        events=[];ext._collection.bindings['button',8].on_change=events.append
        ext._host.receive((191,27,127));ext._host.receive((191,27,0))
        self.assertEqual(events,[])

    def test_pulse_offer_does_not_execute_action_and_uses_ack_button_slot(self):
        ext,learner,sent=self.fixture()
        parameter=test_assignment.AssignmentTests().parameter('Pulse','Reset')
        parameter.owner.name='master'
        learner.pulse(parameter)
        self.assertEqual(parameter.pulses,0)
        packet=self.ack(learner,kind=1,slot=5)
        learner.receive(packet);ext._host.receive(packet)
        state=next(s for s in ext.GetControlStates() if s['slot']==5 and s['kind']=='button')
        self.assertEqual((state['mode'],state['button_type']),('pulse','push'))
        self.assertTrue(state['mapped'])

    def test_wrong_control_type_cannot_leave_old_mapping_active(self):
        ext,learner,sent=self.fixture();parameter=self.parameter()
        ext._host.controls['button',8].mapped=True
        learner.offer(parameter)
        self.assertTrue(learner.receive(self.ack(learner,kind=1,slot=8)))
        self.assertFalse(ext._host.controls['button',8].mapped)
        self.assertIsNone(learner.pending)

    def test_callback_ack_before_learn_off_does_not_unmap_new_hardware_mapping(self):
        ext,learner,sent=self.fixture();p=self.parameter();p.val=6
        self.assertTrue(learner.offer(p));packet=self.ack(learner,slot=2)
        ext._host.controls['knob',2].mapped=True
        ext._host.learning=False;learner.active=False;sent.clear()
        learner.receive(packet);ext._host.receive(packet)
        self.assertFalse(any(m[0]==240 and m[5:7]==(11,14) for m in sent))
        self.assertTrue(ext._host.controls['knob',2].mapped)

if __name__=='__main__':unittest.main()
