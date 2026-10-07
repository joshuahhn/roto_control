"""Mapping-only commits, schema guards and independent drafts."""
from unittest import TestCase
from live_model import ControllerCatalog,StaleDraft
from editor_state import MappingDraft
from test_live_model import Adapter,KEY,state

class ConfigAdapter(Adapter):
    def __init__(self):super().__init__();self.configures=[]
    def Configure(self,key,info,values):
        current=self.records[key][0]
        if not values['minimum']<=current['value']<=values['maximum']:raise ValueError('Range must include current value')
        self.configures.append((key,info['id'],dict(values)))
        semantics=any(values[n]!=current.get(n) for n in ('minimum','maximum','mode'))
        current.update(values)
        if semantics:current.update(mapped=False,requires_relearn=True)

class MappingTests(TestCase):
    def setUp(self):
        self.adapter=ConfigAdapter();self.model=ControllerCatalog(self.adapter);self.model.GetCatalog(KEY)
    def commit(self,**patch):return self.model.Configure(KEY,1,patch,self.model.GetToken(KEY,1))
    def test_combined_configuration_uses_one_api_and_never_writes_value(self):
        self.assertTrue(self.commit(minimum=-1,maximum=2,mode='value'))
        self.assertEqual(len(self.adapter.configures),1);self.assertEqual(self.adapter.writes,[])
        self.assertEqual(self.adapter.records[KEY][0]['value'],.4)
        self.assertEqual(self.model.Health(KEY,1)['code'],'relearn')
    def test_invalid_patch_preserves_mapping_and_rejects_fractional_integer_range(self):
        for patch in [dict(minimum=2),dict(maximum=float('nan')),dict(mode='pulse'),dict(button_type='push'),dict(style='Int')]:
            with self.assertRaises(ValueError):self.commit(**patch)
        self.adapter.records[KEY][0]['parameter_style']='Int';self.model.Sync()
        with self.assertRaises(ValueError):self.commit(minimum=-.5)
        self.assertEqual(self.adapter.configures,[]);self.assertEqual(self.adapter.records[KEY][0]['minimum'],0)
    def test_native_button_menu_mode_and_range_are_fixed(self):
        for style,mode in [('Toggle','toggle'),('Pulse','pulse'),('Menu','cycle')]:
            self.adapter.records[KEY][0].update(kind='button',slot=2,parameter_style=style,mode=mode,button_type='toggle')
            self.model.Sync();schema=self.model.MappingSchema(KEY,9)
            self.assertEqual(schema['modes'],(mode,));self.assertFalse(schema['range_editable'])
            with self.assertRaises(ValueError):self.model.Configure(KEY,9,dict(mode='value'),self.model.GetToken(KEY,9))
            with self.assertRaises(ValueError):self.model.Configure(KEY,9,dict(maximum=3),self.model.GetToken(KEY,9))
    def test_callback_mode_choices_and_input_only_change_keep_ack(self):
        self.adapter.records[KEY][0].update(kind='button',slot=2,parameter_style='',binding_type='callback',mode='toggle',button_type='toggle')
        self.model.Sync();self.assertEqual(self.model.MappingSchema(KEY,9)['modes'],('toggle','pulse'))
        self.model.Configure(KEY,9,dict(button_type='push'),self.model.GetToken(KEY,9))
        self.assertTrue(self.model.Info(KEY,9)['mapped']);self.assertFalse(self.model.Info(KEY,9).get('requires_relearn'))
        self.assertEqual(self.adapter.writes,[])
    def test_configure_rechecks_touch_learn_browse_and_definition_at_execution(self):
        for fields in [dict(touched=True),dict(definition_error='Readonly target')]:
            token=self.model.GetToken(KEY,1);self.adapter.records[KEY][0].update(fields)
            with self.assertRaises(ValueError):self.model.Configure(KEY,1,dict(maximum=2),token)
            self.adapter.records[KEY][0].update(touched=False,definition_error='');self.model.Sync()
        self.adapter.learning=True
        with self.assertRaises(ValueError):self.commit(maximum=2)
        self.adapter.learning=False;other=('layout','track','other');self.adapter.records[other]=[state()]
        with self.assertRaises(ValueError):self.model.Configure(other,1,dict(maximum=2),self.model.GetToken(other,1))
        self.assertEqual(self.adapter.configures,[])
    def test_mapping_draft_keeps_runtime_values_but_expires_on_metadata(self):
        draft=MappingDraft();values=draft.Open(self.model,KEY,1)
        token=draft.token;self.adapter.records[KEY][0]['value']=.7;self.model.Sync()
        self.assertFalse(draft.IsStale(self.model,KEY,1));self.assertEqual(draft.token,token)
        values['maximum']=2;changed,fresh=draft.Apply(self.model,KEY,1,values)
        self.assertTrue(changed);self.assertEqual(fresh['maximum'],2)
        self.assertEqual(self.adapter.records[KEY][0]['value'],.7)
        self.assertIn('re-LEARN',draft.message)
        self.adapter.records[KEY][0]['id']='replacement';self.model.Sync()
        with self.assertRaises(StaleDraft):draft.Apply(self.model,KEY,1,fresh)
    def test_noop_and_current_value_exclusion_have_no_mutation(self):
        self.assertFalse(self.commit(maximum=1));self.assertEqual(self.adapter.configures,[])
        with self.assertRaises(ValueError):self.commit(maximum=.2)
        self.assertEqual(self.adapter.configures,[]);self.assertEqual(self.adapter.records[KEY][0]['maximum'],1)
    def test_cancel_only_discards_local_mapping_draft(self):
        draft=MappingDraft();draft.Open(self.model,KEY,1);draft.Close()
        self.assertFalse(draft.open);self.assertIsNone(draft.token);self.assertIsNone(draft.original)
        self.assertEqual(self.adapter.configures,[]);self.assertEqual(self.adapter.writes,[])
