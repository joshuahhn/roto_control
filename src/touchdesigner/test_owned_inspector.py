"""Owned packaging boundaries; native serialization/geometry remain live checks."""
import copy
import importlib.util
from pathlib import Path
from types import SimpleNamespace as S
import unittest
from unittest.mock import Mock, patch

SOURCE = Path(__file__).parent

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec); spec.loader.exec_module(result)
    return result

runtime = load('owned_inspector_runtime', SOURCE/'code/py/roto_python/inspector/owned_runtime.py')
builder = load('owned_inspector_builder', SOURCE/'build_inspector.py')

class Parameter:
    def __init__(self, value=None, default=None):
        self.val=value;self.default=default;self.expr=''
    def eval(self):return self.val

class Node:
    """Native hierarchy boundary only, not a simulated controller/runtime."""
    def __init__(self,name,parent=None,kind='baseCOMP'):
        self.name=name;self._parent=parent;self.OPType=kind;self.valid=True;self.id=id(self)
        self.children=[];self.storage={};self.par=S();self.text=''
        if kind.endswith('DAT'):
            self.par=S(file=Parameter('/external/source.py'),syncfile=Parameter(True),loadonstart=Parameter(True))
        self.extensions=[None];self.ext=S()
        if parent:parent.children.append(self)
    @property
    def path(self):return (self._parent.path if self._parent else '')+'/'+self.name
    def parent(self):return self._parent
    def op(self,path):
        node=self
        for part in path.split('/'):
            node=next((v for v in node.children if v.name==part),None)
            if node is None:return None
        return node
    def findChildren(self,**kwargs):return [v for c in self.children for v in [c]+c.findChildren()]
    def fetch(self,key,default=None):return self.storage.get(key,default)
    def store(self,key,value):self.storage[key]=value


def fixture(name='roto_python'):
    project=Node('demo');c=Node(name,project);w=Node('inspector',c);m=Node('inspector_model',w)
    m.par.Controller=Parameter(c)
    current=S(ownerComp=m,RefreshWatchers=Mock(),onDestroyTD=Mock(),_subscribers={},_closed=False)
    m.extensions[0]=m.ext.InspectorModel=current
    for name in runtime.OBSERVER_NAMES:
        n=Node(name,m,'parameterexecuteDAT');n.par=S(active=True,op=Parameter('/outside'),pars=Parameter('Amount'))
    views=[]
    for name in runtime.VIEW_NAMES:
        v=Node(name,w,'containerCOMP');views.append(v);v.par.Model=Parameter(m)
        for n in ('Layout','Track','Device'):setattr(v.par,n,Parameter('saved-owner','saved-owner'))
        draft=Node('base_draft',v);draft.customPars=[]
        for n,val,default in [('Label','private',''),('Destination','/outside.Amount',''),('Minimum',3,0),('Maximum',9,1),('Value',7,0)]:
            p=Parameter(val,default);draft.customPars.append(p);setattr(draft.par,n,p)
        for n in ('text_name','value0','text_status'):
            t=Node(n,v,'textCOMP');t.par.text=Parameter('/outside/private')
        editor=Node('editor',v,'containerCOMP');toggle=Node('mapping_toggle',editor,'containerCOMP');label=Node('text_label',toggle,'textCOMP');label.par.text='MAPPING  3..9'
        ext=S(ownerComp=v,_model=current,Show=Mock(),Disconnect=Mock(),_editors=(editor,))
        v.extensions[0]=v.ext.InspectorView=ext
        for n in ('window_main','window_editor'):
            win=Node(n,v,'windowCOMP');win.isOpen=False;win.par.winclose=S(pulse=Mock())
    def init_model(index):
        current=S(ownerComp=m,RefreshWatchers=Mock(),onDestroyTD=Mock(),_subscribers={},_closed=False)
        m.extensions[0]=m.ext.InspectorModel=current;m.par.Controller.val=c
    m.initializeExtensions=Mock(side_effect=init_model)
    for v in views:
        def init_view(index,v=v):
            v.par.Model.val=m;current=m.ext.InspectorModel
            ext=S(ownerComp=v,_model=current,Show=Mock(),Disconnect=Mock())
            v.extensions[0]=v.ext.InspectorView=ext;current._subscribers[v.name]=(None,None)
        v.initializeExtensions=Mock(side_effect=init_view)
    return c,w,m,views

