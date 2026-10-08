"""Menu label drafts preserve choice semantics and reconcile after validation."""
from types import SimpleNamespace
from unittest import TestCase
import definition_edit as edits
from test_definition_edit import par
from test_parameter_definition import INFO
from ui import InspectorView,MENU_FIELDS
from test_definition_bounds import DraftPars

def menu(count=3):
    p=par('Menu');p.menuNames=['n'+str(i) for i in range(count)]
    p.menuLabels=['Choice '+str(i) for i in range(count)];p.val='n1';p.default='n0'
    return p

class MenuDraftTests(TestCase):
    def test_reconcile_after_setter_noop_and_semantics_preserved(self):
        p=menu();d=edits.begin(INFO,lambda i:p);calls=[]
        def reconcile():calls.append(tuple(p.menuLabels))
        self.assertFalse(edits.apply(INFO,d,d['original'],lambda i:p,reconcile=reconcile))
        self.assertEqual(calls,[])
        self.assertTrue(edits.apply(INFO,d,dict(menuLabels=['A','B','C']),lambda i:p,reconcile=reconcile))
        self.assertEqual(calls,[('A','B','C')])
        self.assertEqual((p.val,p.default,p.menuNames),('n1','n0',['n0','n1','n2']))
        self.assertEqual(d['original']['menuLabels'],('Choice 0','Choice 1','Choice 2'))

    def test_reconciliation_required_before_setters(self):
        p=menu();d=edits.begin(INFO,lambda i:p)
        with self.assertRaisesRegex(ValueError,'reconciliation'):
            edits.apply(INFO,d,dict(menuLabels=['A','B','C']),lambda i:p)
        self.assertEqual(p.menuLabels,list(d['original']['menuLabels']))

    def test_invalid_patch_and_full_fingerprint(self):
        for patch in [dict(menuLabels=['A']),dict(menuLabels=['A','','C']),dict(menuLabels=['A','B\nC','D']),
                      dict(menuLabels=['A','B','X'*129]),dict(menuNames=['a','b','c']),dict(default='n2')]:
            p=menu();d=edits.begin(INFO,lambda i:p);calls=[]
            with self.assertRaises(ValueError):edits.apply(INFO,d,patch,lambda i:p,reconcile=lambda:calls.append(1))
            self.assertEqual(calls,[]);self.assertEqual(p.menuLabels,list(d['original']['menuLabels']))
        p=menu(24);d=edits.begin(INFO,lambda i:p);p.menuLabels[-1]='External'
        with self.assertRaisesRegex(ValueError,'changed'):
            edits.apply(INFO,d,d['original'],lambda i:p,reconcile=lambda:None)
        self.assertEqual(p.menuLabels[-1],'External')

    def test_dynamic_and_unsupported_ownership(self):
        for change in (lambda p:setattr(p,'menuSource',"op('source').par.Menu"),
                       lambda p:setattr(p,'menuNames',['n0','n0','n2']),lambda p:setattr(p,'menuLabels',['A']),
                       lambda p:setattr(p.owner,'clones',[object()])):
            p=menu();change(p)
            with self.assertRaises(ValueError):edits.begin(INFO,lambda i:p)
        for count in (1,25):
            with self.assertRaises(ValueError):edits.begin(INFO,lambda i:menu(count))

    def test_library_change_and_value_traffic(self):
        p=menu();ranges=((('L','T','D'),'id',0.,2.),);d=edits.begin(INFO,lambda i:p,ranges);p.val='n2'
        with self.assertRaisesRegex(ValueError,'Saved mappings changed'):
            edits.apply(INFO,d,dict(menuLabels=['A','B','C']),lambda i:p,(),reconcile=lambda:None)
        self.assertTrue(edits.apply(INFO,d,dict(menuLabels=['A','B','C']),lambda i:p,ranges,reconcile=lambda:None))
        self.assertEqual(p.val,'n2')

    def test_failure_restores_native_and_repairs_binding(self):
        p=menu();d=edits.begin(INFO,lambda i:p);calls=[]
        def reconcile():
            calls.append(tuple(p.menuLabels))
            if len(calls)==1:raise RuntimeError('transport failed')
        with self.assertRaisesRegex(RuntimeError,'native labels restored'):
            edits.apply(INFO,d,dict(menuLabels=['A','B','C']),lambda i:p,reconcile=reconcile)
        self.assertEqual(calls,[('A','B','C'),d['original']['menuLabels']]);self.assertEqual(p.val,'n1')

    def test_failed_binding_repair_is_explicit(self):
        p=menu();d=edits.begin(INFO,lambda i:p)
        def reconcile():raise RuntimeError('failure')
        with self.assertRaisesRegex(RuntimeError,'binding repair incomplete'):
            edits.apply(INFO,d,dict(menuLabels=['A','B','C']),lambda i:p,reconcile=reconcile)
        self.assertEqual(p.menuLabels,list(d['original']['menuLabels']))

    def test_native_setter_failure_never_calls_controller(self):
        p=menu();d=edits.begin(INFO,lambda i:p);calls=[]
        class Failing:
            def __setattr__(self,key,value):
                if key=='menuLabels' and value==['A','B','C']:raise RuntimeError('setter rejected')
                super().__setattr__(key,value)
        wrapped=Failing();wrapped.__dict__.update(vars(p))
        with self.assertRaisesRegex(RuntimeError,'native labels restored'):
            edits.apply(INFO,d,dict(menuLabels=['A','B','C']),lambda i:wrapped,reconcile=lambda:calls.append(1))
        self.assertEqual(calls,[]);self.assertEqual(wrapped.menuLabels,list(d['original']['menuLabels']))

    def test_native_callback_choice_mutation_is_reported(self):
        p=menu();d=edits.begin(INFO,lambda i:p);calls=[]
        class Mutating:
            def __setattr__(self,key,value):
                super().__setattr__(key,value)
                if key=='menuLabels' and value==['A','B','C']:self.menuNames=['other','n1','n2']
        wrapped=Mutating();wrapped.__dict__.update(vars(p))
        with self.assertRaisesRegex(RuntimeError,'native rollback incomplete'):
            edits.apply(INFO,d,dict(menuLabels=['A','B','C']),lambda i:wrapped,reconcile=lambda:calls.append(1))
        self.assertEqual(calls,[]);self.assertEqual(wrapped.val,'n1')

    def test_all_ui_fields_and_discard_scrub(self):
        p=menu(24);d=edits.begin(INFO,lambda i:p)
        view=InspectorView.__new__(InspectorView);view._draft=SimpleNamespace(par=DraftPars({name:'' for key,name in MENU_FIELDS}))
        view._definition_draft=d;view._load_definition_draft(d)
        self.assertEqual(view._definition_patch(),d['original'])
        view._draft.par[MENU_FIELDS[-1][1]]='Last label'
        self.assertEqual(view._definition_patch()['menuLabels'][-1],'Last label')
        view.DiscardDefinition();self.assertTrue(all(not value for value in view._draft.par.values()))
