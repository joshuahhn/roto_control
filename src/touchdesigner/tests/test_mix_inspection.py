import tests
import copy
import unittest
import test_mix
import mix_runtime


class MixInspectionTests(unittest.TestCase):
    def observe(self, e, mix):
        return mix_runtime.inspection(mix, e.ownerComp.fetch('mix_profile', None, search=False), connected=False, plugin=False)

    def test_all_analysis_controls_show_actual_values_without_business_changes(self):
        e, mix, _, _, source, *_ = test_mix.MixTests().fixture()
        source.par.Lowgain.val = 12
        before = test_mix.MixTests().activation_snapshot(e, mix, source)
        view = self.observe(e, mix)
        self.assertEqual(view['hardware'], 'unknown')
        self.assertEqual(view['status'], 'applied')
        self.assertEqual(len(view['items']), 2)
        controls = {c['key']: c for c in view['items'][0]['controls']}
        self.assertEqual(controls['gain']['value'], 12)
        self.assertEqual(controls['active']['caption'], 'On')
        self.assertEqual(test_mix.MixTests().activation_snapshot(e, mix, source), before)
        view['items'][0]['controls'].clear()
        self.assertTrue(self.observe(e, mix)['items'][0]['controls'])

    def test_layer_observation_failure_does_not_latch_or_reconfigure(self):
        e, mix, source = test_mix.MixTests().operation_fixture()
        e.ConfigureMixLayers(mix.scope, 'layer_mix', operation_choices=['over', 'add'])
        source.par.lay0operation.val = 'screen'
        source.par.lay0swapord.enable = False
        before = test_mix.MixTests().activation_snapshot(e, mix, source)
        view = self.observe(e, mix)
        controls = {c['key']: c for c in view['items'][0]['controls']}
        self.assertIn('outside', controls['operation']['reason'])
        self.assertEqual(controls['operation']['caption'], 'Choice 4')
        self.assertFalse(controls['swap']['available'])
        source.inputs.reverse()
        failed = self.observe(e, mix)
        self.assertFalse(failed['available'])
        self.assertFalse(mix.layer_invalid)
        source.inputs.reverse()
        self.assertTrue(self.observe(e, mix)['available'])
        self.assertEqual(test_mix.MixTests().activation_snapshot(e, mix, source), before)
        source.inputs.reverse(); mix.source_valid(); source.inputs.reverse()
        self.assertFalse(self.observe(e, mix)['available'])

    def test_uninitialized_saved_profile_retains_identity_and_rows(self):
        e, mix, *_ = test_mix.MixTests().fixture()
        saved = e.ownerComp.fetch('mix_profile', None, search=False)
        before = copy.deepcopy(saved)
        view = mix_runtime.inspection(None, saved, connected=False, plugin=False)
        self.assertEqual(view['profile'], 'analysis.main')
        self.assertEqual(view['status'], 'unavailable')
        self.assertEqual(len(view['items']), 2)
        self.assertTrue(all(not c['available'] for item in view['items'] for c in item['controls']))
        self.assertEqual(saved, before)
        self.assertEqual(mix_runtime.inspection(None, None, connected=False, plugin=False)['status'], 'empty')

    def test_saved_scope_change_does_not_reuse_previous_runtime_targets(self):
        e,mix,*_=test_mix.MixTests().fixture()
        saved=copy.deepcopy(e.ownerComp.fetch('mix_profile',None,search=False));saved['scope']='missing_scope'
        resolve=e.ownerComp.op;e.ownerComp.op=lambda name:None if name=='missing_scope' else resolve(name)
        view=mix_runtime.inspection(mix,saved,connected=False,plugin=False)
        self.assertEqual(view['scope'],'missing_scope');self.assertFalse(view['available'])
        self.assertTrue(all(control['value'] is None for item in view['items'] for control in item['controls']))

    def test_retargeted_td_proxy_does_not_make_a_replacement_source_available(self):
        e,mix,_,_,source,*_=test_mix.MixTests().fixture()
        source.id+=1
        self.assertFalse(self.observe(e,mix)['available'])

    def test_all_six_analysis_items_and_every_layer_control_are_inspected(self):
        from mix_descriptor import analysis_profile
        e,mix,*_=test_mix.MixTests().fixture()
        mix.configure(mix.scope,analysis_profile('analysis',bands=['Low','Mid','High','Kick','Snare','Rhythm']))
        view=self.observe(e,mix)
        self.assertEqual([item['label'] for item in view['items']],['Low','Mid','High','Kick','Snare','Rhythm'])
        self.assertEqual([len(item['controls']) for item in view['items']],[5,5,5,2,2,2])
        self.assertTrue(all(control['available'] for item in view['items'] for control in item['controls']))
        e,mix,source=test_mix.MixTests().operation_fixture();e.ConfigureMixLayers(mix.scope,'layer_mix')
        view=self.observe(e,mix)
        self.assertEqual([len(item['controls']) for item in view['items']],[6,6])
        self.assertTrue(all(control['available'] for item in view['items'] for control in item['controls']))

    def test_empty_configured_profile_and_drafts_do_not_change_applied_observation(self):
        e,mix,_,_,source,*_=test_mix.MixTests().fixture()
        profile=copy.deepcopy(mix.profile);profile['items']=[]
        mix.configure(mix.scope,profile)
        before=self.observe(e,mix)
        self.assertEqual(before['status'],'applied');self.assertEqual(before['items'],[])
        e.ownerComp.store('mix_draft',dict(source='different',style='layers'))
        self.assertEqual(self.observe(e,mix),before)
        self.assertEqual(mix.state()['inspection'],before)

    def test_runtime_restore_failure_keeps_saved_profile_and_observation_does_not_initialize(self):
        e,mix,*_=test_mix.MixTests().fixture()
        saved=copy.deepcopy(e.ownerComp.fetch('mix_profile',None,search=False))
        mix.profile=None;mix.error='Missing source'
        before=(dict(mix.targets),dict(mix.errors),mix.error,mix.epoch,mix.layer_invalid)
        view=self.observe(e,mix)
        self.assertEqual(view['reason'],'Missing source');self.assertEqual(view['profile'],saved['descriptor']['id'])
        self.assertEqual((dict(mix.targets),dict(mix.errors),mix.error,mix.epoch,mix.layer_invalid),before)
        self.assertEqual(e.ownerComp.fetch('mix_profile',None,search=False),saved)

    def test_disconnected_retained_mode_is_unknown_and_business_scope_guard_is_unchanged(self):
        e,mix,source=test_mix.MixTests().operation_fixture()
        e.ConfigureMixLayers(mix.scope,'layer_mix');mix.active=True
        saved=e.ownerComp.fetch('mix_profile',None,search=False)
        self.assertEqual(self.observe(e,mix)['hardware'],'unknown')
        self.assertEqual(mix_runtime.inspection(mix,saved,connected=True,plugin=False)['hardware'],'MIX')
        mix.active=False
        self.assertEqual(mix_runtime.inspection(mix,saved,connected=True,plugin=True)['hardware'],'PLUGIN')
        mix.scope.valid=False
        self.assertFalse(mix.source_valid());self.assertFalse(mix.layer_invalid)

    def test_missing_target_and_source_keep_applied_assignment_rows(self):
        e, mix, _, _, source, _, operators = test_mix.MixTests().fixture()
        source.par['Lowgain'] = None
        view = self.observe(e, mix)
        self.assertFalse(next(c for c in view['items'][0]['controls'] if c['key'] == 'gain')['available'])
        operators.pop('analysis')
        failed = self.observe(e, mix)
        self.assertEqual(failed['profile'], 'analysis.main')
        self.assertFalse(failed['available'])
        self.assertEqual(len(failed['items']), 2)


if __name__ == '__main__':
    unittest.main()