class LocalGenerationTests(unittest.TestCase):
    """Exact lifecycle methods with explicit native ownership facts; no TD."""
    @staticmethod
    def methods(filename, classname, names):
        import ast
        tree=ast.parse((SOURCE/'prototypes/inspector'/filename).read_text())
        original=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==classname)
        selected=[n for n in original.body if isinstance(n,ast.FunctionDef) and n.name in names]
        assert len(selected)==len(names)
        cls=ast.ClassDef(name=classname,bases=[],keywords=[],body=selected,decorator_list=[])
        module=ast.fix_missing_locations(ast.Module(body=[cls],type_ignores=[]));scope={}
        exec(compile(module,filename+':exact-lifecycle-methods','exec'),scope)
        return scope[classname]

    def boundary(self):
        from types import MethodType
        catalog=load('owned_lifecycle_catalog',SOURCE/'prototypes/inspector/model.py').CatalogModel
        view_type=self.methods('ui.py','InspectorView',{'Connect','Disconnect','onInitTD'})
        model_type=self.methods('live_model.py','InspectorModel',{'onInitTD','onDestroyTD'})
        c,w,m,views=fixture();Node('owned_runtime',w,'textDAT').module=runtime
        def generation():
            g=model_type();g.ownerComp=m;g._closed=False
            g._queued_run=Mock();g._sync_run=Mock();g._subscribers={}
            g._pending={'old':1};g._cache={};g._scheduled=True
            g.adapter=S(Targets=S(Reset=Mock()))
            g.Shutdown=MethodType(catalog.Shutdown,g)
            g.Unsubscribe=MethodType(catalog.Unsubscribe,g)
            g.GetCatalog=Mock(return_value=());g.Subscribe=MethodType(catalog.Subscribe,g)
            g._context=tuple
            g.ActiveContext=Mock(return_value=('active','track','device'))
            return g
        old=generation();current=generation();m.extensions[0]=m.ext.InspectorModel=current
        for node in views:
            v=view_type();v.ownerComp=node;v._model=old;v._identity=node.id
            v._follow_routing=False;v._filter='custom-owner';v._menu_generation=4
            v._mapping=S(Close=Mock());v._popup_extra=0
            v._native_definition=object();v._token=object();v._original=object()
            v.CloseContextMenu=Mock();v.ClosePicker=Mock();v._cancel_popup_geometry=Mock()
            v.Key=lambda:('browse','track','device');v.IsLive=lambda:True
            v.ConfigureMenus=Mock();v.Refresh=Mock();v.OnModelChange=Mock()
            node.extensions[0]=node.ext.InspectorView=v
            old._subscribers[v._identity]=(v.Key(),v.OnModelChange)
        return c,w,m,views,old,current

    def test_quiesce_local_previous_and_current_generations_not_other_instance(self):
        c,w,m,views,old,current=self.boundary();other,ow,om,ov=fixture('other')
        queued=[g._queued_run for g in (old,current)];sync=[g._sync_run for g in (old,current)]
        runtime.quiesce(c)
        for g,q,s in zip((old,current),queued,sync):
            q.kill.assert_called_once();s.kill.assert_called_once()
            self.assertTrue(g._closed);self.assertEqual(g._subscribers,{})
            self.assertEqual(g._pending,{});g.adapter.Targets.Reset.assert_called_once()
            g.onDestroyTD();g.adapter.Targets.Reset.assert_called_once()
        for node in views:self.assertIsNone(node.ext.InspectorView._model)
        current.onInitTD()
        for node in views:
            node.ext.InspectorView.onInitTD()
            self.assertIsNone(node.ext.InspectorView._model)
        with self.assertRaisesRegex(ValueError,'shut down'):runtime.validate(c)
        for node in ov:node.ext.InspectorView.Disconnect.assert_not_called()
        om.ext.InspectorModel.onDestroyTD.assert_not_called()

    def test_all_reference_proofs_precede_any_effect(self):
        class Unreadable:
            @property
            def ownerComp(self):raise RuntimeError('owner read failed')
        for problem in ('foreign','invalid','unreadable','controller','view_parameter','namespace'):
            with self.subTest(problem=problem):
                c,w,m,views,old,current=self.boundary()
                first=views[0].ext.InspectorView;first.Disconnect=Mock()
                if problem=='foreign':
                    # Equal path text is insufficient: these are different native nodes.
                    impostor=Node(m.name,w);self.assertEqual(impostor.path,m.path)
                    views[1].ext.InspectorView._model=S(ownerComp=impostor)
                elif problem=='invalid':old.ownerComp=Node('deleted');old.ownerComp.valid=False
                elif problem=='unreadable':views[1].ext.InspectorView._model=Unreadable()
                elif problem=='controller':m.par.Controller.val=Node('foreign_controller')
                elif problem=='view_parameter':views[1].par.Model.val=Node('foreign_model')
                else:views[1].ext.InspectorView=object()
                for operation in (runtime.quiesce,runtime.attach_views):
                    with self.assertRaises((ValueError,RuntimeError)):operation(c)
                    first.Disconnect.assert_not_called()
                    old._queued_run.kill.assert_not_called();current._queued_run.kill.assert_not_called()
                    self.assertTrue(all(m.op(name).par.active for name in runtime.OBSERVER_NAMES))

    def test_model_oninit_current_attachment_browse_and_transient_invalidation(self):
        c,w,m,views,old,current=self.boundary();queued=old._queued_run
        current.onInitTD()
        self.assertTrue(old._closed);queued.kill.assert_called_once()
        self.assertEqual(old._subscribers,{})
        self.assertEqual(set(current._subscribers),{v.id for v in views})
        self.assertFalse(current._closed);current._queued_run.kill.assert_not_called()
        for node in views:
            v=node.ext.InspectorView;self.assertIs(v._model,current)
            v.ConfigureMenus.assert_called_once_with(('browse','track','device'))
            self.assertEqual((v._filter,v._follow_routing),('custom-owner',False))
            self.assertIsNone(v._token);self.assertIsNone(v._original);self.assertIsNone(v._native_definition)
            v._mapping.Close.assert_called_once();self.assertEqual(v._menu_generation,5)
        runtime.validate(c);current.onInitTD()
        for node in views:
            node.ext.InspectorView.onInitTD()
            node.ext.InspectorView._mapping.Close.assert_called_once()
        self.assertEqual(c.storage,{})

    def test_view_oninit_does_not_keep_truthy_previous_generation(self):
        c,w,m,views,old,current=self.boundary()
        views[0].ext.InspectorView.onInitTD()
        self.assertTrue(old._closed)
        for v in views:self.assertIs(v.ext.InspectorView._model,current)
        runtime.validate(c)

    def test_stale_lifecycle_callback_and_open_remain_strict(self):
        c,w,m,views,old,current=self.boundary()
        with self.assertRaisesRegex(ValueError,'current model'):runtime.validate(c)
        with self.assertRaisesRegex(ValueError,'stale'):old.onInitTD()
        with self.assertRaisesRegex(ValueError,'stale'):
            runtime.attach_views(c,expected_view=S(ownerComp=views[0]))
        self.assertFalse(old._closed);old._queued_run.kill.assert_not_called()
        for node in views:self.assertIs(node.ext.InspectorView._model,old)

    def test_live_reattachment_uses_active_context_without_business(self):
        c,w,m,views,old,current=self.boundary();views[0].ext.InspectorView._follow_routing=True
        current.onInitTD()
        views[0].ext.InspectorView.ConfigureMenus.assert_called_once_with(('active','track','device'))
        views[1].ext.InspectorView.ConfigureMenus.assert_called_once_with(('browse','track','device'))
        self.assertEqual(c.storage,{})


