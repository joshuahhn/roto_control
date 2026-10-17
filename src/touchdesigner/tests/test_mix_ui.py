"""The MIX editor stages configuration; only Apply changes active routing."""
import tests  # Shared paths for direct unittest discovery.
import copy
import posixpath
from types import SimpleNamespace
import unittest
import test_mix
import setup
import mix_descriptor
import mix_runtime
from export_component import reset_mapping_storage, reset_registration


class Par:
    def __init__(self, owner, name, kind):
        self.owner, self.name, self.kind = owner, name, kind
        self.val = ''
        self.menuNames = []; self.menuLabels = []

    def eval(self):
        return self.owner.op(self.val) if self.kind == 'OP' and isinstance(self.val, str) else self.val

    def destroy(self):
        delattr(self.owner.par, self.name)


class Page:
    def __init__(self, owner, name):
        self.owner, self.name = owner, name

    def __getattr__(self, name):
        def append(parameter_name, **kwargs):
            parameter = Par(self.owner, parameter_name, name.removeprefix('append'))
            setattr(self.owner.par, parameter_name, parameter)
            return [parameter]
        return append


class Parameters(SimpleNamespace):
    def __setattr__(self, name, value):
        current = getattr(self, name, None)
        if isinstance(current, Par):
            current.val = value
        else:
            super().__setattr__(name, value)


