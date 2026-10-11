"""Normal Plugin control pages recall by parameter identity, not guessed page numbers."""
import copy
import unittest
from types import SimpleNamespace
import test_layouts
import test_assignment
from protocol import sysex,digest

class ControlPageTests(unittest.TestCase):
    def fixture(self):
        e,m,a=test_layouts.LayoutTests().fixture()
        b=test_assignment.AssignmentTests().parameter(name='Amount')
        oldop=e.ownerComp.op
        e.ownerComp.op=lambda name:SimpleNamespace(par=SimpleNamespace(Speed=a,Amount=b),valid=True) if name=='../master' else oldop(name)
        m.capture(force=True)
        return e,m,a,b

    def ack(self,target):
        return sysex(11,11,(target['index']>>7,target['index']&127,*digest(target['identity'],6),int(target['kind']=='button'),target['slot']-1,0))

    def receive(self,e,m,packet):
        if not m.receive(packet):e._host.receive(packet)
        m.acknowledge()

    def test_page_two_learn_preserves_first_and_both_recall(self):
        e,m,a,b=self.fixture();first=copy.deepcopy(m.record()['targets'][0])
        self.receive(e,m,sysex(10,21))
        e.AssignParameter('knob',1,b,_wire_index=129,_hardware_mapped=True);m.capture(force=True)
        second=copy.deepcopy(m.record()['targets'][0])
        self.assertEqual({t['id'] for t in e.ownerComp.fetch('page_targets',[])},{first['id'],second['id']})
        self.receive(e,m,sysex(10,20));self.receive(e,m,self.ack(first))
        self.assertEqual(e.GetControlState()['parameter'],'Speed');self.assertTrue(e.GetControlState()['mapped'])
        self.receive(e,m,sysex(10,21));self.receive(e,m,self.ack(second))
        self.assertEqual(e.GetControlState()['parameter'],'Amount');self.assertTrue(e.GetControlState()['mapped'])
        self.assertNotIn(first['id'],e.ownerComp.fetch('removed_controls',[]))

    def test_empty_page_disables_old_input_and_unknown_ack(self):
        e,m,a,b=self.fixture();first=copy.deepcopy(m.record()['targets'][0]);self.receive(e,m,self.ack(first))
        value=a.eval();self.receive(e,m,sysex(10,21))
        e._host.receive((191,12,127));e._host.receive((191,44,127))
        self.assertEqual(a.eval(),value);self.assertEqual(e.GetControlStates(),[])
        bad=list(self.ack(first));bad[9]^=1;self.receive(e,m,bad)
        self.assertEqual(e.GetControlStates(),[])

    def test_clear_on_second_page_does_not_delete_first(self):
        e,m,a,b=self.fixture();first=copy.deepcopy(m.record()['targets'][0])
        self.receive(e,m,sysex(10,21));e.AssignParameter('knob',1,b,_wire_index=129,_hardware_mapped=True);m.capture(force=True)
        second=copy.deepcopy(m.record()['targets'][0]);e.RemoveAllControls();m.capture(force=True)
        self.receive(e,m,sysex(10,20));self.receive(e,m,self.ack(first))
        self.assertEqual(e.GetControlState()['id'],first['id'])
        self.assertNotIn(second['id'],[t['id'] for t in e.ownerComp.fetch('page_targets')])

    def test_track_switch_restores_library_without_leaking_other_track(self):
        e,m,a,b=self.fixture();first=copy.deepcopy(m.record()['targets'][0]);t=m.track()['id']
        self.receive(e,m,sysex(10,21));e.AssignParameter('knob',1,b,_wire_index=129,_hardware_mapped=True);m.capture(force=True)
        other=m.create_track('custom','OTHER');m.select_track('custom',other)
        self.receive(e,m,self.ack(first));self.assertEqual(e.GetControlStates(),[])
        m.select_track('custom',t);m.restore();self.receive(e,m,sysex(10,20));self.receive(e,m,self.ack(first))
        self.assertEqual(e.GetControlState()['id'],first['id'])

    def test_freelearn_allocates_index_across_inactive_page_targets(self):
        from free_learn import FreeLearner
        e,m,a,b=self.fixture();a.owner.name=b.owner.name='master'
        e.AssignParameter('knob',1,a,_id='first',_wire_index=128,_hardware_mapped=True);m.capture(force=True)
        self.receive(e,m,sysex(10,21))
        l=FreeLearner(e);e._free_learner=l;l.active=True;e._host.learning=True
        self.assertTrue(l.offer(b));self.assertEqual(l.pending['template'].index,129)
        wire=l.pending['template'];packet=sysex(11,11,(wire.index>>7,wire.index&127,*digest(wire.target_id,6),0,0,0))
        self.assertFalse(l.receive(packet));e._host.receive(packet);m.capture(force=True)
        self.assertEqual({t['index'] for t in e.ownerComp.fetch('page_targets')},{0,128,129})

    def test_reconnect_drops_old_page_slots_and_recalls_other_page(self):
        e,m,a,b=self.fixture();first=copy.deepcopy(m.record()['targets'][0])
        self.receive(e,m,sysex(10,21));e.AssignParameter('knob',1,b,_wire_index=129,_hardware_mapped=True);m.capture(force=True)
        self.receive(e,m,sysex(11,1,(0,)))
        self.assertEqual(e.GetControlStates(),[])
        self.receive(e,m,self.ack(first));self.assertEqual(e.GetControlState()['id'],first['id'])

    def test_new_mapping_same_slot_without_arrow_retains_old_definition(self):
        e,m,a,b=self.fixture();first=copy.deepcopy(m.record()['targets'][0])
        e.AssignParameter('knob',1,b,_wire_index=129,_hardware_mapped=True);m.capture(force=True)
        self.assertIn(first['id'],[t['id'] for t in e.ownerComp.fetch('page_targets')])
        self.receive(e,m,sysex(10,20));self.receive(e,m,self.ack(first))
        self.assertEqual(e.GetControlState()['id'],first['id'])

    def test_eight_pages_128_controls_preserved_and_recalled(self):
        e,m,a,b=self.fixture();e.RemoveAllControls();m.capture(force=True)
        parameters={}
        oldop=e.ownerComp.op
        e.ownerComp.op=lambda name:SimpleNamespace(par=SimpleNamespace(**parameters),valid=True) if name=='../master' else oldop(name)
        pages=[]
        for page in range(8):
            self.receive(e,m,sysex(10,21))
            for kind in ('knob','button'):
                for slot in range(1,9):
                    name=f'P{page}_{kind}{slot}'
                    p=test_assignment.AssignmentTests().parameter('Float' if kind=='knob' else 'Toggle',name)
                    parameters[name]=p
                    e.AssignParameter(kind,slot,p,_wire_index=128+page*16+(0 if kind=='knob' else 8)+slot-1,_hardware_mapped=True)
            m.capture(force=True);pages.append(copy.deepcopy(m.record()['targets']))
        self.assertEqual(len(e.ownerComp.fetch('page_targets')),128)
        for page in reversed(pages):
            self.receive(e,m,sysex(10,20))
            for target in page:self.receive(e,m,self.ack(target))
            self.assertEqual({x['id'] for x in e.GetControlStates()},{x['id'] for x in page})
            self.assertTrue(all(x['mapped'] for x in e.GetControlStates()))
        self.assertEqual(len(e.ownerComp.fetch('page_targets')),128)
