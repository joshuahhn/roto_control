"""Explicit user policy: TD Follow ignores touch, not other guards. Source only."""
import unittest

import test_owner_follow
from protocol import digest, sysex


class FollowTouchPolicyTests(unittest.TestCase):
    def fixture(self):
        fixture=test_owner_follow.OwnerFollowTests().fixture()
        e,m,f,a,b,la,lb,sample,reset,comps=fixture
        track=e.CreateTrack(lb,'Variant')
        variant=e.CreatePlugin(lb,track,'Variant')
        e.SetPluginComp(lb,track,variant,b.owner)
        e.SelectPlugin(lb,track,variant);e.AssignParameter('knob',1,b)
        events=[];e.RegisterAction('preset','Preset',events.append);e.AssignAction(1,'preset')
        e.SelectLayout(la);f.observe(force=True)
        test_owner_follow.OwnerFollowTests().ack(e)
        self.assertNotEqual(variant,m.layout(lb)['owner']['entry_plugin_id'])
        return fixture,track,variant,events

    def touch(self,e,m):
        m.touched.add(52);e._host.touched=True;e._host.controls['knob',1].touched=True

    def select(self,f,sample,comp):
        test_owner_follow.OwnerFollowTests().follow(f,sample,comp,flush=False)

    def ack(self,e):test_owner_follow.OwnerFollowTests().ack(e)

    def test_touched_follow_commits_saved_variant_no_selection_dispatch_and_fresh_ack(self):
        fixture,track,variant,events=self.fixture()
        e,m,f,a,b,la,lb,sample,reset,_=fixture
        target=e._host.controls['knob',1]
        old_ack=sysex(11,11,(target.index>>7,target.index&127,*digest(target.target_id,6),0,0,0))
        self.touch(e,m);self.select(f,sample,b.owner)
        self.assertTrue(f.gated)
        e._receive_midi(old_ack)
        for packet in ((191,12,127),(191,44,127),(191,20,127)):
            e._receive_midi(packet)
        self.assertEqual((a.eval(),b.eval(),reset.pulses,events),(5,5,0,[]))
        f.flush()
        self.assertEqual(m.context()['key'],(lb,track,variant))
        self.assertIsNone(f.pending);self.assertFalse(f.gated)
        self.assertEqual((a.eval(),b.eval(),reset.pulses,events),(5,5,0,[]))
        self.assertEqual(m.touched,{52})  # no fake release or blanket touch reset
        e._receive_midi(old_ack)
        for packet in ((191,12,127),(191,44,127),(191,20,127)):
            e._receive_midi(packet)
        self.assertFalse(e.GetControlState()['mapped'])
        self.assertEqual((a.eval(),b.eval(),reset.pulses,events),(5,5,0,[]))
        self.ack(e);e._receive_midi((191,12,127));e._receive_midi((191,44,127))
        self.assertEqual((a.eval(),b.eval(),reset.pulses,events),(5,10,0,[]))

    def test_lock_learn_and_backlog_still_defer_then_commit_with_touch_still_set(self):
        for guard in ('LOCK','LEARN','backlog'):
            with self.subTest(guard=guard):
                fixture,track,variant,events=self.fixture()
                e,m,f,a,b,la,lb,sample,reset,_=fixture
                self.touch(e,m)
                if guard=='LOCK':m.locked=True
                if guard=='LEARN':e._host.learning=True
                self.select(f,sample,b.owner);f.flush(backlog=guard=='backlog')
                self.assertEqual(m.data['active'],la);self.assertEqual(f.pending['layout_id'],lb)
                m.locked=False;e._host.learning=False
                if guard=='LOCK':f.unlocked()
                self.assertTrue(m.touched and e._host.touched)
                f.flush();self.assertEqual(m.context()['key'],(lb,track,variant))
                self.assertEqual((a.eval(),b.eval(),reset.pulses,events),(5,5,0,[]))

    def test_manual_activation_and_default_shared_guard_still_require_release(self):
        fixture,track,variant,events=self.fixture()
        e,m,f,a,b,la,lb,sample,reset,_=fixture
        self.touch(e,m)
        for activate in (lambda:m.guard(),lambda:e.SelectLayout(lb),
                         lambda:e.SelectPlugin(lb,track,variant),lambda:e.SelectComp(b.owner)):
            with self.assertRaisesRegex(ValueError,'release'):activate()
        self.assertEqual(m.data['active'],la)
        self.assertEqual((a.eval(),b.eval(),reset.pulses,events),(5,5,0,[]))

    def test_general_binding_and_mapping_edit_touch_guards_are_not_relaxed(self):
        fixture,track,variant,events=self.fixture()
        e,m,f,a,b,la,lb,sample,reset,_=fixture
        self.touch(e,m)
        for opt_in in (False,True):
            with self.assertRaisesRegex(ValueError,'touch'):
                e.BindControls([],group_id='test',_allow_empty=True,_automatic_follow=opt_in)
        with self.assertRaisesRegex(ValueError,'release'):e.ConfigureControl(e.GetControlState()['id'],minimum=0)
        self.assertEqual(m.data['active'],la)
        self.assertEqual((a.eval(),b.eval(),reset.pulses,events),(5,5,0,[]))

    def test_touched_follow_failed_install_rolls_back_without_pausing_or_dispatch(self):
        fixture,track,variant,events=self.fixture()
        e,m,f,a,b,la,lb,sample,reset,_=fixture
        real=m.install;attempts=[]
        def install(record,*args,**kwargs):
            attempts.append(record['id'])
            if record['id']==lb:raise ValueError('injected install failure')
            return real(record,*args,**kwargs)
        m.install=install
        self.touch(e,m);self.select(f,sample,b.owner);f.flush()
        self.assertEqual(attempts,[lb,la]);self.assertEqual(m.data['active'],la)
        self.assertFalse(f.paused);self.assertIn('injected install failure',f.error)
        self.assertFalse(e.GetControlState()['mapped'])
        self.assertEqual((a.eval(),b.eval(),reset.pulses,events),(5,5,0,[]))

    def test_touch_is_not_td_pending_reason_but_hardware_selection_policy_is_preserved(self):
        fixture,track,variant,events=self.fixture()
        e,m,f,a,b,la,lb,sample,reset,_=fixture
        self.touch(e,m);m.locked=True;self.select(f,sample,b.owner)
        reason=e.GetCompContext()['pending_reason']
        self.assertIn('LOCK',reason);self.assertNotIn('touch',reason)
        f.request(la,m.track(la)['id'],'hardware',plugin_id=m.plugin(la)['id'])
        self.assertIn('touch',e.GetCompContext()['pending_reason'])
        m.locked=False;f.unlocked();f.flush()
        self.assertIsNotNone(f.pending);self.assertEqual(m.data['active'],la)


if __name__=='__main__':unittest.main()