class OwnedInspectorTests(unittest.TestCase):
    def test_native_pulse_opens_only_current_local_primary_without_business(self):
        RotoPythonExt=load('owned_roto_extension', SOURCE/'code/py/roto_python/RotoPythonExt.py').RotoPythonExt
        c,w,m,views=fixture();dat=Node('owned_runtime',w,'textDAT');dat.module=runtime
        e=RotoPythonExt.__new__(RotoPythonExt);e.ownerComp=c
        e.Connect=Mock();e.Disconnect=Mock();e.Applybinding=Mock();e._publish=Mock()
        before=copy.deepcopy(c.storage);e.onParPulse(S(name='Openinspector'))
        views[0].ext.InspectorView.Show.assert_called_once_with();views[1].ext.InspectorView.Show.assert_not_called()
        for call in (e.Connect,e.Disconnect,e.Applybinding,e._publish):call.assert_not_called()
        self.assertEqual(c.storage,before)

    def test_two_moved_renamed_instances_keep_local_references(self):
        a,aw,am,av=fixture('first');b,bw,bm,bv=fixture('second')
        a.name='renamed';a.parent().name='moved_branch'
        runtime.open_inspector(a);runtime.open_inspector(b)
        self.assertEqual(am.par.Controller.eval().path,'/moved_branch/renamed');self.assertIsNot(am,bm)
        av[0].ext.InspectorView.Show.assert_called_once();bv[0].ext.InspectorView.Show.assert_called_once()
        bm.par.Controller.val=a
        with self.assertRaisesRegex(ValueError,'another controller'):runtime.open_inspector(b)
        self.assertEqual(bv[0].ext.InspectorView.Show.call_count,1)

    def test_foreign_or_stale_view_rejected_before_open(self):
        for field in ('owner','model_parameter','attached_model'):
            c,w,m,views=fixture();v=views[0];ext=v.ext.InspectorView
            if field=='owner':ext.ownerComp=Node('foreign')
            elif field=='model_parameter':v.par.Model.val=Node('foreign')
            else:ext._model=object()
            with self.assertRaises((ValueError,AttributeError)):runtime.open_inspector(c)
            ext.Show.assert_not_called()
        with self.assertRaises(AttributeError):runtime.quiesce(c)
        ext.Disconnect.assert_not_called()

    def test_generic_scrub_preserves_source_local_refs_and_external_state(self):
        c,w,m,views=fixture();source=Node('ui',views[0],'textDAT');source.text='exact embedded code'
        w.store('owned_inspector_sources',{'build':'pin','dat':{'ui':'hash'}})
        m.storage.update(owner_ref='/outside',cache='old target');views[0].storage['draft']='private'
        c.storage={'layout_registry':{'empty':True}};external={'roto_control_owner_id':'external-owner'}
        previous=m.ext.InspectorModel;runtime.sanitize(c)
        self.assertEqual(source.text,'exact embedded code');self.assertEqual(external,{'roto_control_owner_id':'external-owner'})
        self.assertEqual(c.storage,{'layout_registry':{'empty':True}});self.assertEqual(m.storage,{})
        self.assertEqual(views[0].storage,{})
        self.assertEqual(views[0].op('base_draft').par.Destination,'')
        self.assertEqual(views[0].op('text_name').par.text.val,'');self.assertEqual(views[0].op('value0').par.text.val,'')
        self.assertEqual(views[0].op('editor/mapping_toggle/text_label').par.text,'MAPPING  ▸')
        self.assertEqual(m.par.Controller.expr,'parent().parent()');self.assertEqual(views[0].par.Model.expr,"parent().op('inspector_model')")
        watcher=m.op('controller_parameters');self.assertFalse(watcher.par.active)
        self.assertEqual((watcher.par.op,watcher.par.pars),('',''))
        self.assertIsNot(m.ext.InspectorModel,previous);self.assertEqual(len(m.ext.InspectorModel._subscribers),2)
        previous.onDestroyTD.assert_called()

    def test_repeated_initialization_releases_old_model_without_autoopen(self):
        c,w,m,views=fixture();previous=[]
        for _ in range(3):
            previous.append(m.ext.InspectorModel);runtime.initialize(c);runtime.validate(c)
            self.assertEqual(len(m.ext.InspectorModel._subscribers),2)
        for model in previous:model.onDestroyTD.assert_called_once()
        for v in views:v.ext.InspectorView.Show.assert_not_called()

    def test_identical_packaging_noop_and_old_ui_requires_archive(self):
        c,w,m,views=fixture();c.ext.RotoPythonExt=S(_process=None)
        w.store('owned_inspector_sources',{'build':'bundle','dat':{'ui':'exact'}})
        dat=Node('owned_runtime',w,'textDAT');dat.module=runtime
        with patch.object(builder,'_fingerprint',return_value='bundle'),patch.object(builder,'_manifest',return_value={'ui':'exact'}),patch.object(builder,'install_open_parameter'),patch.object(builder,'_verify_runtime_sources'):
            self.assertIs(builder.build(c,SOURCE),w);self.assertIs(builder.build(c,SOURCE),w)
        m.initializeExtensions.assert_not_called()
        for v in views:v.initializeExtensions.assert_not_called()
        Node('lister',w,'containerCOMP')
        with patch.object(builder,'_fingerprint',return_value='changed'),patch.object(builder,'install_open_parameter'),patch.object(builder,'_verify_runtime_sources'):
            with self.assertRaisesRegex(ValueError,'legacy_archive'):builder.build(c,SOURCE)

    def test_open_custompar_and_callback_are_idempotent(self):
        class Callback:
            def __init__(self):self._pars='Connect Disconnect Applybinding'
            @property
            def pars(self):return S(eval=lambda:self._pars)
            @pars.setter
            def pars(self,value):self._pars=value
        page=S(name='Connection');appends=[];c=S(customPages=[page],par=S(Disconnect=S(order=3)))
        def append(name,label):appends.append(name);setattr(c.par,name,S(label=label,page=page,order=0))
        page.appendPulse=append;callback=S(par=Callback());c.op=lambda name:callback
        builder.install_open_parameter(c);builder.install_open_parameter(c)
        self.assertEqual(appends,['Openinspector']);self.assertEqual(callback.par._pars,'Connect Disconnect Applybinding Openinspector')
        self.assertEqual(c.par.Openinspector.order,4)


