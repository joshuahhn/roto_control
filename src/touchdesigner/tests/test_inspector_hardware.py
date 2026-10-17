"""Serial observation projection and installed Details behavior without TD I/O."""
import tests
from copy import deepcopy
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace as S
import unittest
from unittest.mock import Mock, patch

SOURCE=Path(__file__).resolve().parents[1]
sys.path.append(str(SOURCE/'prototypes/inspector'))
from live_model import ControllerCatalog, TDControllerAdapter
from ui import InspectorView
from parity import DETAIL_GROUPS
from test_live_model import Adapter, KEY, state
from test_owned_inspector import load, fixture, Node, Parameter, runtime as owned
import export_component
import upgrade_inspector_hardware as upgrade


def observation():
    expected=[dict(id='target',kind='knob',slot=2,parameter_index=128,parameter_hash=[1,2,3,4,5,6]),
              dict(id='button',kind='button',slot=1,parameter_index=300,parameter_hash=[6,5,4,3,2,1])]
    public=dict(layout_id=KEY[0],track_id=KEY[1],plugin_id=KEY[2],routing_key=KEY,device_id='device identity')
    provenance=dict(device_id='device identity',page_offset=0,observation='snapshot_only',worker_closed=True,
                    endpoint='/dev/cu.fixture',captured_at_utc='2026-10-18T09:00:00Z',serial_session_id='session',
                    physical_device=dict(serial='physical USB'),firmware=dict(version='3.3.0'))
    controls=[dict(row,plugin_hash=[7]*8,control_index=row['slot']-1,
                   haptics=dict(mode='unknown',raw_mode=78,steps=2,labels=['A','B'],indent_positions=[4,8],physical_feel_verified=False),
                   button=dict(mode='toggle',raw_mode=1,steps=2,labels=['off','on'],led_on=3,led_off=0)) for row in expected]
    return dict(result=dict(status='captured',snapshot=dict(context=deepcopy(public),controls=controls,provenance=provenance),
                            error=None,invalidation_reason=None),public=public,manifest=dict(controls=expected,plugin_hash=[7]*8),
                worker_active=False,available=True,quarantined=False)


class HardwareAdapter(Adapter):
    def __init__(self):
        super().__init__();self.hardware=observation();self.reads=[]
    def HardwareObservation(self):return deepcopy(self.hardware)
    def HardwareSnapshot(self,*args):return TDControllerAdapter.HardwareSnapshot(self,*args)
    _hardware_matches=staticmethod(TDControllerAdapter._hardware_matches)
    def ReadHardwareSnapshot(self,key,info,*,port):
        self.reads.append((key,info['id'],port));self.hardware['result'].update(status='reading',snapshot=None)
        self.hardware['worker_active']=True
        return deepcopy(self.hardware['result'])


