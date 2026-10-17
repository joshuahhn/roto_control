"""Each view compares a declared level with the real threshold in its units."""
import copy
import json
import unittest
from mix_runtime import MixRuntime
import setup
import test_mix
import test_mix_assignments


class MixMeterReferenceTests(unittest.TestCase):
    def fixture(self):
        helper=test_mix.MixTests()
        e,mix,_,_,source,channels,operators=helper.fixture()
        e.ConfigureMixAnalysis(mix.scope,'analysis',('Kick',))
        helper.enter(e,mix);helper.focus(e,mix)
        return helper,e,mix,source,channels,operators

    def pair(self,helper,e,lane=0):
        messages=helper.messages(e)
        return [next(m[2] for m in reversed(messages) if m[:2]==[191,cc]) for cc in (65+2*lane,66+2*lane)]

    def test_kick_focus_outputs_lower_level_and_upper_threshold_without_writes(self):
        helper,e,mix,source,_,_=self.fixture()
        self.assertEqual(self.pair(helper,e),[102,33])  # .8 level / .26 threshold over 0..1
        self.assertFalse(source.par.Kickactive.eval())
        self.assertEqual(mix.triggers[0].state,'disabled')
        self.assertEqual(mix.writes,0)

    def test_hardware_and_software_threshold_updates_move_only_reference_not_detection(self):
        helper,e,mix,source,_,_=self.fixture()
        helper.cc(e,52,127);helper.turn(e,0,8192);helper.cc(e,52,0)
        mix.tick(now=3)
        self.assertEqual(self.pair(helper,e),[102,38])
        self.assertAlmostEqual(source.par.Kickthresh.eval(),.6*8192/16383)
        source.par.Kickthresh.val=.5;mix.tick(now=4)
        self.assertEqual(self.pair(helper,e),[102,64])
        self.assertEqual(mix.writes,1)
        self.assertFalse(source.par.Kickactive.eval())
        self.assertEqual(mix.triggers[0].state,'disabled')

    def test_overview_uses_each_detector_threshold_and_preserves_nonreference_band(self):
        helper,e,mix,source,_,_=self.fixture()
        e.ConfigureMixAnalysis(mix.scope,'analysis',('Kick','Snare','Rhythm','Low'))
        helper.enter(e,mix);mix.tick(now=3)
        self.assertEqual(self.pair(helper,e),[102,33])
        self.assertEqual(self.pair(helper,e,1),[51,33])
        self.assertEqual(self.pair(helper,e,2),[89,62])
        self.assertEqual(self.pair(helper,e,3),[32,32])
        helper.focus(e,mix,2)
        self.assertEqual(self.pair(helper,e),[89,62])
        helper.enter(e,mix);source.par.Snarethresh.val=.5;mix.tick(now=4)
        self.assertEqual(self.pair(helper,e,1),[51,64])
        self.assertEqual(self.pair(helper,e,2),[89,62])
        helper.focus(e,mix,3)
        self.assertEqual(self.pair(helper,e),[32,32])
        self.assertEqual(mix.writes,0)

    def test_saved_focus_only_reference_does_not_change_overview(self):
        helper,e,mix,_,_,_=self.fixture()
        profile=e.GetMixProfile()['descriptor']
        profile['items'][0]['meter'].pop('overview_reference')
        e.SetMixProfile(mix.scope,profile)
        restored=MixRuntime(e);e._mix=restored
        helper.enter(e,restored);restored.tick(now=3)
        self.assertEqual(self.pair(helper,e),[102,102])
        helper.focus(e,restored)
        self.assertEqual(self.pair(helper,e),[102,33])
        self.assertEqual(restored.profile,profile)

    def test_legacy_profile_without_reference_reload_stays_unchanged(self):
        helper,e,mix,source,_,_=self.fixture()
        profile=e.GetMixProfile()['descriptor']
        profile['items'][0]['meter'].pop('focus_reference',None)
        profile['items'][0]['meter'].pop('overview_reference',None)
        e.SetMixProfile(mix.scope,profile)
        restored=MixRuntime(e);e._mix=restored
        helper.enter(e,restored);helper.focus(e,restored)
        self.assertEqual(restored.profile,profile)
        self.assertEqual(self.pair(helper,e),[102,102])
        self.assertEqual(restored.writes,0)
        self.assertEqual(source.par.Kickthresh.eval(),.26)

    def test_reference_requires_analysis_mono_scalar_and_existing_float_threshold(self):
        helper,e,mix,_,_,_=self.fixture()
        original=e.GetMixProfile()
        for reference in ('overview_reference','focus_reference'):
            for kind in ('key','missing_control','toggle','stereo','rms','layers'):
                with self.subTest(reference=reference,kind=kind):
                    profile=copy.deepcopy(original['descriptor']);item=profile['items'][0]
                    item['meter'].pop('focus_reference',None);item['meter'].pop('overview_reference',None)
                    item['meter'][reference]='threshold'
                    if kind=='key':item['meter'][reference]='gain'
                    elif kind=='missing_control':del item['controls']['threshold'];item['primary']=None
                    elif kind=='toggle':item['controls']['threshold']['kind']='toggle'
                    elif kind=='stereo':item['meter']['source']['channels']=['low','high']
                    elif kind=='rms':item['meter']['measure']='rms_dbfs'
                    else:profile['style']='layers';item['input']='analysis';item.pop('trigger')
                    with self.assertRaises(ValueError):e.SetMixProfile(mix.scope,profile)
                    self.assertEqual(e.GetMixProfile(),original)

    def test_reference_coalesces_to_latest_value_and_preserves_inflight_tail(self):
        _,e,mix,source,_,_=self.fixture()
        tail=b', 66, 1]}\n';e._pending=tail
        source.par.Kickthresh.val=.2;mix.tick(now=3)
        source.par.Kickthresh.val=.4;mix.tick(now=3.2)
        before=e._pending;source.par.Kickthresh.val=.6;mix.tick(backlog=True,now=3.4)
        self.assertEqual(e._pending,before)
        mix.tick(now=3.6)
        self.assertTrue(e._pending.startswith(tail))
        meters=[json.loads(l)['midi'] for l in e._pending[len(tail):].splitlines()]
        meters=[m for m in meters if len(m)==3 and m[0]==191 and 65<=m[1]<=80]
        self.assertEqual(len(meters),16)
        self.assertEqual(meters[:2],[[191,65,102],[191,66,76]])
        self.assertTrue(all(m[2]==0 for m in meters[2:]))
        self.assertEqual(mix.writes,0)

    def test_missing_level_clears_both_bars_without_stale_reference(self):
        helper,e,mix,_,_,operators=self.fixture()
        operators['analysis/math2'].data.pop('low')
        mix.tick(now=3)
        self.assertEqual(self.pair(helper,e),[0,0])
        self.assertEqual(mix.writes,0)

    def test_reference_uses_actual_threshold_outside_a_narrower_control_range(self):
        helper,e,mix,source,_,_=self.fixture()
        profile=e.GetMixProfile()['descriptor']
        profile['items'][0]['controls']['threshold']['range']=[0,.4]
        source.par.Kickthresh.val=.5
        e.SetMixProfile(mix.scope,profile);helper.focus(e,mix)
        self.assertEqual(self.pair(helper,e),[102,64])
        self.assertEqual(source.par.Kickthresh.eval(),.5)
        self.assertEqual(mix.writes,0)

    def test_changed_threshold_contract_discards_stale_reference_then_clears_bars(self):
        helper,e,mix,source,_,_=self.fixture()
        source.par.Kickthresh.normMax=.5
        mix.tick(now=3);mix.tick(now=3.2)
        self.assertEqual(self.pair(helper,e),[0,0])
        self.assertIn((0,'threshold'),mix.errors)
        self.assertEqual(mix.writes,0)

    def test_custom_slot_explicit_opt_in_uses_its_own_threshold(self):
        ui=test_mix_assignments.MixAssignmentsTests()
        e,mix,c,source,custom,feedback,_=ui.fixture()
        ui.assign(c,custom,feedback)
        self.assertFalse(c.par.Mixslot7compare.eval())
        c.par.Mixslot7compare.val=True;setup.apply_mix_ui(c)
        self.assertEqual(e.GetMixProfile()['descriptor']['items'][6]['meter']['focus_reference'],'threshold')
        self.assertEqual(e.GetMixProfile()['descriptor']['items'][6]['meter']['overview_reference'],'threshold')
        helper=test_mix.MixTests();helper.enter(e,mix);mix.tick(now=3)
        self.assertEqual(self.pair(helper,e,6),[89,38])
        helper.focus(e,mix,6)
        self.assertEqual(self.pair(helper,e),[89,38])
        self.assertEqual(custom.par.Limit.eval(),.3)
        self.assertEqual(mix.writes,0)
        saved=e.GetMixProfile();c.par.Mixslot7channels.val='energy pulse'
        with self.assertRaises(ValueError):setup.apply_mix_ui(c)
        self.assertEqual(e.GetMixProfile(),saved)
        setup.reset_mix_ui(c);self.assertFalse(c.par.Mixslot7compare.eval())


if __name__=='__main__':unittest.main()
