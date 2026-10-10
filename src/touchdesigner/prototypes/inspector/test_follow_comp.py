"""Real command/adapter/controller callbacks; fake native pars/panels, no TD/MIDI PASS."""
from pathlib import Path
from types import SimpleNamespace as S
from unittest import TestCase
from unittest.mock import Mock, patch
import sys

SOURCE=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(SOURCE))
sys.path.insert(0,str(SOURCE/'code/py/roto_python'))
import test_owner_follow
import live_model
from live_model import ControllerCatalog,InspectorModel,TDControllerAdapter
from ui import InspectorView
from test_scheduled_action_details import Network,Parameters


class FollowParameter:
    name='Followcomp';enable=True;readOnly=False;mode='CONSTANT'
    def __init__(self,value,changed):self._value=value;self.changed=changed;self.writes=[]
    def eval(self):return self._value
    @property
    def val(self):return self._value
    @val.setter
    def val(self,value):
        previous=self._value;self._value=value;self.writes.append(value)
        if value!=previous:self.changed(self,previous)


class FollowCompTests(TestCase):
    def fixture(self):
        e,m,f,a,b,la,lb,sample,reset,comps=test_owner_follow.OwnerFollowTests().fixture()
        controller=e.ownerComp;controller.id=99;controller.valid=True
        native_op=controller.op
        inspector=S(fetch=lambda key,default=None:default,store=lambda key,value:None)
        controller.op=lambda path:inspector if path=='inspector' else native_op(path)
        controller.ext=S(RotoPythonExt=e)
        for name in ('GetLayoutContext','GetLayouts','GetCompContext','GetControlStates','GetControlCatalog','GetPluginTargets'):
            setattr(controller,name,getattr(e,name))
        controller.State=dict(Connected=False,Learning=False,Touched=False,Bindingvalid=True,Lasterror='')
        e._host.connected=e._host.plugin=False
        e._publish=Mock()  # TD-only outputs excluded; controller callback is real.
        network=Network();binding=[controller];callbacks=[]
        native={};exec((SOURCE/'code/py/roto_python/parameter_callbacks.py').read_text(),dict(parent=S(RotoPython=controller)),native)
        def changed(par,prev):
            callbacks.append((par.name,prev));native['onValueChange'](par,prev)
            network.parameter_changed()  # actual installed observer callback text
        object.__setattr__(controller.par,'Followcomp',FollowParameter(True,changed))
        scheduler=patch.object(live_model,'run',network.frames.run,create=True)
        scheduler.start();self.addCleanup(scheduler.stop)
        owner=S(par=S(Controller=S(eval=lambda:binding[0])),op=lambda name:None)
        adapter=TDControllerAdapter(owner);adapter._definitions=lambda rows,key:rows
        model=InspectorModel.__new__(InspectorModel)
        model.ownerComp=network;model._queued_run=model._sync_run=None
        model.RefreshWatchers=lambda:None;model.WatchOwners=lambda:[binding[0]] if binding[0] else []
        ControllerCatalog.__init__(model,adapter,schedule=model._schedule_flush)
        network.install(model)
        return e,m,f,a,b,la,lb,sample,reset,controller,network,model,binding,callbacks

    def test_off_on_native_callback_once_current_selection_no_action_or_pulse(self):
        e,m,f,a,b,la,lb,sample,reset,c,n,model,binding,calls=self.fixture()
        events=[];e.RegisterAction('preset','Preset',events.append);e.AssignAction(2,'preset')
        with patch.object(live_model,'run',n.frames.run,create=True):
            self.assertFalse(model.SetFollowComp(False,model.FollowCompToken()))
            sample[0]=(sample[0][0],(b.owner,))
            f.observe(force=True);f.flush();self.assertEqual(m.data['active'],la)
            self.assertTrue(model.SetFollowComp(True,model.FollowCompToken()))
            n.frames.drain()
            self.assertEqual(m.data['active'],lb)
            self.assertEqual(c.par.Followcomp.writes,[False,True])
            self.assertEqual(calls,[('Followcomp',True),('Followcomp',False)])
            self.assertTrue(model.SetFollowComp(True,model.FollowCompToken()))
        self.assertEqual(c.par.Followcomp.writes,[False,True])  # no-op has no callback
        self.assertEqual(events,[]);self.assertEqual(reset.pulses,0)
        self.assertEqual((a.eval(),b.eval()),(5,5));self.assertIsNone(e._process)

    def test_stale_preference_session_routing_or_rebind_never_writes(self):
        for change in ('preference','session','routing','rebind','missing'):
            with self.subTest(change=change):
                e,m,f,a,b,la,lb,sample,reset,c,n,model,binding,calls=self.fixture()
                token=model.FollowCompToken()
                if change=='preference':c.par.Followcomp._value=False
                elif change=='session':f.connection_generation+=1
                elif change=='routing':e.SelectLayout('custom')
                elif change=='rebind':binding[0]=self.fixture()[9]  # different valid bound controller
                else:binding[0]=None
                with patch.object(live_model,'run',n.frames.run,create=True):
                    with self.assertRaises(ValueError):model.SetFollowComp(False,token)
                self.assertEqual(c.par.Followcomp.writes,[]);self.assertEqual(calls,[])

    def test_missing_readonly_mode_unavailable_owner_and_mutation_guards(self):
        for guard in ('missing','readonly','expression','disabled','legacy','owner','quarantine','mutating','dispatch','restore','paused'):
            with self.subTest(guard=guard):
                e,m,f,a,b,la,lb,sample,reset,c,n,model,binding,calls=self.fixture()
                par=c.par.Followcomp
                if guard=='missing':object.__setattr__(c.par,'Followcomp',None)
                elif guard=='readonly':par.readOnly=True
                elif guard=='expression':par.mode='EXPRESSION'
                elif guard=='disabled':par.enable=False
                elif guard=='legacy':m.legacy=True
                elif guard=='owner':a.owner.valid=False
                elif guard=='quarantine':m.quarantined=True
                elif guard=='mutating':m.mutating=True
                elif guard=='dispatch':e._dispatching=True
                elif guard=='restore':e._restoring=True
                else:f.paused=True
                with patch.object(live_model,'run',n.frames.run,create=True):
                    model.Sync()
                    self.assertFalse(model.FollowCompCapability()['enabled'])
                    if guard=='missing':self.assertIsNone(model.FollowCompCapability()['state'])
                    with self.assertRaises(ValueError):model.SetFollowComp(False,model.FollowCompToken())
                self.assertEqual(par.writes,[]);self.assertEqual(calls,[])

    def test_lock_learn_go_through_callback_and_touch_does_not_defer_follow(self):
        e,m,f,a,b,la,lb,sample,reset,c,n,model,binding,calls=self.fixture()
        with patch.object(live_model,'run',n.frames.run,create=True):
            model.SetFollowComp(False,model.FollowCompToken())
            m.locked=True;e._host.learning=True;m.touched.add(52)
            sample[0]=(sample[0][0],(b.owner,))
            model.SetFollowComp(True,model.FollowCompToken())
            self.assertEqual(m.data['active'],la);self.assertEqual(f.pending['layout_id'],lb)
            m.locked=False;f.unlocked();f.flush();self.assertTrue(f.gated)
            e._host.learning=False;self.assertTrue(m.touched);f.flush()
            self.assertEqual(m.data['active'],lb)
            self.assertFalse(e.GetControlState()['mapped']);self.assertEqual(reset.pulses,0)
            n.frames.drain()
        self.assertEqual(len(calls),2)

    def view(self,model,key,live=True):
        v=InspectorView.__new__(InspectorView);v._model=model;v._context=key
        v._follow_routing=live;v._follow_comp_token=None;v._device_message=''
        label=S(par=S(text=''));button=S(par=S(enable=True),op=lambda name:label)
        v.ownerComp=S(op=lambda name:button if name=='follow_comp' else S(par=S(text='')))
        v._filter='actions';v._mapping=S(open=True,message='draft');v.selected=None
        v.Key=lambda:key;v._update_main_status=lambda:None;v.Refresh=Mock();v.CloseContextMenu=Mock()
        v._notifications=v._dirty=v._metadata_dirty=0;v._clear_pending=None
        v._visible=lambda:False;v.ConfigureMenus=Mock();v._theme=v._update_follow_comp
        return v,button,label

    def test_both_views_empty_targets_observer_off_on_without_browse_or_draft_change(self):
        e,m,f,a,b,la,lb,sample,reset,c,n,model,binding,calls=self.fixture()
        empty=e.CreateLayout('Empty');e.SelectLayout(empty);model.Sync()
        active=m.context()['key'];browse=(la,m.track(la)['id'],m.plugin(la)['id'])
        v,button,label=self.view(model,active);w,other,other_label=self.view(model,browse,False)
        for i,view in enumerate((v,w)):model.Subscribe(str(i),view._context,view.OnModelChange)
        with patch.object(live_model,'run',n.frames.run,create=True):
            n.frames.drain();v._update_follow_comp();w._update_follow_comp()
            self.assertTrue(v.ToggleFollowComp());n.frames.drain()
            self.assertEqual((label.par.text,other_label.par.text),('Follow COMP: OFF',)*2)
            self.assertTrue(w.ToggleFollowComp());n.frames.drain()
            self.assertEqual((label.par.text,other_label.par.text),('Follow COMP: ON',)*2)
        self.assertEqual(w.Key(),browse);self.assertFalse(w._follow_routing)
        self.assertEqual((w._filter,w._mapping.open,w._mapping.message),('actions',True,'draft'))
        self.assertGreater(v._notifications,0);self.assertGreater(w._notifications,0)
        v.Refresh.assert_not_called();w.Refresh.assert_not_called()
        self.assertEqual(model.Stats()['subscriber_errors'],[])

    def test_existing_live_action_never_changes_follow_preference(self):
        e,m,f,a,b,la,lb,sample,reset,c,n,model,binding,calls=self.fixture()
        v,button,label=self.view(model,m.context()['key'],False)
        self.assertTrue(v.Action('follow'))
        self.assertTrue(v._follow_routing);v.Refresh.assert_called_once()
        self.assertEqual(c.par.Followcomp.writes,[]);self.assertEqual(calls,[])

    def test_view_stale_token_displays_actual_state_keeps_browse_draft(self):
        e,m,f,a,b,la,lb,sample,reset,c,n,model,binding,calls=self.fixture()
        v,button,label=self.view(model,m.context()['key'],False);v._update_follow_comp()
        f.connection_generation+=1
        with patch.object(live_model,'run',n.frames.run,create=True):self.assertFalse(v.ToggleFollowComp())
        self.assertEqual(label.par.text,'Follow COMP: ON')
        self.assertIn('changed',v._device_message)
        self.assertFalse(v._follow_routing);self.assertTrue(v._mapping.open)
        self.assertEqual(c.par.Followcomp.writes,[])

    def test_shared_builder_installs_two_views_and_one_release_ingress(self):
        class Node:
            def __init__(self,name):self.name=name;self.par=Parameters();self.children={};self.panel=S(inside=True)
            def op(self,name):return self.children.get(name)
            def create(self,kind,name):
                node=Node(name);self.children[name]=node;return node
        views=[Node('main'),Node('popup')]
        for view in views:view.create(None,'text_title')
        source=(SOURCE/'prototypes/inspector/build_activation.py').read_text()
        # Execute the real shared builder and reusable button helper on fake TD nodes.
        exec(compile(source,'build_activation.py','exec'),dict(
                project=S(folder=str(SOURCE)),activation_views=views,op=lambda path:views[0],
                containerCOMP=object(),textCOMP=object(),panelexecuteDAT=object()))
        calls=[]
        for view in views:
            button=view.op('follow_comp');callback=view.op('click_follow_comp')
            self.assertEqual(button.op('text_label').par.text.val,'Follow COMP: —')
            self.assertFalse(button.par.enable.val)
            self.assertEqual((button.par.leftoffset.val,button.par.rightoffset.val),(-150,-62))
            self.assertEqual(button.par.y.expr,'parent().height-8-me.height')
            self.assertEqual(view.op('text_title').par.w.expr,'parent().width-164')
            namespace=dict(parent=S(InspectorDemo=S(FollowCompHint=lambda value:calls.append(('hint',value)),Action=lambda value:calls.append(('action',value)))))
            namespace['parent']=Parent(view,namespace['parent'].InspectorDemo)
            exec(callback.text,namespace)
            namespace['onOffToOn'](S(name='rollover'))
            namespace['onOnToOff'](S(name='rollover'))
            namespace['onOffToOn'](S(name='lselect'))
            namespace['onOnToOff'](S(name='lselect'))
        self.assertEqual(calls,[('hint',True),('hint',False),('action','follow_comp')]*2)


class Parent:
    def __init__(self,view,extension):self.view=view;self.InspectorDemo=extension
    def __call__(self):return self.view