class HeadlessPublicationTests(unittest.TestCase):
    def test_catalog_metadata_change_without_lister_or_title(self):
        data=load('owned_inspector_data', SOURCE/'code/py/roto_python/inspector/inspector_data.py')
        from test_inspector import InspectorTests
        c,w,m,views=fixture()
        Node('owned_runtime',w,'textDAT')
        for name in ('targets','database','context_state'):Node(name,w,'textDAT')
        context=dict(key=('owner','track','device'),label='Device',locked=False)
        c.GetLayoutContext=lambda:copy.deepcopy(context);c.GetLayouts=lambda:[dict(id='owner',category='COMP')]
        c.GetCompContext=lambda:dict(status='disabled')
        state=InspectorTests().state()
        data.refresh(w,[state])
        self.assertIsNone(w.op('lister'));self.assertIsNone(w.op('title'))
        self.assertIn('scene.speed',w.op('targets').text)
        self.assertIn('owner',w.op('context_state').text)
        first=data.projection_signature(w,[state])
        context['label']='Renamed';state['value']=9
        self.assertNotEqual(first,data.projection_signature(w,[state]))
        data.refresh(w,[state]);self.assertIn('Renamed',w.op('context_state').text)
        self.assertIn('9',w.op('database').text)

    def test_owned_error_notification_stays_optional_and_visible_in_metadata(self):
        import test_api,json
        e=test_api.ApiTests().collection();c,w,m,views=fixture()
        data=Node('inspector_data',w,'textDAT')
        data.module=S(refresh=Mock(side_effect=ValueError('projection unavailable')))
        Node('owned_runtime',w,'textDAT');meta=Node('context_state',w,'textDAT')
        meta.text='{"routing": {"key": ["a", "b", "c"]}}'
        e.ownerComp.op=lambda name:w
        e._publish_inspector(force=True)
        self.assertEqual(w.fetch('refresh_error'),'projection unavailable')
        self.assertEqual(json.loads(meta.text)['projection_error'],'projection unavailable')
        self.assertEqual(json.loads(meta.text)['routing']['key'],['a','b','c'])


