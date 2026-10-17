import tests
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace as S
from unittest import TestCase
from unittest.mock import Mock, patch
from test_inspector_hardware import Panel
from test_owned_inspector import load
from test_live_model import Adapter,KEY,state
from live_model import ControllerCatalog,TDControllerAdapter
from ui import InspectorView
from editor_state import MappingDraft

SOURCE=Path(__file__).resolve().parents[1]
OTHER=('layout','track','browsed')
builder=load('mix_inspector_builder',SOURCE/'build/build_mix_inspector.py')


def observation(mode='PLUGIN'):
    return dict(status='applied',available=True,reason='',hardware=mode,connected=mode!='unknown',
                profile='analysis.main',style='analysis',scope='..',source='analysis',view=None,selected=0,
                items=[dict(id='low',label='Low',controls=[dict(key='gain',label='Gain',kind='float',
                target=dict(op='analysis',parameter='Lowgain'),value=12,caption='12',available=True,reason='')])])


class MixAdapter(Adapter):
    def __init__(self):
        super().__init__();self.mix=observation();self.records[OTHER]=[state(.7)]
    def MixObservation(self):return deepcopy(self.mix)
    def Status(self):return dict(super().Status(),Connected=True,ActivationReason='MIX mode' if self.mix['hardware']=='MIX' else '')


def view_fixture(model):
    view=InspectorView.__new__(InspectorView);owner=Panel('view');view.ownerComp=owner
    for name,kind in [('text_title','textCOMP'),('text_style','textCOMP'),('container_scroll','containerCOMP'),('container_context_menu','containerCOMP')]:Panel(name,owner,kind)
    builder.install(owner)
    owner.op('container_mix/text_mix_document').evalTextSize=Mock(return_value=(210,400))
    view._model=model;view._mix_choice='auto';view._mix_visible=False
    view._context=OTHER;view.Key=lambda:OTHER;view._follow_routing=False;view.selected=1
    view._token=model.GetToken(OTHER,1);view._original=dict(model.GetCatalog(OTHER)[1])
    view._value_scope=(OTHER,1,view._token);view._value_type='float'
    view._draft=S(par=S(Value=.91,Mapminimum=.2,Mapmaximum=.7,Mapmode='value'))
    view._mapping=MappingDraft();view._mapping.Open(model,OTHER,1)
    view._clear_pending=((OTHER,1,view._token),999999);view._editors=()
    view._dirty=view._metadata_dirty=view._notifications=view._writes=0
    view._error='';view._picker=None;view._display={1:('Threshold',True,model.ValueText(OTHER,1),'',model.GetCatalog(OTHER)[1]['Value'])}
    view._visible=lambda:False;view._refresh_rows=Mock(return_value=False)
    view._update_editor=Mock();view._editor_layout=Mock();view._theme=Mock();view.ConfigureMenus=Mock()
    view.CloseContextMenu=Mock();view._popup=S(par=S(winclose=S(pulse=Mock())))
    return view


