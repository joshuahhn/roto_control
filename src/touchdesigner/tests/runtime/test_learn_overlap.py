"""Delayed hardware acknowledgements must retain Lowthresh / Mask offers."""
import unittest
from unittest.mock import patch
import test_free_learn
import test_assignment
from protocol import sysex,digest


class LearnOverlapTests(unittest.TestCase):
    def test_lowthresh_ack_survives_later_parameter_offer(self):
        e,f,sent=test_free_learn.FreeLearnTests().fixture()
        low=test_assignment.AssignmentTests().parameter('Float','Lowthresh');low.owner.name='pixelSortV3'
        high=test_assignment.AssignmentTests().parameter('Float','Highthresh');high.owner.name='pixelSortV3'
        self.assertTrue(f.offer(low));t=f.pending['template']
        packet=sysex(11,11,(t.index>>7,t.index&127,*digest(t.target_id,6),0,1,0))
        self.assertTrue(f.offer(high))
        self.assertNotEqual(t.index,f.pending['template'].index)
        f.receive(packet);e._host.receive(packet)
        self.assertTrue(any(s['kind']=='knob' and s['slot']==2 and s['parameter']=='Lowthresh' and s['mapped'] for s in e.GetControlStates()))
        packet=test_free_learn.FreeLearnTests().ack(f,slot=3)
        f.receive(packet);e._host.receive(packet)
        self.assertTrue(any(s['slot']==3 and s['parameter']=='Highthresh' and s['mapped'] for s in e.GetControlStates()))

    def test_mask_button_ack_survives_later_parameter_offer(self):
        e,f,sent=test_free_learn.FreeLearnTests().fixture()
        mask=test_assignment.AssignmentTests().parameter('Menu','Masksource');mask.owner.name='pixelSortV3'
        mask.menuNames=['source','control'];mask.menuLabels=['Source (Input 1)','Control (Input 2)'];mask.val='source'
        mix=test_assignment.AssignmentTests().parameter('Float','Mix');mix.owner.name='pixelSortV3'
        # The real capture has no selection CC before the edit: the selected
        # button kind is first reported in this delayed ACK on LEARN exit.
        self.assertTrue(f.offer(mask));t=f.pending['template']
        packet=sysex(11,11,(t.index>>7,t.index&127,*digest(t.target_id,6),1,0,0))
        self.assertTrue(f.offer(mix))
        f.receive(packet);e._host.receive(packet)
        self.assertTrue(any(s['kind']=='button' and s['slot']==1 and s['parameter']=='Masksource' and s['mapped'] and s['mode']=='cycle' for s in e.GetControlStates()))
        now=[1.0];e._host.clock=lambda:now[0]
        e._host.learning=False;e._host.receive((191,20,127))
        self.assertEqual(mask.eval(),'control')
        now[0]+=1
        e._host.receive((191,20,0))
        self.assertEqual(mask.eval(),'source')  # toggle TYPE cycles on both edges

    def test_context_or_session_reset_cancels_all_offers(self):
        e,f,sent=test_free_learn.FreeLearnTests().fixture()
        f.offer(test_assignment.AssignmentTests().parameter('Float','Lowthresh'))
        first=test_free_learn.FreeLearnTests().ack(f,slot=2)
        f.offer(test_assignment.AssignmentTests().parameter('Float','Highthresh'))
        second=test_free_learn.FreeLearnTests().ack(f,slot=3)
        f.pending=None  # existing Layout/page/fence/Disconnect invalidation contract
        for packet in (first,second):
            self.assertFalse(f.receive(packet))
        self.assertFalse(any(s['parameter'] in ('Lowthresh','Highthresh') for s in e.GetControlStates()))

    def test_expired_offer_cannot_commit_after_new_offer(self):
        e,f,sent=test_free_learn.FreeLearnTests().fixture()
        with patch('free_learn.time.monotonic',return_value=1):
            f.offer(test_assignment.AssignmentTests().parameter('Float','Lowthresh'))
            packet=test_free_learn.FreeLearnTests().ack(f,slot=2)
        with patch('free_learn.time.monotonic',return_value=32):
            f.offer(test_assignment.AssignmentTests().parameter('Float','Highthresh'))
            self.assertFalse(f.receive(packet))
        self.assertFalse(any(s['parameter']=='Lowthresh' for s in e.GetControlStates()))

    def test_reoffering_pending_parameter_preserves_identity(self):
        e,f,sent=test_free_learn.FreeLearnTests().fixture()
        low=test_assignment.AssignmentTests().parameter('Float','Lowthresh')
        f.offer(low);first=f.pending['template']
        f.offer(test_assignment.AssignmentTests().parameter('Float','Highthresh'))
        f.offer(low);second=f.pending['template']
        self.assertEqual((first.index,first.target_id),(second.index,second.target_id))

    def test_menu_options_changed_before_ack_cannot_commit(self):
        e,f,sent=test_free_learn.FreeLearnTests().fixture()
        mask=test_assignment.AssignmentTests().parameter('Menu','Masksource');mask.owner.name='pixelSortV3'
        mask.menuNames=['source','control'];mask.menuLabels=['Source','Control'];mask.val='source'
        f.offer(mask);packet=test_free_learn.FreeLearnTests().ack(f,kind=1,slot=1)
        mask.menuLabels=['Changed','Control']
        self.assertTrue(f.receive(packet))
        self.assertFalse(any(s['parameter']=='Masksource' for s in e.GetControlStates()))

    def test_offer_limit_preserves_earlier_acknowledgements(self):
        e,f,sent=test_free_learn.FreeLearnTests().fixture()
        for i in range(128):
            p=test_assignment.AssignmentTests().parameter('Float','Parameter'+str(i));p.owner.name='pixelSortV3'
            self.assertTrue(f.offer(p))
            if i==0:first=test_free_learn.FreeLearnTests().ack(f,slot=2)
        p=test_assignment.AssignmentTests().parameter('Float','Overflow');p.owner.name='pixelSortV3'
        self.assertFalse(f.offer(p))
        f.receive(first);e._host.receive(first)
        self.assertTrue(any(s['slot']==2 and s['parameter']=='Parameter0' and s['mapped'] for s in e.GetControlStates()))
