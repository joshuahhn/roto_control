"""Lossless conversion, references, registry semantics and compensation boundaries."""
from copy import deepcopy
from types import SimpleNamespace
from unittest import TestCase
import style_migration as migration
from test_definition_edit import par
from test_parameter_definition import INFO
from live_model import TDControllerAdapter
from test_live_model import KEY

RANGES=((KEY,'amount',-2.,7.),)

def native(style='Float'):
    p=par(style);p.val=3;p.default=2;p.order=1
    p.normMin=-2;p.normMax=7;p.min=-4;p.max=8;p.clampMin=p.clampMax=True
    for k,v in migration.DEFAULTS.items():setattr(p,k,v)
    p.startSection=True;p.help='A useful amount';p.enableExpr='me.par.Enabled'
    p.expr='previous expression';p.defaultExpr='previous default'
    p.eval=lambda:p.val;p.isSamePar=lambda q:p is q
    return p

def replace(p,style,draft,metadata,value):
    p.style=style;p.isMenu=False;p.isNumber=True
    p.__dict__.update(metadata);p.val=value
    return p

class StyleMigrationTests(TestCase):
    def test_parameter_preview_exposes_proposed_definition_without_native_edits(self):
        p=native();d=migration.begin(p);candidate=migration.plan(p,d,dict(style='Int',default=1),RANGES)
        view=migration.ParameterPreview(p,candidate)
        self.assertEqual((view.style,view.default,view.val,view.eval()),('Int',1,3,3))
        self.assertIs(view.owner,p.owner);self.assertEqual(view.name,p.name)
        self.assertEqual((p.style,p.default),('Float',2))

    def test_both_directions_preserve_metadata_value_and_reference(self):
        for before,after in [('Float','Int'),('Int','Float')]:
            p=native(before);d=migration.begin(p);calls=[];reference=p
            candidate=migration.plan(p,d,dict(style=after),RANGES)
            patch=dict(style=after,style_value=candidate['value'])
            self.assertTrue(migration.apply(p,d,patch,RANGES,lambda:calls.append(p.style),lambda:None,replace))
            self.assertEqual(calls,[after]);self.assertIs(p,reference)
            self.assertEqual((p.index,p.order,p.val,p.default,p.help,p.enableExpr,p.expr,p.defaultExpr),
                             (4,1,3,2,'A useful amount','me.par.Enabled','previous expression','previous default'))
            self.assertEqual((p.min,p.max,p.normMin,p.normMax,p.clampMin,p.clampMax),(-4,8,-2,7,True,True))

    def test_fractional_value_default_bounds_and_saved_ranges_rejected(self):
        for change in (lambda p:setattr(p,'val',3.5),lambda p:setattr(p,'default',2.5),
                       lambda p:setattr(p,'normMax',7.5),lambda p:setattr(p,'min',-4.5)):
            p=native();change(p);d=migration.begin(p)
            with self.assertRaises(ValueError):migration.plan(p,d,dict(style='Int'),RANGES)
            self.assertEqual(p.style,'Float')
        p=native();d=migration.begin(p)
        with self.assertRaisesRegex(ValueError,'Mapping Range endpoints'):
            migration.plan(p,d,dict(style='Int'),RANGES+((('L','T','other'),'inactive',.25,.75),))

    def test_explicit_default_edit_can_make_candidate_lossless(self):
        p=native();p.default=2.5;d=migration.begin(p)
        result=migration.plan(p,d,dict(style='Int',default=2),RANGES)
        self.assertEqual(result['metadata']['default'],2)
        self.assertEqual(p.default,2.5)

    def test_stale_full_metadata_and_preview_value_reject_before_effects(self):
        for key,value in [('help','External'),('enableExpr','other'),('defaultExpr','1'),('startSection',False),('hidden',True)]:
            p=native();d=migration.begin(p);setattr(p,key,value)
            with self.assertRaisesRegex(ValueError,'definition changed|Hidden'):
                migration.plan(p,d,dict(style='Int'),RANGES)
        p=native();d=migration.begin(p);p.val=4;calls=[]
        for patch in (dict(style='Int'),dict(style='Int',style_value=3)):
            with self.assertRaisesRegex(ValueError,'preview'):
                migration.apply(p,d,patch,RANGES,lambda:calls.append(1),lambda:None,replace)
        self.assertEqual(calls,[]);self.assertEqual((p.style,p.val),('Float',4))

    def test_reconcile_failure_restores_original_and_calls_compensation(self):
        p=native();d=migration.begin(p);events=[]
        def reconcile():events.append(('commit',p.style));raise RuntimeError('registry failed')
        def compensate():events.append(('repair',p.style))
        with self.assertRaisesRegex(RuntimeError,'original definition restored'):
            migration.apply(p,d,dict(style='Int',style_value=3),RANGES,reconcile,compensate,replace)
        self.assertEqual(events,[('commit','Int'),('repair','Float')]);self.assertEqual(migration.begin(p),d)

    def test_setter_failure_restores_without_hardware_calls(self):
        p=native();d=migration.begin(p);calls=[]
        def fail(p,style,draft,metadata,value):
            if style=='Int':p.style=style;p.val=0;raise RuntimeError('native setter failed')
            return replace(p,style,draft,metadata,value)
        with self.assertRaisesRegex(RuntimeError,'original definition restored'):
            migration.apply(p,d,dict(style='Int',style_value=3),RANGES,lambda:calls.append(1),lambda:calls.append(2),fail)
        self.assertEqual(calls,[]);self.assertEqual(migration.begin(p),d);self.assertEqual(p.val,3)

    def test_identity_or_incomplete_binding_repair_is_reported(self):
        p=native();d=migration.begin(p)
        def failure():raise RuntimeError('failed')
        with self.assertRaisesRegex(RuntimeError,'bindings: failed'):
            migration.apply(p,d,dict(style='Int',style_value=3),RANGES,failure,failure,replace)
        self.assertEqual(p.style,'Float')
        p=native();d=migration.begin(p)
        def changed_index(p,style,draft,metadata,value):
            replace(p,style,draft,metadata,value);p.index+=1;return p
        with self.assertRaisesRegex(RuntimeError,'rollback incomplete'):
            migration.apply(p,d,dict(style='Int',style_value=3),RANGES,lambda:None,lambda:None,changed_index)

    def test_candidate_clamps_and_unsupported_styles_write_nothing(self):
        p=native();d=migration.begin(p)
        for patch in (dict(style='Int',max=2),dict(style='Int',min=-1),dict(style='Menu'),dict(style='Int',name='Other')):
            with self.assertRaises(ValueError):migration.plan(p,d,patch,RANGES)
        self.assertEqual(migration.begin(p),d)

    def test_noop_has_no_setter_or_controller_effect(self):
        p=native();d=migration.begin(p);calls=[]
        self.assertFalse(migration.apply(p,d,dict(style='Float'),RANGES,lambda:calls.append(1),lambda:calls.append(2),replace))
        self.assertEqual(calls,[])

    def test_group_clone_bind_and_expression_ownership_reject(self):
        for change in (lambda p:setattr(p,'parGroup',[p,p]),lambda p:setattr(p,'bindReferences',[object()]),
                       lambda p:setattr(p.owner,'clones',[object()]),lambda p:setattr(p,'mode',SimpleNamespace(name='EXPRESSION'))):
            p=native();change(p)
            with self.assertRaises(ValueError):migration.begin(p)


