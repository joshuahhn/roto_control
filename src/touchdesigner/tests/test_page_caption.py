"""Main-screen page hints follow acknowledged bindings without target writes."""
import copy
import json
from types import SimpleNamespace
import unittest

import test_assignment
import test_layouts
from protocol import digest, sysex, text13
from text_comp_follow import CompFollower


class PageCaptionTests(unittest.TestCase):
    def fixture(self):
        e, manager, parameter = test_layouts.LayoutTests().fixture()
        parameter.owner.id = 101
        parameter.page = SimpleNamespace(name='Demo')
        e._receive = e._pending = b''
        e._follow = None
        e._page_caption = None
        return e, manager, parameter

    def ack(self, e, key=('knob', 1), *, wrong=False):
        target = e._host.controls[key]
        identity = digest(target.target_id, 6)
        if wrong:
            identity = (identity[0] ^ 1, *identity[1:])
        e._receive_midi(sysex(11, 11, (target.index >> 7, target.index & 127,
            *identity, int(key[0] == 'button'), key[1] - 1, 0)))
        e._pending = b''

    def flush(self, e, now):
        e._flush_page_caption(now)
        messages = [tuple(json.loads(line)['midi']) for line in e._pending.splitlines()]
        e._pending = b''
        return messages

    def caption(self, label):
        return sysex(10, 0x16, text13(label))

    def test_hint_expires_once_and_never_renames_group_or_writes_target(self):
        e, m, p = self.fixture()
        self.ack(e)
        before = copy.deepcopy(m.data), p.eval(), p.pulses
        self.assertEqual(self.flush(e, 10), [self.caption('Demo')])
        for now in (10, 10.5, 11.999):
            self.assertEqual(self.flush(e, now), [])
        self.assertEqual(self.flush(e, 12), [self.caption('EFFECT')])
        self.assertEqual(self.flush(e, 100), [])
        self.assertEqual((m.data, p.eval(), p.pulses), before)
        self.assertEqual(e._host.track_name, 'EFFECT')

    def test_real_parameter_page_change_restarts_hint_without_value_event(self):
        e, m, p = self.fixture()
        self.ack(e)
        self.flush(e, 0)
        p.page = SimpleNamespace(name='Controls')
        self.assertEqual(self.flush(e, 1), [self.caption('Controls')])
        self.assertEqual(self.flush(e, 2), [])
        self.assertEqual(self.flush(e, 3), [self.caption('EFFECT')])
        p.page.name = 'Demo'
        self.assertEqual(self.flush(e, 4), [self.caption('Demo')])

    def test_partial_mapping_uses_only_matching_ack_then_mixed_pages_fall_back(self):
        e, m, p = self.fixture()
        b = test_assignment.AssignmentTests().parameter(name='Amount')
        b.owner.id = 101
        b.page = SimpleNamespace(name='Controls')
        e.AssignParameter('knob', 2, b)
        e._pending = b''
        self.assertEqual(self.flush(e, 0), [self.caption('EFFECT')])
        self.ack(e, wrong=True)
        self.assertEqual(self.flush(e, .1), [])
        self.ack(e)
        self.assertFalse(e._host.mapped)  # No invented global-ready requirement.
        self.assertEqual(self.flush(e, .2), [self.caption('Demo')])
        self.ack(e, ('knob', 2), wrong=True)
        self.assertEqual(self.flush(e, .3), [])
        self.ack(e, ('knob', 2))
        self.assertEqual(self.flush(e, .4), [self.caption('EFFECT')])
        e._receive_midi(sysex(11, 14, (0, 1)))
        self.assertEqual(self.flush(e, .5), [self.caption('Demo')])

    def test_identically_named_pages_on_different_comps_are_ambiguous(self):
        e, m, p = self.fixture()
        b = test_assignment.AssignmentTests().parameter(name='Amount')
        b.owner.path = '/other'
        b.owner.id = 202
        b.page = SimpleNamespace(name='Demo')
        e.AssignParameter('knob', 2, b)
        self.ack(e)
        self.ack(e, ('knob', 2))
        self.assertEqual(self.flush(e, 0), [self.caption('EFFECT')])

    def test_callback_invalid_or_missing_page_never_claims_a_page(self):
        for condition in ('callback', 'invalid', 'deleted_owner', 'missing_page'):
            with self.subTest(condition=condition):
                e, m, p = self.fixture()
                self.ack(e)
                binding = e._collection.bindings['knob', 1]
                if condition == 'callback':
                    binding.parameter = None
                elif condition == 'invalid':
                    binding.valid = False
                elif condition == 'deleted_owner':
                    p.owner.valid = False
                else:
                    del p.page
                self.assertEqual(self.flush(e, 0), [self.caption('EFFECT')])

    def test_empty_page_and_same_name_recall_restart_after_expired_hint(self):
        e, m, p = self.fixture()
        first = copy.deepcopy(m.record()['targets'][0])
        self.ack(e)
        self.flush(e, 0)
        self.flush(e, 2)
        e._receive_midi(sysex(10, 21))
        self.assertEqual(self.flush(e, 3), [self.caption('EFFECT')])
        e._receive_midi(sysex(11, 11, (first['index'] >> 7, first['index'] & 127,
            *digest(first['identity'], 6), 0, 0, 0)))
        e._pending = b''
        self.assertEqual(self.flush(e, 4), [self.caption('Demo')])

    def test_guards_defer_output_until_safe_and_do_not_extend_deadline(self):
        for guard in ('learning', 'touched', 'receive', 'restore_pending',
                      'restoring', 'mutating', 'locked', 'gated', 'pending', 'paused', 'backlog'):
            with self.subTest(guard=guard):
                e, m, p = self.fixture()
                self.ack(e)
                e._follow = SimpleNamespace(gated=False, pending=None, paused=False,
                    backlog=False, token=(1, 1), context_output=CompFollower.context_output)
                self.flush(e, 0)
                target, attribute, value = (e._host, guard, True)
                if guard in ('receive', 'restore_pending', 'restoring'):
                    target, attribute = e, '_' + guard
                    value = b'partial' if guard == 'receive' else True
                elif guard in ('mutating', 'locked'):
                    target = m
                elif guard in ('gated', 'pending', 'paused', 'backlog'):
                    target = e._follow
                original = getattr(target, attribute)
                setattr(target, attribute, value)
                self.assertEqual(self.flush(e, 3), [])
                setattr(target, attribute, original)
                self.assertEqual(self.flush(e, 4), [self.caption('EFFECT')])

    def test_native_selection_and_new_session_replay_same_page_hint(self):
        e, m, p = self.fixture()
        self.ack(e)
        self.flush(e, 0)
        self.flush(e, 2)
        e._host._command(11, 8, (0, 0, 0))
        e._pending = b''
        self.assertEqual(self.flush(e, 3), [self.caption('Demo')])
        e._host.plugin = False
        self.assertEqual(self.flush(e, 4), [])
        e._host.plugin = True
        self.assertEqual(self.flush(e, 5), [self.caption('Demo')])

    def test_queued_caption_is_removed_by_existing_context_fence(self):
        e, m, p = self.fixture()
        self.ack(e)
        e._follow = CompFollower(e, lambda: (None, ()))
        e._flush_page_caption(0)
        self.assertIn(self.caption('Demo'), [tuple(json.loads(line)['midi']) for line in e._pending.splitlines()])
        e._follow.fence()
        self.assertEqual(e._pending, b'')
        self.assertEqual(self.flush(e, 1), [])


if __name__ == '__main__':
    unittest.main()
