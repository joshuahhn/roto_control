"""Named action references share the proven Button adapter and Layout library."""
import copy
import json
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

import verify_action_presets as native_fixture

import test_layouts
import test_comp_follow
import test_layout_owners
from controls import Actions, Controls
from protocol import digest, sysex


class ActionTests(unittest.TestCase):
    def test_provider_error_provenance_survives_real_state_and_catalog_projection(self):
        e, manager, parameter, events = self.fixture()
        e.RegisterAction('tool.preset.clean', 'Clean',
                         lambda event: dict(status='partial', error='readback mismatch'), replace=True)
        state = self.assign(e); self.ack(e)
        e._update_catalog()
        e.RecallAction('tool.preset.clean')
        actual = e.GetControlState(state['id'])
        self.assertEqual(actual['error'], 'partial: readback mismatch')
        self.assertEqual(actual['mapping_error'], '')
        cached = next(row for row in e.ownerComp.fetch('control_catalog') if row['id']==state['id'])
        cached.update(error='stale cached failure', mapping_error='stale cached failure')
        current = next(row for row in e.GetControlCatalog() if row['id']==state['id'])
        self.assertEqual((current['error'], current['mapping_error']), (actual['error'], ''))
        e.UnregisterAction('tool.preset.clean')
        unavailable = e.GetControlState(state['id'])
        self.assertFalse(unavailable['valid'] or unavailable['action_available'])
        self.assertEqual(unavailable['mapping_error'], unavailable['error'])

    def test_inactive_action_library_keeps_mapping_error_separate_from_provider_details(self):
        e, manager, parameter, events = self.fixture()
        self.assign(e); manager.capture(force=True)
        saved = copy.deepcopy(manager.plugin()['targets'])
        other = manager.create('Other')
        manager.plugin(other)['targets'] = copy.deepcopy(saved)
        e.RegisterAction('tool.preset.clean', 'Clean',
                         lambda event: dict(status='partial', error='partial details'), replace=True)
        e.RecallAction('tool.preset.clean')
        before = copy.deepcopy(manager.data)
        rows = e.GetPluginTargets(other, manager.track(other)['id'], manager.plugin(other)['id'])
        action = next(row for row in rows if row.get('action_id'))
        self.assertEqual(action['error'], 'partial: partial details')
        self.assertEqual(action['mapping_error'], '')
        self.assertEqual(manager.data, before)
        e.UnregisterAction('tool.preset.clean')
        rows = e.GetPluginTargets(other, manager.track(other)['id'], manager.plugin(other)['id'])
        action = next(row for row in rows if row.get('action_id'))
        self.assertFalse(action['valid'] or action['action_available'])
        self.assertEqual(action['mapping_error'], action['error'])

    def fixture(self):
        e, m, p = test_layouts.LayoutTests().fixture()
        e._actions = None
        e._layout_ready = True
        e._process = None
        e._follow = None
        events = []
        e.RegisterAction('tool.preset.clean', 'Clean', events.append)
        return e, m, p, events

    def ack(self, e, slot=1):
        target = e._host.controls['button', slot]
        e._receive_midi(sysex(11, 11, (target.index >> 7, target.index & 127,
                         *digest(target.target_id, 6), 1, slot-1, 0)))
        return target

    def assign(self, e, **kwargs):
        return e.AssignAction(1, 'tool.preset.clean', **kwargs)

    def test_registration_assignment_learn_ack_never_recalls(self):
        e, m, p, events = self.fixture()
        knob = e._host.controls['knob', 1]
        knob.mapped = True
        e._receive_midi(sysex(11, 9, (1,)))
        state = self.assign(e)
        self.assertEqual(state['binding_type'], 'action')
        self.assertEqual((state['mode'], state['button_type']), ('pulse', 'push'))
        self.assertTrue(e.Offerparameter(state['id']))
        self.ack(e)
        e._receive_midi((191, 20, 127))
        self.assertEqual(events, [])
        self.assertIs(knob, e._host.controls['knob', 1])
        self.assertTrue(knob.mapped)
        e._receive_midi(sysex(11, 9, (0,)))
        e._receive_midi((191, 20, 127))
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0], dict(id=state['id'], value=1, origin='hardware',
                                        kind='pulse', action_id='tool.preset.clean'))

    def test_push_repeated_press_and_hold_release_duplicates(self):
        e, m, p, events = self.fixture()
        state = self.assign(e)
        t = self.ack(e)
        for value in (127, 127, 127, 0, 0, 127, 0):
            e._receive_midi((191, 20, value))
        self.assertEqual(len(events), 2)
        self.assertTrue(t.mapped)
        self.assertEqual(e.GetControlState(state['id'])['action_result']['status'], 'succeeded')
        with self.assertRaisesRegex(ValueError, 'Pulse'):
            e.SetValue(1, state['id'])
        self.assertEqual(len(events), 2)

    def test_toggle_uses_existing_latched_adapter(self):
        e, m, p, events = self.fixture()
        self.assign(e, button_type='toggle')
        self.ack(e)
        now = [0.0]
        e._host.clock = lambda: now[0]
        for value in (127, 0, 127, 127):
            e._receive_midi((191, 20, value))
            e._receive_midi((191, 20, value))  # same-batch debounce
            now[0] += .1
        self.assertEqual(len(events), 4)
        self.assertEqual(e._host.controls['button', 1]._pulse_state, 0)

    def test_unmapped_foreign_ack_disconnected_nonplugin_and_mutating(self):
        e, m, p, events = self.fixture()
        self.assign(e)
        t = e._host.controls['button', 1]
        e._receive_midi((191, 20, 127))
        wrong = list(digest(t.target_id, 6)); wrong[0] ^= 1
        e._receive_midi(sysex(11, 11, (0, t.index, *wrong, 1, 0, 0)))
        e._receive_midi((191, 20, 127))
        self.assertEqual(events, [])
        self.ack(e)
        for flag in ('connected', 'plugin'):
            setattr(e._host, flag, False)
            e._receive_midi((191, 20, 127))
            setattr(e._host, flag, True)
        m.mutating = True
        e._receive_midi((191, 20, 127))
        m.mutating = False
        self.assertEqual(events, [])
        e._receive_midi((191, 20, 127))
        self.assertEqual(len(events), 1)

    def test_follow_fence_stale_epoch_and_no_replay(self):
        e, m, f, a, b, t1, t2, sample, _ = test_comp_follow.FollowTests().fixture()
        events = []
        e.RegisterAction('preset', 'Preset', events.append)
        e.AssignAction(1, 'preset'); self.ack(e)
        old_token = f.token
        test_comp_follow.FollowTests().select_hw(e, m, t2)
        self.assertTrue(f.gated)
        e._receive_midi((191, 20, 127), token=old_token)
        f.flush()
        self.assertEqual(events, [])
        e.SelectTrack('custom', t1)
        self.ack(e)
        e._receive_midi((191, 20, 127), token=old_token)
        self.assertEqual(events, [])
        e._receive_midi((191, 20, 127), token=f.token)
        self.assertEqual(len(events), 1)

    def test_exception_partial_and_unavailable_isolate_control(self):
        for failure in ('exception', 'partial', 'unavailable', 'bad_result'):
            with self.subTest(failure=failure):
                e, m, p, events = self.fixture()
                def recall(event):
                    events.append(event)
                    p.val = 8  # arbitrary side effects remain; feedback reads truth
                    if failure == 'exception':
                        raise RuntimeError('consumer failed')
                    return False if failure == 'bad_result' else dict(status=failure, error='consumer result')
                e.RegisterAction('tool.preset.clean', 'Clean', recall, replace=True)
                state = self.assign(e); self.ack(e)
                knob = e._host.controls['knob', 1]; knob.mapped = True
                e._receive_midi((191, 20, 127))
                expected = 'failed' if failure in ('exception', 'bad_result') else failure
                self.assertEqual(e.GetActionState('tool.preset.clean')['result']['status'], expected)
                self.assertFalse(e.GetControlState(state['id'])['valid'])
                self.assertIn(expected, e.GetControlState(state['id'])['error'])
                self.assertTrue(e._host.enabled and e._host.connected and e._host.plugin and knob.mapped)
                self.assertEqual(p.eval(), 8)
                self.assertEqual(e.GetValue('original'), 8)
                e._receive_midi((191, 20, 0)); e._receive_midi((191, 20, 127))
                self.assertEqual(len(events), 1)
                e._receive_midi((191, 12, 127)); e._receive_midi((191, 44, 127))
                self.assertEqual(p.eval(), 10)

    def test_deleted_registration_no_same_label_fallback_and_repair(self):
        e, m, p, events = self.fixture()
        state = self.assign(e); self.ack(e)
        e.UnregisterAction('tool.preset.clean')
        e.RegisterAction('different.id', 'Clean', events.append)
        self.assertFalse(e.GetControlState(state['id'])['action_available'])
        e._receive_midi((191, 20, 127))
        self.assertEqual(events, [])
        self.assertEqual(e.GetActionState('tool.preset.clean')['result']['status'], 'unavailable')
        e.RegisterAction('tool.preset.clean', 'Clean', events.append)
        self.assign(e, id=state['id']); self.ack(e)
        self.assertNotIn(state['id'], e.ownerComp.fetch('removed_controls'))
        e._receive_midi((191, 20, 127))
        self.assertEqual(len(events), 1)

    def test_independent_layouts_and_comp_link_read_true_values(self):
        e, m, p, events = self.fixture()
        custom = self.assign(e)
        m.capture(force=True)
        original = copy.deepcopy(m.plugin())
        b = m.create('Existing COMP-linked configuration'); m.select(b)
        # Existing Focus link metadata, no #9 ownership allocation.
        m.plugin()['focus_comp'] = dict(path='../master', state='bound')
        comp_action = self.assign(e)
        e.AssignParameter('knob', 1, p)
        m.capture(force=True)
        b_definitions = copy.deepcopy(m.record()['targets'])
        def recall(event):
            events.append(event); p.val = 9
        e.RegisterAction('tool.preset.clean', 'Clean', recall, replace=True)
        m.select('custom'); self.ack(e)
        self.assertEqual(e.GetControlState(custom['id'])['action_result'], None)
        e._receive_midi((191, 20, 127))
        self.assertEqual(e.GetValue('original'), 9)
        m.select(b)
        self.assertEqual(e.GetValue(next(s['id'] for s in e.GetControlStates() if s['kind']=='knob')), 9)
        self.assertEqual(m.record()['targets'], b_definitions)
        self.assertEqual(e.GetControlState(comp_action['id'])['slot'], 1)
        self.assertEqual(len(events), 1)
        self.assertNotEqual(custom['id'], comp_action['id'])
        self.assertEqual(m.plugin('custom')['targets'], original['targets'])

    def test_json_reload_reconstructs_hook_before_layout_install(self):
        e, m, p, events = self.fixture()
        state = self.assign(e)
        e._update_catalog(); m.capture(force=True)
        saved = json.loads(json.dumps(e.ownerComp.fetch('layout_registry')))
        identity = e._host.controls['button', 1].target_id
        oldop = e.ownerComp.op
        e.ownerComp.op = lambda name: SimpleNamespace(module=SimpleNamespace(onRegisterActions=lambda c: e.RegisterAction(
            'tool.preset.clean', 'Clean', events.append))) if name == 'registration' else oldop(name)
        e._actions = None; m.data = saved
        e._host.connected = e._host.plugin = False
        self.assertNotEqual(e.Applybinding(), False)
        self.assertEqual(events, [])
        self.assertTrue(e.GetActionState('tool.preset.clean')['available'])
        self.assertEqual(e._host.controls['button', 1].target_id, identity)
        self.assertFalse(e.GetControlState(state['id'])['connected'])
        e._host.connected = e._host.plugin = True
        self.ack(e); e._receive_midi((191, 20, 127))
        self.assertEqual(len(events), 1)

    def test_missing_or_failed_hook_restores_unavailable_reference(self):
        for fail in (False, True):
            e, m, p, events = self.fixture()
            state = self.assign(e); m.capture(force=True)
            oldop = e.ownerComp.op
            def register(c):
                e.RegisterAction('tool.preset.clean', 'Clean', events.append)
                raise RuntimeError('registration stopped')
            e.ownerComp.op = lambda n: SimpleNamespace(module=SimpleNamespace(**(
                {'onRegisterActions': register} if fail else {}))) if n == 'registration' else oldop(n)
            self.assertNotEqual(e.Applybinding(), False)
            self.assertFalse(e.GetControlState(state['id'])['valid'])
            self.assertIn('Action', e.GetControlState(state['id'])['error'])
            self.ack(e); e._receive_midi((191, 20, 127))
            self.assertEqual(events, [])
            self.assertEqual(e.GetActionState('tool.preset.clean')['result']['status'], 'unavailable')

    def test_control_page_recall_rebuilds_action_by_hash_without_execution(self):
        e, m, p, events = self.fixture()
        state = self.assign(e); m.capture(force=True)
        saved = copy.deepcopy(next(t for t in m.record()['targets'] if t['id']==state['id']))
        m.page_changed()
        self.assertEqual(e.GetControlStates(), [])
        e._receive_midi(sysex(11, 11, (saved['index']>>7, saved['index']&127,
                           *digest(saved['identity'], 6), 1, 4, 0)))
        self.assertEqual(e.GetControlState(state['id'])['slot'], 5)
        self.assertEqual(events, [])
        e._receive_midi((191, 24, 127))
        self.assertEqual(len(events), 1)
        e.RemoveControl(state['id']); m.capture(force=True)
        m.page_changed()
        e._receive_midi(sysex(11, 11, (saved['index']>>7, saved['index']&127,
                           *digest(saved['identity'], 6), 1, 4, 0)))
        self.assertEqual(e.GetControlStates(), [])

    def test_configuration_preserves_action_semantics_and_other_assignment(self):
        e, m, p, events = self.fixture()
        state = self.assign(e); t = self.ack(e)
        e.ConfigureControl(state['id'], button_type='toggle')
        self.assertIs(t, e._host.controls['button', 1])
        with self.assertRaisesRegex(ValueError, 'Pulse'):
            e.ConfigureControl(state['id'], mode='toggle')
        e.AssignParameter('knob', 2, test_layouts.test_assignment.AssignmentTests().parameter(name='Other'))
        self.assertEqual(e.GetControlState(state['id'])['action_id'], 'tool.preset.clean')
        self.assertEqual(self.assign(e)['id'], state['id'])
        self.assertEqual(events, [])

    def test_explicit_software_recall_and_recursion_guards(self):
        e, m, p, events = self.fixture()
        def recall(event):
            events.append(event)
            with self.assertRaises(ValueError): e.RecallAction('tool.preset.clean')
            with self.assertRaises(ValueError): e.RegisterAction('recursive', 'Recursive', recall)
            e._receive_midi((191, 20, 127))  # callback reentry cannot dispatch twice
        e.RegisterAction('tool.preset.clean', 'Clean', recall, replace=True)
        state = self.assign(e); self.ack(e)
        result = e.RecallAction('tool.preset.clean')
        self.assertEqual(result['status'], 'succeeded')
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['origin'], 'software')
        for guard in ('_restoring', '_restore_pending'):
            setattr(e, guard, True)
            with self.assertRaises(ValueError): e.RecallAction('tool.preset.clean')
            setattr(e, guard, False)
        e._host.learning = True
        with self.assertRaises(ValueError): e.RecallAction('tool.preset.clean')
        self.assertEqual(len(events), 1)

    def test_provider_validation_execution_failure_and_details_reach_diagnostics(self):
        import test_inspector
        import inspector_data
        for status in ('validation_failed', 'execution_failed', 'partial', 'success'):
            e, m, p, events = self.fixture()
            payload = dict(status=status, error='' if status=='success' else 'entry changed',
                           preset_id='snapshot-id', revision=3,
                           entries=[dict(target_key='target', actual_value=8, attempted=True)])
            e.RegisterAction('tool.preset.clean', 'Clean', lambda event: payload, replace=True)
            state = self.assign(e); self.ack(e)
            e._receive_midi((191, 20, 127))
            current = e.GetControlState(state['id'])
            self.assertEqual(current['action_result']['status'], 'succeeded' if status=='success' else status)
            self.assertEqual(current['action_result']['entries'], payload['entries'])
            payload['entries'].clear()
            self.assertEqual(len(e.GetActionState('tool.preset.clean')['result']['entries']), 1)
            e._update_catalog()
            inspector, table = test_inspector.InspectorTests().inspector()
            inspector_data.refresh(inspector, e.GetControlCatalog())
            row = dict(zip(table.text.splitlines()[0].split('\t'), table.text.splitlines()[9].split('\t')))
            self.assertEqual(row['COMP'], 'Action preset')
            self.assertIn('tool.preset.clean', row['Parameter'])
            self.assertEqual(row['Value'], current['action_result']['status'])
            if status!='success': self.assertIn(status, row['Error'])

    def test_nonserializable_provider_result_fails_without_persisting_handles(self):
        e, m, p, events = self.fixture()
        e.RegisterAction('tool.preset.clean', 'Clean', lambda event: dict(status='success', handle=p), replace=True)
        result = e.RecallAction('tool.preset.clean')
        self.assertEqual(result['status'], 'failed')
        self.assertNotIn('handle', result)
        json.dumps(result, allow_nan=False)

    def test_python_registration_mode_rebuilds_named_actions(self):
        import setup
        e, m, p, events = self.fixture()
        oldop = e.ownerComp.op
        hook = SimpleNamespace(module=SimpleNamespace(
            onRegisterActions=lambda c: c.RegisterAction('hook.preset', 'Hook', events.append),
            onRegister=lambda c: c.BindControls([dict(kind='button', slot=1, id='hook.mapping',
                                                     action_id='hook.preset', label='Hook', mode='pulse', button_type='push')],
                                                group_id='hook.group')))
        e.ownerComp.op = lambda n: hook if n=='registration' else SimpleNamespace(module=setup) if n=='setup' else oldop(n)
        e.ownerComp.ext = SimpleNamespace(RotoPythonExt=e)
        e.ownerComp.RegisterAction = e.RegisterAction
        e.ownerComp.BindControls = e.BindControls
        e.ownerComp.par.Setupmode.val = 'callback'
        self.assertEqual(e.Applybinding(), ('hook.mapping',), e._last_error)
        self.assertTrue(m.legacy)
        self.assertEqual(events, [])
        self.assertEqual(e.Applybinding(), ('hook.mapping',), e._last_error)
        self.assertEqual(events, [])
        self.ack(e); e._receive_midi((191, 20, 127))
        self.assertEqual(len(events), 1)

    def test_generic_export_resets_user_registration_before_first_tick(self):
        from export_component import reset_registration
        e, m, p, events = self.fixture()
        self.assign(e)
        hook = SimpleNamespace(text='user callback source', module=None)
        oldop = e.ownerComp.op
        e.ownerComp.op = lambda n: hook if n=='registration' else oldop(n)
        e.ownerComp.ext = SimpleNamespace(RotoPythonExt=e)
        e._restore_pending = True  # export copy has not had its first Tick
        reset_registration(e.ownerComp)
        namespace = {}; exec(hook.text, namespace)
        hook.module = SimpleNamespace(**namespace)
        self.assertEqual(e.GetActions(), [])
        e._restore_actions()
        self.assertEqual(e.GetActions(), [])
        self.assertNotIn('tool.preset.clean', hook.text)
        with self.assertRaisesRegex(ValueError, 'Configure registration'):
            hook.module.onRegister(e.ownerComp)
        self.assertEqual(events, [])

    def test_action_replacement_does_not_inherit_old_destination_or_override(self):
        import test_assignment
        e, m, p, events = self.fixture()
        toggle = test_assignment.AssignmentTests().parameter('Toggle', 'Enabled')
        original = e.AssignParameter('button', 1, toggle)
        e._update_catalog()
        e.ownerComp.store('control_overrides', {original['id']:dict(mode='toggle', button_type='toggle')})
        state = self.assign(e, id=original['id'])
        e._update_catalog(); catalog = next(s for s in e.GetControlCatalog() if s['id']==state['id'])
        self.assertEqual((catalog['comp'], catalog['parameter'], catalog['mode']), ('', '', 'pulse'))
        self.assertNotIn(state['id'], e.ownerComp.fetch('removed_controls'))
        m.capture(force=True); m.restore()
        self.assertEqual(e.GetControlState(state['id'])['mode'], 'pulse')
        self.assertEqual(events, [])

    def test_action_assignment_preflights_colliding_index_without_mutation(self):
        e, m, p, events = self.fixture()
        e.AssignParameter('knob', 1, p, _wire_index=8, _id='colliding')
        before = copy.deepcopy(e.ownerComp.fetch('parameter_assignments'))
        host = e._host.controls['knob', 1]
        with self.assertRaisesRegex(ValueError, 'indices'):
            self.assign(e)
        self.assertEqual(e.ownerComp.fetch('parameter_assignments'), before)
        self.assertIs(e._host.controls['knob', 1], host)
        self.assertEqual(events, [])

    def test_missing_registration_page_recall_keeps_unavailable_and_recoverable(self):
        e, m, p, events = self.fixture()
        state = self.assign(e); m.capture(force=True)
        saved = copy.deepcopy(next(t for t in m.record()['targets'] if t['id']==state['id']))
        e.UnregisterAction('tool.preset.clean'); m.page_changed()
        e._receive_midi(sysex(11, 11, (saved['index']>>7, saved['index']&127,
                           *digest(saved['identity'], 6), 1, 4, 0)))
        self.assertEqual(e.GetControlState(state['id'])['slot'], 5)
        self.assertFalse(e.GetControlState(state['id'])['valid'])
        self.assertEqual(events, [])
        e._host.learning=True
        self.assertFalse(e.Offerparameter(state['id']))
        e._host.learning=False
        e.RegisterAction('tool.preset.clean', 'Clean', events.append)
        e._receive_midi((191, 24, 127))
        self.assertEqual(len(events), 1)

    def test_real_owner_and_custom_action_definitions_and_library_projection(self):
        import test_layout_owners
        e, m, f, a, b, comps = test_layout_owners.OwnerTests().fixture()
        x = test_layout_owners.OwnerTests().add(comps, '/ActionOwner')
        events = []
        def recall(event): events.append(event); x.val = 8
        e.RegisterAction('owner.preset', 'Owner preset', recall)
        custom = e.AssignAction(1, 'owner.preset')
        custom_par = e.AssignParameter('knob', 1, x)
        m.capture(force=True)
        owned = e.RegisterComp(x.owner); e.SelectLayout(owned)
        own_action = e.AssignAction(1, 'owner.preset')
        own_par = e.AssignParameter('knob', 1, x)
        m.capture(force=True)
        definitions = {p['id']: copy.deepcopy(p['targets']) for p in m.all_plugins()}
        self.ack(e); e._receive_midi((191, 20, 127))
        self.assertEqual(x.eval(), 8)
        e.SelectLayout('custom')
        self.assertEqual(e.GetValue(custom_par['id']), 8)
        self.assertEqual(m.layout(owned)['category'], 'COMP')
        self.assertEqual(m.layout('custom')['category'], 'CUSTOM')
        library = e.GetPluginTargets(owned)
        action = next(t for t in library if t['id']==own_action['id'])
        self.assertTrue(action['valid'] and action['action_available'])
        self.assertEqual(action['binding_type'], 'action')
        self.assertEqual(action['action_result']['status'], 'succeeded')
        self.assertIsNone(action['value'])
        self.assertEqual({p['id']:p['targets'] for p in m.all_plugins()}, definitions)
        e.UnregisterAction('owner.preset')
        missing = next(t for t in e.GetPluginTargets(owned) if t['id']==own_action['id'])
        self.assertFalse(missing['valid']); self.assertIn('unavailable', missing['error'])
        self.assertEqual(len(events), 1)

    def test_recall_rejects_missing_conflict_unregistered_and_quarantined_owner(self):
        import test_layout_owners
        from layouts import OWNER_KEY
        for status in ('missing', 'conflict', 'unregistered', 'returned'):
            e, m, f, a, b, comps = test_layout_owners.OwnerTests().fixture()
            x = test_layout_owners.OwnerTests().add(comps, '/ActionOwner')
            layout = e.RegisterComp(x.owner); e.SelectLayout(layout)
            events = []; e.RegisterAction('owner.preset', 'Owner preset', events.append)
            state = e.AssignAction(1, 'owner.preset'); m.capture(force=True); target = self.ack(e)
            if status=='conflict':
                clone = test_layout_owners.OwnerTests().add(comps, '/Clone')
                clone.owner.store(OWNER_KEY, x.owner.fetch(OWNER_KEY))
            elif status=='unregistered':
                e.SelectLayout('custom'); e.UnregisterLayoutOwner(layout)
                m.data['active']=layout  # simulate persisted active record on reload
                m.restore()
            else:
                x.owner.valid=False
                self.assertFalse(m.owner_ready())
                if status=='returned':
                    x.owner.valid=True
                    self.assertTrue(m.owner_ready()); self.assertTrue(m.quarantined)
            with self.subTest(status=status):
                with self.assertRaises(ValueError): e.RecallAction('owner.preset')
                e._receive_midi((191, 20, 127))
                self.assertEqual(events, [])
                if status=='unregistered':self.assertEqual(e.GetControlStates(),[])
                else:self.assertFalse(e.GetControlState(state['id'])['valid'])
                e._receive_midi(sysex(11, 11, (target.index>>7,target.index&127,
                                      *digest(target.target_id,6),1,0,0)))
                self.assertEqual(events, [])
                if status=='returned':
                    e.SelectLayout(layout)
                    self.assertEqual(events, [])
                    self.ack(e); e._receive_midi((191, 20, 127))
                    self.assertEqual(len(events), 1)

    def test_current_catalog_updates_action_diagnostics_without_persisted_refresh(self):
        e, m, p, events = self.fixture()
        state = self.assign(e); e._update_catalog()
        e.RecallAction('tool.preset.clean')
        # Existing publication cache is deliberately unchanged in this fixture.
        current = next(t for t in e.GetControlCatalog() if t['id']==state['id'])
        self.assertEqual(current['action_result']['status'], 'succeeded')
        self.assertEqual(current['value_source'], 'action')
        e.UnregisterAction('tool.preset.clean')
        current = next(t for t in e.GetControlCatalog() if t['id']==state['id'])
        self.assertFalse(current['action_available'])
        self.assertIn('unavailable', current['error'])

    def test_registration_contract_and_detached_results(self):
        registry = Actions()
        with self.assertRaises(ValueError): registry.register('', 'Label', lambda e: None)
        with self.assertRaises(TypeError): registry.register('id', 'Label', None)
        registry.register('id', 'Label', lambda e: None)
        with self.assertRaises(ValueError): registry.register('id', 'Label', lambda e: None)
        result = registry.recall('id', {})
        result['status'] = 'failed'
        self.assertEqual(registry.state('id')['result']['status'], 'succeeded')
        for spec in (dict(kind='knob', mode='value'), dict(kind='button', mode='toggle')):
            with self.assertRaisesRegex(ValueError, 'Pulse'):
                Controls([dict(spec, slot=1, id='mapping', action_id='id', on_change=lambda e: None)])