def target(id='amount',comp='../effect'):
    return dict(kind='knob',slot=1,id=id,label='Amount',mode='value',button_type=None,minimum=-2,maximum=7,
                index=128,identity=id+':old-float',comp=comp,parameter='Threshold',menu_names=[],menu_labels=[])

class StyleLibraryTests(TestCase):
    def test_pending_value_and_wrong_binding_style_reject_before_replacement(self):
        p=native();binding=SimpleNamespace(valid=True,integer=False,value=3,parameter=p)
        collection=SimpleNamespace(bindings={'key':binding},key=lambda id:'key')
        adapter=SimpleNamespace(controller=SimpleNamespace(ext=SimpleNamespace(RotoPythonExt=SimpleNamespace(_collection=collection))))
        TDControllerAdapter._style_binding_guard(adapter,INFO,dict(value=3))
        for change,reason in ((lambda:setattr(binding,'value',2),'pending'),
                              (lambda:setattr(binding,'integer',True),'stale'),
                              (lambda:setattr(binding,'valid',False),'stale')):
            binding.value=3;binding.integer=False;binding.valid=True;change()
            with self.assertRaisesRegex(ValueError,reason):
                TDControllerAdapter._style_binding_guard(adapter,INFO,dict(value=3))

    def fixture(self):
        item=target();unrelated=target('unrelated','../other')
        plugin=dict(id='device',targets=[deepcopy(item)],state=dict(page_targets=[deepcopy(item)],parameter_assignments=[deepcopy(item)],
            control_catalog=[dict(item,mapped=True)],needs_relearn=('previous',)))
        other=dict(id='other',targets=[deepcopy(unrelated)],state={})
        return dict(records=[dict(id='layout',tracks=[dict(id='track',plugins=[plugin,other])])]),[target('page')]

    def test_all_related_snapshots_change_identity_pending_without_registration_loss(self):
        data,pages=self.fixture();original=deepcopy((data,pages))
        new,updated,ids=migration.rewrite_library(data,pages,'/effect','Threshold','/controller',lambda r:r['id']+':new-int','Int')
        plugin=new['records'][0]['tracks'][0]['plugins'][0]
        for records in (plugin['targets'],plugin['state']['page_targets'],plugin['state']['parameter_assignments'],updated):
            self.assertTrue(all(r['identity'].endswith(':new-int') and r['parameter_style']=='Int' for r in records))
            self.assertTrue(all((r['minimum'],r['maximum'],r['index'],r['slot'])==(-2,7,128,1) for r in records))
        self.assertEqual(plugin['state']['needs_relearn'],('amount','previous'))
        self.assertFalse(plugin['state']['control_catalog'][0]['mapped'])
        self.assertEqual(new['records'][0]['tracks'][0]['plugins'][1],data['records'][0]['tracks'][0]['plugins'][1])
        self.assertEqual(ids,('page',));self.assertEqual((data,pages),original)

    def test_bad_registration_and_rewrite_failure_leave_original_library(self):
        data,pages=self.fixture();before=deepcopy((data,pages))
        def failed(record):raise RuntimeError('identity unavailable')
        with self.assertRaises(RuntimeError):migration.rewrite_library(data,pages,'/effect','Threshold','/controller',failed,'Int')
        self.assertEqual((data,pages),before)
        pages[0]['mode']='pulse'
        with self.assertRaisesRegex(ValueError,'incompatible'):
            migration.rewrite_library(data,pages,'/effect','Threshold','/controller',lambda r:'new','Int')

    def test_matching_is_exact_path_parameter_and_handles_relative_comp(self):
        self.assertTrue(migration.matches(target(),'/effect','Threshold','/controller'))
        self.assertFalse(migration.matches(target(),'/effect','Other','/controller'))
        self.assertFalse(migration.matches(target(),'/effect2','Threshold','/controller'))

    def test_other_controller_saved_registration_blocks_without_initialization(self):
        import live_model
        class Foreign:
            path='/other/controller'
            def fetch(self,key,default):return dict(control_catalog=[target(comp='/effect')]).get(key,default)
        foreign=Foreign();saved_root=getattr(live_model,'root',None);saved_type=getattr(live_model,'textDAT',None)
        live_model.root=SimpleNamespace(findChildren=lambda **kw:[SimpleNamespace(parent=lambda:foreign)])
        live_model.textDAT=object()
        try:
            adapter=SimpleNamespace(controller=object(),StyleModule=lambda:migration)
            with self.assertRaisesRegex(ValueError,'Another controller'):
                TDControllerAdapter._style_foreign_guard(adapter,INFO)
        finally:
            live_model.root=saved_root;live_model.textDAT=saved_type
