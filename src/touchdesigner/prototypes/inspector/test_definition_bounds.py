from types import SimpleNamespace
from unittest import TestCase
import definition_edit as edits
from live_model import TDControllerAdapter
from test_definition_edit import par
from test_parameter_definition import INFO
from test_live_model import KEY

def native(style='Float'):
    p=par(style);p.val=.375 if style=='Float' else 2;p.default=.25 if style=='Float' else 1
    p.eval=lambda: p.val
    return p

RANGES=((KEY,'target',0.,1.),)

class DefinitionBoundsTests(TestCase):
    def test_slider_changes_do_not_change_value_or_mapping(self):
        p=native();d=edits.begin(INFO,lambda i:p,RANGES)
        self.assertTrue(edits.apply(INFO,d,dict(normMin=-1,normMax=2),lambda i:p,RANGES))
        self.assertEqual((p.normMin,p.normMax,p.val),(-1,2,.375))

    def test_compatible_clamps_and_flags_keep_value(self):
        p=native();d=edits.begin(INFO,lambda i:p,RANGES)
        self.assertTrue(edits.apply(INFO,d,dict(min=0,max=2,clampMin=True,clampMax=True),lambda i:p,RANGES))
        self.assertEqual((p.min,p.max,p.clampMin,p.clampMax,p.val),(0,2,True,True,.375))
        d=edits.begin(INFO,lambda i:p,RANGES)
        self.assertTrue(edits.apply(INFO,d,dict(clampMax=False),lambda i:p,RANGES))

    def test_other_device_range_blocks_clamp_narrowing_before_any_setter(self):
        p=native();ranges=RANGES+((('L','T','other'),'inactive',-1.,2.),)
        d=edits.begin(INFO,lambda i:p,ranges)
        with self.assertRaisesRegex(ValueError,'Saved Mapping -1–2'):
            edits.apply(INFO,d,dict(min=0,clampMin=True),lambda i:p,ranges)
        self.assertEqual((p.min,p.clampMin,p.val),(-2,False,.375))

    def test_live_value_changed_since_begin_is_checked_at_apply(self):
        p=native();d=edits.begin(INFO,lambda i:p);p.val=.9
        with self.assertRaisesRegex(ValueError,'Current Value'):
            edits.apply(INFO,d,dict(max=.8),lambda i:p)
        self.assertEqual(p.max,3)

    def test_library_change_and_raw_clamped_value_rejected(self):
        p=native();d=edits.begin(INFO,lambda i:p,RANGES)
        with self.assertRaisesRegex(ValueError,'Saved mapping ranges changed'):
            edits.apply(INFO,d,dict(max=2),lambda i:p,RANGES+((KEY,'page',0,1),))
        p.val=4;p.eval=lambda: 3
        with self.assertRaisesRegex(ValueError,'already clamped'):
            edits.apply(INFO,d,dict(normMax=2),lambda i:p,RANGES)

    def test_invalid_bounds_and_integer_bounds_write_nothing(self):
        p=native('Int');d=edits.begin(INFO,lambda i:p)
        for patch in (dict(normMin=2,normMax=1),dict(min=4,max=3),dict(normMax=1.5),
                      dict(max=float('inf')),dict(clampMin='ON')):
            with self.assertRaises(ValueError):edits.apply(INFO,d,patch,lambda i:p)
        self.assertEqual((p.normMin,p.normMax,p.min,p.max,p.val),(0,1,-2,3,2))

    def test_late_bound_setter_failure_restores_earlier_bound(self):
        p=native()
        class Failing:
            def __setattr__(self,key,value):
                if key=='normMax' and value==2:raise RuntimeError('rejected')
                super().__setattr__(key,value)
        wrapper=Failing();wrapper.__dict__.update(vars(p));p=wrapper
        d=edits.begin(INFO,lambda i:p)
        with self.assertRaisesRegex(RuntimeError,'restored'):
            edits.apply(INFO,d,dict(normMin=-1,normMax=2),lambda i:p)
        self.assertEqual((p.normMin,p.normMax,p.val),(0,1,.375))


