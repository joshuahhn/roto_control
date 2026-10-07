"""Native Delete pulses require a current, explicit popup selection."""
import copy
from types import SimpleNamespace
import unittest

import test_layouts


class DeletePopupTests(unittest.TestCase):
    def fixture(self):
        ext, manager, parameter = test_layouts.LayoutTests().fixture()
        ext.ownerComp.valid = True
        ext.ownerComp.ext = SimpleNamespace(RotoPythonExt=ext)
        ext._delete_request = None
        requests = []
        ext._open_delete_menu = requests.append
        return ext, manager, requests

    def request(self, ext, requests, kind):
        ext.onParPulse(SimpleNamespace(name='Deletetrack' if kind == 'track' else 'Deletelayout'))
        return requests[-1]

    def test_cancel_preserves_configuration_then_confirm_deletes_track_once(self):
        ext, manager, requests = self.fixture()
        other = manager.create_track('custom', 'Other')
        before = copy.deepcopy(manager.data)
        details = self.request(ext, requests, 'track')
        ext._on_delete_choice(dict(details=details, item='Cancel'))
        self.assertEqual(manager.data, before)
        details = self.request(ext, requests, 'track')
        choice = dict(details=details, item=details['item'])
        ext._on_delete_choice(choice)
        self.assertEqual([t['id'] for t in manager.layout()['tracks']], [other])
        ext._on_delete_choice(choice)
        self.assertEqual(len(manager.layout()['tracks']), 1)

    def test_layout_confirmation_deletes_only_requested_layout(self):
        ext, manager, requests = self.fixture()
        other = manager.create('Other')
        details = self.request(ext, requests, 'layout')
        self.assertEqual(len(manager.data['records']), 2)
        ext._on_delete_choice(dict(details=details, item=details['item']))
        self.assertEqual([r['id'] for r in manager.data['records']], [other])

    def test_context_switch_and_reload_expire_popup(self):
        ext, manager, requests = self.fixture()
        other = manager.create('Other')
        details = self.request(ext, requests, 'layout')
        manager.select(other)
        ext._on_delete_choice(dict(details=details, item=details['item']))
        self.assertEqual(len(manager.data['records']), 2)
        details = self.request(ext, requests, 'layout')
        ext.ownerComp.ext.RotoPythonExt = object()
        ext._on_delete_choice(dict(details=details, item=details['item']))
        self.assertEqual(len(manager.data['records']), 2)

    def test_lock_changed_after_open_still_blocks_delete(self):
        ext, manager, requests = self.fixture()
        manager.create('Other')
        details = self.request(ext, requests, 'layout')
        manager.locked = True
        ext._on_delete_choice(dict(details=details, item=details['item']))
        self.assertEqual(len(manager.data['records']), 2)
        self.assertIn('Unlock', ext._last_error)

    def test_last_layout_and_track_do_not_open_popup(self):
        ext, manager, requests = self.fixture()
        ext.onParPulse(SimpleNamespace(name='Deletelayout'))
        self.assertIn('last Layout', ext._last_error)
        ext.onParPulse(SimpleNamespace(name='Deletetrack'))
        self.assertIn('last Track', ext._last_error)
        self.assertEqual(requests, [])


if __name__ == '__main__':
    unittest.main()
