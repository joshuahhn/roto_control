"""Snapshot command intents and native-dialog routing; no native TD execution."""
import copy
from types import SimpleNamespace as S
from unittest import TestCase
from unittest.mock import patch
from live_model import ControllerCatalog
from test_live_model import Adapter, KEY
import ui as view_module


class SnapshotController:
    def __init__(self):
        self.calls=[];self.records={}
    def SaveSnapshot(self,label,targets,scope):
        self.calls.append(('save',label,targets,scope))
        record=dict(id='snapshot.id',label=label,revision=1,scope=dict(context=list(scope)),entries=[dict(kind=kind,slot=slot,value=.4) for kind,slot in (targets or [('knob',2)])])
        self.records[record['id']]=record;return copy.deepcopy(record)
    def GetSnapshot(self,id):return copy.deepcopy(self.records[id])
    def GetSnapshots(self,scope):return [copy.deepcopy(r) for r in self.records.values() if r['scope']['context']==list(scope)]
    def OverwriteSnapshot(self,id,targets,expected_revision):self.calls.append(('overwrite',id,targets,expected_revision))
    def DeleteSnapshot(self,id,expected_revision):self.calls.append(('delete',id,expected_revision))
    def ValidateSnapshot(self,id):self.calls.append(('validate',id));return dict(status='succeeded')
    def RecallAction(self,id):self.calls.append(('recall',id));return dict(status='partial',error='actual failure')
    def AssignAction(self,slot,action_id,**kwargs):self.calls.append(('assign',slot,action_id));return dict(action_id=action_id)


