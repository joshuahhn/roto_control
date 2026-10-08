"""Native metadata and dialog boundary tests, without TD, dialogs or MIDI."""
import json
from types import SimpleNamespace
from unittest import TestCase
import parameter_definition as definitions
from live_model import ControllerCatalog,StaleDraft
from test_live_model import Adapter,KEY,state

def parameter(style='Float'):
    owner=SimpleNamespace(id=12,path='/effect',opened=[])
    owner.openParameters=lambda:owner.opened.append('values')
    return SimpleNamespace(owner=owner,valid=True,name='Threshold',label='Low Threshold',page=SimpleNamespace(name='Mask'),
        style=style,default=.25,defaultMode=SimpleNamespace(name='CONSTANT'),defaultExpr='',defaultBindExpr='',
        mode=SimpleNamespace(name='CONSTANT'),readOnly=False,enable=True,expr='',bindMaster=None,bindRange=False,
        exportOP=None,exportSource=None,normMin=0,normMax=1,min=-2,max=3,clampMin=False,clampMax=True,
        menuNames=[],menuLabels=[],menuSource='',isNumber=style in ('Float','Int','Toggle'),isMenu=style=='Menu',
        isToggle=style=='Toggle',isPulse=style=='Pulse',isCustom=True)

INFO=dict(id='target',comp='/effect',parameter='Threshold')

class DefinitionAdapter(Adapter):
    def __init__(self):super().__init__();self.par=parameter();self.opened=[];self.reads=0
    def ParameterDefinition(self,info,learning,touched):
        self.reads+=1
        return definitions.read(info,lambda info:self.par,learning,touched)
    def OpenNativeEditor(self,info,kind,learning,touched):
        return definitions.open_editor(info,kind,lambda info:self.par,self.opened.append,learning,touched)

