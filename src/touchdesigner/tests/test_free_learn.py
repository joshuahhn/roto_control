"""Unregistered slider -> offer -> actual hardware slot -> persistent mapping."""
import tests  # Shared paths for direct unittest discovery.
from types import SimpleNamespace
import unittest
from unittest.mock import patch
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

    def test_range_changed_before_ack_preserves_registration(self):
        ext, learner, sent = self.fixture()
        old = ext.GetControlCatalog()
        original = ext._collection.bindings['knob', 2]
        parameter = self.parameter()
        learner.offer(parameter)
        packet = self.ack(learner, slot=2)
        parameter.normMax = parameter.max = 20
        self.assertTrue(learner.receive(packet))
        self.assertIs(ext._collection.bindings['knob', 2], original)
        self.assertEqual(ext.GetControlCatalog(), old)
        self.assertFalse(ext._host.controls['knob', 2].mapped)

    def test_equal_value_offer_uses_selected_parameter_identity(self):
        from test_bound_parameter import BoundParameter
        class NativeEqualPar(BoundParameter):
            def __eq__(self, other):
                return isinstance(other, BoundParameter) and self.eval() == other.eval()
        ext, learner, sent = self.fixture()
        old = NativeEqualPar(); old.owner.name = 'master'
        selected = NativeEqualPar(); selected.owner.path = '/selected'; selected.owner.name = 'selected'
        selected.name = 'Other'
        ext.AssignParameter('knob', 3, old)
        old_id = ext._collection.bindings['knob', 3].id
        self.assertTrue(learner.offer(selected))
        self.assertNotEqual(learner.pending['binding'].id, old_id)
        packet = self.ack(learner, slot=3)
        self.assertFalse(learner.receive(packet))
        self.assertIs(ext._collection.bindings['knob', 3].parameter, selected)

    def test_failed_commit_restores_registration_and_saved_assignment(self):
        ext, learner, sent = self.fixture()
        original_parameter = self.parameter()
        original = ext.AssignParameter('knob', 2, original_parameter)
        old_binding = ext._collection.bindings['knob', 2]
        old_assignments = list(ext.ownerComp.fetch('parameter_assignments'))
        selected = self.parameter(); selected.name = 'Other'
        learner.offer(selected)
        packet = self.ack(learner, slot=2)
        store = ext.ownerComp.store
        failed = False
        def fail_once(key, value):
            nonlocal failed
            if key == 'removed_controls' and not failed:
                failed = True
                raise RuntimeError('injected persistence failure')
            return store(key, value)
        ext.ownerComp.store = fail_once
        self.assertTrue(learner.receive(packet))
        self.assertIs(ext._collection.bindings['knob', 2], old_binding)
        self.assertEqual(ext.ownerComp.fetch('parameter_assignments'), old_assignments)
        self.assertEqual(ext.GetControlState(original['id'])['parameter'], 'Speed')
        self.assertFalse(ext._host.controls['knob', 2].mapped)

    def test_equal_valued_pulse_does_not_suppress_another_destination(self):
        from test_bound_parameter import BoundParameter
        class NativeEqualPar(BoundParameter):
            def __eq__(self, other):
                return isinstance(other, BoundParameter) and self.eval() == other.eval()
        ext, learner, sent = self.fixture()
        old = NativeEqualPar('Pulse'); old.name = 'Reset'; old.owner.name = 'master'
        selected = NativeEqualPar('Pulse'); selected.name = 'Other'; selected.owner.name = 'master'
        ext.AssignParameter('button', 3, old)
        ext._collection.bindings['button', 3].pulse_expected = 1
        learner.pulse(selected)
        self.assertIs(learner.pending['parameter'], selected)

    def test_single_target_callback_ignores_equal_valued_foreign_parameter(self):
        from binding import Binding
        from test_bound_parameter import BoundParameter
        class NativeEqualPar(BoundParameter):
            def __eq__(self, other):
                return isinstance(other, BoundParameter) and self.eval() == other.eval()
            def __ne__(self, other):
                return not self == other
        ext, learner, sent = self.fixture()
        target = NativeEqualPar(); foreign = NativeEqualPar(); foreign.name = 'Other'
        ext._binding = Binding('single', 'Single', 0, 10, 4, parameter=target)
        writes = []; ext.SetValue = writes.append
        ext.onTargetValueChange(foreign, 4)
        self.assertEqual(writes, [])

    def test_style_drift_is_rejected_before_assignment(self):
        ext, learner, sent = self.fixture()
        parameter = self.parameter(); parameter.style = 'Pulse'
        parameter.normMax = parameter.max = 1; parameter._value = 0
        learner.offer(parameter)
        packet = self.ack(learner, kind=1, slot=3)
        parameter.style = 'Toggle'
        calls = []; ext.AssignParameter = lambda *args, **kwargs: calls.append(args)
        self.assertTrue(learner.receive(packet))
        self.assertEqual(calls, [])

    def test_late_failure_restores_watcher_and_manual_controls(self):
        ext, learner, sent = self.fixture()
        ext.ownerComp.par.Value.enable = ext.ownerComp.par.Offerparameter.enable = False
        parameter = self.parameter(); learner.offer(parameter)
        packet = self.ack(learner, slot=1)
        watcher = ext.ownerComp.op('base_targets/watch_knob1')
        watcher.par.active = False; watcher.par.pars = 'Original'
        original_op = watcher.par.op.expr
        failed = False
        def publish():
            nonlocal failed
            if not failed:
                failed = True
                raise RuntimeError('injected late publication failure')
        ext._publish = publish
        self.assertTrue(learner.receive(packet))
        self.assertNotIn(('knob', 1), ext._collection.bindings)
        self.assertFalse(ext.ownerComp.par.Value.enable)
        self.assertFalse(ext.ownerComp.par.Offerparameter.enable)
        self.assertFalse(watcher.par.active)
        self.assertEqual(watcher.par.pars, 'Original')
        self.assertEqual(watcher.par.op.expr, original_op)

    def test_failed_layout_commit_restores_saved_library(self):
        import copy
        ext, learner, sent = self.fixture()
        registry = {'library': [{'id': 'off-page', 'value': 8}]}
        manager = SimpleNamespace(data=copy.deepcopy(registry), legacy=False,
                                  quarantined=False, owner_ready=lambda **kwargs: True)
        def capture(**kwargs):
            manager.data['library'].append({'id': 'captured'})
            ext.ownerComp.store('layout_registry', copy.deepcopy(manager.data))
            ext.ownerComp.store('page_targets', [{'id': 'changed'}])
        manager.capture = capture
        ext._layouts = manager
        ext.ownerComp.store('layout_registry', copy.deepcopy(registry))
        ext.ownerComp.store('page_targets', [{'id': 'off-page', 'index': 129}])
        parameter = self.parameter(); learner.offer(parameter)
        packet = self.ack(learner, slot=2)
        store = ext.ownerComp.store
        failed = False
        def fail_once(key, value):
            nonlocal failed
            if key == 'removed_controls' and not failed:
                failed = True
                raise RuntimeError('injected commit failure')
            return store(key, value)
        ext.ownerComp.store = fail_once
        self.assertTrue(learner.receive(packet))
        self.assertEqual(manager.data, registry)
        self.assertEqual(ext.ownerComp.fetch('layout_registry'), registry)
        self.assertEqual(ext.ownerComp.fetch('page_targets'), [{'id': 'off-page', 'index': 129}])

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

    def test_free_offer_matches_registered_metadata_without_target_writes(self):
        for style,kind in (('Float','knob'),('Toggle','button'),('Pulse','button'),
                           ('Menu','knob'),('Menu','button')):
            with self.subTest(style=style,kind=kind):
                ext,learner,sent=self.fixture()
                parameter=test_assignment.AssignmentTests().parameter(style,'Offered')
                parameter.owner.name='master'
                if style=='Menu':
                    parameter.menuNames=['alpha','beta','gamma']
                    parameter.menuLabels=['Alpha','Beta','Gamma'];parameter.val='beta'
                learner.selected_kind=kind
                before=parameter.eval();pulses=getattr(parameter,'pulses',0)
                read=type(parameter).val.fget
                with patch.object(type(parameter),'val',property(read,
                        lambda *args:self.fail('LEARN offer wrote a target parameter'))):
                    self.assertTrue(learner.offer(parameter))
                template=learner.pending['template'];binding=learner.pending['binding']
                c=controls.Controls([dict(kind=kind,slot=1,id=binding.id,parameter=parameter,
                    mode=template.mode,button_type=template.button_type,index=template.index)])
                registered=[]
                h=collection_protocol.CollectionHost(registered.append,lambda *args:None,
                    list(c.specs()),'comparison')
                h.controls[kind,1]._parameter_details()
                self.assertEqual(sent,registered)
                self.assertEqual(parameter.eval(),before)
                self.assertEqual(getattr(parameter,'pulses',0),pulses)

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
