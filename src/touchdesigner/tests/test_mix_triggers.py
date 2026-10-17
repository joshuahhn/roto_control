"""Actual analysis pulse feedback, isolated from writable MIX targets."""
import tests  # Shared paths for direct unittest discovery.
import copy
import unittest
from mix_descriptor import validate
from mix_runtime import MixRuntime
from protocol import SysExCommand, text13
import test_mix


class MixTriggerTests(unittest.TestCase):
    def fixture(self, enabled=True):
        helpers=test_mix.MixTests()
        e,mix,manager,follower,source,channels,operators=helpers.fixture()
        source.par.Kickactive.val=enabled
        e.ConfigureMixAnalysis(mix.scope,'analysis',('Kick',))
        helpers.enter(e,mix);helpers.focus(e,mix)
        return helpers,e,mix,source,channels,operators

    def captions(self, e, text):
        return list(SysExCommand.PARAM_VALUES.message((0,4,*text13(text)))) in test_mix.MixTests().messages(e)

    def test_kick_controls_meter_and_trigger_are_independent(self):
        helpers,e,mix,source,channels,_=self.fixture()
        item=e.GetMixProfile()['descriptor']['items'][0]
        self.assertEqual(set(item['controls']),{'threshold','active'})
        self.assertEqual(mix.addresses(),[(0,'threshold')]+[None]*7)
        self.assertEqual(item['meter']['range'],[0,1])
        self.assertEqual(mix.triggers[0].state,'idle')  # level .8 is above threshold .26
        self.assertIn([191,65,102],helpers.messages(e))
        self.assertTrue(self.captions(e,'Trig 0'))
        before={name:p.eval() for name,p in source.par.items()}
        helpers.cc(e,56,127);helpers.turn(e,4,16383);helpers.cc(e,56,0)
        self.assertEqual({name:p.eval() for name,p in source.par.items()},before)
        self.assertEqual(mix.writes,0)

    def test_observed_pulse_between_display_updates_is_held_then_expires(self):
        _,e,mix,_,channels,_=self.fixture()
        e._pending=b''
        channels['kick'].vals=[1];mix.tick(now=2.03)
        channels['kick'].vals=[0];mix.tick(now=2.04)
        self.assertEqual(mix.triggers[0].state,'high')
        mix.tick(now=2.12)
        self.assertTrue(self.captions(e,'Trig 1'))
        mix.tick(now=2.25)
        self.assertTrue(self.captions(e,'Trig 0'))
        self.assertEqual(mix.writes,0)

    def test_disabled_is_distinct_from_idle_and_clears_the_hold(self):
        _,e,mix,source,channels,_=self.fixture()
        channels['kick'].vals=[1];mix.tick(now=2.11)
        source.par.Kickactive.val=False;mix.tick(now=2.22)
        self.assertTrue(self.captions(e,'Trig Off'))
        self.assertEqual(mix.triggers[0].state,'disabled')
        channels['kick'].vals=[0];source.par.Kickactive.val=True;mix.tick(now=2.33)
        self.assertTrue(self.captions(e,'Trig 0'))

    def test_steady_readonly_trigger_text_is_renewed_and_coalesced(self):
        helpers,e,mix,_,_,_=self.fixture(False)
        e._pending=b'';mix.tick(now=2.2)
        self.assertTrue(self.captions(e,'Trig Off'))
        e._pending=b'';mix.tick(now=2.4)
        self.assertTrue(self.captions(e,'Trig Off'))
        mix.tick(now=2.6)
        texts=[m for m in helpers.messages(e) if m[:9]==list(SysExCommand.PARAM_VALUES.message((0,4)))[:9]]
        self.assertEqual(len(texts),1)

    def test_bad_pulse_sample_clears_stale_high_without_disabling_controls(self):
        for bad in ([],[float('nan')],[float('inf')]):
            with self.subTest(sample=bad):
                helpers,e,mix,source,channels,_=self.fixture()
                channels['kick'].vals=[1];mix.tick(now=2.11)
                channels['kick'].vals=bad;mix.tick(now=2.22)
                self.assertTrue(self.captions(e,'Trig ?'))
                self.assertEqual(mix.triggers[0].state,'unavailable')
                self.assertTrue(mix.ready)
                self.assertIn('threshold',[key for _,key in mix.targets])
                channels['kick'].vals=[0];mix.tick(now=2.33)
                self.assertTrue(self.captions(e,'Trig 0'))
                self.assertEqual(source.par.Kickthresh.eval(),.26)

    def test_replaced_signal_or_missing_channel_reports_unavailable(self):
        for change in ('replace','remove'):
            with self.subTest(change=change):
                _,e,mix,_,channels,operators=self.fixture()
                channels['kick'].vals=[1];mix.tick(now=2.11)
                if change=='replace':
                    replacement=copy.copy(operators['analysis/out1']);replacement.id=999
                    operators['analysis/out1']=replacement
                else:
                    channels.pop('kick')
                mix.tick(now=2.22)
                self.assertTrue(self.captions(e,'Trig ?'))
                self.assertTrue(mix.state()['triggers'][0]['error'])
                self.assertEqual(mix.writes,0)

    def test_optional_enabled_flag_and_missing_feedback_are_explicit(self):
        _,e,mix,source,channels,_=self.fixture(False)
        profile=e.GetMixProfile()['descriptor']
        del profile['items'][0]['trigger']['enabled']
        e.SetMixProfile(mix.scope,profile)
        channels['kick'].vals=[1]
        mix.tick(now=3)
        self.assertEqual(mix.triggers[0].state,'high')
        profile['items'][0]['trigger']['source']['op']='missing'
        e.SetMixProfile(mix.scope,profile)
        mix.tick(now=4)
        self.assertEqual(mix.triggers[0].state,'unavailable')
        self.assertFalse(source.par.Kickactive.eval())

    def test_trigger_hold_resets_on_mode_view_reload_clear_and_backlog_is_not_replayed(self):
        helpers,e,mix,_,channels,_=self.fixture()
        channels['kick'].vals=[1];mix.tick(now=2.11)
        channels['kick'].vals=[0]
        e._receive_midi(SysExCommand.SET_PLUGIN_MODE.message((0,)),e._ingress_token())
        self.assertEqual(mix.triggers[0].state,'unknown')
        helpers.enter(e,mix);helpers.focus(e,mix)
        self.assertEqual(mix.triggers[0].state,'idle')
        channels['kick'].vals=[1];mix.tick(backlog=True,now=3)
        channels['kick'].vals=[0];mix.tick(now=3.1)
        self.assertEqual(mix.triggers[0].state,'idle')
        restored=MixRuntime(e)
        self.assertEqual(restored.triggers[0].state,'unknown')
        e.ClearMixProfile()
        self.assertEqual(e.GetMixState()['triggers'],[])

    def test_trigger_schema_and_flag_type_do_not_accept_other_styles_or_bad_holds(self):
        _,e,mix,_,_,_=self.fixture()
        before=e.GetMixProfile()
        for hold in (-1,1001,True,1.5):
            with self.subTest(hold=hold):
                profile=copy.deepcopy(before['descriptor']);profile['items'][0]['trigger']['hold_ms']=hold
                with self.assertRaises(ValueError):e.SetMixProfile(mix.scope,profile)
                self.assertEqual(e.GetMixProfile(),before)
        profile=copy.deepcopy(before['descriptor'])
        profile['style']='layers';profile['items'][0]['input']='analysis'
        profile['items'][0]['controls']={};profile['items'][0]['primary']=None
        profile['items'][0]['meter'].pop('focus_reference',None)
        profile['items'][0]['meter'].pop('overview_reference',None)
        with self.assertRaisesRegex(ValueError,'analysis items'):validate(profile)
        profile=copy.deepcopy(before['descriptor'])
        profile['items'][0]['trigger']['enabled']['parameter']='Kickthresh'
        e.SetMixProfile(mix.scope,profile)
        self.assertEqual(mix.triggers[0].state,'unavailable')
        self.assertIn('Toggle',mix.triggers[0].error)


if __name__=='__main__':unittest.main()
