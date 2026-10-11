"""Exercise the real Clear UI/command boundary without native TD or MIDI."""
from types import SimpleNamespace as S
from unittest import TestCase
from live_model import ControllerCatalog
from test_live_model import Adapter, KEY
from ui import InspectorView


class ClearConfirmationTests(TestCase):
    def fixture(self):
        adapter=Adapter();model=ControllerCatalog(adapter);model.GetCatalog(KEY)
        view=object.__new__(InspectorView)
        view._model=model;view._context=KEY;view.selected=1
        view._token=model.GetToken(KEY,1);view._clear_pending=None;view._editors=[]
        view.CloseContextMenu=lambda:None;view.Key=lambda:KEY;view.IsLive=lambda:True
        view.CloseEditor=lambda:None;view._set_error=lambda text:None
        view._disarm_clear=lambda:setattr(view,'_clear_pending',None)
        view.ownerComp=S(op=lambda name:S(par=S(text='')))
        return adapter,model,view

    def test_confirmation_rechecks_once_and_dispatches_once(self):
        adapter,model,view=self.fixture()
        self.assertTrue(view.Action('clear'));self.assertEqual(adapter.clears,[])
        before=model.Stats()['sync_calls']
        self.assertTrue(view.Action('clear'))
        # One fresh preflight plus one post-mutation observation.
        self.assertEqual(model.Stats()['sync_calls']-before,2)
        self.assertEqual(adapter.clears,[(KEY,'target')])
        self.assertFalse(view.Action('clear'))
        self.assertEqual(len(adapter.clears),1)

    def test_touch_learn_or_replacement_between_clicks_blocks_clear(self):
        for drift in ('touch','learn','replacement','session'):
            adapter,model,view=self.fixture();view.Action('clear')
            if drift=='touch':adapter.records[KEY][0]['touched']=True
            elif drift=='learn':adapter.learning=True
            elif drift=='replacement':adapter.records[KEY][0]['id']='replacement'
            else:adapter.session+=1
            self.assertFalse(view.Action('clear'),drift)
            self.assertEqual(adapter.clears,[],drift)
            self.assertIsNone(view._clear_pending)