class LibraryRangeTests(TestCase):
    def controller(self):
        def target(id,low,high):
            return dict(id=id,parameter='Threshold',comp='../effect',minimum=low,maximum=high)
        plugins=[dict(id='device',targets=[target('target',-2,3)]),
                 dict(id='other',targets=[target('inactive',-1,2)])]
        manager=SimpleNamespace(legacy=False,data=dict(records=[dict(id='layout',tracks=[dict(id='track',plugins=plugins)])]))
        c=SimpleNamespace(path='/controller',ext=SimpleNamespace(RotoPythonExt=SimpleNamespace(_layout_manager=lambda:manager)),
            fetch=lambda key,default: [target('page',0,1)] if key=='page_targets' else [],
            GetControlCatalog=lambda:[dict(target('target',0,1),comp='/effect')])
        return c,manager

    def test_active_overrides_saved_range_and_inactive_page_ranges_included(self):
        c,manager=self.controller()
        adapter=SimpleNamespace(controller=c,ActiveContext=lambda:KEY)
        rows=TDControllerAdapter._definition_ranges(adapter,INFO)
        self.assertEqual(rows,((KEY,'page',0.,1.),(KEY,'target',0.,1.),(('layout','track','other'),'inactive',-1.,2.)))

    def test_scan_bound_is_enforced_even_for_unrelated_callback_entries(self):
        c,manager=self.controller();manager.data['records'][0]['tracks'][0]['plugins'][0]['targets']=[{}]*4097
        adapter=SimpleNamespace(controller=c,ActiveContext=lambda:KEY)
        with self.assertRaisesRegex(ValueError,'scan limit'):
            TDControllerAdapter._definition_ranges(adapter,INFO)

from test_definition_edit import WriteAdapter
from live_model import ControllerCatalog
from ui import InspectorView,DEFINITION_FIELDS

class DraftPars(dict):
    def __getitem__(self,key):
        return SimpleNamespace(eval=lambda:dict.__getitem__(self,key))
    def __getattr__(self,key):
        if key not in self:raise AttributeError(key)
        return self[key]

class BoundsViewTokenTests(TestCase):
    def test_apply_renews_view_token_before_reading_changed_native_definition(self):
        class Adapter(WriteAdapter):
            def ApplyDefinition(self,*args):
                result=super().ApplyDefinition(*args)
                self.records[KEY][0]['parameter_definition']=(self.par.min,self.par.max)
                return result
        a=Adapter();a.par.val=.4;a.par.eval=lambda:a.par.val
        m=ControllerCatalog(a);token=m.GetToken(KEY,1)
        draft=m.DefinitionDraft(KEY,1,token)
        values=dict(draft['original']);values['max']=2
        pars=DraftPars({name:value if key.startswith('clamp') else str(value) for key,name in DEFINITION_FIELDS for value in (values[key],)})
        view=InspectorView.__new__(InspectorView)
        view._model=m;view._context=KEY;view.selected=1;view._token=token;view._details_open=True
        view._definition_draft=draft;view._definition_scope=(KEY,1,token)
        view._draft=SimpleNamespace(par=pars);view.Key=lambda:KEY
        view.CloseContextMenu=lambda:None
        view._update_details=lambda:None
        captures=[]
        view._capture_definition=lambda:captures.append(m.ParameterDefinition(KEY,1,view._token))
        view._set_error=lambda message:None
        self.assertIsNot(view.Action('definition_apply'),False)
        self.assertNotEqual(view._token,token)
        self.assertEqual(view._token,m.GetToken(KEY,1))
        self.assertEqual(captures[0]['native']['clamp_limits'],('-2','2'))
        self.assertIsNone(view._definition_draft)
        self.assertEqual(a.par.val,.4)