class HardwareProjectionTests(unittest.TestCase):
    def setUp(self):
        self.adapter=HardwareAdapter();self.model=ControllerCatalog(self.adapter);self.model.Sync()
    def rows(self):return dict((k,v) for k,v,kind in self.model.HardwareSnapshot(KEY,1)['rows'])
    def test_complete_unique_batch_matches_in_any_order_and_keeps_unknown_mode_honest(self):
        rows=self.rows();self.assertEqual(rows['Detected mode'],'UNKNOWN · raw 78')
        self.assertIn('unverified',rows['Indents / feel']);self.assertIn('historical',rows['Serial session'])
        self.adapter.hardware['result']['snapshot']['controls'].reverse();self.model.Sync()
        self.assertEqual(self.rows(),rows)
    def test_incomplete_duplicate_extra_or_changed_identity_withholds_all_detected_settings(self):
        mutations=[lambda o:o['result']['snapshot']['controls'].pop(),
                   lambda o:o['result']['snapshot']['controls'].append(deepcopy(o['result']['snapshot']['controls'][0])),
                   lambda o:o['result']['snapshot']['controls'][1].update(id='target',kind='knob',slot=2,parameter_index=128,parameter_hash=[1,2,3,4,5,6],control_index=1)]
        for field,value in [('id','other'),('kind','button'),('slot',3),('parameter_index',129),('parameter_hash',[9]*6),('control_index',2),('plugin_hash',[8]*8)]:
            mutations.append(lambda o,f=field,v=value:o['result']['snapshot']['controls'][0].__setitem__(f,v))
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                self.adapter.hardware=observation();mutate(self.adapter.hardware);self.model.Sync()
                rows=self.rows();self.assertNotIn('Detected mode',rows);self.assertIn('withheld',rows['Association'])
    def test_wrong_context_device_page_or_quarantined_routing_never_inherits_settings(self):
        changes=[lambda o:o['result']['snapshot']['context'].update(device_id='different Device'),
                 lambda o:o['result']['snapshot']['context'].update(routing_key=('other','track','device')),
                 lambda o:o['result']['snapshot']['provenance'].update(page_offset=1),
                 lambda o:o.update(quarantined=True)]
        for mutate in changes:
            self.adapter.hardware=observation();mutate(self.adapter.hardware);self.model.Sync()
            self.assertNotIn('Detected mode',self.rows())
        other=('layout','track','other');self.adapter.records[other]=[state()]
        self.assertFalse(self.model.HardwareSnapshot(other,1)['read_enabled'])
        self.assertNotIn('Detected mode',str(self.model.HardwareSnapshot(other,1)['rows']))
    def test_stale_exact_snapshot_retains_history_reason_and_changed_binding_withholds(self):
        self.adapter.hardware['result'].update(status='stale',invalidation_reason='Controller disconnected')
        self.model.Sync();rows=self.rows();self.assertIn('stale',rows['State']);self.assertEqual(rows['Stale reason'],'Controller disconnected')
        self.assertIn('Detected mode',rows)
        self.adapter.hardware['manifest']['controls'][0]['parameter_hash']=[8]*6;self.model.Sync()
        self.assertNotIn('Detected mode',self.rows());self.assertIn('Captured at',self.rows())
    def test_error_reading_never_read_clear_old_fields_and_busy_cleanup_disables_read(self):
        for status in ('error','reading','never_read'):
            self.adapter.hardware['result'].update(status=status,snapshot=None,error=dict(code='busy_port',message='Port is busy') if status=='error' else None)
            self.adapter.hardware['worker_active']=True;self.model.Sync()
            view=self.model.HardwareSnapshot(KEY,1);self.assertFalse(view['read_enabled']);self.assertNotIn('Detected mode',str(view['rows']))
        self.adapter.hardware['worker_active']=False;self.model.Sync();self.assertTrue(self.model.HardwareSnapshot(KEY,1)['read_enabled'])
    def test_only_explicit_read_calls_api_once_and_busy_requires_explicit_retry(self):
        for _ in range(5):self.model.Inspect(KEY,1);self.model.HardwareSnapshot(KEY,1);self.model.Sync()
        self.assertEqual(self.adapter.reads,[])
        self.model.ReadHardwareSnapshot(KEY,1,port='/dev/cu.typed')
        self.assertEqual(self.adapter.reads,[(KEY,'target','/dev/cu.typed')])
        with self.assertRaisesRegex(ValueError,'cleanup'):self.model.ReadHardwareSnapshot(KEY,1,port='/dev/cu.typed')
        self.assertEqual(len(self.adapter.reads),1)
        self.adapter.hardware['worker_active']=False;self.adapter.hardware['result']['status']='error';self.model.Sync()
        self.assertEqual(len(self.adapter.reads),1)
    def test_detected_button_mode_does_not_change_declared_rx_adapter(self):
        info=dict(id='button',kind='button',slot=1,button_type='push')
        view=TDControllerAdapter.HardwareSnapshot(self.adapter,self.adapter.hardware,KEY,info)
        rows=dict((k,v) for k,v,kind in view['rows'])
        self.assertEqual(rows['Detected mode'],'TOGGLE · raw 1');self.assertEqual(info['button_type'],'push')
        self.assertEqual(rows['LED on / off'],'3 / 0')
    def test_fresh_adapter_guard_rejects_context_or_control_change_without_read(self):
        current=S(public=observation()['public'],manifest=observation()['manifest'])
        controller=S(ext=S(RotoPythonExt=S(_hardware_context=lambda:(current,True))),ReadHardwareConfig=Mock())
        adapter=TDControllerAdapter(S(par=S(Controller=S(eval=lambda:controller))))
        info=dict(id='target',kind='knob',slot=2)
        with self.assertRaises(ValueError):adapter.ReadHardwareSnapshot(('other','track','device'),info,port='/dev/cu.fixture')
        with self.assertRaises(ValueError):adapter.ReadHardwareSnapshot(KEY,dict(info,id='removed'),port='/dev/cu.fixture')
        controller.ReadHardwareConfig.assert_not_called()
        adapter.ReadHardwareSnapshot(KEY,info,port='/dev/cu.fixture')
        controller.ReadHardwareConfig.assert_called_once_with(port='/dev/cu.fixture')
    def test_shutdown_discards_transient_cache(self):
        self.assertIsNotNone(self.model._hardware);self.model.Shutdown();self.assertIsNone(self.model._hardware)


