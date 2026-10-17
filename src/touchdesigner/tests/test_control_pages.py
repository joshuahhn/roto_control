"""Normal Plugin control pages recall by parameter identity, not guessed page numbers."""
import tests  # Shared paths for direct unittest discovery.
import copy
import unittest
from types import SimpleNamespace
import test_layouts
import test_assignment
import test_menu
from test_bound_parameter import BoundParameter
from protocol import SysExCommand,digest

class ControlPageTests(unittest.TestCase):
    def fixture(self):
        e,m,a=test_layouts.LayoutTests().fixture()
        b=test_assignment.AssignmentTests().parameter(name='Amount')
        oldop=e.ownerComp.op
        e.ownerComp.op=lambda name:SimpleNamespace(par=SimpleNamespace(Speed=a,Amount=b),valid=True) if name=='../master' else oldop(name)
        m.capture(force=True)
        return e,m,a,b

    def ack(self,target):
        return SysExCommand.CONTROL_MAPPED.message((target['index']>>7,target['index']&127,*digest(target['identity'],6),int(target['kind']=='button'),target['slot']-1,0))

    def receive(self,e,m,packet):
        if not m.receive(packet):e._host.receive(packet)
        m.acknowledge()

    def test_page_two_learn_preserves_first_and_both_recall(self):
        e,m,a,b=self.fixture();first=copy.deepcopy(m.record()['targets'][0])
        self.receive(e,m,SysExCommand.ROTO_PAGE_RIGHT.message())
        e.AssignParameter('knob',1,b,_wire_index=129,_hardware_mapped=True);m.capture(force=True)
        second=copy.deepcopy(m.record()['targets'][0])
        self.assertEqual({t['id'] for t in e.ownerComp.fetch('page_targets',[])},{first['id'],second['id']})
        self.receive(e,m,SysExCommand.ROTO_PAGE_LEFT.message());self.receive(e,m,self.ack(first))
        self.assertEqual(e.GetControlState()['parameter'],'Speed');self.assertTrue(e.GetControlState()['mapped'])
        self.receive(e,m,SysExCommand.ROTO_PAGE_RIGHT.message());self.receive(e,m,self.ack(second))
        self.assertEqual(e.GetControlState()['parameter'],'Amount');self.assertTrue(e.GetControlState()['mapped'])
        self.assertNotIn(first['id'],e.ownerComp.fetch('removed_controls',[]))

    def test_empty_page_disables_old_input_and_unknown_ack(self):
        e,m,a,b=self.fixture();first=copy.deepcopy(m.record()['targets'][0]);self.receive(e,m,self.ack(first))
        value=a.eval();self.receive(e,m,SysExCommand.ROTO_PAGE_RIGHT.message())
        e._host.receive((191,12,127));e._host.receive((191,44,127))
        self.assertEqual(a.eval(),value);self.assertEqual(e.GetControlStates(),[])
        bad=list(self.ack(first));bad[9]^=1;self.receive(e,m,bad)
        self.assertEqual(e.GetControlStates(),[])

    def test_clear_on_second_page_does_not_delete_first(self):
        e,m,a,b=self.fixture();first=copy.deepcopy(m.record()['targets'][0])
        self.receive(e,m,SysExCommand.ROTO_PAGE_RIGHT.message());e.AssignParameter('knob',1,b,_wire_index=129,_hardware_mapped=True);m.capture(force=True)
        second=copy.deepcopy(m.record()['targets'][0]);e.RemoveAllControls();m.capture(force=True)
        self.receive(e,m,SysExCommand.ROTO_PAGE_LEFT.message());self.receive(e,m,self.ack(first))
        self.assertEqual(e.GetControlState()['id'],first['id'])
        self.assertNotIn(second['id'],[t['id'] for t in e.ownerComp.fetch('page_targets')])

    def test_track_switch_restores_library_without_leaking_other_track(self):
        e,m,a,b=self.fixture();first=copy.deepcopy(m.record()['targets'][0]);t=m.track()['id']
        self.receive(e,m,SysExCommand.ROTO_PAGE_RIGHT.message());e.AssignParameter('knob',1,b,_wire_index=129,_hardware_mapped=True);m.capture(force=True)
        other=m.create_track('custom','OTHER');m.select_track('custom',other)
        self.receive(e,m,self.ack(first));self.assertEqual(e.GetControlStates(),[])
        m.select_track('custom',t);m.restore();self.receive(e,m,SysExCommand.ROTO_PAGE_LEFT.message());self.receive(e,m,self.ack(first))
        self.assertEqual(e.GetControlState()['id'],first['id'])

    def test_freelearn_allocates_index_across_inactive_page_targets(self):
        from free_learn import FreeLearner
        e,m,a,b=self.fixture();a.owner.name=b.owner.name='master'
        e.AssignParameter('knob',1,a,_id='first',_wire_index=128,_hardware_mapped=True);m.capture(force=True)
        self.receive(e,m,SysExCommand.ROTO_PAGE_RIGHT.message())
        l=FreeLearner(e);e._free_learner=l;l.active=True;e._host.learning=True
        self.assertTrue(l.offer(b));self.assertEqual(l.pending['template'].index,129)
        wire=l.pending['template'];packet=SysExCommand.CONTROL_MAPPED.message((wire.index>>7,wire.index&127,*digest(wire.target_id,6),0,0,0))
        self.assertFalse(l.receive(packet));e._host.receive(packet);m.capture(force=True)
        self.assertEqual({t['index'] for t in e.ownerComp.fetch('page_targets')},{0,128,129})

    def test_reconnect_drops_old_page_slots_and_recalls_other_page(self):
        e,m,a,b=self.fixture();first=copy.deepcopy(m.record()['targets'][0])
        self.receive(e,m,SysExCommand.ROTO_PAGE_RIGHT.message());e.AssignParameter('knob',1,b,_wire_index=129,_hardware_mapped=True);m.capture(force=True)
        self.receive(e,m,SysExCommand.SET_PLUGIN_MODE.message((0,)))
        self.assertEqual(e.GetControlStates(),[])
        self.receive(e,m,self.ack(first));self.assertEqual(e.GetControlState()['id'],first['id'])

    def test_reconnect_recalls_toggle_with_native_menu_fields_without_writing(self):
        class RecordingToggle(BoundParameter):
            @BoundParameter.val.setter
            def val(self,value):
                self.writes.append(value)
                BoundParameter.val.fset(self,value)
        e,m,a,b=self.fixture();p=RecordingToggle('Toggle');p.name='Enabled'
        p.normMax=p.max=1;p._value=0;p.writes=[]
        p.menuNames=['off','on'];p.menuLabels=['Off','On']
        oldop=e.ownerComp.op
        e.ownerComp.op=lambda name:SimpleNamespace(par=SimpleNamespace(Speed=a,Amount=b,Enabled=p),valid=True) if name=='../master' else oldop(name)
        state=e.AssignParameter('button',1,p,_wire_index=130,_hardware_mapped=True);m.capture(force=True)
        saved=copy.deepcopy(e.ownerComp.fetch('page_targets'))
        target=next(t for t in saved if t['id']==state['id'])
        self.assertEqual((target['menu_names'],target['menu_labels']),([],[]))
        sent=[];e._host.send=sent.append;p._value=1
        self.receive(e,m,SysExCommand.SET_PLUGIN_MODE.message((0,)))
        self.assertEqual(e.GetControlStates(),[])
        bad=list(self.ack(target));bad[9]^=1;self.receive(e,m,bad)
        self.assertEqual(e.GetControlStates(),[])
        self.receive(e,m,self.ack(target))
        recalled=e.GetControlStates()
        self.assertEqual(len(recalled),1,e._last_error)
        self.assertEqual((recalled[0]['id'],recalled[0]['kind'],recalled[0]['slot'],recalled[0]['mode']),
                         (target['id'],'button',1,'toggle'))
        self.assertTrue(recalled[0]['mapped']);self.assertTrue(recalled[0]['valid'])
        self.assertEqual(recalled[0]['value'],1)
        wire=e._host.controls['button',1]
        self.assertEqual((wire.index,wire.target_id),(target['index'],target['identity']))
        self.assertEqual(e.ownerComp.fetch('page_targets'),saved)
        self.assertEqual(p.writes,[]);self.assertEqual(p.eval(),1)
        self.assertFalse(any(SysExCommand.identify(packet) is SysExCommand.UNMAP_CTL for packet in sent))

    def test_reconnect_rejects_changed_menu_names_or_labels(self):
        for field in ('menuNames','menuLabels'):
            with self.subTest(field=field):
                e,m,a,b=self.fixture();p=test_menu.menu();p.name='Mode'
                oldop=e.ownerComp.op
                e.ownerComp.op=lambda name:SimpleNamespace(par=SimpleNamespace(Speed=a,Amount=b,Mode=p),valid=True) if name=='../master' else oldop(name)
                state=e.AssignParameter('knob',2,p,_wire_index=130,_hardware_mapped=True);m.capture(force=True)
                saved=copy.deepcopy(e.ownerComp.fetch('page_targets'))
                target=next(t for t in saved if t['id']==state['id'])
                self.receive(e,m,SysExCommand.SET_PLUGIN_MODE.message((0,)))
                getattr(p,field)[-1]='Changed'
                self.receive(e,m,self.ack(target))
                self.assertEqual(e.GetControlStates(),[])
                self.assertEqual(e._last_error,'Control page Menu choices changed; re-LEARN required')
                self.assertEqual(e.ownerComp.fetch('page_targets'),saved)
                self.assertEqual(p.eval(),'beta')

    def test_reconnect_rejects_menu_replaced_by_numeric_until_relearn(self):
        e,m,a,b=self.fixture();p=test_menu.menu();p.name='Mode'
        parameters=SimpleNamespace(Speed=a,Amount=b,Mode=p)
        oldop=e.ownerComp.op
        e.ownerComp.op=lambda name:SimpleNamespace(par=parameters,valid=True) if name=='../master' else oldop(name)
        state=e.AssignParameter('knob',2,p,_wire_index=130,_hardware_mapped=True);m.capture(force=True)
        saved=copy.deepcopy(e.ownerComp.fetch('page_targets'))
        target=next(t for t in saved if t['id']==state['id'])
        self.assertTrue(target['menu_names']);self.assertTrue(target['menu_labels'])
        self.receive(e,m,SysExCommand.SET_PLUGIN_MODE.message((0,)))
        replacement=test_assignment.AssignmentTests().parameter('Float','Mode')
        parameters.Mode=replacement
        value=replacement.eval()
        self.receive(e,m,self.ack(target))
        self.assertEqual(e.GetControlStates(),[])
        self.assertEqual(e._last_error,'Control page Menu choices changed; re-LEARN required')
        self.assertEqual(e.ownerComp.fetch('page_targets'),saved)
        self.assertEqual(replacement.eval(),value)
        state=e.AssignParameter('knob',2,replacement)
        wire=e._host.controls['knob',2]
        self.assertNotEqual(wire.target_id,target['identity'])
        self.receive(e,m,self.ack(target))
        self.assertFalse(e.GetControlState(state['id'])['mapped'])
        self.receive(e,m,SysExCommand.SET_DEVICE_LEARN.message((1,)))
        self.assertTrue(e.Offerparameter(state['id']))
        self.receive(e,m,SysExCommand.CONTROL_MAPPED.message((wire.index>>7,wire.index&127,*digest(wire.target_id,6),0,1,0)))
        self.assertTrue(e.GetControlState(state['id'])['mapped'])
        self.assertEqual(replacement.eval(),value)

    def test_new_mapping_same_slot_without_arrow_retains_old_definition(self):
        e,m,a,b=self.fixture();first=copy.deepcopy(m.record()['targets'][0])
        e.AssignParameter('knob',1,b,_wire_index=129,_hardware_mapped=True);m.capture(force=True)
        self.assertIn(first['id'],[t['id'] for t in e.ownerComp.fetch('page_targets')])
        self.receive(e,m,SysExCommand.ROTO_PAGE_LEFT.message());self.receive(e,m,self.ack(first))
        self.assertEqual(e.GetControlState()['id'],first['id'])

    def test_eight_pages_128_controls_preserved_and_recalled(self):
        e,m,a,b=self.fixture();e.RemoveAllControls();m.capture(force=True)
        parameters={}
        oldop=e.ownerComp.op
        e.ownerComp.op=lambda name:SimpleNamespace(par=SimpleNamespace(**parameters),valid=True) if name=='../master' else oldop(name)
        pages=[]
        for page in range(8):
            self.receive(e,m,SysExCommand.ROTO_PAGE_RIGHT.message())
            for kind in ('knob','button'):
                for slot in range(1,9):
                    name=f'P{page}_{kind}{slot}'
                    p=test_assignment.AssignmentTests().parameter('Float' if kind=='knob' else 'Toggle',name)
                    parameters[name]=p
                    e.AssignParameter(kind,slot,p,_wire_index=128+page*16+(0 if kind=='knob' else 8)+slot-1,_hardware_mapped=True)
            m.capture(force=True);pages.append(copy.deepcopy(m.record()['targets']))
        self.assertEqual(len(e.ownerComp.fetch('page_targets')),128)
        for page in reversed(pages):
            self.receive(e,m,SysExCommand.ROTO_PAGE_LEFT.message())
            for target in page:self.receive(e,m,self.ack(target))
            self.assertEqual({x['id'] for x in e.GetControlStates()},{x['id'] for x in page})
            self.assertTrue(all(x['mapped'] for x in e.GetControlStates()))
        self.assertEqual(len(e.ownerComp.fetch('page_targets')),128)
