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