class ReviewResponseTests(unittest.TestCase):
    def test_archive_is_taken_before_upgrade_source_or_file_settings(self):
        import ast
        tree=ast.parse((SOURCE/'upgrade_layouts.py').read_text())
        function=next(n for n in tree.body if isinstance(n,ast.FunctionDef))
        archive_line=next(n.lineno for n in ast.walk(function) if isinstance(n,ast.Call)
                          and isinstance(n.func,ast.Subscript) and isinstance(n.func.slice,ast.Constant)
                          and n.func.slice.value=='archive_legacy')
        writes=[n.lineno for n in ast.walk(function) if isinstance(n,ast.Assign)
                and any(isinstance(t,ast.Attribute) and t.attr in ('text','file','syncfile','loadonstart') for t in n.targets)]
        self.assertLess(archive_line,min(writes))
        # The archive helper preserves exact pre-upgrade content and rejects reuse.
        import tempfile
        c,w,m,views=fixture();Node('lister',w,'containerCOMP')
        old=Node('inspector_data',w,'textDAT');old.text='old source';old.par.file='old/file.py'
        saved=[]
        def save(path,createFolders):
            saved.append((old.text,old.par.file));Path(path).write_bytes(b'fake boundary only')
        w.save=Mock(side_effect=save)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'old.tox';receipt=builder.archive_legacy(c,path)
            old.text='new source';old.par.file=''
            builder._check_archive(c,w,receipt)
            with self.assertRaises(ValueError):builder.archive_legacy(c,path)
        self.assertEqual(saved,[('old source','old/file.py')])

    def test_required_runtime_and_helper_source_mismatch_stops_packaging(self):
        c,w,m,views=fixture()
        names=('RotoPythonExt','protocol','collection_protocol','controls','binding',
               'free_learn','layouts','layout_migration','text_comp_follow','setup',
               'parameter_callbacks','lifecycle_callbacks','target_callbacks','learn_parameters')
        for name in names:
            n=Node(name,c,'textDAT');n.text=(SOURCE/'code/py/roto_python'/f'{name}.py').read_text()
        base=Node('base_targets',c)
        marker=Node('mapping_marks',base,'textDAT');marker.text=(SOURCE/'code/py/roto_python/base_targets/mapping_marks.py').read_text()
        for kind in ('knob','button'):
            for slot in range(1,9):
                n=Node(f'watch_{kind}{slot}',base,'parameterexecuteDAT');n.text=(SOURCE/'code/py/roto_python/control_callbacks.py').read_text()
        helper=Node('midi_process',c,'textDAT');helper.text=(SOURCE/'midi_process.py').read_text()
        builder._verify_runtime_sources(c,SOURCE)
        helper.text='wrong helper'
        with self.assertRaisesRegex(ValueError,'MIDI helper'):builder._verify_runtime_sources(c,SOURCE)
        helper.text=(SOURCE/'midi_process.py').read_text();c.op('protocol').text='wrong runtime'
        with self.assertRaisesRegex(ValueError,'protocol'):builder._verify_runtime_sources(c,SOURCE)

    def test_packaging_embeds_controller_docs_and_all_existing_sources_before_init(self):
        import ast
        tree=ast.parse((SOURCE/'build_inspector.py').read_text())
        function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='build')
        embeds=[n for n in ast.walk(function) if isinstance(n,ast.Call) and isinstance(n.func,ast.Subscript)
                and isinstance(n.func.slice,ast.Constant) and n.func.slice.value=='embed_project_docs']
        self.assertTrue(any([ast.unparse(a) for a in n.args]==['controller','source'] for n in embeds))
        isolation=next(n for n in ast.walk(function) if isinstance(n,ast.Call)
                       and isinstance(n.func,ast.Name) and n.func.id=='_isolate_sources'
                       and ast.unparse(n.args[0])=='controller')
        init=next(n for n in ast.walk(function) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='initializeExtensions')
        self.assertLess(isolation.lineno,init.lineno)

    def test_cleanup_preserves_same_name_user_annotation_and_removes_tagged_or_explicit_only(self):
        cleanup=load('owned_cleanup',SOURCE/'cleanup_network.py')
        c=Node('roto');notes=[Node('annotate_focus',c,'annotateCOMP'),Node('owned',c,'annotateCOMP'),Node('old_managed',c,'annotateCOMP')]
        notes[1].store('roto_network_group',True)
        for note in notes:note.destroy=Mock()
        plans=[dict(path=c.path,positions={},boxes=[])]
        with patch.object(cleanup,'plan',return_value=plans),patch.object(cleanup,'verify',return_value={'ok':True}):
            cleanup.apply(c,obsolete_annotations=(notes[2].path,))
        notes[0].destroy.assert_not_called();notes[1].destroy.assert_called_once();notes[2].destroy.assert_called_once()