class NativeParameter:
    def __init__(self,value=None):self.val=value;self.expr=''
    def eval(self):return self.val
    def pulse(self):self.val=True


class NativePars:
    def __init__(self):object.__setattr__(self,'values',{})
    def __getattr__(self,name):return self.values.setdefault(name,NativeParameter())
    def __setattr__(self,name,value):getattr(self,name).val=value


class Panel(Node):
    def __init__(self,name,parent=None,kind='containerCOMP'):
        super().__init__(name,parent,kind);self.par=NativePars();self.width=300
        self.nodeX=13;self.nodeY=27;self.panel=S(inside=True)
    def create(self,kind,name):return Panel(name,self,kind)


def editor_fixture():
    editor=Panel('editor');node=editor
    for name in ('container_details','container_readout','container_info'):node=Panel(name,node)
    for name in ('text_details','reveal','repair'):Panel(name,editor.op('container_details'),'textCOMP')
    for index,(title,capacity) in enumerate(DETAIL_GROUPS[:3]):
        group=Panel('group'+str(index),node);Panel('text_heading',group,'textCOMP')
        for i in range(capacity):Panel('label'+str(i),group,'textCOMP');Panel('value'+str(i),group,'textCOMP')
    builder=load('hardware_parity_builder',SOURCE/'prototypes/inspector/build_parity.py')
    return editor,builder