class NativeEvidenceTests(unittest.TestCase):
    """Disk/lifecycle checks only; fake holders are not native acceptance."""
    def test_fixture_observes_registered_owner_entry_without_relink(self):
        e, manager, follower, a, b, comps = test_layout_owners.OwnerTests().fixture()
        consumer = a.owner
        layout = e.RegisterComp(consumer)
        e.SelectLayout(layout)
        entry = manager.plugin()
        link = copy.deepcopy(entry['focus_comp'])
        native_fixture._verify_owner_entry(e, e, consumer, layout)
        self.assertEqual(entry['focus_comp'], link)
        with self.assertRaisesRegex(ValueError, 'Use RelinkLayoutOwner'):
            e.SetPluginComp(*e.GetLayoutContext()['key'], consumer)
        self.assertEqual(entry['focus_comp'], link)
        with self.assertRaises(AssertionError):
            native_fixture._verify_owner_entry(e, e, b.owner, layout)

    def test_fixture_toggle_stage_refreshes_ack_without_recall(self):
        e, manager, parameter, events = ActionTests().fixture()
        state = ActionTests().assign(e)
        original = ActionTests().ack(e)
        controller = SimpleNamespace(ext=SimpleNamespace(RotoPythonExt=e),
            ConfigureControl=e.ConfigureControl, Offerparameter=e.Offerparameter,
            GetControlState=e.GetControlState,
            op=lambda name: SimpleNamespace(module=SimpleNamespace(sysex=sysex, digest=digest)))
        tool = SimpleNamespace(par=SimpleNamespace(Recalls=SimpleNamespace(eval=lambda: len(events))))
        native_fixture._configure_toggle(controller, tool, state['id'])
        self.assertEqual(events, [])
        self.assertIs(e._host.controls['button', 1], original)
        self.assertTrue(e.GetControlState(state['id'])['mapped'])
        clock = [0.0]
        e._host.clock = lambda: clock[0]
        for value in (127, 0, 127):
            e._receive_midi((191, 20, value))
            clock[0] += .1
        self.assertEqual(len(events), 3)

    def holder(self, directory):
        storage = dict(action_fixture=True, temp_paths=[],
                       result=dict(fixture_id='fixture-test', artifact_dir=str(directory)))
        h = SimpleNamespace(valid=True, path='/test/action_fixture', name='fixture',
                            par=SimpleNamespace(), ext=SimpleNamespace(), isCOMP=True, extensions=[])
        h.fetch = lambda name, default=None: storage.get(name, default)
        h.store = lambda name, value: storage.__setitem__(name, value)
        h.findChildren = lambda: []
        h.errors = lambda **kwargs: 'original native failure'
        h.destroy = lambda: setattr(h, 'valid', False)
        return h

    def test_failure_retains_holder_artifact_and_captures_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            h = self.holder(directory)
            artifact = Path(directory)/'reload.tox'
            artifact.write_bytes(b'not-native-test-copy')
            h.store('temp_paths', [str(artifact)])
            r = native_fixture.capture_failure(h, 'exercise', RuntimeError('rejected'))
            self.assertTrue(h.valid)
            self.assertFalse(r['native_fixture_pass'])
            self.assertEqual(r['native_errors_before_quiesce'], 'original native failure')
            self.assertEqual(r['artifacts'][0]['sha256'], hashlib.sha256(artifact.read_bytes()).hexdigest())
            evidence = Path(h.fetch('last_evidence'))
            native_fixture.cleanup(h)
            self.assertFalse(h.valid)
            self.assertTrue(evidence.is_file())
            self.assertTrue(artifact.is_file())

    def test_cleanup_requires_matching_captured_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            h = self.holder(directory)
            with self.assertRaisesRegex(ValueError, 'Capture evidence'):
                native_fixture.cleanup(h)
            wrong = Path(directory)/'other.json'
            wrong.write_text(json.dumps(dict(fixture_id='other')))
            h.store('last_evidence', str(wrong))
            with self.assertRaisesRegex(ValueError, 'different fixture'):
                native_fixture.cleanup(h)
            self.assertTrue(h.valid)

    def test_failed_stage_retains_holder_even_when_evidence_write_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            h = self.holder(directory)
            @native_fixture._preserve_failure
            def failed(holder):
                raise RuntimeError('stage rejected')
            with self.assertRaisesRegex(RuntimeError, 'stage rejected'):
                failed(h)
            self.assertTrue(h.valid)
            self.assertTrue(Path(h.fetch('last_evidence')).is_file())
            with patch.object(native_fixture, 'capture_failure', side_effect=OSError('disk full')):
                with self.assertRaisesRegex(RuntimeError, 'stage rejected'):
                    failed(h)
            self.assertTrue(h.valid)

    def test_quiesce_stops_all_callbacks_before_disconnect(self):
        with tempfile.TemporaryDirectory() as directory:
            h = self.holder(directory)
            callback = SimpleNamespace(path='/test/execute', par=SimpleNamespace(
                active=SimpleNamespace(val=True), syncfile=SimpleNamespace(val=True)), isCOMP=False)
            host = SimpleNamespace(enabled=True, connected=True, plugin=True)
            controller = SimpleNamespace(path='/test/generic1', par=SimpleNamespace(),
                ext=SimpleNamespace(RotoPythonExt=type('RotoPythonExt', (SimpleNamespace,), {})(_host=host)),
                isCOMP=True)
            controller.ext.RotoPythonExt.ownerComp = controller
            controller.extensions = [controller.ext.RotoPythonExt]
            def disconnect():
                self.assertFalse(callback.par.active.val)
                self.assertFalse(callback.par.syncfile.val)
            controller.Disconnect = disconnect
            h.findChildren = lambda: [controller, callback]
            self.assertEqual(native_fixture._quiesce(h), [])
            self.assertFalse(host.enabled or host.connected or host.plugin)

    def inherited_fixture(self, directory):
        h = self.holder(directory)
        external_host = SimpleNamespace(enabled=True, connected=True, plugin=True)
        external = SimpleNamespace(path='/original', par=SimpleNamespace(), calls=0)
        ancestor = SimpleNamespace(ownerComp=external, _host=external_host)
        external.ext = SimpleNamespace(RotoPythonExt=ancestor)
        external.Disconnect = lambda: setattr(external, 'calls', external.calls+1)
        h.ext = external.ext  # TD lookup may inherit from outside the holder.
        callbacks = [SimpleNamespace(path=h.path+'/execute'+str(i),
            par=SimpleNamespace(**{name: SimpleNamespace(val=True)
                                  for name in ('active', 'syncfile', 'loadonstart')}),
            ext=external.ext, isCOMP=False) for i in range(3)]
        controllers = []
        for name in ('source', 'generic_loaded'):
            c = SimpleNamespace(path=h.path+'/'+name, par=SimpleNamespace(), calls=0, isCOMP=True)
            c.ext = SimpleNamespace(RotoPythonExt=type('RotoPythonExt', (SimpleNamespace,), {})(ownerComp=c,
                _host=SimpleNamespace(enabled=True, connected=True, plugin=True)))
            c.extensions = [None, c.ext.RotoPythonExt,
                            SimpleNamespace(ownerComp=c)]  # unrelated local extension
            def disconnect(c=c):
                c.calls += 1
                self.assertTrue(all(not p.val for dat in callbacks
                                    for p in vars(dat.par).values()))
            c.Disconnect = disconnect
            controllers.append(c)
        # Neither inherited descendant has an owned/promoted Disconnect method.
        inside = SimpleNamespace(path=controllers[0].path+'/text', par=SimpleNamespace(),
                                 ext=controllers[0].ext, isCOMP=True, extensions=[])
        outside = SimpleNamespace(path=h.path+'/consumer', par=SimpleNamespace(), ext=external.ext,
                                  isCOMP=True, extensions=[])
        outside.Disconnect = external.Disconnect  # promoted inherited method is also unsafe
        h.findChildren = lambda: [*controllers, inside, outside, *callbacks]
        return h, controllers, external, callbacks

    def test_quiesce_skips_inherited_extensions_and_stops_each_local_owner_once(self):
        with tempfile.TemporaryDirectory() as directory:
            h, controllers, external, callbacks = self.inherited_fixture(directory)
            self.assertEqual(native_fixture._quiesce(h), [])
            self.assertEqual([c.calls for c in controllers], [1, 1])
            for c in controllers:
                host = c.ext.RotoPythonExt._host
                self.assertFalse(host.enabled or host.connected or host.plugin)
            self.assertEqual(external.calls, 0)
            host = external.ext.RotoPythonExt._host
            self.assertTrue(host.enabled and host.connected and host.plugin)

    def test_owned_quiesce_failures_retained_and_block_cleanup(self):
        with tempfile.TemporaryDirectory() as directory:
            for failure in ('access', 'owner', 'disconnect', 'disable', 'callback'):
                with self.subTest(failure=failure):
                    h, controllers, external, callbacks = self.inherited_fixture(directory)
                    c = controllers[0]
                    if failure == 'access':
                        class UnreadableExt:
                            @property
                            def RotoPythonExt(self):
                                raise RuntimeError('owned extension access failed')
                        c.ext = UnreadableExt()
                    elif failure == 'owner':
                        def unreadable_owner(extension):
                            raise AttributeError('owned extension owner unreadable')
                        broken = type('RotoPythonExt', (), {'ownerComp': property(unreadable_owner)})()
                        c.ext.RotoPythonExt = broken
                        c.extensions = [broken]
                    elif failure == 'disconnect':
                        c.Disconnect = lambda: (_ for _ in ()).throw(RuntimeError('owned Disconnect failed'))
                    elif failure == 'disable':
                        class UnwritableHost:
                            @property
                            def enabled(self): return True
                            @enabled.setter
                            def enabled(self, value): raise RuntimeError('owned host disable failed')
                        c.ext.RotoPythonExt._host = UnwritableHost()
                    else:
                        class UnwritablePar:
                            @property
                            def val(self): return True
                            @val.setter
                            def val(self, value): raise RuntimeError('callback stop failed')
                        callbacks[0].par.active = UnwritablePar()
                    h.fetch('result')['native_fixture_pass'] = True
                    artifact = Path(directory)/('saved-'+failure+'.tox')
                    artifact.write_bytes(b'retained-copy')
                    h.store('temp_paths', [str(artifact)])
                    record = native_fixture.capture_failure(h, 'quiesce-'+failure, RuntimeError('native stage failed'))
                    self.assertFalse(record['native_fixture_pass'])
                    self.assertTrue(record['quiesce_errors'])
                    self.assertEqual(record['native_errors_before_quiesce'], 'original native failure')
                    self.assertEqual(record['artifacts'][0]['sha256'], hashlib.sha256(artifact.read_bytes()).hexdigest())
                    self.assertEqual(controllers[1].calls, 1)  # independent owner still stops
                    with self.assertRaisesRegex(RuntimeError, 'incomplete'):
                        native_fixture.cleanup(h)
                    self.assertTrue(h.valid and artifact.is_file())
                    self.assertEqual(external.calls, 0)

    def test_unreadable_local_extension_attributeerror_cannot_pass_or_cleanup(self):
        with tempfile.TemporaryDirectory() as directory:
            for failure in ('named', 'local', 'mismatched'):
                with self.subTest(failure=failure):
                    h, controllers, external, callbacks = self.inherited_fixture(directory)
                    host = controllers[0].extensions[1]._host
                    if failure == 'named':
                        class UnreadableExt:
                            @property
                            def RotoPythonExt(self):
                                raise AttributeError('owned extension accessor unreadable')
                        controllers[0].ext = UnreadableExt()
                        expected = 'owned extension accessor unreadable'
                    elif failure == 'local':
                        class UnreadableInventory:
                            def __iter__(self):
                                raise AttributeError('owned local inventory unreadable')
                        controllers[0].extensions = UnreadableInventory()
                        expected = 'owned local inventory unreadable'
                    else:
                        # Local object exists, but named resolution returns an ancestor.
                        controllers[0].ext = external.ext
                        expected = 'Controller extension is not attached locally'
                    h.fetch('result')['native_fixture_pass'] = True
                    record = native_fixture._capture(h, native_fixture._checkpoint(h), 'finish')
                    self.assertFalse(record['native_fixture_pass'])
                    self.assertTrue(any(expected in error for error in record['quiesce_errors']))
                    self.assertEqual(controllers[0].calls, 0)
                    self.assertTrue(host.enabled and host.connected and host.plugin)
                    with self.assertRaisesRegex(RuntimeError, 'incomplete'):
                        native_fixture.cleanup(h)
                    self.assertTrue(h.valid)
                    self.assertEqual(external.calls, 0)

    def test_finish_keeps_strict_owned_quiesce_gate_and_saved_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            (source/'export_component.py').write_text(
                "def export(controller, path):\n    path.write_bytes(b'fake-generic-copy')\n")
            for fail in (False, 'disconnect', 'attribute', 'owner_mismatch'):
                with self.subTest(owned_disconnect_fails=fail):
                    h, controllers, external, callbacks = self.inherited_fixture(directory)
                    c, generic = controllers
                    for node in controllers:
                        extension = node.ext.RotoPythonExt
                        extension._host.connected = False; extension._process = None
                        extension._layouts = SimpleNamespace(all_plugins=lambda: [])
                        node.Applybinding = lambda: True
                        node.errors = lambda **kwargs: ''
                    c.GetActionState = lambda action_id: dict(available=True)
                    generic.GetActions = lambda: []
                    generic.GetControlStates = lambda: []
                    generic.par.Followcomp = SimpleNamespace(eval=lambda: False)
                    generic.par.Focuscomp = SimpleNamespace(eval=lambda: None)
                    h.op = lambda name: SimpleNamespace(par=SimpleNamespace(
                        Recalls=SimpleNamespace(eval=lambda: 0)))
                    h.loadTox = lambda path: generic
                    h.store('definitions', {})
                    h.fetch('result').update(source=directory, count_before_reload=0)
                    source_extension = c.ext.RotoPythonExt
                    if fail == 'disconnect':
                        c.Disconnect = lambda: (_ for _ in ()).throw(RuntimeError('owned Disconnect failed'))
                    elif fail == 'attribute':
                        class UnreadableExt:
                            @property
                            def RotoPythonExt(self):
                                raise AttributeError('owned extension accessor unreadable')
                        c.ext = UnreadableExt()
                    elif fail == 'owner_mismatch':
                        source_extension.ownerComp = external
                    evidence = source/('finish-'+str(fail)+'.json')
                    with patch.object(native_fixture, '_controller', return_value=(c, source_extension)):
                        if fail:
                            with self.assertRaisesRegex(AssertionError, 'quiesce recovery'):
                                native_fixture.finish(h, evidence)
                        else:
                            r = native_fixture.finish(h, evidence)
                            self.assertTrue(r['native_fixture_pass'])
                            self.assertEqual(r['quiesce_errors'], [])
                            self.assertEqual([node.calls for node in controllers], [1, 1])
                    record = json.loads(evidence.read_text())
                    self.assertEqual(record['native_fixture_pass'], not fail)
                    self.assertEqual(record['native_errors_before_quiesce'], 'original native failure')
                    self.assertTrue(h.valid)
                    self.assertEqual(external.calls, 0)
                    saved = [Path(item['path']) for item in record['artifacts']]
                    self.assertTrue(saved and all(p.is_file() for p in saved))
                    if fail:
                        with self.assertRaisesRegex(RuntimeError, 'incomplete'):
                            native_fixture.cleanup(h)
                        self.assertTrue(h.valid)
                    else:
                        native_fixture.cleanup(h)
                        self.assertFalse(h.valid)
                    self.assertTrue(all(p.is_file() for p in saved))

    def test_local_controller_owner_mismatch_is_failure_before_cleanup(self):
        with tempfile.TemporaryDirectory() as directory:
            h, controllers, external, callbacks = self.inherited_fixture(directory)
            c, generic = controllers
            extension = c.ext.RotoPythonExt
            extension.ownerComp = external
            self.assertTrue(any(extension is local for local in c.extensions))
            self.assertIs(c.ext.RotoPythonExt, extension)
            self.assertNotEqual(extension.ownerComp, c)
            h.fetch('result')['native_fixture_pass'] = True
            artifact = Path(directory)/'owner-mismatch.tox'
            artifact.write_bytes(b'fake-retained-copy')
            h.store('temp_paths', [str(artifact)])
            record = native_fixture._capture(h, native_fixture._checkpoint(h), 'finish')
            self.assertFalse(record['native_fixture_pass'])
            self.assertTrue(any('Controller extension owner does not match local COMP' in error
                                for error in record['quiesce_errors']))
            self.assertEqual(c.calls, 0)
            self.assertEqual(external.calls, 0)
            self.assertEqual(generic.calls, 1)
            self.assertTrue(extension._host.enabled and extension._host.connected and extension._host.plugin)
            self.assertTrue(external.ext.RotoPythonExt._host.enabled)
            self.assertEqual(record['native_errors_before_quiesce'], 'original native failure')
            self.assertEqual(record['artifacts'][0]['sha256'], hashlib.sha256(artifact.read_bytes()).hexdigest())
            evidence = Path(h.fetch('last_evidence'))
            with self.assertRaisesRegex(RuntimeError, 'incomplete'):
                native_fixture.cleanup(h)
            self.assertTrue(h.valid and artifact.is_file() and evidence.is_file())

    def test_evidence_collision_does_not_overwrite_or_destroy(self):
        with tempfile.TemporaryDirectory() as directory:
            h = self.holder(directory)
            path = Path(directory)/'accepted.json'
            path.write_text('original')
            with self.assertRaises(FileExistsError):
                native_fixture._capture(h, native_fixture._checkpoint(h), 'finish', evidence_path=path)
            self.assertEqual(path.read_text(), 'original')
            self.assertTrue(h.valid)

    def test_missing_or_unreadable_artifact_cannot_report_success_or_cleanup(self):
        with tempfile.TemporaryDirectory() as directory:
            for missing in (True, False):
                with self.subTest(missing=missing):
                    h = self.holder(directory)
                    path = Path(directory)/('missing.tox' if missing else 'unreadable.tox')
                    if not missing: path.write_bytes(b'placeholder')
                    h.store('temp_paths', [str(path)])
                    h.fetch('result')['native_fixture_pass'] = True
                    if missing:
                        r = native_fixture._capture(h, native_fixture._checkpoint(h), 'finish')
                    else:
                        with patch.object(Path, 'read_bytes', side_effect=OSError('hash read failed')):
                            r = native_fixture._capture(h, native_fixture._checkpoint(h), 'finish')
                    self.assertFalse(r['native_fixture_pass'])
                    self.assertEqual(r['artifact_capture_errors'], [str(path)])
                    # Missing copy prevents destroying the recoverable holder.
                    if missing:
                        with self.assertRaisesRegex(RuntimeError, 'incomplete'):
                            native_fixture.cleanup(h)
                    self.assertTrue(h.valid)

    def test_reload_load_failure_retains_actual_saved_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            h = self.holder(directory)
            e = SimpleNamespace(_follow=SimpleNamespace(refresh_links=lambda: None),
                _layouts=SimpleNamespace(capture=lambda **kwargs: None))
            c = SimpleNamespace(errors=lambda **kwargs: '', Disconnect=lambda: None)
            parent = SimpleNamespace(loadTox=lambda path: (_ for _ in ()).throw(RuntimeError('load rejected')))
            h.parent = lambda: parent
            h.save = lambda path: Path(path).write_bytes(b'saved-native-copy-placeholder')
            with patch.object(native_fixture, '_controller', return_value=(c,e)):
                with self.assertRaisesRegex(RuntimeError, 'load rejected'):
                    native_fixture.save_reload(h)
            self.assertFalse(h.valid)  # required destroy/load stage, not failure cleanup
            files = list(Path(directory).glob('*.tox'))
            self.assertEqual(len(files), 1)
            records = [json.loads(p.read_text()) for p in Path(directory).glob('save_reload-*.json')]
            self.assertEqual(len(records), 1)
            self.assertFalse(records[0]['native_fixture_pass'])
            self.assertEqual(records[0]['artifacts'][0]['sha256'], hashlib.sha256(files[0].read_bytes()).hexdigest())


if __name__ == '__main__':
    unittest.main()