def isolation_boundary():
    """Required native source shapes plus an annotation DAT lacking syncfile."""
    c=Node('roto_python');w=Node('inspector',c)
    names=('RotoPythonExt','protocol','collection_protocol','controls','binding',
           'free_learn','layouts','layout_migration','text_comp_follow','setup',
           'parameter_callbacks','lifecycle_callbacks','target_callbacks','learn_parameters')
    required=[]
    for name in names:
        n=Node(name,c,'textDAT');n.text=(SOURCE/'code/py/roto_python'/f'{name}.py').read_text();required.append(n)
    base=Node('base_targets',c)
    marker=Node('mapping_marks',base,'textDAT');marker.text=(SOURCE/'code/py/roto_python/base_targets/mapping_marks.py').read_text();required.append(marker)
    for kind in ('knob','button'):
        for slot in range(1,9):
            n=Node(f'watch_{kind}{slot}',base,'parameterexecuteDAT');n.text=(SOURCE/'code/py/roto_python/control_callbacks.py').read_text();required.append(n)
    helper=Node('midi_process',c,'textDAT');helper.text=(SOURCE/'midi_process.py').read_text();required.append(helper)
    annotation=Node('annotation',w,'annotateCOMP');internal=Node('help',annotation,'textDAT')
    class InternalPars:
        def __init__(self):
            object.__setattr__(self,'file',Parameter('/help.py'))
            object.__setattr__(self,'loadonstart',Parameter(True))
        def __setattr__(self,name,value):
            if name not in ('file','loadonstart'):raise AttributeError('no native parameter '+name)
            getattr(self,name).val=value
    internal.par=InternalPars()
    return c,w,required,internal