class HardwareDetailsTests(unittest.TestCase):
    def test_additive_builder_is_idempotent_preserves_all_existing_ids_and_geometry(self):
        editor,builder=editor_fixture();original=[editor]+editor.findChildren()
        before=[(node.id,node.OPType,node.nodeX,node.nodeY) for node in original]
        group=builder.install_hardware_snapshot(editor);first={node.id for node in editor.findChildren()}
        self.assertIs(builder.install_hardware_snapshot(editor),group)
        self.assertEqual({node.id for node in editor.findChildren()},first)
        self.assertEqual([(node.id,node.OPType,node.nodeX,node.nodeY) for node in original],before)
        self.assertEqual(len([node for node in group.children if node.name.startswith('value')]),DETAIL_GROUPS[3][1])
    def test_uncommitted_edit_text_drives_one_read_and_syncs_only_same_view_editors(self):
        editors=[]
        for _ in range(2):
            editor,builder=editor_fixture();builder.install_hardware_snapshot(editor);editors.append(editor)
        view=InspectorView.__new__(InspectorView);view._editors=tuple(editors);view._hardware_port=''
        other_view=InspectorView.__new__(InspectorView);other_view._editors=();other_view._hardware_port='/dev/cu.other-view'
        view.selected=1;view._context=KEY;view._model=S(IsLive=True,ReadHardwareSnapshot=Mock());view._update_details=Mock()
        field=editors[0].op('container_details/container_readout/container_info/group3/field_endpoint')
        field.editText='/dev/cu.uncommitted';field.par.text='old committed text'
        callback=field.par.callbacks.eval();namespace=dict(parent=S(InspectorDemo=view));exec(callback.text,namespace)
        namespace['onTextEdit'](field)
        self.assertEqual(view._hardware_port,'/dev/cu.uncommitted')
        self.assertEqual(editors[1].op('container_details/container_readout/container_info/group3/field_endpoint').par.text.eval(),field.editText)
        self.assertEqual(field.par.text.eval(),'old committed text');view.ReadHardware()
        view._model.ReadHardwareSnapshot.assert_called_once_with(KEY,1,port='/dev/cu.uncommitted')
        self.assertEqual(other_view._hardware_port,'/dev/cu.other-view')
        view.HardwareEndpoint('');self.assertTrue(all(editor.op('container_details/container_readout/container_info/group3/field_endpoint').par.text.eval()=='' for editor in editors))
    def view(self,model):
        editors=[]
        for _ in range(2):
            editor,builder=editor_fixture();builder.install_hardware_snapshot(editor);editors.append(editor)
        view=InspectorView.__new__(InspectorView);view._editors=tuple(editors);view._model=model;view.selected=1;view._context=KEY
        view._token=model.GetToken(KEY,1);view._details_open=True;view._diagnostics={};view._native_definition=None
        view._definition_draft=None;view._follow_routing=True;view._hardware_port='';view._details_display=None
        return view
    def test_renderer_replaces_actual_value_nodes_after_editor_cache_hit_and_clears_old_capture(self):
        adapter=HardwareAdapter();model=ControllerCatalog(adapter);model.Sync()
        model.Health=lambda *args:dict(label='Mapped');model.Capabilities=lambda *args:dict(assign=dict(enabled=True,reason=''))
        view=self.view(model);view._editor_display=('KNOB 2 · Mapped','',False,(('assign',True,''),));view._error='';view._value_type=None
        view._editor_status=lambda:'';view._update_typed_value=Mock();view._update_mapping=Mock();view._update_picker=Mock()
        model.ValueText=lambda *args:'.4'
        view._update_editor();signature=view._editor_display
        before=[editor.op('container_details/container_readout/container_info/group3/value0').par.text.eval() for editor in view._editors]
        self.assertEqual(before,['Captured snapshot']*2)
        adapter.hardware['result'].update(status='error',snapshot=None,error=dict(code='wrong_device',message='No endpoint'))
        model.Sync();view._update_editor();self.assertEqual(view._editor_display,signature)
        for editor in view._editors:
            group=editor.op('container_details/container_readout/container_info/group3')
            self.assertEqual(group.op('value0').par.text.eval(),'Controller Serial error')
            self.assertNotIn('/dev/cu.fixture',str([group.op('value'+str(i)).par.text.eval() for i in range(DETAIL_GROUPS[3][1])]))


