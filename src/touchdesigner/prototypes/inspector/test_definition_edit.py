from types import SimpleNamespace
from unittest import TestCase
import definition_edit as edits
from test_parameter_definition import parameter,INFO

def par(style='Float'):
    p=parameter(style);p.parGroup=[p];p.sequence=None;p.index=4;p.bindReferences=[]
    p.owner.par=SimpleNamespace(clone=SimpleNamespace(eval=lambda: None));p.owner.clones=[]
    return p

class DefinitionEditTests(TestCase):
    def test_label_default_change_keeps_live_value_and_draft_detached(self):
        p=par();p.val=.7
        d=edits.begin(INFO,lambda i:p)
        self.assertTrue(edits.apply(INFO,d,dict(label='Threshold A',default=.5),lambda i:p))
        self.assertEqual((p.label,p.default,p.val),('Threshold A',.5,.7))
        self.assertEqual(d['original']['default'],.25)

    def test_value_traffic_does_not_invalidate_metadata_draft(self):
        p=par();d=edits.begin(INFO,lambda i:p);p.val=.9
        self.assertFalse(edits.apply(INFO,d,d['original'],lambda i:p))

    def test_external_native_changes_reject_without_overwriting(self):
        for field,value in [('label','External'),('default',.3),('normMax',2),('normMax',1.000000000001),('index',5),('default',.250000000001)]:
            p=par();d=edits.begin(INFO,lambda i:p);setattr(p,field,value)
            with self.assertRaisesRegex(ValueError,'changed'):edits.apply(INFO,d,dict(label='Draft',default=.5),lambda i:p)
            self.assertEqual(getattr(p,field),value)

    def test_group_clone_binding_expression_and_non_numeric_rejected(self):
        for mutate in (lambda p:setattr(p,'parGroup',[p,p]),lambda p:setattr(p.owner,'clones',[object()]),
                       lambda p:setattr(p,'bindReferences',[object()]),lambda p:setattr(p,'mode',SimpleNamespace(name='BIND')),
                       lambda p:setattr(p,'defaultMode',SimpleNamespace(name='EXPRESSION')),lambda p:setattr(p,'readOnly',True),
                       lambda p:setattr(p,'sequence',object()),lambda p:setattr(p,'isCustom',False),lambda p:setattr(p,'style','Toggle')):
            p=par();mutate(p)
            with self.assertRaises(ValueError):edits.begin(INFO,lambda i:p)

    def test_invalid_typed_defaults_and_labels_write_nothing(self):
        p=par('Int');p.clampMin=True;p.min=0;p.max=3
        d=edits.begin(INFO,lambda i:p)
        for label,value in [('A',.5),('A',float('nan')),('A',float('inf')),('A',4),('',1),('A\nB',1)]:
            with self.assertRaises(ValueError):edits.apply(INFO,d,dict(label=label,default=value),lambda i:p)
            self.assertEqual((p.label,p.default),('Low Threshold',.25))

    def test_setter_failure_rolls_back_preceding_label(self):
        p=par()
        class Failing:
            def __setattr__(self,key,value):
                if key=='default' and value==.5:raise RuntimeError('setter rejected')
                super().__setattr__(key,value)
        wrapper=Failing();wrapper.__dict__.update(vars(p));p=wrapper
        d=edits.begin(INFO,lambda i:p)
        with self.assertRaisesRegex(RuntimeError,'restored'):edits.apply(INFO,d,dict(label='Changed',default=.5),lambda i:p)
        self.assertEqual((p.label,p.default),('Low Threshold',.25))

from live_model import ControllerCatalog,TDControllerAdapter,StaleDraft
from test_parameter_definition import DefinitionAdapter
from test_live_model import KEY

class WriteAdapter(DefinitionAdapter):
    def __init__(self):
        super().__init__();self.par=par()
        self.controller=SimpleNamespace(GetLayoutContext=lambda:dict(quarantined=False),State=dict(Learning=False,Touched=False),
            GetControlState=lambda id:dict(touched=False))
    def DefinitionDraft(self,key,info):
        TDControllerAdapter._definition_guard(self,key,info)
        return edits.begin(info,lambda i:self.par)
    def ApplyDefinition(self,key,info,draft,patch):
        TDControllerAdapter._definition_guard(self,key,info)
        return edits.apply(info,draft,patch,lambda i:self.par)

class DefinitionCommandTests(TestCase):
    def test_fresh_hardware_guard_and_session_reject_without_metadata_writes(self):
        a=WriteAdapter();m=ControllerCatalog(a);token=m.GetToken(KEY,1)
        d=m.DefinitionDraft(KEY,1,token)
        for field in ('Learning','Touched'):
            a.controller.State[field]=True
            with self.assertRaises(ValueError):m.ApplyDefinition(KEY,1,token,d,dict(label='Draft',default=.5))
            a.controller.State[field]=False
        a.session+=1
        with self.assertRaises(StaleDraft):m.ApplyDefinition(KEY,1,token,d,dict(label='Draft',default=.5))
        self.assertEqual((a.par.label,a.par.default),('Low Threshold',.25))
        self.assertEqual(a.writes,[]);self.assertEqual(a.pings,[])

    def test_apply_keeps_mapping_identity_range_and_value(self):
        a=WriteAdapter();m=ControllerCatalog(a);token=m.GetToken(KEY,1)
        before=dict(m.GetCatalog(KEY)[1])
        d=m.DefinitionDraft(KEY,1,token)
        self.assertTrue(m.ApplyDefinition(KEY,1,token,d,dict(label='Native only',default=.5)))
        self.assertEqual(dict(m.GetCatalog(KEY)[1]),before)
        self.assertEqual((a.par.label,a.par.default),('Native only',.5))
        self.assertEqual(a.writes,[]);self.assertEqual(a.pings,[])
