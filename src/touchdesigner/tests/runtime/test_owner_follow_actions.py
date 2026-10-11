"""Issue #10 interoperability with accepted #12; source mocks, not TD/MIDI evidence."""
import copy
import unittest

import test_owner_follow
from layouts import Layouts
from protocol import digest, sysex


class OwnerFollowActionTests(unittest.TestCase):
    def fixture(self):
        fixture = test_owner_follow.OwnerFollowTests().fixture()
        e, m, f, a, b, la, lb, sample, reset, comps = fixture
        events = []
        ids = {}
        for layout in (la, lb, 'custom'):
            action_id = 'preset.' + layout
            e.RegisterAction(action_id, action_id, events.append)
            e.SelectLayout(layout)
            ids[layout] = e.AssignAction(1, action_id)['id']
        e.SelectLayout(la)
        f.observe(force=True)
        self.ack(e)
        return fixture, events, ids

    def ack(self, e):
        test_owner_follow.OwnerFollowTests().ack(e)

    def follow(self, f, sample, comp, flush=True):
        test_owner_follow.OwnerFollowTests().follow(f, sample, comp, flush)

    def button_ack(self, e):
        target = e._host.controls['button', 1]
        return sysex(11, 11, (target.index >> 7, target.index & 127,
                             *digest(target.target_id, 6), 1, 0, 0))

    def test_a_b_a_and_custom_keep_action_library_without_recall_or_value_writes(self):
        fixture, events, ids = self.fixture()
        e, m, f, a, b, la, lb, sample, reset, _ = fixture
        libraries = {layout: copy.deepcopy(m.plugin(layout)['targets'])
                     for layout in (la, lb, 'custom')}
        a.val = 2; b.val = 8
        for comp, layout, value in ((b.owner, lb, 8), (a.owner, la, 2)):
            self.follow(f, sample, comp)
            self.assertEqual(m.data['active'], layout)
            self.assertEqual(e.GetValue(), value)
            self.assertEqual(e.GetControlState(ids[layout])['action_id'], 'preset.' + layout)
            self.assertFalse(e.GetControlState(ids[layout])['mapped'])
            self.ack(e)
            e.GetPluginTargets(lb); e.GetLayoutRegistry()
        e.SelectLayout('custom')
        f.observe(force=True); f.flush()
        self.assertEqual(m.data['active'], 'custom')
        self.assertEqual(events, [])
        self.assertEqual((a.eval(), b.eval(), reset.pulses), (2, 8, 0))
        for layout, targets in libraries.items():
            self.assertEqual(m.plugin(layout)['targets'], targets)

    def test_lock_keeps_current_action_then_unlock_learn_fence_ignores_touch_and_fresh_ack(self):
        fixture, events, ids = self.fixture()
        e, m, f, a, b, la, lb, sample, _, _ = fixture
        old_ack = self.button_ack(e)
        m.locked = True
        self.follow(f, sample, b.owner, flush=False)
        self.assertFalse(f.gated)
        e._receive_midi((191, 20, 127)); e._receive_midi((191, 20, 0))
        self.assertEqual([event['action_id'] for event in events], ['preset.' + la])
        with self.assertRaisesRegex(ValueError, 'fenced'): e.RecallAction('preset.' + la)
        m.locked = False; f.unlocked()
        e._host.learning = True; m.touched.add(52); e._host.touched = True
        f.flush(); self.assertTrue(f.gated); self.assertEqual(m.data['active'], la)
        e._receive_midi(old_ack); e._receive_midi((191, 20, 127))
        e._host.learning = False
        self.assertTrue(m.touched)
        f.flush(); self.assertEqual(m.data['active'], lb)
        e._receive_midi(old_ack); e._receive_midi((191, 20, 127))
        self.assertFalse(e.GetControlState(ids[lb])['mapped'])
        self.assertEqual(len(events), 1)
        self.ack(e); e._receive_midi((191, 20, 127))
        self.assertEqual([event['action_id'] for event in events],
                         ['preset.' + la, 'preset.' + lb])

    def test_fresh_intent_during_commit_or_rollback_keeps_restored_actions_fenced(self):
        for rollback in (False, True):
            with self.subTest(rollback=rollback):
                fixture, events, ids = self.fixture()
                e, m, f, a, b, la, lb, sample, _, _ = fixture
                real = m.install; failed = [False]
                def install(record, *args, **kwargs):
                    if rollback and record['id'] == lb and not failed[0]:
                        failed[0] = True
                        raise RuntimeError('Action interoperability rollback')
                    result = real(record, *args, **kwargs)
                    if record['id'] == (la if rollback else lb):
                        dest, comp = (lb, b.owner) if rollback else (la, a.owner)
                        f.request(dest, m.track(dest)['id'], 'td', comp, m.plugin(dest)['id'])
                    return result
                m.install = install
                self.follow(f, sample, b.owner)
                self.assertTrue(f.gated); self.assertIsNotNone(f.pending)
                self.ack(e); e._receive_midi((191, 20, 127))
                with self.assertRaisesRegex(ValueError, 'fenced'): e.RecallAction('preset.' + la)
                self.assertEqual(events, [])
                m.install = real; f.flush()
                dest = lb if rollback else la
                self.assertEqual(m.data['active'], dest)
                self.assertFalse(e.GetControlState(ids[dest])['mapped'])
                self.ack(e); e._receive_midi((191, 20, 127))
                self.assertEqual([event['action_id'] for event in events], ['preset.' + dest])

    def test_action_callback_selection_uses_arbiter_and_does_not_dispatch_new_device(self):
        fixture, events, ids = self.fixture()
        e, m, f, a, b, la, lb, sample, _, _ = fixture
        def recall(event):
            events.append(event)
            self.follow(f, sample, b.owner)
            self.assertEqual(m.data['active'], la)  # callback is still dispatching
        e.RegisterAction('preset.' + la, 'A', recall, replace=True)
        e._receive_midi((191, 20, 127))
        self.assertTrue(f.gated); self.assertEqual(f.pending['layout_id'], lb)
        e._receive_midi((191, 20, 0)); e._receive_midi((191, 20, 127))
        f.flush(); self.assertEqual(m.data['active'], lb)
        self.assertFalse(e.GetControlState(ids[lb])['mapped'])
        self.assertEqual([event['action_id'] for event in events], ['preset.' + la])
        self.ack(e); e._receive_midi((191, 20, 127))
        self.assertEqual([event['action_id'] for event in events], ['preset.' + la, 'preset.' + lb])

    def test_partial_action_result_survives_follow_browse_and_keeps_mapping_error_separate(self):
        fixture, events, ids = self.fixture()
        e, m, f, a, b, la, lb, sample, _, _ = fixture
        def recall(event):
            events.append(event); a.val = 9
            return dict(status='partial', error='consumer readback')
        e.RegisterAction('preset.' + la, 'A', recall, replace=True)
        e._receive_midi((191, 20, 127))
        self.assertEqual(e.GetValue(), 9)
        self.follow(f, sample, b.owner)
        route = m.context()['key']
        row = next(row for row in e.GetPluginTargets(la) if row.get('action_id'))
        self.assertEqual(row['action_result']['status'], 'partial')
        self.assertEqual(row['mapping_error'], '')
        self.assertEqual(m.context()['key'], route)
        self.follow(f, sample, a.owner)
        state = e.GetControlState(ids[la])
        self.assertEqual(state['action_result']['status'], 'partial')
        self.assertEqual(state['mapping_error'], '')
        self.assertEqual(e.GetValue(), 9)
        self.assertEqual(len(events), 1)

    def test_reloaded_saved_owner_variant_reconstructs_action_without_recall(self):
        fixture, events, ids = self.fixture()
        e, m, f, a, b, la, lb, sample, _, _ = fixture
        track = e.CreateTrack(lb, 'Variant')
        variant = e.CreatePlugin(lb, track, 'Saved')
        e.SetPluginComp(lb, track, variant, b.owner)
        e.SelectPlugin(lb, track, variant)
        state = e.AssignAction(1, 'preset.' + lb)
        e.SelectLayout(la)
        saved = copy.deepcopy(m.plugin(lb, track, variant))
        e._layouts = m = Layouts(e); m.restore(); f.invalidate()
        sample[0] = (sample[0][0], (b.owner,))
        f.observe(force=True); f.flush()
        self.assertEqual(m.data['active'], la); self.assertEqual(events, [])
        self.follow(f, sample, a.owner); self.follow(f, sample, b.owner)
        self.assertEqual(m.context()['key'], (lb, track, variant))
        self.assertEqual(m.plugin()['targets'], saved['targets'])
        self.assertEqual(e.GetControlState(state['id'])['action_id'], 'preset.' + lb)
        self.assertEqual(events, [])


if __name__ == '__main__':
    unittest.main()
