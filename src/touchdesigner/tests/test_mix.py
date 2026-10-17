"""MIX business behavior through the real extension, independent of PLUGIN."""
import tests  # Shared paths for direct unittest discovery.
import copy
import json
import unittest
import time
from types import SimpleNamespace
from unittest.mock import patch, Mock
import test_comp_follow
from test_bound_parameter import BoundParameter
from midi_queue import discard, business_output
from mix_descriptor import analysis_profile, validate, projection
from mix_runtime import MixRuntime, Signal
from protocol import SysExCommand, digest, text13, raw_value


class Pars(dict):
    def __getattr__(self, name):
        return self[name]


class Channel:
    def __init__(self, values): self.vals = values
    def __getitem__(self, index): return self.vals[index]


class MixTests(unittest.TestCase):
    def layer_fixture(self):
        e,mix,manager,follower,analysis,channels,operators=self.fixture()
        images=[SimpleNamespace(valid=True,id=901+i,path='/demo/image_'+str(i)) for i in range(2)]
        source=SimpleNamespace(valid=True,OPType='layermixTOP',id=900,path='/demo/layer_mix',inputs=images,par=Pars(),seq=SimpleNamespace(lay=SimpleNamespace(numBlocks=2)))
        for flag in ('enableopac','enablebright','enablelevels'):
            p=BoundParameter('Toggle');p.name=flag;p.owner=source;p.val=True;source.par[flag]=p
        p=BoundParameter('Menu');p.name='operand';p.owner=source;p.val='add';source.par[p.name]=p
        for index in range(2):
            for suffix,value,high in (('opacity',.25+.5*index,1),('bright',1,2),('black',0,2),('gamma',1,3)):
                p=BoundParameter();p.name='lay'+str(index)+suffix;p.owner=source;p.enable=True
                p.normMin=p.min=0;p.normMax=p.max=high;p.val=value;source.par[p.name]=p
        operators['layer_mix']=source
        for image in images:operators[image.path.rsplit('/',1)[1]]=image
        mix.scope.relativePath=lambda n:n.path.removeprefix('/demo/')
        return e,mix,source,images,analysis

    def operation_fixture(self):
        e,mix,source,*_=self.layer_fixture();source.par.operand.val='opperlayer'
        for index in range(2):
            p=BoundParameter('Menu');p.name='lay'+str(index)+'operation';p.owner=source;p.enable=True
            p.menuNames=['add','over','multiply','screen','overlay','softlight','hardlight','difference','subtract','divide','average'] + ['choice_'+str(i) for i in range(11,46)]
            p.menuLabels=['Choice '+str(i+1) for i in range(46)]
            p.val=p.menuNames[0];source.par[p.name]=p
            p=BoundParameter('Toggle');p.name='lay'+str(index)+'swapord';p.owner=source;p.enable=True;p.val=False
            source.par[p.name]=p
        return e,mix,source

    def focus(self,e,mix,index=0):
        e._receive_midi(SysExCommand.SELECT_TRACK.message((0,index)),e._ingress_token())
        e._receive_midi(SysExCommand.SET_MIXER_SELECTED_MODE.message((0,)),e._ingress_token());mix.tick(now=2)

    def preset_fixture(self, choices=None):
        e, mix, source = self.operation_fixture()
        e.ConfigureMixLayers(mix.scope, 'layer_mix', operation_choices=['over', 'add'] if choices is None else choices)
        identity = e.SaveMixOperationPreset('Selected', ['screen', 'multiply'])
        return e, mix, source, identity

    def activation_snapshot(self, e, mix, source):
        state = {key: copy.deepcopy(value) for key, value in vars(mix).items()
                 if key not in ('e', 'scope', 'source', 'targets', 'meters', 'triggers')}
        return (e.GetMixProfile(), state, dict(mix.targets), dict(mix.meters), dict(mix.triggers),
                e._pending, {n: p.eval() for n, p in source.par.items() if p is not None},
                {key: (copy.deepcopy(target.description), target.chain, target.binding.value,
                       target.binding.expected, target.binding.valid) for key, target in mix.targets.items()},
                e.GetMixOperationPresets())

    def test_preset_activation_uses_saved_record_and_preserves_values_and_other_controls(self):
        for choices in (['screen', 'multiply'], ['screen','multiply','over','add','hardlight','difference']):
            with self.subTest(choices=choices):
                e, mix, source, identity = self.preset_fixture()
                e.SaveMixOperationPreset('Selected', choices, identity)
                source.par.lay0operation.val = 'choice_45'
                source.par.lay0swapord.enable = False
                before = copy.deepcopy(mix.profile)
                values = {n: p.eval() for n, p in source.par.items()}
                mix.selected = 1
                result = e.ActivateMixOperationPreset(identity, source=source)
                for item in before['items']: item['controls']['operation']['choices'] = choices
                self.assertEqual(mix.profile, before)
                self.assertEqual(result['descriptor'], before)
                self.assertEqual({n: p.eval() for n, p in source.par.items()}, values)
                self.assertEqual(mix.selected, 0); self.assertTrue(mix.select_pending)
                self.assertEqual(mix.writes, 0); self.assertIsNone(e._process)
                result['descriptor']['items'].clear()
                self.assertEqual(mix.profile, before)
                epoch = mix.epoch
                e.ActivateMixOperationPreset(identity, source=source)
                self.assertEqual(mix.epoch, epoch)

    def test_preset_activation_adds_only_omitted_operation_controls(self):
        e, mix, source, identity = self.preset_fixture(choices=[])
        before = copy.deepcopy(mix.profile)
        e.ActivateMixOperationPreset(identity, source=source)
        for index, item in enumerate(before['items']):
            item['controls']['operation'] = dict(label='Op', kind='menu',
                target=dict(op='layer_mix', parameter='lay' + str(index) + 'operation'),
                choices=['screen', 'multiply'])
        self.assertEqual(mix.profile, before)
        self.assertEqual(mix.writes, 0)

    def test_omitted_operation_preflight_rejects_each_invalid_layer_before_commit(self):
        for change in ('choice', 'style', 'disabled', 'missing', 'readonly', 'labels'):
            with self.subTest(change=change):
                e, mix, source, identity = self.preset_fixture(choices=[])
                p = source.par.lay1operation
                if change == 'choice': p.menuNames.remove('screen'); p.menuLabels.pop()
                elif change == 'style': p.style = 'Float'
                elif change == 'disabled': p.enable = False
                elif change == 'missing': source.par['lay1operation'] = None
                elif change == 'readonly': p.readOnly = True
                else: p.menuLabels.pop()
                before = self.activation_snapshot(e, mix, source)
                with self.assertRaises(ValueError): e.ActivateMixOperationPreset(identity, source=source)
                self.assertEqual(self.activation_snapshot(e, mix, source), before)

    def test_existing_operation_labels_ranges_and_nonfatal_meter_failure_are_preserved(self):
        e, mix, source, identity = self.preset_fixture()
        candidate = copy.deepcopy(mix.profile)
        candidate['items'][0]['controls']['operation'].update(label='Blend', range=[0,45])
        candidate['items'][0]['meter']['source']['op'] = 'missing'
        e.SetMixProfile(mix.scope, candidate)
        e.ActivateMixOperationPreset(identity, source=source)
        expected = copy.deepcopy(candidate)
        for item in expected['items']: item['controls']['operation']['choices'] = ['screen','multiply']
        self.assertEqual(mix.profile, expected)
        self.assertEqual(mix.errors, {})

    def test_existing_bind_master_identity_change_is_rejected_without_rebinding(self):
        e, mix, source, identity = self.preset_fixture()
        parameter = source.par.lay1bright
        master = BoundParameter(); master.owner.id = 999; master.enable = True; master.val = 1
        parameter.mode.name = 'BIND'; parameter.bindMaster = master
        e.ConfigureMixLayers(mix.scope, 'layer_mix', operation_choices=['over','add'])
        replacement = BoundParameter(); replacement.owner.id = 1000; replacement.enable = True; replacement.val = 1
        parameter.bindMaster = replacement
        before = self.activation_snapshot(e, mix, source)
        with self.assertRaises(ValueError): e.ActivateMixOperationPreset(identity, source=source)
        self.assertEqual(self.activation_snapshot(e, mix, source), before)
        self.assertIs(parameter.bindMaster, replacement)
        self.assertEqual((master.eval(), replacement.eval()), (1,1))

    def test_preset_rejection_keeps_complete_runtime_profile_queue_and_values(self):
        cases = ('wrong', 'replacement', 'rewire', 'setup', 'sequence', 'missing', 'disabled',
                 'menu', 'readonly', 'range', 'bind', 'target_set', 'errors', 'layer_invalid',
                 'dispatch', 'restore', 'restore_pending', 'touch', 'host_touch', 'learning',
                 'returning', 'drain', 'unknown', 'buffer', 'partial')
        for case in cases:
            with self.subTest(case=case):
                e, mix, source, identity = self.preset_fixture()
                requested = source
                if case == 'wrong': requested = SimpleNamespace(valid=True, id=777, OPType='layermixTOP')
                elif case == 'replacement':
                    source.id += 1
                    requested = copy.copy(source); requested.id += 1
                    oldop = mix.scope.op
                    mix.scope.op = lambda name: requested if name == 'layer_mix' else oldop(name)
                elif case == 'rewire': source.inputs.reverse()
                elif case == 'setup': source.par.enablebright.val = False
                elif case == 'sequence': source.seq.lay.numBlocks = 3
                elif case == 'missing': source.par['lay1operation'] = None
                elif case == 'disabled': source.par.lay1operation.enable = False
                elif case == 'menu': source.par.lay1operation.menuNames.remove('screen')
                elif case == 'readonly': source.par.lay1bright.readOnly = True
                elif case == 'range': source.par.lay1gamma.normMax = 9
                elif case == 'bind':
                    source.par.lay1bright.mode.name = 'BIND'
                    source.par.lay1bright.bindMaster = BoundParameter()
                elif case == 'target_set': mix.targets.pop((1, 'gamma'))
                elif case == 'errors': mix.errors[1, 'gamma'] = 'old error'
                elif case == 'layer_invalid': mix.layer_invalid = True
                elif case == 'dispatch': e._dispatching = True
                elif case == 'restore': e._restoring = True
                elif case == 'restore_pending': e._restore_pending = True
                elif case == 'touch': mix.touched.add(0)
                elif case == 'host_touch': e._host.touched = True
                elif case == 'learning': e._host.learning = True
                elif case == 'returning': mix.returning = True
                elif case == 'drain': e._mix_preset_drain = True
                elif case == 'unknown': identity = 'missing'
                elif case == 'buffer': e._receive = b'{"ready":true}\n'
                elif case == 'partial': e._receive = b'{"midi":'
                before = self.activation_snapshot(e, mix, source)
                with self.assertRaises(ValueError): e.ActivateMixOperationPreset(identity, source=requested)
                self.assertEqual(self.activation_snapshot(e, mix, source), before)

    def test_strict_configure_rejects_new_target_errors_before_any_commit(self):
        e, mix, source, _ = self.preset_fixture()
        candidate = copy.deepcopy(mix.profile)
        candidate['items'][1]['controls']['brightness']['target']['parameter'] = 'lay0bright'
        before = self.activation_snapshot(e, mix, source)
        with self.assertRaises(ValueError): mix.configure(mix.scope, candidate, strict_targets=True)
        self.assertEqual(self.activation_snapshot(e, mix, source), before)
        mix.configure(mix.scope, candidate)
        self.assertIn((1, 'brightness'), mix.errors)

    def test_preset_probe_retains_read_bytes_with_old_token_and_rejects_unavailable_process(self):
        for observation in (b'{"midi":', b'', OSError('pipe unavailable'), 'connecting', 'failed'):
            with self.subTest(observation=observation):
                e, mix, source, identity = self.preset_fixture()
                child = Mock(); child.poll.return_value = 1 if observation == 'failed' else None
                e._process = child; e._transport_ready = observation != 'connecting'
                token = e._ingress_token(); before = self.activation_snapshot(e, mix, source)
                with patch('RotoPythonExt.os.read', side_effect=[observation]) as read:
                    with self.assertRaises(ValueError): e.ActivateMixOperationPreset(identity, source=source)
                self.assertEqual(self.activation_snapshot(e, mix, source), before)
                if isinstance(observation, bytes) and observation:
                    self.assertEqual(e._receive, observation); self.assertEqual(e._receive_epoch, token)
                else: self.assertEqual(e._receive, b'')
                self.assertLessEqual(read.call_count, 1)

    def test_probe_retained_complete_input_runs_only_against_old_profile_on_normal_tick(self):
        e, mix, source, identity = self.preset_fixture()
        self.enter(e, mix); self.focus(e, mix)
        child = Mock(); child.poll.return_value = None
        e._process = child; e._transport_ready = True; e._trace_control_midi = Mock()
        packet = b''.join((json.dumps({'midi': m}) + '\n').encode() for m in
                          ((191,56,127), (191,16,0), (191,48,0), (191,56,0)))
        token = e._ingress_token(); before = self.activation_snapshot(e, mix, source)
        with patch('RotoPythonExt.os.read', return_value=packet) as read:
            with self.assertRaises(ValueError): e.ActivateMixOperationPreset(identity, source=source)
        read.assert_called_once_with(child.stdout.fileno(), 65536)
        self.assertEqual(self.activation_snapshot(e, mix, source), before)
        self.assertEqual(e._receive_epoch, token)
        with patch('RotoPythonExt.os.read', side_effect=BlockingIOError), patch('RotoPythonExt.os.write', side_effect=lambda fd, data: len(data)):
            e.Tick()
        self.assertEqual(source.par.lay0operation.eval(), 'over'); self.assertEqual(mix.writes, 1)
        self.assertEqual(mix.profile['items'][0]['controls']['operation']['choices'], ['over','add'])

    def test_drain_survives_eof_general_configuration_and_clear_until_eagain_or_disconnect(self):
        e, mix, source, identity = self.preset_fixture()
        self.enter(e, mix)
        child = Mock(); child.poll.return_value = None
        e._process = child; e._transport_ready = True; e._trace_control_midi = Mock()
        with patch('RotoPythonExt.os.read', side_effect=BlockingIOError):
            e.ActivateMixOperationPreset(identity, source=source)
        e.ConfigureMixLayers(mix.scope, 'layer_mix')
        with patch('RotoPythonExt.os.read', return_value=b''), patch('RotoPythonExt.os.write', side_effect=lambda fd, data: len(data)):
            e.Tick()
        self.assertTrue(e._mix_preset_drain); self.assertFalse(mix.ready)
        e.ClearMixProfile(); self.assertTrue(e._mix_preset_drain)
        e.Disconnect(); self.assertFalse(e._mix_preset_drain)

    def test_preset_live_tick_fences_caps_partial_tail_and_fresh_gesture(self):
        for backlog in ('read_cap', 'event_cap', 'partial'):
            with self.subTest(backlog=backlog):
                e, mix, source, identity = self.preset_fixture()
                self.enter(e, mix); self.focus(e, mix)
                child = Mock(); child.poll.return_value = None
                e._process = child; e._transport_ready = True; e._trace_control_midi = Mock()
                old_token = e._ingress_token()
                with patch('RotoPythonExt.os.read', side_effect=BlockingIOError):
                    e.ActivateMixOperationPreset(identity, source=source)
                self.assertTrue(e._mix_preset_drain); self.assertFalse(mix.ready)
                def line(m): return (json.dumps({'midi': m}) + '\n').encode()
                gesture = line((191,56,127)) + line((191,16,127)) + line((191,48,127))
                def tick(chunks):
                    with patch('RotoPythonExt.os.read', side_effect=chunks), patch('RotoPythonExt.os.write', side_effect=lambda fd, data: len(data)):
                        e.Tick()
                if backlog == 'read_cap':
                    tick([line((191,16,127))] * 8)
                    self.assertFalse(mix.ready); self.assertTrue(e._mix_preset_drain)
                    tick([gesture, BlockingIOError])
                elif backlog == 'event_cap':
                    tick([line((191,16,127)) * 257 + gesture, BlockingIOError])
                    self.assertTrue(e._mix_preset_drain); self.assertFalse(mix.ready)
                    tick([BlockingIOError])
                else:
                    tick([gesture[:-4], BlockingIOError])
                    self.assertTrue(e._mix_preset_drain); self.assertFalse(mix.ready)
                    tick([gesture[-4:], BlockingIOError])
                self.assertFalse(e._mix_preset_drain); self.assertFalse(mix.ready)
                self.assertEqual(mix.writes, 0)
                tick([BlockingIOError]); self.assertTrue(mix.ready)
                self.cc(e,56,0); self.cc(e,56,127,old_token); self.turn(e,4,16383)
                self.assertEqual(mix.writes,0)
                self.cc(e,56,0); self.cc(e,56,127); self.cc(e,48,127)
                self.assertEqual(mix.writes,0)
                self.turn(e,4,16383); self.cc(e,56,0)
                self.assertEqual(source.par.lay0operation.eval(),'multiply'); self.assertEqual(mix.writes,1)

    def test_layer_curated_operation_uses_real_names_and_writes_only_selected_input(self):
        e,mix,source=self.operation_fixture()
        before={n:p.eval() for n,p in source.par.items()}
        e.ConfigureMixLayers(mix.scope,'layer_mix',custom_operations=['choice_45'])
        self.assertEqual({n:p.eval() for n,p in source.par.items()},before)
        self.enter(e,mix);self.focus(e,mix,1)
        self.assertEqual(mix.addresses()[4:6],[(1,'operation'),(1,'swap')])
        self.cc(e,56,127);self.turn(e,4,16383);self.cc(e,56,0)
        self.assertEqual(source.par.lay1operation.eval(),'choice_45')
        self.assertEqual(source.par.lay0operation.eval(),'add')
        self.assertEqual(len(mix.targets[1,'operation'].binding.menu_names),46)
        self.assertEqual(mix.writes,1)
        mix.tick(now=3)
        self.assertIn(SysExCommand.PARAM_VALUES.message((0,4,*text13('Op 5 Choice 46'))),[tuple(m) for m in self.messages(e)])

    def test_layer_operation_libraries_and_custom_choices_validate_atomically(self):
        e,mix,source=self.operation_fixture()
        e.ConfigureMixLayers(mix.scope,'layer_mix',operation_library='math',custom_operations=['choice_45','add'])
        before=e.GetMixProfile()
        self.assertEqual(before['descriptor']['items'][0]['controls']['operation']['choices'],
                         ['add','subtract','multiply','divide','difference','average','choice_45'])
        for kwargs in ({'operation_library':'missing'}, {'operation_library':[]}, {'custom_operations':['missing']}, {'custom_operations':['add']*5}):
            with self.assertRaises(ValueError):e.ConfigureMixLayers(mix.scope,'layer_mix',**kwargs)
            self.assertEqual(e.GetMixProfile(),before)
        self.assertEqual(source.par.lay0operation.eval(),'add');self.assertEqual(mix.writes,0)

    def test_explicit_operation_choices_have_no_implicit_library_and_empty_omits_control(self):
        e,mix,source=self.operation_fixture()
        e.ConfigureMixLayers(mix.scope,'layer_mix',operation_choices=['choice_45','add'])
        item=e.GetMixProfile()['descriptor']['items'][0]
        self.assertEqual(item['controls']['operation']['choices'],['choice_45','add'])
        before=e.GetMixProfile()
        for choices in (['over'], ['missing','add'], ['over']*25):
            with self.assertRaises(ValueError):e.ConfigureMixLayers(mix.scope,'layer_mix',operation_choices=choices)
            self.assertEqual(e.GetMixProfile(),before)
        with self.assertRaises(ValueError):
            e.ConfigureMixLayers(mix.scope,'layer_mix',operation_choices=['over','add'],operation_library='common')
        e.ConfigureMixLayers(mix.scope,'layer_mix',operation_choices=[])
        item=e.GetMixProfile()['descriptor']['items'][0]
        self.assertNotIn('operation',item['controls']);self.assertIn('swap',item['controls'])
        self.assertEqual(source.par.lay0operation.eval(),'add');self.assertEqual(mix.writes,0)

    def test_layer_per_layer_fields_must_exist_before_registration(self):
        e,mix,source=self.operation_fixture();before=e.GetMixProfile()
        source.par['lay0operation']=None
        with self.assertRaisesRegex(ValueError,'Cook Layer Mix'):e.ConfigureMixLayers(mix.scope,'layer_mix')
        self.assertEqual(e.GetMixProfile(),before);self.assertEqual(mix.writes,0)

    def test_layer_operation_outside_library_is_preserved_without_false_motor_feedback(self):
        e,mix,source=self.operation_fixture();source.par.lay0operation.val='choice_20'
        e.ConfigureMixLayers(mix.scope,'layer_mix');self.enter(e,mix);self.focus(e,mix)
        self.assertEqual(source.par.lay0operation.eval(),'choice_20');self.assertEqual(mix.writes,0)
        self.assertFalse(any(m[:2] in ([191,16],[191,48]) for m in self.messages(e)))
        self.assertIn(SysExCommand.PARAM_VALUES.message((0,4,*text13('Op * Choice 21'))),[tuple(m) for m in self.messages(e)])
        self.cc(e,56,127);self.turn(e,4,16383);self.cc(e,56,0)
        self.assertEqual(source.par.lay0operation.eval(),'screen');self.assertEqual(mix.writes,1)

    def test_layer_swap_is_a_typed_knob_with_no_focus_button_fallback(self):
        e,mix,source=self.operation_fixture();e.ConfigureMixLayers(mix.scope,'layer_mix')
        self.enter(e,mix);self.focus(e,mix,1)
        self.cc(e,57,127);self.turn(e,5,16383);self.cc(e,57,0)
        self.assertTrue(source.par.lay1swapord.eval());self.assertFalse(source.par.lay0swapord.eval())
        self.cc(e,21,127);self.cc(e,21,0)
        self.assertTrue(source.par.lay1swapord.eval());self.assertEqual(mix.writes,1)
        source.par.lay1swapord.val=False;mix.tick(now=3)
        self.assertIn([191,17,0],self.messages(e))

    def test_layer_disabled_swap_recovers_after_release_without_reconfiguring_menu(self):
        e,mix,source=self.operation_fixture();source.par.lay0swapord.enable=False
        e.ConfigureMixLayers(mix.scope,'layer_mix');self.enter(e,mix);self.focus(e,mix)
        self.cc(e,57,127);self.turn(e,5,16383)
        self.assertFalse(source.par.lay0swapord.eval());self.assertEqual(mix.writes,0)
        source.par.lay0swapord.enable=True;mix.tick(now=3);self.turn(e,5,16383)
        self.assertFalse(source.par.lay0swapord.eval())
        self.cc(e,57,0);self.cc(e,57,127);self.turn(e,5,16383);self.cc(e,57,0)
        self.assertTrue(source.par.lay0swapord.eval());self.assertEqual(mix.writes,1)

    def test_layer_menu_changes_suspend_old_route_and_per_layer_changes_fence_source(self):
        for change in ('names','labels','global'):
            with self.subTest(change=change):
                e,mix,source=self.operation_fixture();e.ConfigureMixLayers(mix.scope,'layer_mix')
                self.enter(e,mix);self.focus(e,mix);self.cc(e,56,127)
                if change=='names':source.par.lay0operation.menuNames.reverse()
                elif change=='labels':source.par.lay0operation.menuLabels.reverse()
                else:source.par.operand.val='over'
                self.turn(e,4,16383);mix.tick(now=3)
                self.assertEqual(source.par.lay0operation.eval(),'add');self.assertEqual(mix.writes,0)
                if change=='global':
                    source.par.operand.val='opperlayer';mix.tick(now=4);self.assertFalse(mix.ready)

    def test_layer_disabled_swap_does_not_reuse_a_partial_pair_after_enable(self):
        e,mix,source=self.operation_fixture();source.par.lay0swapord.enable=False
        e.ConfigureMixLayers(mix.scope,'layer_mix');self.enter(e,mix);self.focus(e,mix)
        self.cc(e,57,127);self.cc(e,17,127)
        source.par.lay0swapord.enable=True;self.cc(e,49,127)
        self.assertFalse(source.par.lay0swapord.eval());self.assertEqual(mix.writes,0)
        self.cc(e,57,0);self.cc(e,57,127);self.turn(e,5,16383);self.cc(e,57,0)
        self.assertTrue(source.par.lay0swapord.eval());self.assertEqual(mix.writes,1)

    def test_layer_operation_projection_and_send_metadata_preserve_gaps(self):
        e,mix,source=self.operation_fixture();e.ConfigureMixLayers(mix.scope,'layer_mix')
        self.enter(e,mix);self.focus(e,mix)
        self.assertIn(list(SysExCommand.NUM_SENDS.message((4,))),self.messages(e))
        p=e.GetMixProfile()['descriptor']
        self.assertEqual(projection(p,('all',(0,2,0,2)),0)[:2],[(0,'operation'),(1,'operation')])
        self.assertEqual(projection(p,('all',(0,2,0,3)),0)[:2],[(0,'swap'),(1,'swap')])
        self.assertEqual(projection(p,('all',(0,2,0,4)),0),[None]*8)
        self.assertEqual(projection(p,('focus',8),0),[None]*8)
        source.par.operand.val='add';e.ConfigureMixLayers(mix.scope,'layer_mix')
        self.assertNotIn('operation',e.GetMixProfile()['descriptor']['items'][0]['controls'])
        self.assertNotIn('swap',e.GetMixProfile()['descriptor']['items'][0]['controls'])

    def test_layer_adapter_is_readonly_and_opacity_drives_independent_meter_and_input(self):
        e,mix,source,images,analysis=self.layer_fixture()
        before={n:p.eval() for n,p in source.par.items()};old_analysis={n:p.eval() for n,p in analysis.par.items()}
        profile=e.ConfigureMixLayers(mix.scope,'layer_mix')
        self.assertEqual(profile['descriptor']['style'],'layers')
        self.assertEqual(profile['descriptor']['items'][0]['input'],'image_0')
        self.assertEqual({n:p.eval() for n,p in source.par.items()},before)
        self.enter(e,mix);mix.tick(now=2)
        self.assertIn([191,65,32],self.messages(e));self.assertIn([191,67,95],self.messages(e))
        self.cc(e,52,127);self.turn(e,0,8192);self.cc(e,52,0)
        self.assertAlmostEqual(source.par.lay0opacity.eval(),8192/16383)
        self.assertEqual(source.par.lay1opacity.eval(),.75)
        self.assertEqual({n:p.eval() for n,p in analysis.par.items()},old_analysis)
        self.cc(e,20,127);self.cc(e,20,0);self.assertEqual(mix.writes,1)

    def test_layer_focus_has_own_four_fields_and_reuses_target_guards(self):
        e,mix,source,*_=self.layer_fixture();e.ConfigureMixLayers(mix.scope,'layer_mix')
        self.enter(e,mix);e._receive_midi(SysExCommand.SELECT_TRACK.message((0,1)),e._ingress_token())
        e._receive_midi(SysExCommand.SET_MIXER_SELECTED_MODE.message((0,)),e._ingress_token());mix.tick(now=2)
        self.assertEqual(mix.addresses()[:4],[(1,k) for k in ('opacity','brightness','black_level','gamma')])
        self.cc(e,53,127);self.turn(e,1,8192);self.cc(e,53,0)
        self.assertAlmostEqual(source.par.lay1bright.eval(),2*8192/16383)
        self.assertEqual(source.par.lay0bright.eval(),1)

    def test_layer_rewire_setup_or_sequence_changes_fence_input_until_reconfigured(self):
        for change in ('rewire','setup','sequence'):
            with self.subTest(change=change):
                e,mix,source,images,_=self.layer_fixture();e.ConfigureMixLayers(mix.scope,'layer_mix');self.enter(e,mix)
                self.cc(e,52,127)
                if change=='rewire':source.inputs.reverse()
                elif change=='setup':source.par.enablebright.val=False
                else:source.seq.lay.numBlocks=3
                self.turn(e,0,16383);mix.tick(now=2)
                self.assertEqual(source.par.lay0opacity.eval(),.25);self.assertEqual(mix.writes,0)
                self.assertFalse(mix.ready)

    def test_layer_disabled_fields_are_unavailable_without_changing_setup(self):
        e,mix,source,*_=self.layer_fixture()
        source.par.enableopac.val=False;source.par.enablelevels.val=False
        e.ConfigureMixLayers(mix.scope,'layer_mix');self.enter(e,mix)
        item=e.GetMixProfile()['descriptor']['items'][0]
        self.assertIsNone(item['primary']);self.assertNotIn('meter',item)
        self.assertEqual(set(item['controls']),{'brightness'})
        self.cc(e,52,127);self.turn(e,0,16383);self.cc(e,52,0)
        self.assertFalse(source.par.enableopac.eval());self.assertFalse(source.par.enablelevels.eval())
        self.assertEqual(source.par.lay0opacity.eval(),.25);self.assertEqual(mix.writes,0)

    def test_saved_layer_profile_rejects_new_input_order_and_requires_explicit_reconfigure(self):
        e,mix,source,*_=self.layer_fixture();e.ConfigureMixLayers(mix.scope,'layer_mix')
        saved=e.GetMixProfile();self.enter(e,mix)
        source.inputs.reverse();mix.tick(now=2);self.assertFalse(mix.ready)
        with self.assertRaises(ValueError):e.SetMixProfile(mix.scope,saved['descriptor'])
        self.assertEqual(e.GetMixProfile(),saved)
        source.inputs.reverse();mix.tick(now=3);self.assertFalse(mix.ready)
        e.ConfigureMixLayers(mix.scope,'layer_mix');mix.tick(now=4)
        self.assertTrue(mix.ready);self.turn(e,0,16383);self.assertEqual(mix.writes,0)
        self.cc(e,52,127);self.turn(e,0,16383);self.cc(e,52,0)
        self.assertEqual(source.par.lay0opacity.eval(),1);self.assertEqual(mix.writes,1)

    def fixture(self):
        e, m, f, a, b, *_ = test_comp_follow.FollowTests().fixture()
        source = SimpleNamespace(valid=True, isCOMP=True, id=800, path='/demo/analysis', par=Pars())
        for band in ('Low', 'Mid', 'High'):
            for suffix, value, low, high in (
                    ('thresh', .1, 0, .6), ('gain', 2, 0, 7), ('add', 0, -1, 1),
                    ('smooth', 0, 0, 1), ('active', 1, 0, 1)):
                p = BoundParameter('Toggle' if suffix == 'active' else 'Float')
                p.name = band + suffix; p.owner = source; p.enable = True
                p.normMin = p.min = low; p.normMax = p.max = high; p.val = value
                source.par[p.name] = p
        for prefix,minimum,maximum in (('Kick',0,.6),('Snare',0,.6),('Rythm',10,90)):
            for suffix,kind,value in (('thresh','Float',.26 if prefix!='Rythm' else 49), ('active','Toggle',False)):
                p=BoundParameter(kind);p.name=prefix+suffix;p.owner=source;p.enable=True
                p.normMin=p.min=minimum if kind=='Float' else 0;p.normMax=p.max=maximum if kind=='Float' else 1
                p.val=value;source.par[p.name]=p
        channels = {'low': Channel([.25]), 'mid': Channel([.75]), 'high': Channel([.5]), 'kick': Channel([0]), 'snare':Channel([0]), 'rythm':Channel([0])}
        class Chop:
            valid = True; id = 801; path = '/demo/analysis/out1'
            data = channels
            def __getitem__(self, name): return self.data.get(name)
        chop = Chop()
        level = Chop();level.id=802;level.path='/demo/analysis/math2';level.data={'low':Channel([.8])}
        snare=Chop();snare.id=803;snare.path='/demo/analysis/math16';snare.data={'high':Channel([.4])}
        rhythm=Chop();rhythm.id=804;rhythm.path='/demo/analysis/math10';rhythm.data={'chan0':Channel([70])}
        operators = {'analysis': source, 'analysis/out1': chop, 'analysis/math2':level,'analysis/math16':snare,'analysis/math10':rhythm}
        scope = SimpleNamespace(valid=True, isCOMP=True, id=799, path='/demo', op=operators.get)
        oldop = e.ownerComp.op
        e.ownerComp.op = lambda name: scope if name == '../demo' else oldop(name)
        e.ownerComp.relativePath = lambda op: '../demo'
        mix = MixRuntime(e); e._mix = mix
        mix.configure(scope, analysis_profile('analysis'))
        e._pending = b''
        return e, mix, m, f, source, channels, operators

    def enter(self, e, mix, view=(SysExCommand.SET_MIXER_ALL_MODE, (0, 0, 0, 0))):
        e._receive_midi(view[0].message(view[1]), e._ingress_token())
        mix.tick(now=1)
        e._pending = b''

    def cc(self, e, cc, value, token=None):
        e._receive_midi((191, cc, value), e._ingress_token() if token is None else token)

    def turn(self, e, lane, raw):
        self.cc(e, 12 + lane, raw >> 7); self.cc(e, 44 + lane, raw & 127)

    def messages(self, e):
        return [json.loads(line)['midi'] for line in e._pending.splitlines()]

    def test_saved_descriptor_load_is_independent_and_never_restores_values(self):
        e, mix, m, f, source, *_ = self.fixture()
        saved = e.GetMixProfile(); registry = copy.deepcopy(m.data)
        source.par.Lowgain.val = 4
        restored = MixRuntime(e)
        self.assertEqual(source.par.Lowgain.eval(), 4)
        self.assertFalse(restored.active); self.assertEqual(restored.writes, 0)
        self.assertEqual(e.GetMixProfile(), saved); self.assertEqual(m.data, registry)
        saved['descriptor']['items'][0]['label'] = 'Changed'
        self.assertEqual(e.GetMixProfile()['descriptor']['items'][0]['label'], 'Low')

    def test_high_band_input_meter_and_active_remain_independent(self):
        e, mix, manager, _, source, *_ = self.fixture()
        values = {name:p.eval() for name,p in source.par.items()}
        registry = copy.deepcopy(manager.data)
        e.ConfigureMixAnalysis(mix.scope, 'analysis', ('Low', 'Mid', 'High'))
        self.assertEqual(len(mix.targets), 15)
        self.assertEqual({name:p.eval() for name,p in source.par.items()}, values)
        self.enter(e, mix)
        mix.tick(now=1.2)
        self.assertIn([191, 69, 64], self.messages(e))
        self.assertIn([191, 70, 64], self.messages(e))
        e._receive_midi(SysExCommand.SELECT_TRACK.message((0,2)), e._ingress_token())
        self.cc(e, 54, 127); self.turn(e, 2, 16383); self.cc(e, 54, 0)
        self.assertEqual(source.par.Highthresh.eval(), .1)  # selection fences its accompanying touch
        mix.tick(now=1.4)
        self.cc(e, 54, 127); self.turn(e, 2, 16383); self.cc(e, 54, 0)
        self.assertEqual(source.par.Highthresh.eval(), .6)
        self.cc(e, 22, 127); self.cc(e, 22, 127); self.cc(e, 22, 0)
        self.assertFalse(source.par.Highactive.eval())
        self.focus(e, mix, 2)
        self.cc(e, 53, 127); self.turn(e, 1, 8192); self.cc(e, 53, 0)
        self.assertAlmostEqual(source.par.Highgain.eval(), 7 * 8192 / 16383)
        self.assertEqual(source.par.Highadd.eval(), 0)
        self.assertEqual(source.par.Highsmooth.eval(), 0)
        self.assertEqual({name:p.eval() for name,p in source.par.items() if not name.startswith('High')},
                         {name:value for name,value in values.items() if not name.startswith('High')})
        self.assertEqual(manager.data, registry)
        self.assertEqual(mix.writes, 3)

    def test_analysis_band_order_reload_and_invalid_selections(self):
        e, mix, _, _, source, *_ = self.fixture()
        e.ConfigureMixAnalysis(mix.scope, 'analysis', ('High', 'Low'))
        saved = e.GetMixProfile()
        self.assertEqual([item['id'] for item in saved['descriptor']['items']], ['high', 'low'])
        source.par.Highgain.val = 3
        restored = MixRuntime(e)
        self.assertEqual(restored.profile, saved['descriptor'])
        self.assertEqual(source.par.Highgain.eval(), 3)
        self.assertEqual(restored.writes, 0)
        for bands in ((), ('High', 'High'), ('Unknown',), ('Low', 'Unknown'), 'High', None):
            with self.subTest(bands=bands), self.assertRaises(ValueError):
                e.ConfigureMixAnalysis(mix.scope, 'analysis', bands)
            self.assertEqual(e.GetMixProfile(), saved)

    def test_analysis_overview_selection_caption_persists_and_moves_without_writes(self):
        e, mix, _, _, source, *_ = self.fixture()
        e.ConfigureMixAnalysis(mix.scope, 'analysis', ('Low', 'Mid', 'High'))
        self.enter(e, mix)
        e._receive_midi(SysExCommand.SELECT_TRACK.message((0,2)), e._ingress_token())
        self.cc(e, 54, 127); self.cc(e, 54, 0)
        mix.tick(now=2)
        self.assertIn(list(SysExCommand.PARAM_VALUES.message((0,2,*text13('>High 0.100')))), self.messages(e))
        e._pending = b''
        mix.tick(now=12)
        self.assertIn(list(SysExCommand.PARAM_VALUES.message((0,2,*text13('>High 0.100')))), self.messages(e))
        e._receive_midi(SysExCommand.SELECT_TRACK.message((0,1)), e._ingress_token())
        self.cc(e, 53, 127); self.cc(e, 53, 0)
        mix.tick(now=13)
        self.assertIn(list(SysExCommand.PARAM_VALUES.message((0,1,*text13('>Mid 0.100')))), self.messages(e))
        self.assertIn(list(SysExCommand.PARAM_VALUES.message((0,2,*text13('Thresh 0.100')))), self.messages(e))
        self.assertEqual(mix.writes, 0)
        self.assertEqual(source.par.Highthresh.eval(), .1)

    def test_analysis_focus_uses_control_names_and_long_selection_labels_keep_value(self):
        e, mix, _, _, _, *_ = self.fixture()
        profile = e.GetMixProfile()['descriptor']
        profile['items'][0]['label'] = 'Long band name'
        e.SetMixProfile(mix.scope, profile)
        self.enter(e, mix)
        mix.tick(now=1.2)
        self.assertIn(list(SysExCommand.PARAM_VALUES.message((0,0,*text13('>Long 0.100')))), self.messages(e))
        e._pending = b''
        self.focus(e, mix)
        self.assertIn(list(SysExCommand.PARAM_VALUES.message((0,0,*text13('Thresh 0.100')))), self.messages(e))
        self.assertFalse(any(SysExCommand.identify(m) is SysExCommand.PARAM_VALUES and m[9:10] == [ord('>')] for m in self.messages(e)))

    def test_overview_selection_does_not_resend_unchanged_motor_positions(self):
        e, mix, _, _, source, *_ = self.fixture()
        e.ConfigureMixAnalysis(mix.scope, 'analysis', ('Low','Mid','High'))
        self.enter(e, mix)
        e._receive_midi(SysExCommand.SELECT_TRACK.message((0,2)), e._ingress_token()); mix.tick(now=2)
        e._pending = b''
        # Actual hardware reports selection before touch. Repeating positions
        # here produced extra Knob 3 touch/selection in the physical trace.
        e._receive_midi(SysExCommand.SELECT_TRACK.message((0,0)), e._ingress_token())
        self.cc(e,52,127); self.cc(e,52,0); mix.tick(now=3)
        motors = [m for m in self.messages(e) if len(m)==3 and m[0]==191 and (12<=m[1]<=19 or 44<=m[1]<=51)]
        self.assertEqual(motors, [])
        self.assertEqual(mix.selected, 0)
        self.assertEqual(mix.writes, 0)
        # A real TD edit must still move an untouched knob in this view.
        source.par.Highthresh.val = .45
        mix.tick(now=4)
        self.assertIn([191,14,raw_value(.75)>>7], self.messages(e))

    def test_overview_selection_preserves_queued_motors_but_focus_change_discards_them(self):
        e, mix, *_ = self.fixture()
        self.enter(e, mix)
        tail = b'7]}\n'  # already-started output frame
        e._pending = tail
        queued = [[191,13,42], [191,45,85]]
        for message in queued:
            e._send(message, mix=True)
        e._send(SysExCommand.PARAM_VALUES.message((0,1,*text13('Old text'))), mix=True)
        e._receive_midi(SysExCommand.SELECT_TRACK.message((0,1)), e._ingress_token())
        self.assertTrue(e._pending.startswith(tail))
        self.assertEqual([json.loads(line)['midi'] for line in e._pending[len(tail):].splitlines()], queued)
        e._receive_midi(SysExCommand.SET_MIXER_SELECTED_MODE.message((0,)), e._ingress_token())
        self.assertEqual(e._pending, tail)
        mix.tick(now=2)
        frames = [json.loads(line)['midi'] for line in e._pending[len(tail):].splitlines()]
        self.assertTrue(any(mix.motor_output(message) for message in frames))
        self.assertEqual(mix.writes, 0)

    def test_common_descriptor_rejects_invalid_ranges_refs_and_unknown_style_atomically(self):
        e, mix, *_ = self.fixture(); before = e.GetMixProfile()
        for path, value in ((('version',), 2), (('style',), 'generic'), (('source',), '../foreign')):
            bad = copy.deepcopy(before['descriptor']); bad[path[0]] = value
            with self.assertRaises(ValueError): e.SetMixProfile(mix.scope, bad)
            self.assertEqual(e.GetMixProfile(), before)
        bad = copy.deepcopy(before['descriptor'])
        bad['items'][0]['controls']['gain']['range'] = [0, float('nan')]
        with self.assertRaises(ValueError): validate(bad)

    def test_projection_has_no_missing_function_fallback_or_unaccepted_second_page(self):
        p = analysis_profile('analysis'); del p['items'][1]['controls']['gain']
        self.assertEqual(projection(p, ('all', (0, 1, 0, 0)), 0)[:2], [(0, 'gain'), None])
        self.assertEqual(projection(p, ('all', (0, 2, 2, 1)), 0)[:2], [(0, 'smooth'), (1, 'smooth')])
        for view in (('all', (1, 0, 0, 0)), ('all', (0, 2, 0, 7)), ('focus', 8)):
            self.assertEqual(projection(p, view, 0), [None] * 8)
        self.assertEqual(projection(p, ('focus', 0), 1)[:4], [(1, 'threshold'), None, (1, 'add'), (1, 'smooth')])

    def test_overview_touch_select_then_func_routes_mid_details_without_plugin_writes(self):
        e, mix, m, f, source, *_ = self.fixture(); registry = copy.deepcopy(m.data)
        self.enter(e, mix)
        token = e._ingress_token()
        e._receive_midi(SysExCommand.SELECT_TRACK.message((0,1)), token)  # actual unlocked trace: selection precedes touch
        self.cc(e, 53, 127, token); self.turn(e, 1, 16383)
        self.assertEqual(mix.selected, 1); self.assertEqual(source.par.Midthresh.eval(), .1)
        e._receive_midi(SysExCommand.SET_MIXER_SELECTED_MODE.message((0,)), e._ingress_token()); mix.tick(now=2)
        self.turn(e, 1, 16383)  # old touch cannot write new Focus Gain
        self.assertEqual(source.par.Midgain.eval(), 2)
        self.cc(e, 53, 0); self.cc(e, 53, 127); self.turn(e, 1, 8192)
        self.assertAlmostEqual(source.par.Midgain.eval(), 7 * 8192 / 16383)
        self.assertEqual(source.par.Lowgain.eval(), 2); self.assertEqual(m.data, registry)
        self.assertFalse(e._host.plugin); self.assertFalse(e._host.mapped)

    def test_lock_touch_without_track_selection_keeps_band_and_overview_lane_target(self):
        e, mix, _, _, source, *_ = self.fixture(); self.enter(e, mix)
        epoch = mix.epoch
        # Firmware 3.3.0 LOCK-on trace: CC53 ON/OFF, no General Track selection.
        self.cc(e, 53, 127); self.cc(e, 53, 0); mix.tick(now=2)
        self.assertEqual(mix.selected, 0)
        self.assertEqual(mix.epoch, epoch)
        self.assertEqual(mix.writes, 0)
        self.assertIn(list(SysExCommand.PARAM_VALUES.message((0,0,*text13('>Low 0.100')))), self.messages(e))
        self.assertFalse(any(m[:7] == list(SysExCommand.DAW_SELECT_TRACK.message()[:7]) for m in self.messages(e)))
        # LOCK keeps selection; overview knobs retain their independent targets.
        self.cc(e, 53, 127); self.turn(e, 1, 8192); self.cc(e, 53, 0)
        self.assertAlmostEqual(source.par.Midthresh.eval(), .6 * 8192 / 16383)
        self.assertEqual(source.par.Lowthresh.eval(), .1)
        self.assertEqual(mix.selected, 0)
        self.assertEqual(mix.writes, 1)

    def test_fresh_touch_required_echo_buttons_and_plugin_ack_cannot_write(self):
        e, mix, m, f, source, *_ = self.fixture(); self.enter(e, mix)
        for raw in (0, 16383): self.turn(e, 0, raw)
        for value in (127, 0, 127): self.cc(e, 27, value)  # unassigned MIX button
        target = next(iter(e._host.controls.values()))
        e._receive_midi(SysExCommand.CONTROL_MAPPED.message((target.index >> 7, target.index & 127, *digest(target.target_id, 6), 0, 0, 0)))
        self.assertEqual(source.par.Lowthresh.eval(), .1); self.assertEqual(mix.writes, 0)
        self.assertFalse(target.mapped)
        self.cc(e, 52, 127); self.turn(e, 0, 8192); self.turn(e, 0, 8192)
        self.assertEqual(mix.writes, 1)
        self.cc(e, 52, 0); self.turn(e, 0, 0)
        self.assertAlmostEqual(source.par.Lowthresh.eval(), .6 * 8192 / 16383)

    def test_cc_pair_either_order_stale_and_release_partial_never_replays(self):
        e, mix, _, _, source, *_ = self.fixture(); self.enter(e, mix)
        self.cc(e, 52, 127)
        with patch('mix_runtime.time.monotonic', return_value=10): self.cc(e, 44, 127)
        with patch('mix_runtime.time.monotonic', return_value=10.3): self.cc(e, 12, 127)
        self.assertEqual(mix.writes, 0)
        with patch('mix_runtime.time.monotonic', return_value=11):
            self.cc(e, 44, 127); self.cc(e, 12, 127)
        self.assertEqual(source.par.Lowthresh.eval(), .6)
        self.cc(e, 12, 0); self.cc(e, 52, 0); self.cc(e, 52, 127); self.cc(e, 44, 0)
        self.assertEqual(mix.writes, 1)

    def test_view_backlog_and_stale_ingress_require_new_touch(self):
        e, mix, _, _, source, *_ = self.fixture(); self.enter(e, mix)
        self.cc(e, 52, 127); self.cc(e, 12, 127)
        old = e._ingress_token(); e._receive_midi(SysExCommand.SET_MIXER_SELECTED_MODE.message((0,)), old)
        mix.tick(backlog=True, now=2)
        self.cc(e, 44, 127); self.assertFalse(mix.ready)
        mix.tick(now=3)
        self.cc(e, 52, 0); self.cc(e, 52, 127, old)
        self.turn(e, 0, 16383); self.assertEqual(mix.writes, 0)
        self.cc(e, 52, 0); self.cc(e, 52, 127); self.turn(e, 0, 16383)
        self.assertEqual(source.par.Lowthresh.eval(), .6)

    def test_target_mode_replacement_bind_master_and_range_changes_suspend(self):
        for change in ('mode', 'replacement', 'master', 'range', 'disabled'):
            with self.subTest(change=change):
                e, mix, _, _, source, _, ops = self.fixture(); self.enter(e, mix)
                p = source.par.Lowthresh
                if change == 'mode': p.mode.name = 'EXPRESSION'
                elif change == 'replacement': ops['analysis'] = SimpleNamespace(valid=True, id=900, path=source.path)
                elif change == 'master': p.mode.name = 'BIND'; p.bindMaster = BoundParameter()
                elif change == 'range': p.normMax = .8
                else: p.enable = False
                self.cc(e, 52, 127); self.turn(e, 0, 16383)
                self.assertEqual(mix.writes, 0)
                if change != 'master': self.assertEqual(p.eval(), .1)

    def test_meters_are_independent_bounded_coalesced_and_missing_source_clears(self):
        e, mix, _, _, source, channels, _ = self.fixture(); self.enter(e, mix)
        mix.tick(now=2)
        messages = self.messages(e)
        self.assertIn([191, 65, 32], messages); self.assertIn([191, 67, 95], messages)
        pending = len(e._pending); mix.tick(now=2.01); self.assertEqual(len(e._pending), pending)
        for n in range(100):
            channels['low'].vals = [n / 100]; mix.tick(now=3 + n)
        meters = [m for m in self.messages(e) if len(m) == 3 and 65 <= m[1] <= 80]
        self.assertEqual(len(meters), 16); self.assertIn([191, 65, 126], meters)
        del channels['low']; mix.tick(now=200)
        self.assertIn([191, 65, 0], self.messages(e))
        self.assertEqual(source.par.Lowthresh.eval(), .1)

    def test_software_motor_deferred_while_touched_and_latest_edit_returns_on_release(self):
        e, mix, _, _, source, *_ = self.fixture(); self.enter(e, mix)
        self.cc(e, 52, 127); source.par.Lowthresh.val = .45; mix.tick(now=2)
        self.assertFalse(any(m[:2] == [191, 12] for m in self.messages(e)))
        self.cc(e, 52, 0); mix.tick(now=3)
        self.assertIn([191, 12, 95], self.messages(e))
        self.assertEqual(mix.writes, 0)

    def test_overview_active_button_toggles_once_per_press_without_float_or_plugin_writes(self):
        e, mix, manager, _, source, *_ = self.fixture(); self.enter(e, mix)
        registry = copy.deepcopy(manager.data)
        floats = {name:p.eval() for name,p in source.par.items() if p.style == 'Float'}
        self.cc(e, 20, 127); self.cc(e, 20, 127)
        self.assertFalse(source.par.Lowactive.eval()); self.assertEqual(mix.writes, 1)
        self.cc(e, 20, 0)
        self.assertFalse(source.par.Lowactive.eval()); self.assertEqual(mix.writes, 1)
        self.cc(e, 20, 127); self.cc(e, 20, 0)
        self.assertTrue(source.par.Lowactive.eval()); self.assertEqual(mix.writes, 2)
        self.assertTrue(source.par.Midactive.eval())
        self.assertEqual({name:p.eval() for name,p in source.par.items() if p.style == 'Float'}, floats)
        self.assertEqual(manager.data, registry)

    def test_active_feedback_uses_native_mute_polarity_and_reconfirms_after_release(self):
        e, mix, _, _, source, *_ = self.fixture(); self.enter(e, mix)
        source.par.Midactive.val = 0
        mix.invalidate()
        mix.tick(now=2)
        self.assertIn([191, 20, 0], self.messages(e))  # active -> native mute off
        self.assertIn([191, 21, 127], self.messages(e))
        e._pending = b''; mix.tick(now=3)
        self.assertFalse(any(len(m)==3 and 20<=m[1]<=27 for m in self.messages(e)))
        self.cc(e, 20, 127); mix.tick(now=4); e._pending = b''
        self.cc(e, 20, 0); mix.tick(now=5)
        self.assertIn([191, 20, 127], self.messages(e))  # release cannot reset the state LED
        self.assertIn([191, 65, 32], self.messages(e))  # meter source remains independent
        self.assertEqual(mix.writes, 1)
        source.par.Lowactive.val = 1; mix.tick(now=6)
        buttons = [m for m in self.messages(e) if len(m)==3 and m[1]==20]
        self.assertEqual(buttons, [[191, 20, 0]])  # coalesce obsolete pending state
        self.assertEqual(mix.writes, 1)

    def test_active_buttons_ignore_stale_held_and_unsupported_views(self):
        e, mix, _, _, source, *_ = self.fixture(); self.enter(e, mix)
        old = e._ingress_token()
        e._receive_midi(SysExCommand.SET_MIXER_ALL_MODE.message((0, 1, 0, 0)), old); mix.tick(now=2)
        self.cc(e, 20, 127, old); self.cc(e, 20, 127)
        self.assertEqual(mix.writes, 0)
        self.cc(e, 20, 0); self.cc(e, 20, 127)
        self.assertFalse(source.par.Lowactive.eval()); self.assertEqual(mix.writes, 1)
        for event in (SysExCommand.SET_MIXER_ALL_MODE.message((0, 0, 1, 0)), SysExCommand.SET_MIXER_ALL_MODE.message((0, 0, 2, 0)), SysExCommand.SET_MIXER_SELECTED_MODE.message((0,))):
            e._receive_midi(event, e._ingress_token()); mix.tick(now=3)
            self.cc(e, 20, 0); self.cc(e, 20, 127); self.cc(e, 20, 0)
            self.assertEqual(mix.writes, 1)
        e._receive_midi(SysExCommand.SET_MIXER_ALL_MODE.message((0, 0, 0, 0)), e._ingress_token()); mix.tick(now=4)
        self.cc(e, 27, 127); self.cc(e, 27, 0)
        self.assertEqual(mix.writes, 1)  # unassigned button never falls back

    def test_active_target_replacement_readonly_and_bind_master_changes_suspend(self):
        for change in ('replacement', 'readonly', 'master'):
            with self.subTest(change=change):
                e, mix, _, _, source, _, operators = self.fixture(); self.enter(e, mix)
                p=source.par.Lowactive
                if change=='replacement':operators['analysis']=SimpleNamespace(valid=True,id=900,path=source.path)
                elif change=='readonly':p.readOnly=True
                else:p.mode.name='BIND';p.bindMaster=BoundParameter('Toggle')
                self.cc(e,20,127);self.cc(e,20,0)
                self.assertEqual(mix.writes,0)
                self.assertTrue(source.par.Midactive.eval())

    def test_active_toggle_cannot_be_projected_onto_a_knob(self):
        e,mix,_,_,source,*_=self.fixture()
        profile=e.GetMixProfile()['descriptor'];profile['items'][0]['primary']='active'
        e.SetMixProfile(mix.scope,profile);self.enter(e,mix)
        self.cc(e,52,127);self.turn(e,0,0);self.cc(e,52,0)
        self.assertTrue(source.par.Lowactive.eval());self.assertEqual(mix.writes,0)
        self.cc(e,20,127);self.cc(e,20,0)
        self.assertFalse(source.par.Lowactive.eval());self.assertEqual(mix.writes,1)

    def test_button_held_across_view_change_requires_release_and_new_press(self):
        e,mix,_,_,source,*_=self.fixture();self.enter(e,mix)
        self.cc(e,20,127);self.assertEqual(mix.writes,1)
        e._receive_midi(SysExCommand.SET_MIXER_ALL_MODE.message((0,1,0,0)),e._ingress_token());mix.tick(now=2)
        self.cc(e,20,127);self.assertEqual(mix.writes,1)
        self.cc(e,20,0);self.cc(e,20,127);self.cc(e,20,0)
        self.assertTrue(source.par.Lowactive.eval());self.assertEqual(mix.writes,2)

    def test_shared_track_requests_and_follow_outputs_cannot_mutate_mix_or_plugin(self):
        e, mix, m, f, source, *_ = self.fixture(); self.enter(e, mix)
        before = copy.deepcopy(m.data)
        e._receive_midi(SysExCommand.SELECT_TRACK.message((0, 1)), e._ingress_token())
        self.assertEqual(mix.selected, 1); self.assertEqual(m.data, before)
        e._pending = b''; m.announce_tracks(); m.announce()
        self.assertEqual(e._pending, b'')
        f.gated = True; mix.tick(now=2)
        self.assertTrue(e._pending)  # unrelated PLUGIN gate doesn't suppress MIX

    def test_view_readback_and_send_name_requests_do_not_echo_track_selection(self):
        e, mix, *_ = self.fixture(); self.enter(e, mix)
        e._receive_midi(SysExCommand.SET_MIXER_SELECTED_MODE.message((0,)), e._ingress_token()); mix.tick(now=2)
        self.assertFalse(any(SysExCommand.identify(m) is SysExCommand.DAW_SELECT_TRACK for m in self.messages(e) if len(m) >= 8))
        e._pending = b''
        e._receive_midi(SysExCommand.REQUEST_SEND_TRACK_NAMES.message((6,)), e._ingress_token())
        self.assertEqual(self.messages(e), [list(SysExCommand.SEND_TRACK_NAMES.message((6, *([0] * (8 * 13)))))])
        e._receive_midi(SysExCommand.SET_MIXER_CHANNEL_MODE.message((0,)), e._ingress_token())
        self.assertIn(list(SysExCommand.REFRESH_MIX_MODE.message()), self.messages(e)); self.assertIsNone(mix.view)

    def test_unchanged_focus_text_is_renewed_bounded_and_stops_outside_mix(self):
        e, mix, _, _, source, *_ = self.fixture()
        self.enter(e, mix, (SysExCommand.SET_MIXER_SELECTED_MODE, (0,)))
        before = {name: p.eval() for name, p in source.par.items()}
        mix.tick(now=1.11)
        expected = ('Thresh 0.100', 'Gain 2.000', 'Add 0.000', 'Smooth 0.000')
        def captions():
            return [m for m in self.messages(e) if len(m) >= 10 and m[:7] == list(SysExCommand.PARAM_VALUES.message()[:7])]
        # API 2.23 expires text without renewed SHOW CONTROL VALUE, even when
        # the value is unchanged. Exercise the real extension's output queue.
        self.assertEqual([bytes(m[9:-1]).rstrip(b'\0').decode() for m in captions()], list(expected))
        self.assertFalse(any(len(m) == 3 and m[0] == 191 and (12 <= m[1] <= 19 or 44 <= m[1] <= 51) for m in self.messages(e)))
        pending = e._pending; mix.tick(now=1.12)
        self.assertEqual(e._pending, pending)  # keep the existing 10 Hz bound
        for now in (2, 3, 10, 100): mix.tick(now=now)
        self.assertEqual(len(captions()), 4)  # coalesce unsent renewals
        self.assertEqual(mix.writes, 0)
        self.assertEqual({name: p.eval() for name, p in source.par.items()}, before)
        e._receive_midi(SysExCommand.SET_PLUGIN_MODE.message(), e._ingress_token()); e._pending = b''
        mix.tick(now=101)
        self.assertEqual(captions(), [])

    def test_touching_unassigned_overview_slot_does_not_disable_other_items(self):
        e, mix, *_ = self.fixture(); self.enter(e, mix)
        self.cc(e, 59, 127); self.turn(e, 7, 16383); self.cc(e, 59, 0)
        self.assertTrue(mix.ready); self.assertEqual(mix.selected, 0)
        self.assertEqual(mix.writes, 0)

    def test_plugin_return_restores_metadata_only_after_actual_mode_message(self):
        e, mix, m, f, source, *_ = self.fixture(); self.enter(e, mix, (SysExCommand.SET_MIXER_SELECTED_MODE, (0,)))
        mix.tick(now=2); self.assertFalse(e._host.plugin)
        self.assertFalse(any(m[:7] == list(SysExCommand.NUM_DEVICES.message()[:7]) for m in self.messages(e)))
        token = e._ingress_token(); e._receive_midi(SysExCommand.SET_PLUGIN_MODE.message(), token)
        self.assertTrue(e._host.plugin); self.assertFalse(mix.active)
        self.assertTrue(any(m[:7] == list(SysExCommand.TRACK_DETAILS.message()[:7]) for m in self.messages(e)))
        self.turn(e, 0, 16383); self.assertEqual(mix.writes, 0)
        mix.tick(backlog=True); self.assertTrue(mix.returning)
        mix.tick(); self.assertFalse(mix.returning)
        test_comp_follow.FollowTests().ack(e)
        self.assertTrue(e._host.plugin)

    def test_old_connection_cannot_enter_mix_after_reconnect(self):
        e, mix, _, f, *_ = self.fixture(); old = e._ingress_token()
        f.session_boundary(); e._receive_midi(SysExCommand.SET_MIXER_ALL_MODE.message((0, 0, 0, 0)), old)
        self.assertFalse(mix.active)

    def test_func_retained_across_plugin_returns_directly_to_same_focus(self):
        e, mix, _, _, source, *_ = self.fixture()
        self.enter(e, mix)
        e._receive_midi(SysExCommand.SELECT_TRACK.message((0, 1)), e._ingress_token())
        e._receive_midi(SysExCommand.SET_MIXER_SELECTED_MODE.message((0,)), e._ingress_token()); mix.tick(now=2)
        before = {name: p.eval() for name, p in source.par.items()}
        e._receive_midi(SysExCommand.SET_PLUGIN_MODE.message(), e._ingress_token()); mix.tick(now=3)
        self.assertFalse(mix.active); self.assertIsNone(mix.view)
        # The retained FUNC reports Focus directly, without an All Tracks event.
        e._receive_midi(SysExCommand.SET_MIXER_SELECTED_MODE.message((0,)), e._ingress_token()); mix.tick(now=4)
        self.assertTrue(mix.active); self.assertTrue(mix.ready)
        self.assertEqual(mix.view, ('focus', 0)); self.assertEqual(mix.selected, 1)
        self.assertEqual(mix.addresses()[:4], [(1, key) for key in ('threshold', 'gain', 'add', 'smooth')])
        self.turn(e, 1, 16383)  # returning motor feedback isn't a fresh gesture
        self.assertEqual(mix.writes, 0)
        self.assertEqual({name: p.eval() for name, p in source.par.items()}, before)

    def test_valid_mix_can_connect_when_plugin_binding_is_unavailable(self):
        e, mix, *_ = self.fixture()
        e._host.enabled = False; e.Disconnect = Mock()
        oldop = e.ownerComp.op
        e.ownerComp.op = lambda name: SimpleNamespace(text='embedded MIDI owner') if name == 'midi_process' else oldop(name)
        e.ownerComp.par.Python = SimpleNamespace(eval=lambda: 'python3')
        e.ownerComp.par.Device = SimpleNamespace(eval=lambda: 'ROTO-CONTROL')
        with patch('RotoPythonExt.project', SimpleNamespace(folder='/tmp'), create=True), patch('RotoPythonExt.resolve_python', return_value='/usr/bin/python3'), patch('RotoPythonExt.subprocess.Popen') as spawn, patch('RotoPythonExt.os.set_blocking'):
            e.Connect()
            spawn.assert_called_once()
        e.ClearMixProfile()
        with self.assertRaises(ValueError): e.Connect()

    def test_invalid_selection_and_master_return_clear_feedback_and_never_write(self):
        malformed = (*SysExCommand.SET_MIXER_SELECTED_MODE.message()[:-1], 128, 247)
        for event in (SysExCommand.SELECT_TRACK.message((0, 7)), SysExCommand.SELECT_TRACK.message(), SysExCommand.SET_MIXER_ALL_MODE.message((1, 0, 0, 0)), SysExCommand.SET_MIXER_SELECTED_MODE.message((8,)), malformed):
            with self.subTest(event=event):
                e, mix, _, _, source, *_ = self.fixture(); self.enter(e, mix)
                e._receive_midi(event, e._ingress_token()); mix.tick(now=2)
                self.assertFalse(mix.ready)
                self.cc(e, 52, 127); self.turn(e, 0, 16383)
                self.assertEqual(source.par.Lowthresh.eval(), .1)
                meters = [m[2] for m in self.messages(e) if len(m) == 3 and 65 <= m[1] <= 80]
                self.assertTrue(meters); self.assertFalse(any(meters))

    def test_queue_keeps_frame_tail_and_session_then_latest_feedback(self):
        e, mix, *_ = self.fixture()
        tail = b'127]}\n'
        ping = (json.dumps({'midi': list(SysExCommand.DAW_PING_RESP.message((1,)))}) + '\n').encode()
        motor = (json.dumps({'midi': [191, 12, 127]}) + '\n').encode()
        self.assertEqual(discard(tail + ping + motor, business_output), tail + ping)
        self.assertEqual(discard(b'{"midi": [191,', business_output), b'{"midi": [191,')
        e._pending = tail + ping + motor
        self.enter(e, mix)
        self.assertTrue(mix.active)

    def test_real_tick_partial_line_backlog_cannot_activate_or_replay_previous_view(self):
        e, mix, _, _, source, *_ = self.fixture()
        child = Mock(); child.poll.return_value = None
        e._process = child; e._transport_ready = True; e._started_at = time.monotonic()
        e._trace_control_midi = Mock()
        def line(message): return (json.dumps({'midi': message}) + '\n').encode()
        tail = line((191, 44, 127)); split = len(tail) // 2
        packet = line(SysExCommand.SET_MIXER_ALL_MODE.message((0, 0, 0, 0)))
        packet += line((191, 52, 127)) + line((191, 12, 127)) * 255 + tail[:split]
        def tick(chunks):
            with patch('RotoPythonExt.os.read', side_effect=chunks), patch('RotoPythonExt.os.write', side_effect=lambda fd, data: len(data)):
                e.Tick()
        tick([packet, BlockingIOError]); self.assertFalse(mix.ready)
        tick([BlockingIOError]); self.assertFalse(mix.ready)
        tick([tail[split:], BlockingIOError]); self.assertTrue(mix.ready)
        self.assertEqual(mix.writes, 0); self.assertEqual(source.par.Lowthresh.eval(), .1)
        self.cc(e, 52, 0); self.cc(e, 52, 127); self.turn(e, 0, 16383)
        self.assertEqual(mix.writes, 1)

    def test_real_tick_uses_latest_selection_after_same_batch_view_changes(self):
        for selections in ((1,), (0, 1), (1, 0, 1)):
            with self.subTest(selections=selections):
                e, mix, _, _, source, *_ = self.fixture(); self.enter(e, mix)
                child = Mock(); child.poll.return_value = None
                e._process = child; e._transport_ready = True
                e._started_at = time.monotonic(); e._trace_control_midi = Mock()
                events = [SysExCommand.SET_MIXER_SELECTED_MODE.message((0,))]
                events += [SysExCommand.SELECT_TRACK.message((0, index)) for index in selections]
                events += [(191, 53, 127), (191, 13, 127), (191, 45, 127), (191, 53, 0)]
                packet = b''.join((json.dumps({'midi': event}) + '\n').encode() for event in events)
                with patch('RotoPythonExt.os.read', side_effect=[packet, BlockingIOError]), patch('RotoPythonExt.os.write', side_effect=lambda fd, data: len(data)):
                    e.Tick()
                self.assertTrue(mix.ready)
                self.assertEqual(mix.view, ('focus', 0))
                self.assertEqual(mix.selected, 1)
                self.assertEqual(mix.writes, 0)  # buffered gestures still require a fresh touch
                token = e._ingress_token()
                e._receive_midi(SysExCommand.SELECT_TRACK.message((0, 0)), (token[0] - 1, *token[1:]))
                self.assertEqual(mix.selected, 1)
                self.cc(e, 53, 127); self.turn(e, 1, 16383)
                self.assertEqual(source.par.Midgain.eval(), 7)
                self.assertEqual(source.par.Lowgain.eval(), 2)
                self.assertEqual(mix.writes, 1)

    def test_plugin_owner_failure_cannot_steal_mix_queue_or_block_mix_input(self):
        e, mix, m, f, source, *_ = self.fixture(); self.enter(e, mix)
        m.quarantined = True; f.paused = f.gated = True
        mix.tick(now=2); pending = e._pending
        e._discard_control_output(list(e._host.controls))
        e._discard_context_output()
        self.assertEqual(e._pending, pending)
        self.cc(e, 52, 127); self.turn(e, 0, 16383)
        self.assertEqual(source.par.Lowthresh.eval(), .6)

    def test_generic_export_sanitizes_mix_without_source_values_or_paths(self):
        from export_component import reset_mapping_storage, reset_registration
        e, mix, _, _, source, *_ = self.fixture()
        e.ownerComp.ext = SimpleNamespace(RotoPythonExt=e)
        old = e.ownerComp.op
        registration = SimpleNamespace(text='custom')
        e.ownerComp.op = lambda name: registration if name == 'registration' else old(name)
        reset_mapping_storage(e.ownerComp); reset_registration(e.ownerComp)
        self.assertIsNone(e.ownerComp.fetch('mix_profile')); self.assertIsNone(e._mix)
        self.assertEqual(source.par.Lowgain.eval(), 2)

    def test_cross_comp_scope_is_resolvable_after_save_and_reload(self):
        e, mix, _, _, source, *_ = self.fixture()
        scope = mix.scope
        e.ownerComp.path = '/other/controller'
        old_op = e.ownerComp.op
        e.ownerComp.op = lambda name: scope if name == '../../demo' else old_op(name)
        e.ConfigureMixAnalysis(scope, 'analysis')
        self.assertEqual(e.GetMixProfile()['scope'], '../../demo')
        mix.refresh_scope()
        self.assertEqual(e.GetMixProfile()['scope'], '../../demo')
        restored = MixRuntime(e)
        self.assertIs(restored.scope, scope)
        self.assertEqual(len(restored.targets), 10)
        self.assertEqual(restored.writes, 0)
        self.assertEqual(source.par.Lowgain.eval(), 2)

    def test_documented_custom_analyzer_example_controls_foreign_names_and_independent_level(self):
        from pathlib import Path
        e, mix, _, _, analysis, *_ = self.fixture()
        before = {n:p.eval() for n,p in analysis.par.items()}
        custom = SimpleNamespace(valid=True,isCOMP=True,id=1800,path='/demo/my_analyzer',par=Pars())
        for name,style,value in [('Triggerlimit','Float',.2),('Enabled','Toggle',True)]:
            p=BoundParameter(style);p.name=name;p.owner=custom;p.val=value;p.enable=True
            p.normMin=p.min=0;p.normMax=p.max=1;custom.par[name]=p
        class Level:
            valid=True;id=1801;path='/demo/my_analyzer/levels'
            def __getitem__(self,name):return Channel([.35]) if name=='band_energy' else None
        levels=Level()
        custom.op=lambda name:custom if name=='.' else levels if name=='levels' else None
        old=e.ownerComp.op
        e.ownerComp.op=lambda name:custom if name=='../demo/my_analyzer' else old(name)
        proxy=SimpleNamespace(SetMixProfile=e.SetMixProfile,GetMixState=e.GetMixState)
        doc=(Path(__file__).parents[1]/'docs/functions/mix_analysis.md').read_text()
        example=doc.split('```python\n',1)[1].split('```',1)[0]
        exec(example,{'op':lambda name:proxy if name=='roto_python' else custom if name=='my_analyzer' else None,
                      'print':lambda *args:None})
        self.assertEqual(mix.writes,0);self.assertEqual(mix.errors,{})
        self.enter(e,mix)
        self.cc(e,52,127);self.turn(e,0,8192);self.cc(e,52,0)
        self.assertAlmostEqual(custom.par.Triggerlimit.eval(),.6*8192/16383)
        self.cc(e,20,127);self.cc(e,20,0)
        self.assertFalse(custom.par.Enabled.eval());self.assertEqual(mix.writes,2)
        mix.tick(now=2)
        self.assertIn([191,65,44],self.messages(e))
        self.assertEqual({n:p.eval() for n,p in analysis.par.items()},before)

    def test_rms_and_scalar_feedback_have_explicit_separate_ranges(self):
        e, mix, _, _, _, channels, _ = self.fixture()
        channels['low'].vals = [.5, -.5]
        signal = Signal(mix.scope, dict(kind='chop', op='analysis/out1', channels=['low']))
        self.assertAlmostEqual(signal.sample('rms_dbfs')[0], -6.020599913)
        self.assertEqual(signal.sample('scalar'), [.5, .5])


if __name__ == '__main__': unittest.main()