class MixUiTests(unittest.TestCase):
    def fixture(self, layers=False):
        fixtures = test_mix.MixTests()
        if layers:
            e, mix, source = fixtures.operation_fixture()
            source.par.operand.menuNames = source.par.lay0operation.menuNames + ['opperlayer']
            source.par.operand.menuLabels = source.par.lay0operation.menuLabels + ['Per Layer']
            source.name = 'layer_mix'; source.isCOMP = False
        else:
            e, mix, _, _, source, *_ = fixtures.fixture()
            source.name = 'analysis'; source.OPType = 'baseCOMP'
        scope = mix.scope
        source.parent = lambda: scope
        c = e.ownerComp
        c.parent = lambda: SimpleNamespace(path='/')
        c.ext = SimpleNamespace(RotoPythonExt=e)
        c.customPages = []
        def append(name):
            page = Page(c, name); c.customPages.append(page); return page
        c.appendCustomPage = append
        old_op = c.op
        callbacks = SimpleNamespace(par=Parameters(pars=Par(c, 'pars', 'Str')))
        callbacks.par.pars.val = 'Connect'
        registration = SimpleNamespace(text='user hook')
        c.op = lambda name: (None if name in ('', 'missing') else
                             SimpleNamespace(module=setup) if name == 'setup' else
                             SimpleNamespace(module=mix_descriptor) if name == 'mix_descriptor' else
                             SimpleNamespace(module=mix_runtime) if name == 'mix_runtime' else
                             callbacks if name == 'parameter_callbacks' else
                             registration if name == 'registration' else
                             source if name == posixpath.relpath(source.path, c.parent().path) else old_op(name))
        c.ConfigureMixAnalysis = e.ConfigureMixAnalysis
        c.ConfigureMixLayers = e.ConfigureMixLayers
        if layers:
            e.ConfigureMixLayers(scope, source.name, custom_operations=['choice_45'])
        setup.install_mix_ui(c)
        return e, mix, c, source

    def test_install_loads_existing_profile_without_writes_and_keeps_a_saved_draft(self):
        e, mix, c, source = self.fixture()
        before = e.GetMixProfile()
        self.assertIs(c.par.Mixsource.eval(), source)
        self.assertEqual(c.par.Mixsource.val, 'demo/analysis')
        self.assertIn('analysis: /demo/analysis', c.par.Mixsummary.eval())
        self.assertTrue(all(getattr(c.par, name).eval() == setup.MIX_NO_OPERATION
                            for name in setup.MIX_CUSTOM_PARAMETERS))
        c.par.Mixsource.val = 'missing'
        setup.install_mix_ui(c)
        self.assertEqual(c.par.Mixsource.val, 'missing')
        self.assertEqual(e.GetMixProfile(), before)
        self.assertEqual(mix.writes, 0)

    def test_draft_changes_and_invalid_apply_preserve_active_profile_and_values(self):
        e, mix, c, source = self.fixture()
        before = e.GetMixProfile()
        values = {name: p.eval() for name, p in source.par.items()}
        c.par.Mixsource.val = 'missing'
        e.onParValueChange(c.par.Mixsource, source)
        self.assertEqual(e.GetMixProfile(), before)
        e.onParPulse(c.par.Applymix)
        self.assertIn('Choose an existing MIX source', c.par.Mixsummary.eval())
        self.assertEqual(e.GetMixProfile(), before)
        self.assertEqual({name: p.eval() for name, p in source.par.items()}, values)
        self.assertEqual(mix.writes, 0)

    def test_apply_routes_through_existing_api_without_connecting_or_value_recall(self):
        e, mix, c, source = self.fixture()
        registry = copy.deepcopy(e._layouts.data)
        c.par.Mixsource.val = source
        e.onParPulse(c.par.Applymix)
        self.assertEqual(e.GetMixProfile()['descriptor']['style'], 'analysis')
        self.assertEqual(e._layouts.data, registry)
        self.assertIn('analysis: /demo/analysis', c.par.Mixsummary.eval())
        self.assertEqual(source.par.Lowgain.eval(), 2)
        self.assertEqual(mix.writes, 0)
        self.assertIsNone(e._process)

    def test_analysis_band_draft_applies_ordered_high_without_value_recall(self):
        e, mix, c, source = self.fixture()
        before = e.GetMixProfile()
        values = {name:p.eval() for name,p in source.par.items()}
        c.par.Mixanalysisbands.val = 'high, LOW'
        setup.install_mix_ui(c)
        self.assertEqual(c.par.Mixanalysisbands.eval(), 'high, LOW')
        self.assertEqual(e.GetMixProfile(), before)
        e.onParPulse(c.par.Applymix)
        self.assertEqual([item['id'] for item in e.GetMixProfile()['descriptor']['items']], ['high', 'low'])
        self.assertIn('High, Low', c.par.Mixsummary.eval())
        self.assertEqual({name:p.eval() for name,p in source.par.items()}, values)
        self.assertEqual(mix.writes, 0)
        self.assertIsNone(e._process)

    def test_invalid_or_missing_analysis_bands_preserve_the_applied_profile(self):
        e, mix, c, source = self.fixture()
        before = e.GetMixProfile()
        for bands in ('', 'Low Low', 'Unknown', 'High Unknown'):
            with self.subTest(bands=bands):
                c.par.Mixanalysisbands.val = bands
                e.onParPulse(c.par.Applymix)
                self.assertEqual(e.GetMixProfile(), before)
                self.assertIn('Choose unique analysis bands', c.par.Mixsummary.eval())
        c.par.Mixanalysisbands.val = 'Low Mid High'
        source.par['Highgain'] = None
        e.onParPulse(c.par.Applymix)
        self.assertEqual(e.GetMixProfile(), before)
        self.assertIn('Low/Mid/High controls', c.par.Mixsummary.eval())
        self.assertEqual(mix.writes, 0)

    def test_new_band_field_hydrates_a_known_saved_profile_without_applying(self):
        e, mix, c, source = self.fixture()
        e.ConfigureMixAnalysis(mix.scope, source.name, ('High', 'Mid'))
        before = e.GetMixProfile()
        c.par.Mixanalysisbands.destroy()
        setup.install_mix_ui(c)
        self.assertEqual(c.par.Mixanalysisbands.eval(), 'High Mid')
        self.assertEqual(e.GetMixProfile(), before)
        self.assertEqual(mix.writes, 0)

    def test_kick_editor_uses_only_existing_controls_without_enabling_detection(self):
        e, mix, c, source = self.fixture()
        values = {name:p.eval() for name,p in source.par.items()}
        c.par.Mixanalysisbands.val = 'Low, Mid High kick'
        e.onParPulse(c.par.Applymix)
        profile = e.GetMixProfile()['descriptor']
        self.assertEqual([item['id'] for item in profile['items']], ['low','mid','high','kick'])
        self.assertEqual(set(profile['items'][3]['controls']), {'threshold','active'})
        self.assertEqual(len(mix.targets), 17)
        self.assertEqual(len(mix.triggers), 1)
        self.assertEqual({name:p.eval() for name,p in source.par.items()}, values)
        self.assertEqual(mix.writes, 0)
        self.assertIsNone(e._process)

    def test_kick_feedback_preflight_preserves_profile_when_source_is_missing(self):
        e, mix, c, source = self.fixture()
        before = e.GetMixProfile()
        c.par.Mixanalysisbands.val = 'Kick'
        scope = source.parent();old_op=scope.op
        scope.op = lambda name: None if name == 'analysis/math2' else old_op(name)
        e.onParPulse(c.par.Applymix)
        self.assertEqual(e.GetMixProfile(), before)
        self.assertIn('Analysis feedback unavailable', c.par.Mixsummary.eval())
        self.assertFalse(source.par.Kickactive.eval())

    def test_layer_editor_loads_custom_names_and_retains_full_source_menu(self):
        e, mix, c, source = self.fixture(layers=True)
        self.assertEqual(c.par.Mixcustom1.eval(), 'over')
        self.assertEqual(c.par.Mixcustom5.eval(), 'choice_45')
        self.assertEqual(len(c.par.Mixcustom1.menuNames), 47)  # None plus all 46 blend modes.
        self.assertNotIn('opperlayer', c.par.Mixcustom1.menuNames)
        setup.set_mix_operation_draft(c, ['add', 'choice_45'])
        e.onParPulse(c.par.Applymix)
        self.assertEqual(e.GetMixProfile()['descriptor']['items'][0]['controls']['operation']['choices'],
                         ['add', 'choice_45'])
        self.assertEqual(source.par.lay0operation.eval(), 'add')
        self.assertEqual(mix.writes, 0)

    def test_named_presets_with_two_or_six_choices_load_only_a_draft(self):
        e, mix, c, source = self.fixture(layers=True)
        before = e.GetMixProfile()
        setup.set_mix_operation_draft(c, ['add', 'over'])
        c.par.Mixpresetname.val = 'Two modes'
        e.onParPulse(c.par.Newmixpreset)
        two = c.par.Mixoperationpreset.eval()
        self.assertEqual(e.GetMixOperationPresets()[0]['operations'], ['add', 'over'])
        setup.set_mix_operation_draft(c, ['over', 'multiply', 'screen', 'overlay', 'hardlight', 'difference'])
        c.par.Mixpresetname.val = 'Six modes'
        e.onParPulse(c.par.Newmixpreset)
        self.assertEqual(len(e.GetMixOperationPresets()), 2)
        c.par.Mixoperationpreset.val = two
        e.onParValueChange(c.par.Mixoperationpreset, None)
        self.assertEqual(setup.mix_draft_operations(c), ['add', 'over'])
        self.assertTrue(all(getattr(c.par, n).eval() == setup.MIX_NO_OPERATION for n in setup.MIX_CUSTOM_PARAMETERS[2:]))
        self.assertEqual(c.par.Mixpresetname.eval(), 'Two modes')
        self.assertEqual(e.GetMixProfile(), before)
        self.assertEqual(mix.writes, 0)

    def test_preset_save_rename_delete_do_not_change_applied_choices(self):
        e, mix, c, source = self.fixture(layers=True)
        before = e.GetMixProfile()
        setup.set_mix_operation_draft(c, ['add', 'over'])
        c.par.Mixpresetname.val = 'Original'; e.onParPulse(c.par.Newmixpreset)
        identity = c.par.Mixoperationpreset.eval()
        setup.set_mix_operation_draft(c, ['screen', 'multiply'])
        c.par.Mixpresetname.val = 'Renamed'; e.onParPulse(c.par.Savemixpreset)
        self.assertEqual(e.GetMixOperationPresets(), [dict(id=identity, name='Renamed', operations=['screen', 'multiply'])])
        e.onParPulse(c.par.Deletemixpreset)
        self.assertEqual(e.GetMixOperationPresets(), [])
        self.assertEqual(c.par.Mixoperationpreset.eval(), setup.MIX_DRAFT_PRESET)
        self.assertEqual(setup.mix_draft_operations(c), ['screen', 'multiply'])
        self.assertEqual(e.GetMixProfile(), before)

    def test_invalid_presets_preserve_saved_data_and_active_profile(self):
        e, mix, c, source = self.fixture(layers=True)
        identity = e.SaveMixOperationPreset('Existing', ['over', 'add'])
        before = e.GetMixOperationPresets(); profile = e.GetMixProfile()
        for name, choices, preset_id in [('existing', ['add','screen'],None), ('', ['over','add'],None),
                ('One',['over'],None), ('Too many',['over']*7,None), ('Missing',['over','add'],'missing')]:
            with self.subTest(name=name), self.assertRaises(ValueError):
                e.SaveMixOperationPreset(name, choices, preset_id)
            self.assertEqual(e.GetMixOperationPresets(), before)
            self.assertEqual(e.GetMixProfile(), profile)
        detached = e.GetMixOperationPresets(); detached[0]['operations'].clear()
        self.assertEqual(e.GetMixOperationPresets(), before)

    def test_legacy_library_draft_migrates_without_changing_active_profile(self):
        e, mix, c, source = self.fixture(layers=True)
        before = e.GetMixProfile()
        c.par.Mixoperationlibrary = Par(c, 'Mixoperationlibrary', 'Menu')
        c.par.Mixoperationlibrary.val = 'common'
        setup.set_mix_operation_draft(c, ['choice_45'])
        setup.install_mix_ui(c)
        self.assertIsNone(getattr(c.par, 'Mixoperationlibrary', None))
        self.assertEqual(setup.mix_draft_operations(c), ['over','add','multiply','screen','choice_45'])
        self.assertEqual(e.GetMixProfile(), before)

    def test_oversized_legacy_draft_is_not_truncated_by_upgrade(self):
        e, mix, c, source = self.fixture(layers=True)
        before = e.GetMixProfile()
        c.par.Mixoperationlibrary = Par(c, 'Mixoperationlibrary', 'Menu')
        c.par.Mixoperationlibrary.val = 'math'
        setup.set_mix_operation_draft(c, ['choice_45'])
        with self.assertRaisesRegex(ValueError, 'more than six'):
            setup.install_mix_ui(c)
        self.assertEqual(c.par.Mixoperationlibrary.eval(), 'math')
        self.assertEqual(c.par.Mixcustom1.eval(), 'choice_45')
        self.assertEqual(e.GetMixProfile(), before)

    def test_unavailable_custom_choice_is_visible_and_cannot_silently_replace_profile(self):
        e, mix, c, source = self.fixture(layers=True)
        before = e.GetMixProfile()
        c.par.Mixcustom1.val = 'missing'
        setup.refresh_mix_ui(c)
        self.assertEqual(c.par.Mixcustom1.eval(), 'missing')
        self.assertIn('Unavailable: missing', c.par.Mixcustom1.menuLabels)
        e.onParPulse(c.par.Applymix)
        self.assertEqual(e.GetMixProfile(), before)
        self.assertIn('not in the current TD menu', c.par.Mixsummary.eval())
        self.assertEqual(mix.writes, 0)

    def test_wrong_analysis_source_is_rejected_before_replacing_profile(self):
        e, mix, c, source = self.fixture(layers=True)
        before = e.GetMixProfile()
        c.par.Mixstyle.val = 'analysis'
        e.onParPulse(c.par.Applymix)
        self.assertEqual(e.GetMixProfile(), before)
        self.assertIn('audioAnalysis COMP', c.par.Mixsummary.eval())

    def test_apply_and_clear_require_release_exit_learn_and_no_dispatch(self):
        for action in ('Applymix', 'Clearmix'):
            for guard in ('mix_touch', 'plugin_touch', 'learn', 'dispatch'):
                with self.subTest(action=action, guard=guard):
                    e, mix, c, source = self.fixture()
                    before = e.GetMixProfile()
                    if guard == 'mix_touch': mix.touched.add(0)
                    elif guard == 'plugin_touch': e._host.touched = True
                    elif guard == 'learn': e._host.learning = True
                    else: e._dispatching = True
                    e.onParPulse(getattr(c.par, action))
                    self.assertEqual(e.GetMixProfile(), before)
                    self.assertEqual(mix.writes, 0)

    def test_clear_removes_only_mix_and_does_not_apply_or_erase_draft(self):
        e, mix, c, source = self.fixture()
        registry = copy.deepcopy(e._layouts.data)
        e.onParPulse(c.par.Clearmix)
        self.assertIsNone(e.GetMixProfile())
        self.assertIsNone(mix.profile)
        self.assertEqual(c.par.Mixsummary.eval(), 'Unassigned')
        self.assertIs(c.par.Mixsource.eval(), source)
        self.assertEqual(e._layouts.data, registry)
        self.assertEqual(source.par.Lowgain.eval(), 2)

    def test_generic_reset_removes_draft_paths_and_custom_choices_without_source_writes(self):
        e, mix, c, source = self.fixture(layers=True)
        before = {name: p.eval() for name, p in source.par.items()}
        e.SaveMixOperationPreset('User blend set', ['over', 'add'])
        reset_mapping_storage(c); reset_registration(c)
        self.assertIsNone(c.par.Mixsource.eval())
        self.assertEqual(c.par.Mixstyle.eval(), 'analysis')
        self.assertEqual(c.par.Mixanalysisbands.eval(), setup.MIX_ANALYSIS_DEFAULT)
        self.assertEqual(c.par.Mixsummary.eval(), 'Unassigned')
        self.assertEqual(c.par.Mixcustom1.eval(), setup.MIX_NO_OPERATION)
        self.assertEqual(c.par.Mixcustom1.menuNames, [setup.MIX_NO_OPERATION])
        self.assertIsNone(e.GetMixProfile())
        self.assertEqual(e.GetMixOperationPresets(), [])
        self.assertEqual({name: p.eval() for name, p in source.par.items()}, before)


if __name__ == '__main__': unittest.main()