class MixInspectorTests(TestCase):
    def model(self):
        adapter=MixAdapter();model=ControllerCatalog(adapter);model.Sync();model.Flush()
        return adapter,model

    def test_mix_publication_is_display_only_and_suppresses_identical_data(self):
        adapter,model=self.model();events=[];model.Subscribe('view',OTHER,lambda *args:events.append(args))
        token=model.GetToken(OTHER,1);adapter.mix['hardware']='MIX'
        model.Sync();model.Flush()
        self.assertEqual(len(events),1);self.assertEqual(events[0][1:4],(0,0,False))
        self.assertEqual(model.GetToken(OTHER,1),token)
        for _ in range(5):model.Sync();model.Flush()
        self.assertEqual(len(events),1)
        detached=model.MixObservation();detached['items'].clear()
        self.assertTrue(model.MixObservation()['items'])
        self.assertEqual(adapter.writes,[]);self.assertEqual(adapter.pings,[]);self.assertEqual(adapter.clears,[])

    def test_auto_and_explicit_choices_are_per_view_and_never_route_or_write(self):
        adapter,model=self.model();one=view_fixture(model);two=view_fixture(model)
        model.Subscribe('one',OTHER,one.OnModelChange);model.Subscribe('two',OTHER,two.OnModelChange)
        saved=(one._context,one._token,one._clear_pending,deepcopy(vars(one._draft.par)),one._mapping.token,one._original)
        adapter.mix['hardware']='MIX';model.Sync();model.Flush()
        self.assertTrue(one.IsMix());self.assertTrue(two.IsMix())
        self.assertTrue(one.ownerComp.op('container_mix').par.display.eval())
        self.assertIn('Lowgain',one.ownerComp.op('container_mix/text_mix_document').par.text.eval())
        self.assertNotIn('Threshold',one.ownerComp.op('container_mix/text_mix_document').par.text.eval())
        one.SelectInspection(dict(item='PLUGIN'));self.assertFalse(one.IsMix());self.assertTrue(two.IsMix())
        adapter.mix=observation('unknown');model.Sync();model.Flush();self.assertFalse(two.IsMix())
        two.SelectInspection(dict(item='MIX'));self.assertTrue(two.IsMix())
        self.assertIn('Hardware: unknown · disconnected',two.ownerComp.op('container_mix/text_mix_document').par.text.eval())
        two.SelectInspection(dict(item='Auto'));self.assertFalse(two.IsMix())
        self.assertEqual((one._context,one._token,one._clear_pending,vars(one._draft.par),one._mapping.token,one._original),saved)
        self.assertFalse(one._follow_routing);self.assertEqual(adapter.active,KEY)
        self.assertEqual(adapter.writes+adapter.pings+adapter.clears,[])

    def test_hidden_plugin_display_changes_preserve_drafts_but_real_metadata_expires_token(self):
        adapter,model=self.model();view=view_fixture(model)
        model.Subscribe('view',OTHER,view.OnModelChange)
        pending=view._clear_pending;draft=deepcopy(vars(view._draft.par));token=view._token
        adapter.mix['hardware']='MIX'
        adapter.records[OTHER][0]['plugin']=False
        model.Sync();model.Flush()
        self.assertEqual(view._clear_pending,pending);self.assertEqual(vars(view._draft.par),draft)
        self.assertEqual(model.GetToken(OTHER,1),token);self.assertTrue(view._mapping.open)
        adapter.records[OTHER][0]['id']='replacement';model.Sync();model.Flush()
        self.assertNotEqual(model.GetToken(OTHER,1),token)
        self.assertIsNone(view._clear_pending);self.assertIn('Mapping changed',view._error)

    def test_stale_plugin_actions_and_typed_callbacks_cannot_write_while_mix_visible(self):
        adapter,model=self.model();view=view_fixture(model);view._mix_choice='mix'
        before=(deepcopy(vars(view._draft.par)),view._value_scope,view._clear_pending)
        for action in ('apply','ping','clear','mapping_apply','follow_comp','activate_device','slot1'):
            self.assertFalse(view.Action(action))
        self.assertFalse(view.LiveValue('.3'));self.assertFalse(view.TypedValue(.3))
        self.assertFalse(view.BeginValueEdit());self.assertFalse(view.EndValueEdit())
        self.assertFalse(view.ConfirmSnapshot({}));self.assertFalse(view.ConfirmClearDevice({}))
        self.assertEqual((vars(view._draft.par),view._value_scope,view._clear_pending),before)
        self.assertEqual(adapter.writes+adapter.pings+adapter.clears,[])

    def test_full_precision_plugin_value_updates_survive_unchanged_rounded_text(self):
        adapter,model=self.model();view=view_fixture(model);view._value_scope=None
        view._draft.par.Value=.7;model.Subscribe('view',OTHER,view.OnModelChange)
        old_text=model.ValueText(OTHER,1)
        adapter.records[OTHER][0]['value']=.70001;model.Sync();model.Flush()
        self.assertEqual(model.ValueText(OTHER,1),old_text)
        self.assertEqual(view._draft.par.Value,.70001)
        self.assertEqual(model.Stats()['subscriber_errors'],[])

    def test_removed_browsed_device_recovers_context_before_reading_selected_value(self):
        adapter,model=self.model();view=view_fixture(model)
        pars=type(view.ownerComp.par)
        view.ownerComp.par=type('IndexedPars',(pars,),dict(__getitem__=lambda self,name:getattr(self,name)))()
        for name,value in zip(('Layout','Track','Device'),OTHER):
            setattr(view.ownerComp.par,name,value)
            parameter=getattr(view.ownerComp.par,name);parameter.menuNames=[value];parameter.menuLabels=[value]
        view.Key=lambda:InspectorView.Key(view)
        view.ConfigureMenus=lambda preferred:InspectorView.ConfigureMenus(view,preferred)
        def refresh():
            view._context=view.Key();model.Subscribe('view',view._context,view.OnModelChange)
        view.Refresh=Mock(side_effect=refresh)
        model.Subscribe('view',OTHER,view.OnModelChange)
        del adapter.records[OTHER];model.Sync();model.Flush()
        self.assertEqual(view._context,KEY);self.assertEqual(model.Stats()['subscribers'],1)
        self.assertEqual(model.Stats()['subscriber_errors'],[]);view.Refresh.assert_called_once_with()

    def test_queued_plugin_menu_callbacks_preserve_hidden_drafts(self):
        _,model=self.model();view=view_fixture(model);view._mix_choice='mix';view._menu_generation=3
        view._filter='all';view._definition_draft=dict(style='Float');view._definition_scope=(OTHER,1,view._token)
        before=(vars(view._draft.par).copy(),view._value_scope,view._clear_pending,view._mapping.token)
        details=dict(context=OTHER,slot=1,token=view._token,generation=3)
        self.assertFalse(view.SelectValueType(dict(item='Int',details=details)))
        self.assertFalse(view.SelectMappingChoice(dict(item='value',details=dict(details,field='mode',token=view._mapping.token))))
        self.assertFalse(view.SelectDefinitionStyle(dict(item='Int',details=dict(details,model_generation=model.Stats()['generation']))))
        self.assertFalse(view.SelectFilter(dict(item='All',details=dict(details,choices={'All':'all'}))))
        self.assertEqual((vars(view._draft.par),view._value_scope,view._clear_pending,view._mapping.token),before)

    def test_additive_panel_installs_once_without_touching_existing_geometry(self):
        _,model=self.model();view=view_fixture(model);owner=view.ownerComp
        old=[(n.id,n.nodeX,n.nodeY) for n in owner.findChildren()]
        builder.install(owner)
        self.assertEqual([(n.id,n.nodeX,n.nodeY) for n in owner.findChildren()],old)
        wrong=owner.op('container_mix');wrong.OPType='textCOMP'
        with self.assertRaises(ValueError):builder.validate(owner)

    def test_opening_mix_keeps_hidden_plugin_editor_draft(self):
        _,model=self.model();view=view_fixture(model);view._mix_choice='mix'
        view.HideOtherViews=Mock();view.CloseEditor=Mock();view.Refresh=Mock();view._main=S(isOpen=True)
        before=(view._clear_pending,vars(view._draft.par).copy(),view._token,view._mapping.token)
        view.Show();view.CloseEditor.assert_not_called()
        self.assertEqual((view._clear_pending,vars(view._draft.par),view._token,view._mapping.token),before)
        view._mix_choice='plugin';view.Show();view.CloseEditor.assert_called_once_with()

    def test_adapter_reads_published_observation_without_calling_lazy_runtime(self):
        import json
        value=observation('MIX');controller=S(op=lambda name:S(text=json.dumps(dict(mix=value))),GetMixState=Mock(side_effect=AssertionError('lazy runtime read')))
        adapter=TDControllerAdapter(S(par=S(Controller=S(eval=lambda:controller))))
        self.assertEqual(adapter.MixObservation(),value)
        controller.GetMixState.assert_not_called()
