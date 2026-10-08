"""Exercise the actual editor actions without native windows or MIDI."""
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch
from live_model import ControllerCatalog
from test_live_model import Adapter, KEY
from ui import InspectorView,ICONS

class Panel:
    def __init__(self):self.par=SimpleNamespace(text='');self.children={}
    def op(self,name):return self.children.setdefault(name,Panel())

class EditorActionsTests(TestCase):
    def setUp(self):
        self.adapter=Adapter();self.model=ControllerCatalog(self.adapter)
        self.view=InspectorView.__new__(InspectorView)
        self.view._model=self.model;self.view._context=KEY;self.view.selected=1
        self.view._token=self.model.GetToken(KEY,1);self.view._original=None
        self.view._clear_pending=None;self.view._error=''
        self.view._editors=(Panel(),Panel());self.view.ownerComp=Panel()
        self.view.Key=lambda:KEY;self.view._editor_layout=lambda:None;self.view._theme=lambda:None

    def test_clear_requires_second_click_and_keeps_parameter_value(self):
        original_value=self.adapter.records[KEY][0]['value']
        self.assertTrue(self.view.Action('clear'));self.assertEqual(self.adapter.clears,[])
        for editor in self.view._editors:self.assertEqual(editor.op('clear/text_label').par.text,ICONS['confirm'])
        self.assertTrue(self.view.Action('clear'))
        self.assertEqual(self.adapter.clears,[(KEY,'target')]);self.assertIsNone(self.view.selected)
        self.assertEqual(self.adapter.writes,[]);self.assertEqual(original_value,.4)

    def test_expired_confirmation_requires_two_fresh_clicks(self):
        with patch('ui.monotonic',return_value=10):self.view.Action('clear')
        with patch('ui.monotonic',return_value=19):self.view.Action('clear')
        self.assertEqual(self.adapter.clears,[])
        with patch('ui.monotonic',return_value=20):self.view.Action('clear')
        self.assertEqual(len(self.adapter.clears),1)

    def test_changed_mapping_cancels_confirmation_without_removing_replacement(self):
        self.view.Action('clear');self.adapter.records[KEY][0]['id']='replacement'
        self.assertFalse(self.view.Action('clear'))
        self.assertEqual(self.adapter.clears,[]);self.assertIsNone(self.view._clear_pending)
        self.assertIn('Mapping changed',self.view._error)

    def test_cancel_and_ping_disarm_clear(self):
        self.view.Action('clear');self.view.Action('cancel')
        self.assertIsNone(self.view.selected);self.assertIsNone(self.view._clear_pending)
        self.view.selected=1;self.view._token=self.model.GetToken(KEY,1)
        self.view.Action('clear');self.adapter.learning=True
        self.assertTrue(self.view.Action('ping'));self.assertIsNone(self.view._clear_pending)
        self.assertEqual(self.adapter.clears,[]);self.assertEqual(len(self.adapter.pings),1)
        self.assertIn('mapping already acknowledged',self.view._error)

    def test_ping_already_acknowledged_does_not_claim_a_new_ack(self):
        self.adapter.learning=True
        self.assertTrue(self.view.Action('ping'))
        self.assertEqual(self.view._error,'Ping sent · mapping already acknowledged')
        self.assertEqual(len(self.adapter.pings),1)

    def test_ping_unacknowledged_mapping_waits_for_hardware(self):
        self.adapter.records[KEY][0].update(mapped=False,requires_relearn=True)
        self.model.Sync();self.view._token=self.model.GetToken(KEY,1)
        self.adapter.learning=True
        self.assertTrue(self.view.Action('ping'))
        self.assertEqual(self.view._error,'Ping sent · awaiting hardware ACK')

    def test_ping_refreshes_cached_ack_before_describing_readiness(self):
        self.assertTrue(self.model.Info(KEY,1)['mapped'])
        self.adapter.records[KEY][0].update(mapped=False,requires_relearn=True)
        self.adapter.learning=True
        # No manual Sync: the validated Ping command must refresh this target.
        self.assertTrue(self.view.Action('ping'))
        self.assertEqual(self.view._error,'Ping sent · awaiting hardware ACK')

    def test_ping_without_learn_explains_required_step_and_does_not_offer(self):
        self.assertFalse(self.view.Action('ping'))
        self.assertIn('HW LEARN',self.view._error);self.assertEqual(self.adapter.pings,[])

    def test_learn_started_after_confirm_does_not_clear(self):
        self.view.Action('clear');self.adapter.learning=True
        self.assertFalse(self.view.Action('clear'))
        self.assertEqual(self.adapter.clears,[]);self.assertIsNone(self.view._clear_pending)

    def test_hover_names_icons_without_offering_or_hiding_clear_confirmation(self):
        self.view.Hint('ping',True)
        self.assertIn('Ping',self.view._editors[0].op('text_status').par.text)
        self.assertEqual(self.adapter.pings,[])
        self.view.Action('clear');question=self.view._error
        self.view.Hint('ping',True);self.view.Hint('ping',False)
        self.assertEqual(self.view._editors[0].op('text_status').par.text,question)