class HardwarePublicationTests(unittest.TestCase):
    def test_real_revision_dat_callback_schedules_display_only_updates_to_both_views(self):
        from test_scheduled_action_details import ScheduledActionDetailsTests
        import live_model
        from hardware_config import HardwareConfig
        fixture=ScheduledActionDetailsTests().source_fixture()
        network,extension,model,provider,recalls,nodes,events,observations,key=fixture
        controller=extension.ownerComp;controller.GetHardwareConfig=extension.GetHardwareConfig
        native=TDControllerAdapter(S(par=S(Controller=S(eval=lambda:controller))))
        model.adapter.HardwareObservation=native.HardwareObservation
        extension._hardware_config=HardwareConfig()
        owner=extension._hardware_config;owner.observe(extension._hardware_context()[0])
        with patch('RotoPythonExt.run',network.frames.run,create=True),patch.object(live_model,'run',network.frames.run,create=True):
            extension._hardware_changed();network.frames.drain();token=model.GetToken(key,8)
            for status,active in [('reading',True),('captured',False),('stale',False),('error',True),('error',False)]:
                for stream in events:stream.clear()
                owner.result.update(status=status,error=dict(code='failure',message='Serial failure') if status=='error' else None)
                owner.job={'marker':'cleanup'} if active else None
                extension._hardware_changed();network.frames.drain()
                for stream in events:
                    self.assertEqual(len(stream),1);self.assertEqual(stream[0][1:4],(65535,0,False))
                self.assertEqual(model.GetToken(key,8),token)
                payload=json.loads(nodes['context_state'].text)
                self.assertIs(type(payload['hardware_revision']),int)
                self.assertNotIn('snapshot',payload);self.assertNotIn('endpoint',str(payload))
                for stream in events:stream.clear()
                extension._hardware_changed();network.frames.drain();self.assertEqual(events,[[],[]])
            owner.job=None
    def test_get_observation_invalidates_changed_context_and_publishes_once(self):
        from test_hardware_config import ExtensionHardwareTests
        from hardware_config import ReadContext
        extension,manager,parameter=ExtensionHardwareTests().fixture()
        owner=extension._hardware_owner();current,available=extension._hardware_context()
        owner.observe(current);owner.result.update(status='captured',snapshot=dict(marker='historical'))
        extension.GetHardwareConfig();revision=extension._hardware_revision;extension._publish_inspector.reset_mock()
        changed=ReadContext(current.host,current.signature+('changed',),current.manifest,current.public)
        extension._hardware_context=lambda:(changed,available)
        self.assertEqual(extension.GetHardwareConfig()['status'],'stale')
        self.assertEqual(extension._hardware_revision,revision+1);extension._publish_inspector.assert_called_once()
        extension.GetHardwareConfig();self.assertEqual(extension._hardware_revision,revision+1)
    def test_display_notification_preserves_mapping_and_value_draft_contents_and_pending_clear(self):
        adapter=HardwareAdapter();model=ControllerCatalog(adapter);model.Sync();model.Flush()
        view=InspectorView.__new__(InspectorView);view._model=model;view._context=KEY;view.selected=1
        view._token=model.GetToken(KEY,1);view._value_scope=(KEY,1,view._token);view._clear_pending=('armed',view._token)
        view._draft=S(par=S(Value=.91,Mapminimum=.2,Mapmaximum=.7,Mapmode='value',Mapinput='push'))
        view._mapping=S(open=True,token=view._token,original=dict(minimum=0,maximum=1))
        view._dirty=view._metadata_dirty=view._notifications=0;view._error='';view._editors=()
        view._visible=lambda:True;view._refresh_rows=lambda *args:False;view._update_editor=Mock()
        model.Subscribe('actual-view',KEY,view.OnModelChange);before=deepcopy(vars(view._draft.par));pending=view._clear_pending
        for status in ('reading','captured','stale','error'):
            adapter.hardware['result']['status']=status;model.Sync();model.Flush()
            self.assertEqual(vars(view._draft.par),before);self.assertEqual(view._clear_pending,pending)
            self.assertTrue(view._mapping.open);self.assertEqual(view._mapping.token,view._token)
        self.assertEqual(view._update_editor.call_count,4)
    def test_get_tick_invalidation_and_worker_cleanup_publish_real_transitions_once(self):
        from test_hardware_config import ExtensionHardwareTests
        e,manager,parameter=ExtensionHardwareTests().fixture();owner=e._hardware_owner()
        owner.observe(e._hardware_context()[0]);owner.result.update(status='captured',snapshot=dict(marker='historic'))
        e.GetHardwareConfig();revision=e._hardware_revision;e._publish_inspector.reset_mock()
        e.GetHardwareConfig();e._publish_inspector.assert_not_called()
        e._invalidate_hardware('manual boundary');self.assertEqual(e._hardware_revision,revision+1)
        owner.job={'cleanup':True};owner.tick=Mock(side_effect=lambda context:setattr(owner,'job',None))
        e._hardware_changed();e._publish_inspector.reset_mock();revision=e._hardware_revision
        e._tick_hardware();self.assertEqual(e._hardware_revision,revision+1);e._publish_inspector.assert_called_once()