def execute_isolation_call_sites(module,c,w):
    """Execute the actual two isolation statements from build, not copied loops."""
    import ast
    tree=ast.parse(Path(module.__file__).read_text())
    function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='build')
    statements=[]
    for statement in function.body:
        if isinstance(statement,ast.For) and isinstance(statement.iter,ast.Call):
            f=statement.iter.func
            if isinstance(f,ast.Attribute) and f.attr=='findChildren' and isinstance(f.value,ast.Name) and f.value.id in ('controller','wrapper'):
                statements.append(statement)
        elif isinstance(statement,ast.Expr) and isinstance(statement.value,ast.Call):
            f=statement.value.func
            if isinstance(f,ast.Name) and f.id=='_isolate_sources':statements.append(statement)
    if len(statements)!=2:raise AssertionError('Expected both production isolation call sites')
    scope=dict(module.__dict__,controller=c,wrapper=w,DAT=Node)
    with patch.object(module,'DAT',Node,create=True):
        for statement in statements:
            exec(compile(ast.Module(body=[statement],type_ignores=[]),module.__file__,'exec'),scope)


class NativeIsolationResponseTests(unittest.TestCase):
    def test_actual_both_call_sites_handle_internal_dat_and_embed_required_sources(self):
        c,w,required,internal=isolation_boundary()
        builder._verify_runtime_sources(c,SOURCE)
        execute_isolation_call_sites(builder,c,w)
        self.assertFalse(hasattr(internal.par,'syncfile'))
        self.assertEqual((internal.par.file.eval(),internal.par.loadonstart.eval()),('',False))
        for node in required:
            self.assertEqual(tuple(getattr(node.par,n).eval() for n in ('file','syncfile','loadonstart')),('',False,False))
        builder._verify_runtime_sources(c,SOURCE)

    def test_required_missing_flag_and_supported_assignment_exception_are_failures(self):
        c,w,required,internal=isolation_boundary()
        del c.op('protocol').par.syncfile
        with self.assertRaisesRegex(ValueError,'protocol.syncfile'):
            builder._verify_runtime_sources(c,SOURCE)
        class Unwritable(Parameter):
            @property
            def val(self):return True
            @val.setter
            def val(self,value):raise RuntimeError('supported flag setter failed')
        flag=Unwritable.__new__(Unwritable);object.__setattr__(internal.par,'loadonstart',flag)
        with patch.object(builder,'DAT',Node,create=True):
            with self.assertRaisesRegex(RuntimeError,'supported flag setter failed'):
                builder._isolate_sources(w)


