"""Six real analyzer items plus explicit independent custom feedback/targets."""
from types import SimpleNamespace
import unittest
from test_bound_parameter import BoundParameter
from mix_runtime import MixRuntime
from protocol import sysex, text13
import setup
import test_mix
import test_mix_ui


class MixAssignmentsTests(unittest.TestCase):
    def fixture(self):
        e,mix,c,source=test_mix_ui.MixUiTests().fixture()
        custom=SimpleNamespace(valid=True,isCOMP=True,id=1900,path='/demo/other_analyzer',par=test_mix.Pars())
        for name,kind,value in (('Limit','Float',.3),('Enabled','Toggle',True),('Boost','Float',.4)):
            p=BoundParameter(kind);p.name=name;p.owner=custom;p.enable=True
            p.normMin=p.min=0;p.normMax=p.max=1;p.val=value;custom.par[name]=p
        channels={'energy':test_mix.Channel([.7]),'pulse':test_mix.Channel([0])}
        class Feedback:
            valid=True;isCHOP=True;id=1901;path='/demo/other_analyzer/levels'
            def __getitem__(self,name):return channels.get(name)
        feedback=Feedback()
        old=mix.scope.op
        mix.scope.op=lambda name: custom if name=='other_analyzer' else feedback if name=='other_analyzer/levels' else old(name)
        return e,mix,c,source,custom,feedback,channels

    def assign(self,c,custom,feedback,slot=7):
        for suffix,value in dict(name='My band',source=custom,primary='threshold',threshold='Limit',
                active='Enabled',meter=feedback,channels='energy',stage='custom processed energy',
                trigger=feedback,pulse='pulse').items():
            getattr(c.par,'Mixslot'+str(slot)+suffix).val=value

    def test_six_items_use_native_ranges_separate_levels_and_actual_pulses(self):
        helper=test_mix.MixTests()
        e,mix,_,_,source,channels,_=helper.fixture()
        e.ConfigureMixAnalysis(mix.scope,'analysis',('Low','Mid','High','Kick','Snare','Rhythm'))
        self.assertEqual(len(mix.targets),21)
        self.assertEqual(len(mix.meters),6)
        self.assertEqual(len(mix.triggers),3)
        self.assertEqual(mix.targets[5,'threshold'].binding.minimum,10)
        self.assertEqual(mix.targets[5,'threshold'].binding.maximum,90)
        helper.enter(e,mix)
        helper.cc(e,57,127);helper.cc(e,57,0);mix.tick(now=1.5)
        helper.cc(e,57,127);helper.turn(e,5,8192);helper.cc(e,57,0)
        self.assertAlmostEqual(source.par.Rythmthresh.eval(),10+80*8192/16383)
        self.assertEqual(source.par.Snarethresh.eval(),.26)
        helper.cc(e,25,127);helper.cc(e,25,127);helper.cc(e,25,0)
        self.assertTrue(source.par.Rythmactive.eval())
        helper.focus(e,mix,5)
        self.assertIn([191,65,89],helper.messages(e))  # actual score 70 / 100
        self.assertEqual(mix.triggers[5].state,'idle')
        channels['rythm'].vals=[1];mix.tick(now=2.11)
        self.assertEqual(mix.triggers[5].state,'high')
        self.assertEqual(mix.addresses(),[(5,'threshold')]+[None]*7)
        self.assertEqual(mix.writes,2)

    def test_rhythm_overview_and_focus_keep_three_decimal_value_on_wire(self):
        helper=test_mix.MixTests()
        e,mix,_,_,source,*_=helper.fixture()
        source.par.Rythmthresh.val=49.4591
        e.ConfigureMixAnalysis(mix.scope,'analysis',('Low','Rhythm'))
        helper.enter(e,mix);mix.tick(now=1.2)
        self.assertIn(list(sysex(10,24,(0,1,*text13('Thres 49.459')))),helper.messages(e))
        e._pending=b'';helper.focus(e,mix,1)
        self.assertIn(list(sysex(10,24,(0,0,*text13('Thres 49.459')))),helper.messages(e))
        self.assertEqual(source.par.Rythmthresh.eval(),49.4591)
        self.assertEqual(mix.writes,0)

    def test_two_custom_slots_keep_positions_targets_feedback_and_saved_draft_independent(self):
        e,mix,c,source,custom,feedback,channels=self.fixture()
        c.par.Mixanalysisbands.val=setup.MIX_ANALYSIS_DEFAULT
        self.assign(c,custom,feedback)
        self.assign(c,custom,feedback,8)
        c.par.Mixslot8name.val='Other band'
        c.par.Mixslot8threshold.val='Boost'
        original={n:p.eval() for n,p in source.par.items()}
        setup.apply_mix_ui(c)
        profile=e.GetMixProfile()
        self.assertEqual([i['id'] for i in profile['descriptor']['items']],
                         ['low','mid','high','kick','snare','rhythm','custom.7','custom.8'])
        self.assertEqual(len(mix.targets),25)
        self.assertEqual({n:p.eval() for n,p in source.par.items()},original)
        self.assertEqual(mix.writes,0)
        self.assertIsNone(e._process)
        c.par.Mixslot7name.val='Unapplied rename'
        setup.install_mix_ui(c)
        self.assertEqual(e.GetMixProfile(),profile)
        self.assertEqual(c.par.Mixslot7name.eval(),'Unapplied rename')
        restored=MixRuntime(e)
        self.assertEqual(restored.profile,profile['descriptor'])
        self.assertEqual(restored.writes,0)
        helper=test_mix.MixTests();helper.enter(e,mix);helper.focus(e,mix,6)
        helper.cc(e,52,127);helper.turn(e,0,8192);helper.cc(e,52,0)
        self.assertAlmostEqual(custom.par.Limit.eval(),8192/16383)
        self.assertEqual(custom.par.Boost.eval(),.4)
        self.assertEqual({n:p.eval() for n,p in source.par.items()},original)
        channels['pulse'].vals=[1];mix.tick(now=2.11)
        self.assertEqual(mix.triggers[6].state,'high')

    def test_snare_is_independent_of_kick_and_other_items_when_reordered(self):
        helper=test_mix.MixTests()
        e,mix,_,_,source,channels,_=helper.fixture()
        e.ConfigureMixAnalysis(mix.scope,'analysis',('Snare','Kick'))
        helper.enter(e,mix)
        helper.cc(e,20,127);helper.cc(e,20,0)
        self.assertTrue(source.par.Snareactive.eval())
        self.assertFalse(source.par.Kickactive.eval())
        helper.focus(e,mix)
        helper.cc(e,52,127);helper.turn(e,0,8192);helper.cc(e,52,0)
        self.assertAlmostEqual(source.par.Snarethresh.eval(),.6*8192/16383)
        self.assertEqual(source.par.Kickthresh.eval(),.26)
        channels['snare'].vals=[1];mix.tick(now=2.11)
        self.assertEqual(mix.triggers[0].state,'high')
        self.assertEqual(mix.triggers[1].state,'disabled')
        self.assertEqual(mix.writes,2)

    def test_readonly_slot8_without_slot7_does_not_shift_or_create_targets(self):
        e,mix,c,_,custom,feedback,_=self.fixture()
        for suffix,value in dict(name='Centroid',source=custom,meter=feedback,channels='energy',stage='centroid normalized').items():
            getattr(c.par,'Mixslot8'+suffix).val=value
        setup.apply_mix_ui(c)
        items=e.GetMixProfile()['descriptor']['items']
        self.assertEqual(len(items),8)
        self.assertEqual(items[6]['controls'],{})
        self.assertEqual(items[7]['id'],'custom.8')
        self.assertIsNone(items[7]['primary'])
        helper=test_mix.MixTests();helper.enter(e,mix);helper.focus(e,mix,7)
        self.assertEqual(mix.addresses(),[None]*8)
        helper.cc(e,52,127);helper.turn(e,0,16383);helper.cc(e,52,0)
        self.assertEqual(mix.writes,0)
        self.assertIn([191,65,89],helper.messages(e))

    def test_invalid_custom_assignments_preserve_previous_profile_and_values(self):
        for suffix,value in (('source',None),('threshold','Missing'),('threshold','Enabled'),
                ('channels','missing'),('channels','energy pulse third'),('maximum',0),
                ('stage',''),('pulse','missing'),('primary','gain')):
            with self.subTest(suffix=suffix,value=value):
                e,mix,c,source,custom,feedback,_=self.fixture()
                before=e.GetMixProfile();self.assign(c,custom,feedback)
                getattr(c.par,'Mixslot7'+suffix).val=value
                with self.assertRaises((ValueError,TypeError)):setup.apply_mix_ui(c)
                self.assertEqual(e.GetMixProfile(),before)
                self.assertEqual(mix.writes,0)
                self.assertEqual(custom.par.Limit.eval(),.3)
                self.assertFalse(source.par.Kickactive.eval())

    def test_disabled_custom_name_retains_draft_without_applying_and_generic_clears_every_reference(self):
        e,mix,c,_,custom,feedback,_=self.fixture()
        self.assign(c,custom,feedback)
        c.par.Mixslot7name.val=''
        setup.apply_mix_ui(c)
        self.assertEqual(len(e.GetMixProfile()['descriptor']['items']),2)
        self.assertIs(c.par.Mixslot7source.eval(),custom)
        setup.reset_mix_ui(c)
        self.assertEqual(c.par.Mixanalysisbands.eval(),setup.MIX_ANALYSIS_DEFAULT)
        for slot in (7,8):
            for suffix,_,_,default in setup.MIX_ANALYSIS_SLOT_FIELDS:
                self.assertEqual(getattr(c.par,'Mixslot'+str(slot)+suffix).val,default)
        self.assertEqual(custom.par.Limit.eval(),.3)


if __name__=='__main__':unittest.main()