class SnapshotCommandsTests(TestCase):
    def test_default_save_and_overwrite_fence_other_captured_knobs_and_slot_membership(self):
        for operation, drift in [('save','definition'), ('save','new_slot'), ('overwrite','definition')]:
            a,m=self.model()
            a.records[KEY].append(dict(a.records[KEY][0],id='other',slot=1))
            m.Sync()
            if operation=='overwrite':
                a.controller.records['snapshot.id']=dict(id='snapshot.id',label='Saved',revision=1,
                    scope=dict(context=list(KEY)),entries=[dict(kind='knob',slot=1,value=.4)])
            intent=m.SnapshotIntent(KEY,preset_id='snapshot.id' if operation=='overwrite' else None,slot=1)
            if drift=='new_slot':
                a.records[KEY].append(dict(a.records[KEY][0],id='new',slot=3))
            else:
                a.records[KEY][-1]['id']='replacement'
            m.Sync()
            with self.assertRaises(ValueError):m.SnapshotCommand(operation,intent,'Stale')
            self.assertEqual(a.controller.calls,[])

    def test_default_capture_details_only_remain_valid_and_buttons_never_selected(self):
        a,m=self.model()
        intent=m.SnapshotIntent(KEY,slot=1)
        a.records[KEY][0]['value']=.9
        m.Sync()
        m.SnapshotCommand('save',intent,'Fresh positions')
        self.assertEqual(a.controller.calls[-1],('save','Fresh positions',None,KEY))
        a.records[KEY].append(dict(a.records[KEY][0],kind='button',slot=2,id='toggle',mode='toggle'))
        m.Sync()
        with self.assertRaisesRegex(ValueError,'Knob'):
            m.SnapshotIntent(KEY,[(KEY,9,m.GetToken(KEY,9))])

    def model(self):
        a=Adapter();a.controller=SnapshotController();a.parameter=S(name='Threshold')
        a.records[KEY][0].update(binding_type='parameter')
        m=ControllerCatalog(a);m.GetCatalog(KEY)
        return a,m

    def save(self,a,m):
        token=m.GetToken(KEY,1)
        intent=m.SnapshotIntent(KEY,[(KEY,1,token)])
        m.SnapshotCommand('save',intent,'Clean')
        return intent

    def test_explicit_parameter_selection_capture_and_queries_are_scoped(self):
        a,m=self.model();self.save(a,m)
        self.assertEqual(a.controller.calls,[('save','Clean',[('knob',2)],KEY)])
        self.assertEqual(m.Snapshots(KEY)[0]['id'],'snapshot.id')
        self.assertEqual(a.writes,[])
        for mode,kind in [('pulse','parameter'),('pulse','action'),('value','callback')]:
            a.records[KEY][0].update(mode=mode,binding_type=kind);m.Sync()
            with self.assertRaises(ValueError):m.SnapshotIntent(KEY,[(KEY,1,m.GetToken(KEY,1))])

    def test_stale_session_definition_snapshot_revision_or_context_never_commits(self):
        for drift in ('session','definition','revision','deleted','owner'):
            a,m=self.model();intent=self.save(a,m)
            intent=m.SnapshotIntent(KEY,intent['selections'],'snapshot.id')
            a.controller.calls.clear()
            if drift=='session':a.session+=1
            elif drift=='definition':a.records[KEY][0]['id']='replacement'
            elif drift=='revision':a.controller.records['snapshot.id']['revision']+=1
            elif drift=='deleted':a.records.clear()
            else:a.Status=lambda:dict(Active=KEY,Connected=True,ContextOwners={KEY[0]:dict(category='COMP',owner=dict(state='missing'))})
            with self.assertRaises((ValueError,RuntimeError)):m.SnapshotCommand('overwrite',intent)
            self.assertEqual(a.controller.calls,[])

    def test_details_only_do_not_expire_intent_but_assignment_requires_button_and_active(self):
        a,m=self.model();intent=self.save(a,m)
        a.records[KEY][0]['value']=.8;m.Sync()
        m.SnapshotCommand('save',intent,'Another')
        scalar=m.SnapshotIntent(KEY,preset_id='snapshot.id',slot=1)
        with self.assertRaisesRegex(ValueError,'Button'):m.SnapshotCommand('assign',scalar)
        a.Assign=lambda *args:None
        a.records[KEY].append(dict(a.records[KEY][0],id='button',kind='button',slot=1,mode='pulse',binding_type='action'))
        m.Sync();button=m.SnapshotIntent(KEY,preset_id='snapshot.id',slot=8)
        m.SnapshotCommand('assign',button)
        self.assertEqual(a.controller.calls[-1],('assign',1,'snapshot.id'))
        result=m.SnapshotCommand('recall',button)
        self.assertEqual(result['status'],'partial')

    def test_confirmation_cancel_and_duplicate_callbacks_are_zero_or_once(self):
        a,m=self.model();intent=m.SnapshotIntent(KEY,[(KEY,1,m.GetToken(KEY,1))])
        view=object.__new__(view_module.InspectorView)
        view._model=m;view._snapshot_generation=3;view._snapshot_selections=list(intent['selections'])
        view.Key=lambda:KEY;view._set_error=lambda message:None
        details=dict(generation=3,intent=intent,operation='save')
        self.assertFalse(view.ConfirmSnapshot(dict(buttonNum=1,details=details)))
        self.assertEqual(a.controller.calls,[])
        self.assertTrue(view.ConfirmSnapshot(dict(buttonNum=2,enteredText='Clean',details=details)))
        self.assertFalse(view.ConfirmSnapshot(dict(buttonNum=2,enteredText='Again',details=details)))
        self.assertEqual(len(a.controller.calls),1)

    def test_native_menu_routes_checkbox_and_name_dialog_without_implicit_recall(self):
        a,m=self.model();view=object.__new__(view_module.InspectorView)
        view._model=m;view._context=KEY;view.selected=1;view._snapshot_generation=0;view._snapshot_selections=[]
        view.Key=lambda:KEY;view._set_error=lambda message:None
        opened=[];resources=S(op=lambda name:S(Open=lambda **kwargs:opened.append(kwargs)),
                              PopDialog=S(OpenDefault=lambda **kwargs:opened.append(kwargs)))
        with patch.object(view_module,'op',S(TDResources=resources),create=True):
            self.assertTrue(view.OpenSnapshots())
            d=opened[-1]['callbackDetails']
            self.assertTrue(view.SelectSnapshot(dict(item='Add/remove selected Knob',details=d)))
            self.assertEqual(len(view._snapshot_selections),1);self.assertEqual(a.controller.calls,[])
            self.assertTrue(view.OpenSnapshots());d=opened[-1]['callbackDetails']
            self.assertTrue(view.SelectSnapshot(dict(item='Save 1 Knobs (0–1, this Device/page)…',details=d)))
            dialog=opened[-1];self.assertEqual(dialog['buttons'],['Cancel','Save'])
            self.assertTrue(view.ConfirmSnapshot(dict(buttonNum=2,enteredText='Named',details=dialog['details'])))
            self.assertEqual(a.controller.calls[-1][0:2],('save','Named'))
