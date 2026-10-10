"""User edits write immediately; programmatic updates never dispatch."""
from types import SimpleNamespace
from unittest import TestCase
from test_editor_actions import Panel
from test_live_model import Adapter,KEY
from live_model import ControllerCatalog
from ui import InspectorView

class LiveValueTests(TestCase):
    def setUp(self):
        self.adapter=Adapter();self.model=ControllerCatalog(self.adapter);self.model.GetCatalog(KEY)
        self.view=InspectorView.__new__(InspectorView);v=self.view
        v._model=self.model;v._context=KEY;v.selected=1;v._token=self.model.GetToken(KEY,1)
        v._value_scope=None;v._clear_pending=None;v._error='';v._editors=(Panel(),Panel())
        v._update_editor=lambda **kwargs:None
        v._draft=SimpleNamespace(par=SimpleNamespace(Value=.4))
    def test_user_input_writes_immediately_once_and_deduplicates_same_value(self):
        self.view.BeginValueEdit();self.assertTrue(self.view.LiveValue('.6'))
        self.assertEqual(self.adapter.writes,[(KEY,'target',.6)])
        self.assertFalse(self.view.LiveValue('.6'));self.assertEqual(len(self.adapter.writes),1)
    def test_unfocused_programmatic_input_does_not_write(self):
        self.assertFalse(self.view.LiveValue('.7'));self.assertEqual(self.adapter.writes,[])
        self.adapter.records[KEY][0]['value']=.8;self.model.Sync();self.view.EndValueEdit()
        self.assertEqual(self.view._draft.par.Value,.8);self.assertEqual(self.adapter.writes,[])
    def test_incomplete_invalid_or_outside_range_text_does_not_write(self):
        self.view.BeginValueEdit()
        for text in ('','-','.','nan','inf','oops','2'):
            self.assertFalse(self.view.LiveValue(text))
        self.assertEqual(self.adapter.writes,[])
    def test_stale_selection_mapping_learn_touch_are_rechecked(self):
        self.view.BeginValueEdit();self.adapter.learning=True
        self.assertFalse(self.view.LiveValue('.6'));self.adapter.learning=False
        self.adapter.records[KEY][0]['touched']=True;self.assertFalse(self.view.LiveValue('.6'))
        self.adapter.records[KEY][0]['touched']=False;self.adapter.records[KEY][0]['id']='replacement'
        self.assertFalse(self.view.LiveValue('.6'));self.view.selected=2
        self.assertFalse(self.view.LiveValue('.6'));self.assertEqual(self.adapter.writes,[])
    def test_value_focus_disarms_clear_and_end_follows_latest_value(self):
        self.view._clear_pending=('confirmation',999);self.view.BeginValueEdit()
        self.assertIsNone(self.view._clear_pending)
        self.view.LiveValue('.6');self.view.EndValueEdit()
        self.assertIsNone(self.view._value_scope);self.assertEqual(self.view._draft.par.Value,.6)
