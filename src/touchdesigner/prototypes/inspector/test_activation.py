"""Explicit activation rejects stale intent and never writes target Values."""
from types import SimpleNamespace as S
from unittest import TestCase
from live_model import ControllerCatalog,TDControllerAdapter
from ui import InspectorView
from test_live_model import Adapter,KEY,state

OTHER=('layout','track','other')
class ActivationAdapter(Adapter):
    def __init__(self):
        super().__init__();self.records[OTHER]=[state(.7)];self.activations=[];self.reason='';self.fail=False
    def Status(self):return dict(super().Status(),ActivationReason=self.reason)
    def Activate(self,key):
        if self.fail:raise ValueError('Fixture install failed')
        self.activations.append(key);self.active=key

class ActivationTests(TestCase):
    def setup_model(self):
        a=ActivationAdapter();m=ControllerCatalog(a);m.GetCatalog(OTHER);return a,m
    def test_browse_and_value_updates_never_route_but_one_activation_does(self):
        a,m=self.setup_model();token=m.ActivationToken(OTHER)
        a.records[KEY][0]['value']=.9;m.Sync()
        self.assertEqual(a.activations,[])
        self.assertTrue(m.Activate(OTHER,token));self.assertEqual(a.activations,[OTHER]);self.assertEqual(a.writes,[])
        self.assertEqual(m.Status['Active'],OTHER)
        with self.assertRaisesRegex(ValueError,'Already'):m.Activate(OTHER,m.ActivationToken(OTHER))
        self.assertEqual(a.activations,[OTHER])
    def test_fresh_session_routing_or_deleted_destination_rejects_intent(self):
        for change in ('session','routing','deleted'):
            a,m=self.setup_model();token=m.ActivationToken(OTHER)
            if change=='session':a.session+=1
            elif change=='routing':a.active=OTHER
            else:del a.records[OTHER]
            with self.assertRaises(ValueError):m.Activate(OTHER,token)
            self.assertEqual(a.activations,[])
    def test_fresh_guard_and_install_failure_keep_old_routing(self):
        a,m=self.setup_model();token=m.ActivationToken(OTHER);a.reason='Exit LEARN'
        with self.assertRaisesRegex(ValueError,'LEARN'):m.Activate(OTHER,token)
        a.reason='';a.fail=True
        with self.assertRaisesRegex(ValueError,'install failed'):m.Activate(OTHER,token)
        self.assertEqual(m.Status['Active'],KEY);self.assertEqual(a.activations,[])
    def test_actual_adapter_guards_all_selection_fences(self):
        h=S(learning=False,touched=False,connected=True,plugin=True)
        manager=S(legacy=False,touched=False,locked=False,mutating=False)
        f=S(paused=False,gated=False,backlog=False,pending=None)
        e=S(_host=h,_layout_manager=lambda:manager,_follow=f,_dispatching=False,_process=S())
        calls=[];c=S(ext=S(RotoPythonExt=e),SelectPlugin=lambda *k:calls.append(k))
        adapter=TDControllerAdapter(S(par=S(Controller=S(eval=lambda:c))));adapter.Exists=lambda key:True
        guards=((manager,'legacy',True),(h,'learning',True),(h,'touched',True),(manager,'touched',True),
            (manager,'locked',True),(manager,'mutating',True),(e,'_dispatching',True),
            (f,'paused',True),(f,'gated',True),(f,'backlog',True),(f,'pending',{'request':1}),(h,'plugin',False))
        for obj,key,value in guards:
            old=getattr(obj,key);setattr(obj,key,value)
            self.assertTrue(adapter.ActivationReason())
            with self.assertRaises(ValueError):adapter.Activate(OTHER)
            setattr(obj,key,old)
        self.assertEqual(calls,[]);adapter.Activate(OTHER);self.assertEqual(calls,[OTHER])
        e._process=None;h.connected=h.plugin=False
        self.assertEqual(adapter.ActivationReason(),'')  # Offline saved library selection is supported.
    def test_adapter_missing_destination_never_calls_selector(self):
        adapter=TDControllerAdapter(S(par=S(Controller=S(eval=lambda:None))));adapter.ActivationReason=lambda:'';adapter.Exists=lambda key:False
        with self.assertRaisesRegex(ValueError,'removed'):adapter.Activate(OTHER)

class ActivationViewTests(TestCase):
    def view(self):
        v=InspectorView.__new__(InspectorView);v._context=OTHER;v._activation_token=('snapshot',);v._follow_routing=False
        v.calls=[];v.IsLive=lambda:True;v.Key=lambda:OTHER;v.CloseEditor=lambda:v.calls.append('close');v.Refresh=lambda:v.calls.append('refresh')
        v._model=S(Activate=lambda *args:v.calls.append(args) or True)
        return v
    def test_success_follows_activated_context_and_closes_old_draft(self):
        v=self.view();self.assertTrue(v.ActivateDevice())
        self.assertEqual(v.calls,[(OTHER,('snapshot',)),'close','refresh']);self.assertTrue(v._follow_routing)
    def test_failed_activation_keeps_draft_and_browse(self):
        v=self.view()
        def fail(*args):raise ValueError('Unlock hardware')
        v._model.Activate=fail
        self.assertFalse(v.ActivateDevice());self.assertEqual(v.calls,['refresh']);self.assertFalse(v._follow_routing)
        self.assertEqual(v._device_message,'Unlock hardware')
    def test_changed_view_key_does_not_dispatch(self):
        v=self.view();v.Key=lambda:KEY
        self.assertFalse(v.ActivateDevice());self.assertEqual(v.calls,[])