def demo_callback_boundary(source_path,shortcut,existing=False,reject_text=False):
    """Execute the exact production DAT creation/binding block without TD."""
    import ast,os
    trace=[]
    class SourceDat:
        def __init__(self):
            self.par=S(file='/user/source.py',syncfile=True,loadonstart=True)
            self._text='user source'
            class Link:
                @property
                def expr(link):return ''
                @expr.setter
                def expr(link,value):
                    trace.append(('bind',self.par.file,self.par.syncfile,self.par.loadonstart,self._text,value))
            self.par.op=Link()
        @property
        def text(self):return self._text
        @text.setter
        def text(self,value):
            trace.append(('text',self.par.syncfile,self.par.loadonstart))
            if reject_text:raise RuntimeError('native source setter failed')
            self._text=value
    dat=SourceDat()
    demo=S(op=lambda name:dat if existing else None,create=lambda kind,name:dat)
    tree=ast.parse(source_path.read_text())
    function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='upgrade')
    loop=next(n for n in function.body if isinstance(n,ast.For) and 'base_parameter_demo' in ast.unparse(n.iter))
    start=next(i for i,n in enumerate(loop.body) if isinstance(n,ast.Assign)
               and any(isinstance(t,ast.Name) and t.id=='dat' for t in n.targets))
    scope=dict(demo=demo,parameterexecuteDAT=object(),source=SOURCE,shortcut=shortcut,
               project=S(folder='/saved/project'),os=os)
    exec(compile(ast.Module(body=loop.body[start:],type_ignores=[]),str(source_path),'exec'),scope)
    return dat,trace


class DemoEmbeddingResponseTests(unittest.TestCase):
    def test_both_generated_callbacks_embed_exact_bytes_before_observer_binding(self):
        for shortcut,filename in (('ParameterDemo','parameter_demo.py'),('CallbackDemo','callback_demo.py')):
            with self.subTest(shortcut=shortcut):
                dat,trace=demo_callback_boundary(SOURCE/'upgrade_network.py',shortcut)
                text=(SOURCE/'code/py'/filename).read_text()
                self.assertEqual(trace[0],('text',False,False))
                self.assertEqual(trace[1],('bind','',False,False,text,'parent.'+shortcut))
                self.assertEqual(dat.text,text)
                self.assertEqual((dat.par.file,dat.par.syncfile,dat.par.loadonstart),('',False,False))
                self.assertEqual((dat.par.pars,dat.par.custom,dat.par.builtin,dat.par.valuechange,dat.par.onpulse),('Usebinding Setvalue',True,False,False,True))

    def test_existing_user_source_settings_preserved_and_source_errors_propagate(self):
        for shortcut in ('ParameterDemo','CallbackDemo'):
            dat,trace=demo_callback_boundary(SOURCE/'upgrade_network.py',shortcut,existing=True)
            self.assertEqual((dat.text,dat.par.file,dat.par.syncfile,dat.par.loadonstart),('user source','/user/source.py',True,True))
            self.assertEqual([row[0] for row in trace],['bind'])
        with self.assertRaisesRegex(RuntimeError,'native source setter failed'):
            demo_callback_boundary(SOURCE/'upgrade_network.py','ParameterDemo',reject_text=True)
