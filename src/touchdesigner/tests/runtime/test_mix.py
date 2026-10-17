"""MIX business behavior through the real extension, independent of PLUGIN."""
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
from protocol import sysex, digest


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
        for index in range(2):
            for suffix,value,high in (('opacity',.25+.5*index,1),('bright',1,2),('black',0,2),('gamma',1,3)):
                p=BoundParameter();p.name='lay'+str(index)+suffix;p.owner=source;p.enable=True
                p.normMin=p.min=0;p.normMax=p.max=high;p.val=value;source.par[p.name]=p
        operators['layer_mix']=source
        for image in images:operators[image.path.rsplit('/',1)[1]]=image
        mix.scope.relativePath=lambda n:n.path.removeprefix('/demo/')
        return e,mix,source,images,analysis

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
        self.enter(e,mix);e._receive_midi(sysex(10,9,(0,1)),e._ingress_token())
        e._receive_midi(sysex(12,2,(0,)),e._ingress_token());mix.tick(now=2)
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
        for band in ('Low', 'Mid'):
            for suffix, value, low, high in (
                    ('thresh', .1, 0, .6), ('gain', 2, 0, 7), ('add', 0, -1, 1),
                    ('smooth', 0, 0, 1), ('active', 1, 0, 1)):
                p = BoundParameter('Toggle' if suffix == 'active' else 'Float')
                p.name = band + suffix; p.owner = source; p.enable = True
                p.normMin = p.min = low; p.normMax = p.max = high; p.val = value
                source.par[p.name] = p
        channels = {'low': Channel([.25]), 'mid': Channel([.75])}
        class Chop:
            valid = True; id = 801; path = '/demo/analysis/out1'
            def __getitem__(self, name): return channels.get(name)
        chop = Chop()
        operators = {'analysis': source, 'analysis/out1': chop}
        scope = SimpleNamespace(valid=True, isCOMP=True, id=799, path='/demo', op=operators.get)
        oldop = e.ownerComp.op
        e.ownerComp.op = lambda name: scope if name == '../demo' else oldop(name)
        e.ownerComp.relativePath = lambda op: '../demo'
        mix = MixRuntime(e); e._mix = mix
        mix.configure(scope, analysis_profile('analysis'))
        e._pending = b''
        return e, mix, m, f, source, channels, operators

    def enter(self, e, mix, view=(1, (0, 0, 0, 0))):
        e._receive_midi(sysex(12, *view), e._ingress_token())
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
        self.cc(e, 53, 127); self.turn(e, 1, 16383)
        self.assertEqual(mix.selected, 1); self.assertEqual(source.par.Midthresh.eval(), .1)
        e._receive_midi(sysex(12, 2, (0,)), e._ingress_token()); mix.tick(now=2)
        self.turn(e, 1, 16383)  # old touch cannot write new Focus Gain
        self.assertEqual(source.par.Midgain.eval(), 2)
        self.cc(e, 53, 0); self.cc(e, 53, 127); self.turn(e, 1, 8192)
        self.assertAlmostEqual(source.par.Midgain.eval(), 7 * 8192 / 16383)
        self.assertEqual(source.par.Lowgain.eval(), 2); self.assertEqual(m.data, registry)
        self.assertFalse(e._host.plugin); self.assertFalse(e._host.mapped)

    def test_fresh_touch_required_echo_buttons_and_plugin_ack_cannot_write(self):
        e, mix, m, f, source, *_ = self.fixture(); self.enter(e, mix)
        for raw in (0, 16383): self.turn(e, 0, raw)
        for value in (127, 0, 127): self.cc(e, 27, value)  # unassigned MIX button
        target = next(iter(e._host.controls.values()))
        e._receive_midi(sysex(11, 11, (target.index >> 7, target.index & 127, *digest(target.target_id, 6), 0, 0, 0)))
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
        old = e._ingress_token(); e._receive_midi(sysex(12, 2, (0,)), old)
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
        e._receive_midi(sysex(12, 1, (0, 1, 0, 0)), old); mix.tick(now=2)
        self.cc(e, 20, 127, old); self.cc(e, 20, 127)
        self.assertEqual(mix.writes, 0)
        self.cc(e, 20, 0); self.cc(e, 20, 127)
        self.assertFalse(source.par.Lowactive.eval()); self.assertEqual(mix.writes, 1)
        for event in (sysex(12, 1, (0, 0, 1, 0)), sysex(12, 1, (0, 0, 2, 0)), sysex(12, 2, (0,))):
            e._receive_midi(event, e._ingress_token()); mix.tick(now=3)
            self.cc(e, 20, 0); self.cc(e, 20, 127); self.cc(e, 20, 0)
            self.assertEqual(mix.writes, 1)
        e._receive_midi(sysex(12, 1, (0, 0, 0, 0)), e._ingress_token()); mix.tick(now=4)
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
        e._receive_midi(sysex(12,1,(0,1,0,0)),e._ingress_token());mix.tick(now=2)
        self.cc(e,20,127);self.assertEqual(mix.writes,1)
        self.cc(e,20,0);self.cc(e,20,127);self.cc(e,20,0)
        self.assertTrue(source.par.Lowactive.eval());self.assertEqual(mix.writes,2)

    def test_shared_track_requests_and_follow_outputs_cannot_mutate_mix_or_plugin(self):
        e, mix, m, f, source, *_ = self.fixture(); self.enter(e, mix)
        before = copy.deepcopy(m.data)
        e._receive_midi(sysex(10, 9, (0, 1)), e._ingress_token())
        self.assertEqual(mix.selected, 1); self.assertEqual(m.data, before)
        e._pending = b''; m.announce_tracks(); m.announce()
        self.assertEqual(e._pending, b'')
        f.gated = True; mix.tick(now=2)
        self.assertTrue(e._pending)  # unrelated PLUGIN gate doesn't suppress MIX

    def test_view_readback_and_send_name_requests_do_not_echo_track_selection(self):
        e, mix, *_ = self.fixture(); self.enter(e, mix)
        e._receive_midi(sysex(12, 2, (0,)), e._ingress_token()); mix.tick(now=2)
        self.assertFalse(any(m[5:7] == [12, 4] for m in self.messages(e) if len(m) >= 8))
        e._pending = b''
        e._receive_midi(sysex(12, 7, (6,)), e._ingress_token())
        self.assertEqual(self.messages(e), [list(sysex(12, 8, (6, *([0] * (8 * 13)))))])
        e._receive_midi(sysex(12, 5, (0,)), e._ingress_token())
        self.assertIn(list(sysex(12, 9)), self.messages(e)); self.assertIsNone(mix.view)

    def test_unchanged_focus_text_is_renewed_bounded_and_stops_outside_mix(self):
        e, mix, _, _, source, *_ = self.fixture()
        self.enter(e, mix, (2, (0,)))
        before = {name: p.eval() for name, p in source.par.items()}
        mix.tick(now=1.11)
        expected = ('Thresh 0.100', 'Gain 2.000', 'Add 0.000', 'Smooth 0.000')
        def captions():
            return [m for m in self.messages(e) if len(m) >= 10 and m[:7] == list(sysex(10, 24)[:7])]
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
        e._receive_midi(sysex(11, 1), e._ingress_token()); e._pending = b''
        mix.tick(now=101)
        self.assertEqual(captions(), [])

    def test_touching_unassigned_overview_slot_does_not_disable_other_items(self):
        e, mix, *_ = self.fixture(); self.enter(e, mix)
        self.cc(e, 59, 127); self.turn(e, 7, 16383); self.cc(e, 59, 0)
        self.assertTrue(mix.ready); self.assertEqual(mix.selected, 0)
        self.assertEqual(mix.writes, 0)

    def test_plugin_return_restores_metadata_only_after_actual_mode_message(self):
        e, mix, m, f, source, *_ = self.fixture(); self.enter(e, mix, (2, (0,)))
        mix.tick(now=2); self.assertFalse(e._host.plugin)
        self.assertFalse(any(m[:7] == list(sysex(11, 2)[:7]) for m in self.messages(e)))
        token = e._ingress_token(); e._receive_midi(sysex(11, 1), token)
        self.assertTrue(e._host.plugin); self.assertFalse(mix.active)
        self.assertTrue(any(m[:7] == list(sysex(10, 7)[:7]) for m in self.messages(e)))
        self.turn(e, 0, 16383); self.assertEqual(mix.writes, 0)
        mix.tick(backlog=True); self.assertTrue(mix.returning)
        mix.tick(); self.assertFalse(mix.returning)
        test_comp_follow.FollowTests().ack(e)
        self.assertTrue(e._host.plugin)

    def test_old_connection_cannot_enter_mix_after_reconnect(self):
        e, mix, _, f, *_ = self.fixture(); old = e._ingress_token()
        f.session_boundary(); e._receive_midi(sysex(12, 1, (0, 0, 0, 0)), old)
        self.assertFalse(mix.active)

    def test_func_retained_across_plugin_returns_directly_to_same_focus(self):
        e, mix, _, _, source, *_ = self.fixture()
        self.enter(e, mix)
        e._receive_midi(sysex(10, 9, (0, 1)), e._ingress_token())
        e._receive_midi(sysex(12, 2, (0,)), e._ingress_token()); mix.tick(now=2)
        before = {name: p.eval() for name, p in source.par.items()}
        e._receive_midi(sysex(11, 1), e._ingress_token()); mix.tick(now=3)
        self.assertFalse(mix.active); self.assertIsNone(mix.view)
        # The retained FUNC reports Focus directly, without an All Tracks event.
        e._receive_midi(sysex(12, 2, (0,)), e._ingress_token()); mix.tick(now=4)
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
        malformed = (*sysex(12, 2)[:-1], 128, 247)
        for event in (sysex(10, 9, (0, 7)), sysex(10, 9), sysex(12, 1, (1, 0, 0, 0)), sysex(12, 2, (8,)), malformed):
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
        ping = (json.dumps({'midi': list(sysex(10, 3, (1,)))}) + '\n').encode()
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
        packet = line(sysex(12, 1, (0, 0, 0, 0)))
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

    def test_rms_and_scalar_feedback_have_explicit_separate_ranges(self):
        e, mix, _, _, _, channels, _ = self.fixture()
        channels['low'].vals = [.5, -.5]
        signal = Signal(mix.scope, dict(kind='chop', op='analysis/out1', channels=['low']))
        self.assertAlmostEqual(signal.sample('rms_dbfs')[0], -6.020599913)
        self.assertEqual(signal.sample('scalar'), [.5, .5])


if __name__ == '__main__': unittest.main()
