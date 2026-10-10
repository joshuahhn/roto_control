"""Composed Snapshot/Follow command + observer + UI seams; fake TD, no native PASS."""
from contextlib import contextmanager
from copy import deepcopy
from types import SimpleNamespace as S
from unittest import TestCase
from unittest.mock import Mock, patch
import test_follow_comp as follow_fixture
import live_model
import ui as view_module


class SnapshotFollowInteropTests(TestCase):
    def test_automatic_follow_touch_bypass_does_not_relax_snapshot_guards(self):
        values,v,button,label=self.fixture()
        e,m,f,a,b,la,lb,sample,reset,c,n,model,binding,calls=values
        record=e.SaveSnapshot('Touched A')
        manager=e._snapshot_manager();manager.recall=Mock(wraps=manager.recall)
        with patch.object(live_model,'run',n.frames.run,create=True),self.target_writes(a) as writes:
            self.assertTrue(v.Action('follow_comp'));n.frames.drain()
            m.touched.add(52)
            e._host.controls['knob',1].touched=True;e._host._sync()
            with self.assertRaisesRegex(ValueError,'release'):
                e.SaveSnapshot('Blocked capture')
            with self.assertRaisesRegex(ValueError,'release'):
                e.OverwriteSnapshot(record['id'],expected_revision=1)
            self.assertEqual(e.ValidateSnapshot(record['id'])['status'],'validation_failed')
            self.assertEqual(e.RecallAction(record['id'])['status'],'validation_failed')
            manager.recall.reset_mock()
            sample[0]=(sample[0][0],(b.owner,))
            self.assertTrue(v.Action('follow_comp'));n.frames.drain()
            self.assertEqual(m.data['active'],lb)
            self.assertEqual(m.touched,{52})  # No invented touch-release event.
            self.assertFalse(e.GetControlState()['mapped'])
            self.assertEqual(e.GetSnapshot(record['id'])['validation']['status'],'validation_failed')
            manager.recall.assert_not_called()
            # Fresh routing does not grant a blanket Snapshot touch exemption.
            current=e.SaveSnapshot('Current B')
            e._host.controls['knob',1].touched=True;e._host._sync()
            with self.assertRaisesRegex(ValueError,'release'):
                e.SaveSnapshot('Still blocked')
            self.assertEqual(e.RecallAction(current['id'])['status'],'validation_failed')
        self.assertEqual(writes,[])
        self.assertEqual((a.eval(),b.eval(),reset.pulses),(5,5,0))
        self.assertEqual(c.par.Followcomp.writes,[False,True])
        self.assertEqual(model.Stats()['subscriber_errors'],[])

    def fixture(self):
        helper = follow_fixture.FollowCompTests()
        self.addCleanup(helper.doCleanups)
        values = helper.fixture()
        e,m,f,a,b,la,lb,sample,reset,c,n,model,binding,calls = values
        for name in ('SaveSnapshot','OverwriteSnapshot','DeleteSnapshot','GetSnapshot',
                     'GetSnapshots','ValidateSnapshot','RecallAction','AssignAction'):
            setattr(c,name,getattr(e,name))
        key = m.context()['key']
        model.GetCatalog(key)
        view,button,label = helper.view(model,key,False)
        view.selected = 0
        view._token = model.GetToken(key,0)
        view._error = ''
        view._value_scope = False
        view._draft = S(par=S(Value=a.eval()))
        view._snapshot_selections = [(key,0,view._token)]
        view._snapshot_generation = 0
        view._editors = []
        view._set_error = lambda message:setattr(view,'_error',message)
        model.Subscribe('snapshot-follow',key,view.OnModelChange)
        view._update_follow_comp()
        return values,view,button,label

    @contextmanager
    def target_writes(self, parameter):
        original = type(parameter).val
        writes = []
        def write(par,value):
            writes.append((par,value));original.fset(par,value)
        with patch.object(type(parameter),'val',property(original.fget,write)):
            yield writes

    def dialogs(self):
        opened=[]
        resources=S(op=lambda name:S(Open=lambda **kwargs:opened.append(kwargs)),
                    PopDialog=S(OpenDefault=lambda **kwargs:opened.append(kwargs)))
        return opened,patch.object(view_module,'op',S(TDResources=resources),create=True)

    def save_dialog(self, view, opened):
        self.assertTrue(view.OpenSnapshots())
        menu=opened[-1]
        choice=next(name for name in menu['items'] if name.startswith('Save '))
        self.assertTrue(view.SelectSnapshot(dict(item=choice,details=menu['callbackDetails'])))
        return opened[-1]['details']

    def test_follow_button_keeps_snapshot_selection_browse_and_draft_without_recall(self):
        values,v,button,label=self.fixture()
        e,m,f,a,b,la,lb,sample,reset,c,n,model,binding,calls=values
        record=e.SaveSnapshot('Existing')
        manager=e._snapshot_manager()
        manager.recall=Mock(wraps=manager.recall)
        selection=list(v._snapshot_selections)
        intent=model.SnapshotIntent(v.Key(),selection)
        with self.target_writes(a) as writes, patch.object(live_model,'run',n.frames.run,create=True):
            self.assertTrue(v.Action('follow_comp'));n.frames.drain()
            self.assertEqual(label.par.text,'Follow COMP: OFF')
            self.assertTrue(v.Action('follow_comp'));n.frames.drain()
        self.assertEqual(c.par.Followcomp.writes,[False,True])
        self.assertEqual(len(calls),2)
        self.assertEqual(v._snapshot_selections,selection)
        self.assertFalse(v._follow_routing)
        self.assertEqual((v._mapping.open,v._mapping.message,v._draft.par.Value),(True,'draft',5))
        self.assertEqual(model.SnapshotIntent(v.Key(),selection),intent)
        self.assertEqual(writes,[]);manager.recall.assert_not_called()
        self.assertEqual(reset.pulses,0)
        self.assertGreater(v._notifications,0)
        self.assertEqual(model.Stats()['subscriber_errors'],[])
        self.assertEqual(e.GetSnapshot(record['id'])['entries'][0]['value'],.5)

    def test_routing_follow_or_session_observer_invalidates_snapshot_name_dialog(self):
        for drift in ('routing','session'):
            with self.subTest(drift=drift):
                values,v,button,label=self.fixture()
                e,m,f,a,b,la,lb,sample,reset,c,n,model,binding,calls=values
                opened,dialogs=self.dialogs()
                with dialogs,patch.object(live_model,'run',n.frames.run,create=True):
                    details=self.save_dialog(v,opened)
                    if drift=='routing':
                        self.assertTrue(v.Action('follow_comp'));n.frames.drain()
                        sample[0]=(sample[0][0],(b.owner,))
                        self.assertTrue(v.Action('follow_comp'));n.frames.drain()
                        self.assertEqual(m.data['active'],lb)
                    else:
                        f.connection_generation+=1
                        n.parameter_changed();n.frames.drain()
                    writes_before=list(c.par.Followcomp.writes)
                    self.assertFalse(v.ConfirmSnapshot(dict(buttonNum=2,enteredText='Stale',details=details)))
                self.assertEqual(e.GetSnapshots(),[])
                self.assertEqual(c.par.Followcomp.writes,writes_before)
                self.assertEqual((a.eval(),b.eval(),reset.pulses),(5,5,0))
                self.assertEqual(model.Stats()['subscriber_errors'],[])

    def test_value_and_action_details_observer_preserve_dialog_and_capture_live_position(self):
        values,v,button,label=self.fixture()
        e,m,f,a,b,la,lb,sample,reset,c,n,model,binding,calls=values
        record=e.SaveSnapshot('Existing')
        e.AssignAction(2,record['id'])
        e._action_registry().results[record['id']]=dict(action_id=record['id'],status='succeeded',error='',entries=[dict(actual_value=5)])
        model.Sync();v._token=model.GetToken(v.Key(),0)
        action_token=model.GetToken(v.Key(),9)
        v._snapshot_selections=[(v.Key(),0,v._token)]
        opened,dialogs=self.dialogs()
        with dialogs,patch.object(live_model,'run',n.frames.run,create=True):
            details=self.save_dialog(v,opened)
            intent=deepcopy(details['intent'])
            a.val=8;e.onControlChange(('knob',1),a)
            e._action_registry().results[record['id']]['entries'][0]['actual_value']=8
            n.parameter_changed();n.frames.drain()
            self.assertEqual(model.SnapshotIntent(v.Key(),v._snapshot_selections,None,0),intent)
            self.assertEqual(model.Info(v.Key(),9)['action_result']['entries'][0]['actual_value'],8)
            self.assertEqual(model.GetToken(v.Key(),9),action_token)
            self.assertTrue(v.ConfirmSnapshot(dict(buttonNum=2,enteredText='Current',details=details)))
        self.assertEqual(next(r for r in e.GetSnapshots() if r['label']=='Current')['entries'][0]['value'],.8)
        self.assertEqual(c.par.Followcomp.writes,[]);self.assertEqual(calls,[])
        self.assertEqual(reset.pulses,0)
        self.assertEqual(model.Stats()['subscriber_errors'],[])

    def test_snapshot_menu_save_delete_never_write_follow_or_targets_or_recall(self):
        values,v,button,label=self.fixture()
        e,m,f,a,b,la,lb,sample,reset,c,n,model,binding,calls=values
        manager=e._snapshot_manager();manager.recall=Mock(wraps=manager.recall)
        opened,dialogs=self.dialogs()
        with dialogs,self.target_writes(a) as writes:
            details=self.save_dialog(v,opened)
            self.assertTrue(v.ConfirmSnapshot(dict(buttonNum=2,enteredText='Disposable',details=details)))
            record=e.GetSnapshots()[0]
            self.assertTrue(v.OpenSnapshots(record['id']))
            menu=opened[-1]
            self.assertTrue(v.SelectSnapshot(dict(item='Delete Snapshot…',details=menu['callbackDetails'])))
            self.assertTrue(v.ConfirmSnapshot(dict(buttonNum=2,details=opened[-1]['details'])))
        self.assertEqual(e.GetSnapshots(),[])
        self.assertEqual(c.par.Followcomp.writes,[]);self.assertEqual(calls,[])
        self.assertEqual(writes,[]);manager.recall.assert_not_called()
        self.assertEqual(reset.pulses,0)

    def test_shared_builder_follow_button_and_existing_snapshot_filter_both_present(self):
        class Node:
            def __init__(self,name):self.name=name;self.par=follow_fixture.Parameters();self.children={};self.panel=S(inside=True)
            def op(self,name):return self.children.get(name)
            def create(self,kind,name):
                node=Node(name);self.children[name]=node;return node
        views=[Node('main'),Node('popup')]
        for view in views:view.create(None,'text_title')
        source=(follow_fixture.SOURCE/'prototypes/inspector/build_activation.py').read_text()
        exec(compile(source,'build_activation.py','exec'),dict(
            project=S(folder=str(follow_fixture.SOURCE)),activation_views=views,op=lambda path:views[0],
            containerCOMP=object(),textCOMP=object(),panelexecuteDAT=object()))
        values,v,button,label=self.fixture()
        v._menu_generation=0
        v._filter_info=lambda:[]
        opened,dialogs=self.dialogs()
        with dialogs:
            v.OpenFilter()
            self.assertIn('Snapshot presets…',opened[-1]['items'])
            self.assertTrue(v.SelectFilter(dict(item='Snapshot presets…',details=opened[-1]['callbackDetails'])))
            self.assertTrue(any(name.startswith('Save ') for name in opened[-1]['items']))
        for view in views:
            self.assertIsNotNone(view.op('follow_comp'))
            self.assertIsNotNone(view.op('activate_device'))
            self.assertIsNotNone(view.op('click_follow_comp'))
        e,m,f,a,b,la,lb,sample,reset,c,n,model,binding,calls=values
        self.assertEqual(c.par.Followcomp.writes,[]);self.assertEqual(e.GetSnapshots(),[])
        self.assertEqual((a.eval(),b.eval(),reset.pulses),(5,5,0))
