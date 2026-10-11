"""Slot-position Snapshot tests: fake TD/synthetic MIDI, not physical evidence."""
import copy
import json
import unittest
from types import SimpleNamespace as S
import test_action_presets as actions
from test_bound_parameter import BoundParameter
from snapshots import STORE
from export_component import reset_mapping_storage, reset_registration
from protocol import raw_value


class Parameter(BoundParameter):
    def __init__(self, name='Amount', style='Float', value=.4, master=None):
        super().__init__(style, master)
        self.name = self.label = name
        self._value = value
        self.normMin = self.min = 0
        self.normMax = self.max = 1 if style in ('Float', 'Toggle') else 8
        self.owner = S(path='/values/'+name, valid=True, par=S())
        setattr(self.owner.par, name, self)
        self.on_write = None
        self.writes = []
        self.valid = True
        if style == 'Menu':
            self.menuNames = ['alpha', 'beta', 'gamma']
            self.menuLabels = ['Alpha', 'Beta', 'Gamma']

    @BoundParameter.val.setter
    def val(self, value):
        self.writes.append(value)
        if self.mode.name == 'BIND':
            self.bindMaster.val = value
        else:
            self._value = value
        if self.on_write:
            self.on_write(self, value)


class SnapshotTests(unittest.TestCase):
    def test_all_eight_knobs_roundtrip_with_saved_precision_and_no_definition_changes(self):
        e, m, _ = self.fixture()
        pars = [Parameter('K'+str(i), value=i/10+.000000001) for i in range(1, 9)]
        e.BindControls([dict(kind='knob', slot=i, id='k'+str(i), parameter=par)
                        for i, par in enumerate(pars, 1)], group_id='test')
        record = e.SaveSnapshot('Eight')
        m.capture(force=True)
        before = copy.deepcopy(m.record()['targets'])
        for par in pars:
            par._value = .1
        result = e.RecallAction(record['id'])
        self.assertEqual(result['status'], 'succeeded')
        self.assertEqual([p.eval() for p in pars], [i/10+.000000001 for i in range(1, 9)])
        self.assertEqual(m.record()['targets'], before)

    def fixture(self):
        e, m, _, _ = actions.ActionTests().fixture()
        pars = [Parameter(), Parameter('Steps', 'Int', 3),
                Parameter('Enabled', 'Toggle', True), Parameter('Choice', 'Menu', 'beta')]
        specs = [dict(kind='knob', slot=1, id='amount', parameter=pars[0]),
                 dict(kind='knob', slot=2, id='steps', parameter=pars[1]),
                 dict(kind='button', slot=2, id='enabled', parameter=pars[2], mode='toggle'),
                 dict(kind='knob', slot=3, id='choice', parameter=pars[3])]
        e.BindControls(specs, group_id='test')
        return e, m, pars

    def all_slots(self):
        return [('knob', 1), ('knob', 2), ('knob', 3)]

    def save(self, e):
        return e.SaveSnapshot('Clean', self.all_slots())

    def test_knob_styles_roundtrip_excludes_button_values(self):
        e, m, p = self.fixture()
        r = self.save(e)
        self.assertEqual([s['value'] for s in r['entries']], [.4, 3/8, .5])
        for par, value in zip(p, [.9, 7, False, 'gamma']):
            par._value = value
        result = e.RecallAction(r['id'])
        self.assertEqual(result['status'], 'succeeded', result)
        self.assertEqual([par.eval() for par in p], [.4, 3, False, 'beta'])
        self.assertTrue(all(s['verified'] for s in result['entries']))
        self.assertEqual(p[2].writes, [])
        default = e.SaveSnapshot('Knobs')
        self.assertEqual([(s['kind'], s['slot']) for s in default['entries']], [('knob', 1), ('knob', 2), ('knob', 3)])

    def test_replacement_follows_current_slot_and_current_range_not_original_target(self):
        e, m, p = self.fixture()
        r = e.SaveSnapshot('Single', [('knob', 1)])
        blur = Parameter('Blur', value=8)
        blur.normMax = blur.max = 10
        state = e.AssignParameter('knob', 1, blur)
        self.assertEqual(e.RecallAction(r['id'])['status'], 'succeeded')
        self.assertEqual(blur.eval(), 4)
        self.assertEqual(p[0].eval(), .4)
        self.assertEqual(p[0].writes, [])
        self.assertEqual(e.GetSnapshot(r['id'])['entries'][0]['mapping_id'], state['id'])
        self.assertEqual(e._host.controls['knob', 1].value, raw_value(.4)/16383)

    def test_current_page_slots_follow_page_replacement_indices_without_saved_ids(self):
        e, m, p = self.fixture()
        r = e.SaveSnapshot('Page', [('knob', 1)])
        q = Parameter('NextPage', value=.9)
        e.BindControls([dict(kind='knob', slot=1, id='next.page', index=200, parameter=q)], group_id='test')
        self.assertEqual(e.RecallAction(r['id'])['status'], 'succeeded')
        self.assertEqual(q.eval(), .4)
        self.assertEqual(p[0].writes, [])
        entry = r['entries'][0]
        self.assertEqual(set(entry), {'kind', 'slot', 'value'})

    def test_changed_menu_assignment_uses_current_option_position(self):
        e, m, p = self.fixture()
        r = e.SaveSnapshot('Menu', [('knob', 3)])
        q = Parameter('NewChoice', 'Menu', 'red')
        q.menuNames = ['red', 'green', 'blue', 'white', 'black']
        q.menuLabels = list(q.menuNames)
        e.AssignParameter('knob', 3, q)
        self.assertEqual(e.RecallAction(r['id'])['status'], 'succeeded')
        self.assertEqual(q.eval(), 'blue')
        self.assertEqual(p[3].writes, [])

    def test_save_inspect_validate_detached_and_zero_writes(self):
        e, m, p = self.fixture()
        r = self.save(e)
        view = e.GetSnapshot(r['id'])
        view['entries'][0]['value'] = 999
        self.assertEqual(e.GetSnapshot(r['id'])['entries'][0]['value'], .4)
        self.assertEqual(e.ValidateSnapshot(r['id'])['status'], 'succeeded')
        self.assertTrue(all(not par.writes for par in p))
        data = json.loads(json.dumps(e.ownerComp.fetch(STORE), allow_nan=False))
        self.assertEqual(data['version'], 2)
        self.assertNotIn('target_key', json.dumps(data))
        self.assertNotIn('/values', json.dumps(data))

    def test_overwrite_stable_action_mapping_revision_and_no_implicit_overwrite(self):
        e, m, p = self.fixture()
        r = self.save(e)
        state = e.AssignAction(1, r['id'])
        original = e._host.controls['button', 1]
        p[0]._value = .7
        new = e.OverwriteSnapshot(r['id'], expected_revision=1)
        self.assertEqual((new['id'], new['revision']), (r['id'], 2))
        self.assertEqual(new['entries'][0]['value'], .7)
        self.assertIs(e._host.controls['button', 1], original)
        self.assertEqual(e.GetControlState(state['id'])['action_id'], r['id'])
        with self.assertRaisesRegex(ValueError, 'revision'):
            e.DeleteSnapshot(r['id'], expected_revision=1)
        with self.assertRaisesRegex(ValueError, 'exists'):
            self.save(e)
        self.assertTrue(all(not par.writes for par in p))

    def test_delete_dangling_button_new_same_name_does_not_redirect(self):
        e, m, p = self.fixture()
        r = self.save(e)
        state = e.AssignAction(1, r['id'])
        m.capture(force=True)
        before = copy.deepcopy(m.record()['targets'])
        e.DeleteSnapshot(r['id'], expected_revision=1)
        self.assertEqual(m.record()['targets'], before)
        self.assertFalse(e.GetControlState(state['id'])['action_available'])
        self.assertEqual(e.RecallAction(r['id'])['status'], 'unavailable')
        new = self.save(e)
        self.assertNotEqual(new['id'], r['id'])
        self.assertFalse(e.GetActionState(r['id'])['available'])

    def test_current_mapping_readiness_batch_before_any_writes(self):
        for drift in ('missing', 'readonly', 'invalid', 'driven', 'range', 'menu', 'pulse'):
            with self.subTest(drift=drift):
                e, m, p = self.fixture()
                r = self.save(e)
                p[0]._value = .9
                if drift == 'missing':
                    e.RemoveControl('steps')
                elif drift == 'readonly':
                    p[1].readOnly = True
                elif drift == 'invalid':
                    p[1].valid = False
                elif drift == 'driven':
                    p[1].mode.name = 'EXPRESSION'
                elif drift == 'range':
                    p[1].max = 2
                elif drift == 'menu':
                    p[3].menuNames.reverse()
                else:
                    e._collection.modes['knob', 2] = 'pulse'
                result = e.RecallAction(r['id'])
                self.assertEqual(result['status'], 'validation_failed', result)
                self.assertTrue(all(not par.writes for par in p))

    def test_capture_invalid_slots_values_and_callbacks_preserve_database(self):
        e, m, p = self.fixture()
        self.save(e)
        before = copy.deepcopy(e.ownerComp.fetch(STORE))
        for slots in ([], [('knob', 1), ('knob', 1)], [('knob', 9)], [('button', 1)], [('button', 2)], [('knob', True)]):
            with self.assertRaises(ValueError):
                e.SaveSnapshot('Bad', slots)
            self.assertEqual(e.ownerComp.fetch(STORE), before)
        p[0]._value = float('nan')
        with self.assertRaises(ValueError):
            e.SaveSnapshot('NaN')
        self.assertEqual(e.ownerComp.fetch(STORE), before)
        m.legacy = True
        e.BindControls([dict(kind='knob', slot=1, id='callback', value=.4, on_change=lambda e:None)], group_id='test')
        with self.assertRaisesRegex(ValueError, 'callbacks'):
            e.SaveSnapshot('Callback')

    def test_reload_no_custom_hook_json_store_rebuilds_before_mapping_restore(self):
        e, m, p = self.fixture()
        r = self.save(e)
        state = e.AssignAction(1, r['id'])
        m.capture(force=True)
        before = copy.deepcopy(m.record()['targets'])
        old = e.ownerComp.op
        def resolve(path):
            if path.startswith('../values/'):
                return next((par.owner for par in p if par.owner.path == '/'+path[3:]), None)
            return old(path)
        e.ownerComp.op = resolve
        e.ownerComp.store(STORE, json.loads(json.dumps(e.ownerComp.fetch(STORE))))
        e._snapshots = e._actions = None
        self.assertNotEqual(e.Applybinding(), False, e._last_error)
        self.assertEqual(m.record()['targets'], before)
        self.assertTrue(e.GetControlState(state['id'])['action_available'])
        self.assertTrue(all(not par.writes for par in p))
        p[0]._value = .9
        self.assertEqual(e.RecallAction(r['id'])['status'], 'succeeded')
        self.assertEqual(p[0].eval(), .4)

    def test_python_registration_mode_restores_values_without_snapshot_hook(self):
        import setup
        e, m, p = self.fixture()
        m.legacy = True
        r = e.SaveSnapshot('Registration')
        old = e.ownerComp.op
        def register(c):
            c.BindControls([dict(kind='knob', slot=1, id='fresh', parameter=p[0]),
                dict(kind='knob', slot=2, id='fresh.steps', parameter=p[1]),
                dict(kind='knob', slot=3, id='fresh.menu', parameter=p[3]),
                dict(kind='button', slot=1, id='saved.button', mode='pulse', action_id=r['id'])], group_id='test')
        hook = S(module=S(onRegister=register))
        e.ownerComp.op = lambda name:hook if name=='registration' else S(module=setup) if name=='setup' else old(name)
        e.ownerComp.ext = S(RotoPythonExt=e)
        e.ownerComp.BindControls = e.BindControls
        e.ownerComp.par.Setupmode.val = 'callback'
        self.assertNotEqual(e.Applybinding(), False, e._last_error)
        self.assertTrue(e.GetControlState('saved.button')['action_available'])
        self.assertTrue(all(not par.writes for par in p))
        p[0]._value = .9
        self.assertEqual(e.RecallAction(r['id'])['status'], 'succeeded')
        self.assertEqual(p[0].eval(), .4)

    def test_failed_action_hook_does_not_prevent_saved_snapshot_providers(self):
        e, m, p = self.fixture()
        r = self.save(e)
        old = e.ownerComp.op
        def fail(c):raise ValueError('other hook failure')
        e.ownerComp.op = lambda name:S(module=S(onRegisterActions=fail)) if name=='registration' else old(name)
        e._restore_actions()
        self.assertTrue(e.GetActionState(r['id'])['available'])
        self.assertFalse(e.GetActionState('tool.preset.clean')['available'])
        self.assertEqual(e.RecallAction(r['id'])['status'], 'succeeded')

    def test_runtime_failure_after_setter_reports_partial_actual_values_no_rollback(self):
        e, m, p = self.fixture()
        r = self.save(e)
        p[0]._value = .9
        p[1]._value = 7
        def fail(par, value):raise ValueError('consumer failed after write')
        p[1].on_write = fail
        result = e.RecallAction(r['id'])
        self.assertEqual(result['status'], 'partial', result)
        self.assertEqual(result['entries'][1]['actual_value'], 3)
        self.assertFalse(result['entries'][2]['attempted'])
        self.assertEqual(p[0].eval(), .4)
        self.assertEqual(e._host.controls['knob', 1].value, raw_value(.4)/16383)
        self.assertEqual(e._host.controls['knob', 2].value, raw_value(3/8)/16383)

    def test_late_callback_readback_and_nonfinite_failures_json_safe(self):
        for corrupt in (.9, float('nan')):
            e, m, p = self.fixture()
            r = self.save(e)
            p[0]._value = .8
            p[1]._value = 7
            p[1].on_write = lambda par, value:setattr(p[0], '_value', corrupt)
            result = e.RecallAction(r['id'])
            self.assertEqual(result['status'], 'partial')
            self.assertFalse(result['entries'][0]['verified'])
            json.dumps(result, allow_nan=False)

    def test_mapping_change_during_recall_stops_batch_and_reports_partial(self):
        e, m, p = self.fixture()
        r = self.save(e)
        p[0]._value = .9
        p[0].on_write = lambda par, value:e._collection.bindings.pop(('knob', 2))
        result = e.RecallAction(r['id'])
        self.assertEqual(result['status'], 'partial')
        self.assertFalse(result['entries'][1]['attempted'])
        self.assertEqual(p[1].writes, [])
        e, m, p = self.fixture()
        r = self.save(e)
        p[0]._value = .9
        p[0].on_write = lambda par, value:setattr(e._collection.bindings['knob', 1], 'valid', False)
        result = e.RecallAction(r['id'])
        self.assertEqual(result['status'], 'partial')
        self.assertEqual(result['entries'][0]['actual_value'], .4)
        self.assertFalse(result['entries'][0]['verified'])

    def test_button_existing_push_toggle_guards_failure_repair_and_ack_zero_recall(self):
        for adapter, traffic, count in [('push', [127,127,0,0], 1), ('toggle', [127,0,127], 3)]:
            e, m, p = self.fixture()
            r = self.save(e)
            state = e.AssignAction(1, r['id'], button_type=adapter)
            actions.ActionTests().ack(e)
            calls = []
            provider = e._actions.entries[r['id']][1]
            def recall(event):calls.append(event);return provider(event)
            recall._snapshot_provider = True
            e.RegisterAction(r['id'], 'Clean', recall, replace=True)
            clock = [0.]
            e._host.clock = lambda:clock[0]
            for value in traffic:
                e._receive_midi((191,20,value));clock[0] += .1
            self.assertEqual(len(calls), count)
            e._host.learning = True
            e._receive_midi((191,20,127))
            self.assertEqual(len(calls), count)
            e._host.learning = False
            p[1].readOnly = True
            e._receive_midi((191,20,127))
            self.assertFalse(e.GetControlState(state['id'])['mapped'])
            self.assertEqual(e.GetControlState(state['id'])['action_result']['status'], 'validation_failed')
            p[1].readOnly = False
            e.AssignParameter('knob', 2, p[1])  # Repair the independently suspended target mapping.
            e.AssignAction(1, r['id'], id=state['id'])
            calls_before = len(calls)
            actions.ActionTests().ack(e)
            self.assertEqual(len(calls), calls_before)
            e._receive_midi((191,20,127))
            self.assertEqual(e.GetControlState(state['id'])['action_result']['status'], 'succeeded')

    def test_browse_selection_inactive_snapshot_is_zero_recall(self):
        e, m, p = self.fixture()
        r = self.save(e)
        m.capture(force=True)
        other = m.create('Other')
        m.select(other)
        p[0]._value = .9
        result = e.RecallAction(r['id'])
        self.assertEqual(result['status'], 'validation_failed')
        self.assertEqual(p[0].eval(), .9)
        self.assertFalse(e.GetSnapshot(r['id'])['validation']['status']=='succeeded')
        with self.assertRaisesRegex(ValueError, 'Activate'):
            e.SaveSnapshot('Inactive', scope=tuple(r['scope']['context']))
        self.assertTrue(all(not par.writes for par in p))

    def test_definition_invariance_and_shared_parameter_true_feedback(self):
        import test_layout_owners
        e, m, f, a, b, comps = test_layout_owners.OwnerTests().fixture()
        layout = e.RegisterComp(a.owner)
        key = (layout, m.track(layout)['id'], m.plugin(layout)['id'])
        m.select(key[0])
        par = Parameter('Shared')
        e.AssignParameter('knob', 1, par)
        r = e.SaveSnapshot('COMP')
        m.capture(force=True)
        comp_before = copy.deepcopy(m.record()['targets'])
        custom = next(row['id'] for row in m.data['records'] if row['category']=='CUSTOM')
        m.select(custom)
        assigned = e.AssignParameter('knob', 1, par)
        e.ConfigureControl(assigned['id'], minimum=0, maximum=.5)
        m.capture(force=True)
        custom_before = copy.deepcopy(m.record()['targets'])
        custom_snapshot = e.SaveSnapshot('CUSTOM')
        self.assertNotEqual(r['scope'], custom_snapshot['scope'])
        par._value = .1
        self.assertEqual(e.RecallAction(custom_snapshot['id'])['status'], 'succeeded')
        self.assertEqual(par.eval(), .4)
        self.assertEqual(m.record()['targets'], custom_before)
        old = e.ownerComp.op
        e.ownerComp.op = lambda path:par.owner if path=='../values/Shared' else old(path)
        m.select(key[0])
        self.assertEqual(e.GetControlStates()[0]['value'], .4)
        self.assertEqual(m.record()['targets'], comp_before)
        self.assertEqual(e.GetSnapshots(scope=key)[0]['id'], r['id'])

    def test_management_and_shared_software_guards(self):
        for guard in ('_dispatching', '_restoring', '_restore_pending'):
            e, m, p = self.fixture()
            setattr(e, guard, True)
            with self.assertRaises(ValueError):e.SaveSnapshot('Blocked')
        for fence in ('pending','gated','paused','backlog'):
            e, m, p = self.fixture()
            r = self.save(e)
            e._follow = S(pending=False,gated=False,paused=False,backlog=False)
            setattr(e._follow, fence, True)
            with self.assertRaises(ValueError):e.RecallAction(r['id'])
            self.assertTrue(all(not par.writes for par in p))
        e, m, p = self.fixture()
        r = self.save(e)
        e._host.controls['knob', 1].touched = True
        e._host._sync()
        self.assertEqual(e.RecallAction(r['id'])['status'], 'validation_failed')
        self.assertTrue(all(not par.writes for par in p))

    def test_generic_export_clears_saved_values_registry_and_hooks(self):
        e, m, p = self.fixture()
        self.save(e)
        old = e.ownerComp.op
        dat = S(text='user registration')
        e.ownerComp.op = lambda name:dat if name=='registration' else old(name)
        e.ownerComp.ext = S(RotoPythonExt=e)
        reset_mapping_storage(e.ownerComp)
        reset_registration(e.ownerComp)
        self.assertEqual(e.ownerComp.fetch(STORE), dict(version=2,records=[],deleted=[]))
        self.assertIsNone(e._actions)
        self.assertIsNone(e._snapshots)
        self.assertNotIn('Clean', dat.text)
        self.assertNotIn('onRegisterSnapshotTargets', dat.text)
        self.assertTrue(all(not par.writes for par in p))

    def test_corrupt_store_preserved_reserved_namespace(self):
        e, m, p = self.fixture()
        e.ownerComp.store(STORE, dict(version=1,records=[]))
        with self.assertRaisesRegex(ValueError, 'Unsupported'):e.GetSnapshots()
        self.assertEqual(e.ownerComp.fetch(STORE)['version'], 1)
        with self.assertRaisesRegex(ValueError, 'namespace'):
            e.RegisterAction('snapshot.user', 'Hijack', lambda e:None)
        e.ownerComp.store(STORE, dict(version=2,records=[],deleted=[]))
        r = self.save(e)
        data = e.ownerComp.fetch(STORE)
        data['records'][0]['entries'][0]['value'] = float('nan')
        with self.assertRaises(ValueError):e.GetSnapshot(r['id'])
        data['records'][0]['entries'][0]['value'] = .4
        data['records'][0]['entries'][0]['kind'] = 'button'
        with self.assertRaisesRegex(ValueError, 'Knobs only'):
            e.GetSnapshots()
        self.assertTrue(all(not par.writes for par in p))