class ParameterDefinitionTests(TestCase):
    def test_snapshot_keeps_slider_clamp_default_and_style_distinct_without_value_read(self):
        p=parameter();result=definitions.snapshot(p)
        self.assertEqual(result['native']['slider_range'],('0','1'))
        self.assertEqual(result['native']['clamp_limits'],('-2','3'))
        self.assertEqual(result['native']['clamps'],(False,True))
        self.assertEqual(result['native']['default'],'0.25')
        self.assertEqual(result['native']['style'],'Float')
        self.assertEqual(p.owner.opened,[])
        self.assertIn('Slider range',dict((a,b) for a,b,c in result['rows']))
        json.dumps(result)  # No Par/OP/runtime handles in detached snapshot.
        p.normMax=8;self.assertEqual(result['native']['slider_range'],('0','1'))

    def test_menu_preview_bounded_with_total_labels_source_and_no_false_numeric_range(self):
        p=parameter('Menu');p.menuNames=['n'+str(i) for i in range(30)];p.menuLabels=['Choice '+str(i) for i in range(30)]
        p.menuSource="op('menu').par.Options"
        result=definitions.snapshot(p)
        self.assertEqual(len(result['native']['menu_preview']),8)
        self.assertEqual(result['native']['menu_count'],30)
        self.assertEqual(result['native']['slider_range'],())
        self.assertIn('22 more',str(result['rows']))
        self.assertIn('Choice 7 [n7]',str(result['rows']))
        self.assertIn("op('menu')",str(result['rows']))

    def test_expression_export_and_default_modes_are_metadata_not_evaluated_values(self):
        p=parameter();p.mode.name='EXPRESSION';p.expr="op('source')['amount']"
        p.defaultMode.name='BIND';p.defaultBindExpr="op('defaults').par.Amount"
        result=definitions.snapshot(p)
        self.assertIn(p.expr,str(result['rows']));self.assertIn(p.defaultBindExpr,str(result['rows']))
        p.mode.name='EXPORT';p.exportOP=SimpleNamespace(path='/source')
        p.exportSource=SimpleNamespace(owner=p.exportOP,name='amount')
        self.assertEqual(definitions.snapshot(p)['native']['export_source'],'/source.amount')
        p.defaultMode.name='EXPRESSION';p.defaultExpr='me.time.frame'
        self.assertIn('me.time.frame',str(definitions.snapshot(p)['rows']))

    def test_bind_assigned_owner_and_resolved_master_are_separate_and_cycles_bounded(self):
        p=parameter();alias=parameter();master=parameter()
        alias.owner.path='/alias';master.owner.path='/master';alias.mode.name='BIND';alias.bindMaster=master
        p.mode.name='BIND';p.bindMaster=alias;p.bindRange=True
        result=definitions.snapshot(p)
        self.assertEqual(result['target']['comp'],'/effect')
        self.assertEqual(result['native']['bind_master'],'/alias.Threshold')
        self.assertEqual(result['native']['resolved_master'],'/master.Threshold')
        self.assertIn('inherited',str(result['rows']))
        alias.bindMaster=p
        json.dumps(definitions.snapshot(p))  # Cyclic metadata never loops forever.

    def test_callback_unassigned_deleted_and_builtin_reasons_are_specific(self):
        for info,reason in [({},'Unassigned'),(dict(id='callback'),'Python callback'),(INFO,'unavailable')]:
            result=definitions.read(info,lambda info:None)
            self.assertIn(reason,result['reason'])
            self.assertTrue(all(not c['enabled'] for c in result['actions'].values()))
        p=parameter();p.isCustom=False
        result=definitions.read(INFO,lambda info:p)
        self.assertTrue(result['actions']['values']['enabled']);self.assertFalse(result['actions']['definition']['enabled'])
        p.valid=False;self.assertIn('unavailable',definitions.read(INFO,lambda info:p)['reason'])

    def test_exact_dialog_dispatch_with_learn_touch_and_resolution_race_guards(self):
        p=parameter();calls=[]
        self.assertEqual(definitions.open_editor(INFO,'values',lambda info:p,calls.append),'/effect')
        definitions.open_editor(INFO,'definition',lambda info:p,calls.append)
        self.assertEqual(p.owner.opened,['values']);self.assertEqual(calls,[p.owner])
        for kwargs,reason in [(dict(learning=True),'LEARN'),(dict(touched=True),'Release')]:
            with self.assertRaisesRegex(ValueError,reason):definitions.open_editor(INFO,'definition',lambda info:p,calls.append,**kwargs)
        replacement=parameter();replacement.owner.id=99;targets=iter([p,replacement])
        with self.assertRaisesRegex(ValueError,'changed'):definitions.open_editor(INFO,'values',lambda info:next(targets),calls.append)
        with self.assertRaisesRegex(ValueError,'Unknown'):definitions.open_editor(INFO,'other',lambda info:p,calls.append)
        self.assertEqual(p.owner.opened,['values']);self.assertEqual(calls,[p.owner])

    def test_command_fences_session_mapping_and_owner_replacement_but_allows_live_value(self):
        a=DefinitionAdapter();m=ControllerCatalog(a);token=m.GetToken(KEY,1)
        self.assertEqual(m.ParameterDefinition(KEY,1,token)['native']['style'],'Float')
        a.records[KEY][0]['value']=.8;m.Sync()
        m.OpenNativeEditor(KEY,1,token,'values');self.assertEqual(a.par.owner.opened,['values'])
        for change in ('session','mapping','owner'):
            token=m.GetToken(KEY,1)
            if change=='session':a.session+=1
            elif change=='mapping':a.records[KEY][0]['id']='replacement'
            else:a.records[KEY][0]['parameter_definition']=((99,'/effect','Threshold'),)
            with self.assertRaises(StaleDraft):m.OpenNativeEditor(KEY,1,token,'definition')
        self.assertEqual(a.writes,[]);self.assertEqual(a.pings,[]);self.assertEqual(a.clears,[]);self.assertEqual(a.opened,[])

    def test_readonly_browse_disconnected_readout_and_state_guards_do_not_mutate(self):
        a=DefinitionAdapter();other=('layout','track','other');a.records[other]=[state()]
        a.records[other][0]['connected']=False;m=ControllerCatalog(a)
        result=m.ParameterDefinition(other,1,m.GetToken(other,1));self.assertTrue(result['actions']['definition']['enabled'])
        a.learning=True;m.Sync();result=m.ParameterDefinition(KEY,1,m.GetToken(KEY,1))
        self.assertEqual(result['native']['default'],'0.25');self.assertFalse(result['actions']['values']['enabled'])
        with self.assertRaisesRegex(ValueError,'LEARN'):m.OpenNativeEditor(KEY,1,m.GetToken(KEY,1),'definition')
        a.learning=False;a.records[KEY][0]['touched']=True;m.Sync()
        with self.assertRaisesRegex(ValueError,'Release'):m.OpenNativeEditor(KEY,1,m.GetToken(KEY,1),'values')
        self.assertEqual(a.writes,[]);self.assertEqual(a.opened,[])