class HardwarePackagingTests(unittest.TestCase):
    def test_generic_scrubs_endpoint_literals_cache_and_publication_token(self):
        controller,wrapper,model,views=fixture();Node('registration',controller,'textDAT')
        controller.ext.RotoPythonExt=S(_hardware_config=observation(),_hardware_observation=observation(),_hardware_revision=9)
        for view in views:
            endpoint=Node('field_endpoint',view,'textCOMP');endpoint.par.text=Parameter('/dev/cu.private')
        export_component.reset_registration(controller);owned.sanitize(controller)
        self.assertIsNone(controller.ext.RotoPythonExt._hardware_config)
        self.assertIsNone(controller.ext.RotoPythonExt._hardware_observation)
        self.assertEqual(controller.ext.RotoPythonExt._hardware_revision,0)
        self.assertTrue(all(view.op('field_endpoint').par.text.val=='' for view in views))
    def test_installer_rejects_wrong_project_foreign_owner_and_active_transports_before_mutation(self):
        controller,wrapper,model,views=fixture();Node('owned_runtime',wrapper,'textDAT').module=owned
        marker=dict(build='previous full build',dat={'ui':'old hash'});wrapper.store('owned_inspector_sources',marker)
        controller.ext.RotoPythonExt=S(ownerComp=controller,_process=None,_hardware_config=None)
        controller.save=Mock()
        with TemporaryDirectory() as directory,patch.object(upgrade,'project',S(folder=directory,name='expected'),create=True):
            kwargs=dict(expected_project=Path(directory)/'expected.toe',recovery_path=Path(directory)/'new.tox')
            with self.assertRaisesRegex(ValueError,'Active project'):upgrade.install(controller,SOURCE,**dict(kwargs,expected_project=Path(directory)/'other.toe'))
            self.assertEqual(wrapper.fetch('owned_inspector_sources'),marker)
            for mode in ('midi','serial','foreign'):
                controller.ext.RotoPythonExt._process=object() if mode=='midi' else None
                controller.ext.RotoPythonExt._hardware_config=S(active=True) if mode=='serial' else None
                controller.ext.RotoPythonExt.ownerComp=object() if mode=='foreign' else controller
                with self.subTest(mode=mode),self.assertRaises(ValueError):upgrade.install(controller,SOURCE,**kwargs)
                self.assertEqual(wrapper.fetch('owned_inspector_sources'),marker)
            controller.save.assert_not_called()
    def test_installer_invalidates_full_build_marker_only_after_successful_final_validation(self):
        for reject_final in (False,True):
            with self.subTest(reject_final=reject_final),TemporaryDirectory() as directory:
                controller,wrapper,model,views=fixture()
                marker=dict(build='previous full build',dat={'ui':'old hash'})
                wrapper.store('owned_inspector_sources',deepcopy(marker));wrapper.store('unrelated','preserved')
                wrapper.unstore=lambda key:wrapper.storage.pop(key,None)
                def validate(target):
                    self.assertEqual(wrapper.fetch('owned_inspector_sources'),marker)
                    result=owned.validate(target)
                    if reject_final and lifecycle.validate.call_count==2:raise ValueError('Final validation failed')
                    return result
                lifecycle=S(validate=Mock(side_effect=validate),initialize=owned.initialize,quiesce=owned.quiesce)
                Node('owned_runtime',wrapper,'textDAT').module=lifecycle
                for name,parent in [('RotoPythonExt',controller),('inspector_data',wrapper),('live_model',model)]:Node(name,parent,'textDAT')
                Node('parity',Node('base_commands',model),'textDAT')
                for view in views:
                    for name in ('ui','parity'):Node(name,view,'textDAT')
                    content=Node('container_content',Node('container_scroll',view))
                    popup=Node('editor_popup',Node('base_popup',view));editors=[]
                    for name,parent in [('editor_below',content),('container_editor_content',popup)]:
                        editor,_=editor_fixture();editor.name=name;editor._parent=parent;parent.children.append(editor);editors.append(editor)
                    view.ext.InspectorView._editors=tuple(editors)
                controller.ext.RotoPythonExt=S(ownerComp=controller,_process=None,_hardware_config=None,_cancel_inspector_refresh=Mock(),_publish_inspector=Mock())
                controller.initializeExtensions=Mock();controller.Applybinding=Mock(return_value=True)
                controller.save=lambda path:Path(path).write_bytes(b'recovery')
                with patch.object(upgrade,'project',S(folder=directory,name='expected'),create=True):
                    kwargs=dict(expected_project=Path(directory)/'expected.toe',recovery_path=Path(directory)/'new.tox')
                    if reject_final:
                        with self.assertRaisesRegex(ValueError,'Final validation'):upgrade.install(controller,SOURCE,**kwargs)
                        self.assertEqual(wrapper.fetch('owned_inspector_sources'),marker)
                    else:
                        self.assertIs(upgrade.install(controller,SOURCE,**kwargs),wrapper)
                        self.assertNotIn('owned_inspector_sources',wrapper.storage)
                self.assertEqual(wrapper.fetch('unrelated'),'preserved')
