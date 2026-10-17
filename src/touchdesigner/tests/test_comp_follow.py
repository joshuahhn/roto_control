"""Real routing adapters with sampled UI events and integrated fenced MIDI input."""
import copy
import json
import time
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
import test_layouts
import test_assignment
from text_comp_follow import CompFollower
from layouts import ActivationRollbackError
from protocol import sysex, digest


class FollowTests(unittest.TestCase):
    def fixture(self, pulse=False):
        e, m, a = test_layouts.LayoutTests().fixture()
        b = test_assignment.AssignmentTests().parameter()
        a.owner.isCOMP = b.owner.isCOMP = True
        a.owner.id = 10; b.owner.id = 20; b.owner.path = '/other'
        a.owner.par = SimpleNamespace(Speed=a); b.owner.par = SimpleNamespace(Speed=b)
        oldop = e.ownerComp.op
        e.ownerComp.op = lambda n: a.owner if n == '../master' else b.owner if n == '../other' else oldop(n)
        t1 = m.track()['id']; t2 = m.create_track('custom', 'B')
        m.select_track('custom', t2); e.AssignParameter('knob', 1, b)
        m.select_track('custom', t1)
        reset = None
        if pulse:
            reset = test_assignment.AssignmentTests().parameter('Pulse', 'Reset')
            reset.owner = a.owner; a.owner.par.Reset = reset
            e.AssignParameter('button', 1, reset)
        e.ownerComp.par.Followcomp = test_layouts.Par(True)
        e._process = None; e._receive = b''; e._receive_epoch = None
        sample = [((1, 100, '/'), (a.owner,))]
        f = CompFollower(e, lambda: sample[0]); e._follow = f
        f.set_link('custom', t1, a.owner); f.set_link('custom', t2, b.owner)
        f.observe(force=True)
        e._pending = b''
        self.ack(e)
        e._pending = b''
        return e, m, f, a, b, t1, t2, sample, reset

    def ack(self, e):
        for t in list(e._host.controls.values()):
            e._receive_midi(sysex(11, 11, (t.index >> 7, t.index & 127,
                *digest(t.target_id, 6), int(t.key[0] == 'button'), t.key[1]-1, 0)))

    def select_hw(self, e, m, track):
        index = [t['id'] for t in m.layout()['tracks']].index(track)
        e._receive_midi(sysex(10, 9, (index >> 7, index & 127)))

    def test_same_batch_and_backlog_never_write_old_or_new_target(self):
        for backlog in (False, True):
            with self.subTest(backlog=backlog):
                e,m,f,a,b,t1,t2,s,_ = self.fixture()
                self.select_hw(e,m,t2)
                e._receive_midi((191,12,127)); e._receive_midi((191,44,127))
                self.assertEqual((a.eval(),b.eval()),(5,5)); self.assertTrue(f.gated)
                self.assertFalse(e.GetControlState()['mapped'])
                self.ack(e); self.assertFalse(e.GetControlState()['mapped'])
                f.flush(backlog=backlog)
                if backlog:
                    self.assertEqual(m.track()['id'],t1)
                    e._receive_midi((191,12,127)); f.flush()
                self.assertEqual(m.track()['id'],t2)
                e._receive_midi((191,44,127)); self.assertEqual(b.eval(),5)
                self.ack(e)
                e._receive_midi((191,12,127)); e._receive_midi((191,44,127))
                self.assertEqual((a.eval(),b.eval()),(5,10))

    def test_pulse_and_toggle_reports_fenced_and_not_replayed(self):
        e,m,f,a,b,t1,t2,s,p = self.fixture(pulse=True)
        self.select_hw(e,m,t2)
        for value in (127,0,127):e._receive_midi((191,20,value))
        self.ack(e); self.assertEqual(p.pulses,0)
        f.flush(); self.assertEqual(p.pulses,0)
        e.SelectTrack('custom',t1); self.ack(e)
        e._receive_midi((191,20,127)); self.assertEqual(p.pulses,1)

    def test_locked_browsing_preserves_old_then_unlock_fences_until_release(self):
        e,m,f,a,b,t1,t2,s,_ = self.fixture()
        e._receive_midi(sysex(11,13,(1,))); self.select_hw(e,m,t2)
        self.assertFalse(f.gated)
        e._receive_midi((191,12,127)); e._receive_midi((191,44,127))
        self.assertEqual(a.eval(),10)
        e._receive_midi((191,52,127)); e._receive_midi(sysex(11,9,(1,)))
        e._receive_midi(sysex(11,13,(0,)))
        self.assertTrue(f.gated)
        e._receive_midi((191,12,0)); e._receive_midi((191,44,0)); f.flush()
        self.assertEqual(m.track()['id'],t1); self.assertEqual(a.eval(),10)
        e._receive_midi((191,52,0)); e._receive_midi(sysex(11,9,(0,))); f.flush()
        self.assertEqual(m.track()['id'],t2)

    def test_latest_td_hardware_intent_single_activation_both_orders(self):
        for last in ('td','hardware'):
            with self.subTest(last=last):
                e,m,f,a,b,t1,t2,s,_ = self.fixture()
                e._receive_midi(sysex(11,13,(1,)))
                f.request('custom',t2,'td',b.owner)
                self.select_hw(e,m,t1)
                if last == 'td':
                    s[0]=(s[0][0],(b.owner,)); f.observe(force=True)
                else:
                    s[0]=(s[0][0],(b.owner,)); f.observe(force=True); self.select_hw(e,m,t1)
                installed=[]; real=m.install
                m.install=lambda *args,**kw:(installed.append(args[0]['track_name']),real(*args,**kw))[1]
                e._receive_midi(sysex(11,13,(0,))); f.flush()
                self.assertEqual(m.track()['id'],t2 if last=='td' else t1)
                self.assertLessEqual(len(installed),1)
                f.flush(); self.assertLessEqual(len(installed),1)

    def test_zero_mixed_current_pane_and_baseline_only_restore(self):
        e,m,f,a,b,t1,t2,s,_ = self.fixture()
        f.flush(); self.assertEqual(m.track()['id'],t1)
        top=SimpleNamespace(valid=True,isCOMP=False,id=30,path='/top')
        for selected in ((),(b.owner,top),(a.owner,b.owner)):
            s[0]=(s[0][0],selected); f.observe(force=True); f.flush()
            self.assertEqual(m.track()['id'],t1)
        s[0]=(s[0][0],(b.owner,)); f.observe(force=True); f.flush()
        self.assertEqual(m.track()['id'],t2)
        e.SelectTrack('custom',t1); f.flush(); self.assertEqual(m.track()['id'],t1)
        f.invalidate(); f.flush(); self.assertEqual(m.track()['id'],t1)

    def test_pending_canceled_by_pane_exit_and_return_not_replayed(self):
        e,m,f,a,b,t1,t2,s,_=self.fixture()
        m.locked=True;s[0]=(s[0][0],(b.owner,));f.observe(force=True)
        self.assertIsNotNone(f.pending)
        s[0]=(None,()); f.observe(force=True); self.assertIsNone(f.pending)
        m.locked=False;s[0]=((1,100,'/'),(b.owner,));f.flush()
        self.assertEqual(m.track()['id'],t1)

    def test_duplicate_link_unlink_and_active_layout_scope(self):
        e,m,f,a,b,t1,t2,s,_=self.fixture();before=copy.deepcopy(m.data)
        with self.assertRaisesRegex(ValueError,'already'):e.SetTrackComp('custom',t2,a.owner)
        self.assertEqual(m.data,before)
        e.SetTrackComp('custom',t2,None)
        with self.assertRaises(ValueError):e.SelectComp(b.owner)
        other=m.create('Other');m.select(other)
        with self.assertRaises(ValueError):e.SelectComp(a.owner)

    def test_live_identity_rename_reparent_delete_recreate_and_reopen(self):
        e,m,f,a,b,t1,t2,s,_=self.fixture()
        a.owner.path='/renamed'; e.ownerComp.path='/moved/controller'
        f.refresh_links();self.assertEqual(m.plugin('custom',t1)['focus_comp']['path'],'../../renamed')
        a.owner.valid=False;f.refresh_links();self.assertEqual(m.plugin('custom',t1)['focus_comp']['state'],'missing')
        replacement=SimpleNamespace(valid=True,isCOMP=True,id=40,path='/renamed')
        oldop=e.ownerComp.op
        e.ownerComp.op=lambda path:replacement if path=='../../renamed' else b.owner if path=='../../other' else oldop(path)
        f.refresh_links();self.assertNotIn(t1,f.handles)
        reloaded=CompFollower(e,lambda:s[0]);e._follow=reloaded;reloaded.refresh_links()
        self.assertNotIn(t1,reloaded.handles)
        e.SetTrackComp('custom',t1,replacement);self.assertEqual(reloaded.resolve(replacement),('custom',t1,m.plugin('custom',t1)['id']))

    def test_domain_preflight_and_rollback_failures_no_retry_or_disconnect(self):
        for rollback_failed in (False,True):
            with self.subTest(rollback_failed=rollback_failed):
                e,m,f,a,b,t1,t2,s,_=self.fixture()
                self.select_hw(e,m,t2);before=m.track()['id'];calls=[]
                real=m.install
                def fail(record,*args,**kw):
                    calls.append(record['id'])
                    if record['track_name']=='B' or rollback_failed:raise RuntimeError('injected install failure')
                    return real(record,*args,**kw)
                m.install=fail;e.Disconnect=Mock()
                f.flush();f.flush();f.flush()
                self.assertEqual(m.track()['id'],before);e.Disconnect.assert_not_called()
                self.assertEqual(len(calls),2);self.assertEqual(f.paused,rollback_failed)
                self.assertIsNone(f.pending)
                self.assertFalse(e.GetControlState()['mapped'])

    def test_failed_preflight_preserves_registry_and_requires_new_intent(self):
        e,m,f,a,b,t1,t2,s,_=self.fixture(); m.plugin('custom',t2)['targets'][0]['minimum']=-100
        before=copy.deepcopy(m.data);self.select_hw(e,m,t2);f.flush()
        self.assertEqual(m.data,before);self.assertEqual(m.track()['id'],t1)
        self.assertEqual(f.status,'failed');self.assertIsNone(f.pending)
        f.flush();self.assertEqual(m.data,before)

    def test_disconnect_same_manager_cancels_both_sources_and_offline_follow(self):
        for source in ('td','hardware'):
            with self.subTest(source=source):
                e,m,f,a,b,t1,t2,s,_=self.fixture();m.locked=True
                f.request('custom',t2,source,b.owner if source=='td' else None)
                token=f.token;e.Disconnect()
                self.assertIs(e._layouts,m);self.assertIsNone(f.pending);self.assertFalse(m.locked)
                self.assertEqual(m.selected_track,t1);self.assertNotEqual(token,f.token)
                e._host.connected=e._host.plugin=True
                f.flush();self.assertEqual(m.track()['id'],t1)
                e._receive_midi(sysex(10,9,(0,1)),token);self.assertIsNone(f.pending)
                e._host.connected=e._host.plugin=False
                f.invalidate();f.observe(force=True)
                s[0]=(s[0][0],(b.owner,));f.observe(force=True);f.flush()
                self.assertEqual(m.track()['id'],t2);self.assertIsNone(e._process)

    def test_old_epoch_mapping_cannot_restore_target_and_output_is_framing_safe(self):
        e,m,f,a,b,t1,t2,s,_=self.fixture();token=f.token
        old=e._host.controls['knob',1]
        packet=sysex(11,11,(0,old.index,*digest(old.target_id,6),0,0,0))
        partial=b'2, 44, 127]}\n'
        e._pending=partial+(json.dumps({'midi':(191,12,127)})+'\n').encode()
        self.select_hw(e,m,t2)
        self.assertEqual(e._pending,partial)
        f.flush();e._receive_midi(packet,token)
        self.assertFalse(e.GetControlState()['mapped'])

    def test_child_failure_cancels_intent_in_real_tick(self):
        e,m,f,a,b,t1,t2,s,_=self.fixture();m.locked=True;self.select_hw(e,m,t2)
        process=Mock();process.poll.return_value=1
        e._process=process;e._transport_ready=True;e._started_at=time.monotonic()
        with patch('RotoPythonExt.os.read',side_effect=BlockingIOError),self.assertRaises(RuntimeError):e.Tick()
        self.assertIsNone(e._process);self.assertIsNone(f.pending);self.assertFalse(m.locked)
        self.assertEqual(m.track()['id'],t1)

    def test_callback_mode_return_preserves_preference_and_waits(self):
        e,m,f,a,b,t1,t2,s,_=self.fixture();m.legacy=True
        f.observe(force=True);self.assertTrue(f.enabled);self.assertEqual(f.status,'unavailable')
        m.legacy=False;s[0]=(s[0][0],(b.owner,));f.flush()
        self.assertEqual(m.track()['id'],t1)
        f.observe(force=True,explicit=True);f.flush();self.assertEqual(m.track()['id'],t2)

    def test_real_tick_backlog_and_partial_line_keep_ingress_epoch(self):
        e,m,f,a,b,t1,t2,s,_=self.fixture()
        child=Mock();child.poll.return_value=None
        e._process=child;e._transport_ready=True;e._started_at=time.monotonic()
        e._trace_control_midi=Mock()  # fixture has no native diagnostic DAT
        def line(message):return (json.dumps({'midi':message})+'\n').encode()
        old=e._host.controls['knob',1]
        mapping=sysex(11,11,(0,old.index,*digest(old.target_id,6),0,0,0))
        tail=line(mapping);split=len(tail)//2
        packet=line(sysex(10,9,(0,1)))+line((191,12,127))+line((191,44,127))
        packet+=line((191,12,127))*254+tail[:split]
        with patch('RotoPythonExt.os.read',side_effect=[packet,BlockingIOError]),patch('RotoPythonExt.os.write',side_effect=lambda fd,data:len(data)):
            e.Tick()
        self.assertEqual(m.track()['id'],t1);self.assertTrue(f.gated)
        with patch('RotoPythonExt.os.read',side_effect=BlockingIOError),patch('RotoPythonExt.os.write',side_effect=lambda fd,data:len(data)):
            e.Tick()
        self.assertEqual(m.track()['id'],t2);self.assertFalse(f.gated)
        # An old partial report may not restore A into B's page after commit.
        with patch('RotoPythonExt.os.read',side_effect=[tail[split:],BlockingIOError]),patch('RotoPythonExt.os.write',side_effect=lambda fd,data:len(data)):
            e.Tick()
        self.assertEqual(e._collection.bindings['knob',1].parameter,b)
        self.assertFalse(e.GetControlState()['mapped']);self.assertEqual((a.eval(),b.eval()),(5,5))

    def test_unexpected_observer_failure_pauses_without_transport_disconnect(self):
        e,m,f,a,b,t1,t2,s,_=self.fixture()
        f.sampler=Mock(side_effect=RuntimeError('broken observer'));f.next_sample=0
        e.Disconnect=Mock();e.Tick();e.Tick()
        self.assertTrue(f.paused);self.assertTrue(f.gated);e.Disconnect.assert_not_called()
        self.assertEqual(f.status,'paused');self.assertEqual(f.sampler.call_count,1)
        f.sampler=lambda:s[0];f.repair();f.flush()
        self.assertFalse(f.paused);self.assertFalse(f.gated);self.assertIsNone(f.pending)

    def test_follow_off_hardware_still_defers_once_and_recovery_needs_recall(self):
        e,m,f,a,b,t1,t2,s,_=self.fixture();e.ownerComp.par.Followcomp.val=False
        f.observe(force=True);m.locked=True;self.select_hw(e,m,t2)
        self.assertFalse(f.gated);self.assertTrue(e.GetControlState()['mapped'])
        e._receive_midi(sysex(11,13,(0,)));self.assertTrue(f.gated)
        f.flush();identity=e.GetControlState()['id'];f.flush()
        self.assertEqual(m.track()['id'],t2);self.assertEqual(e.GetControlState()['id'],identity)
        self.assertFalse(e.GetControlState()['mapped']);self.assertFalse(m.confirmed)
        self.ack(e);self.assertTrue(e.GetControlState()['mapped'])

    def test_latest_original_track_cannot_reuse_prefence_mapping(self):
        e,m,f,a,b,t1,t2,s,_=self.fixture()
        self.select_hw(e,m,t2);self.select_hw(e,m,t1);f.flush()
        self.assertEqual(m.track()['id'],t1);self.assertFalse(e.GetControlState()['mapped'])
        e._receive_midi((191,44,127));self.assertEqual(a.eval(),5)
        self.ack(e);e._receive_midi((191,44,127));self.assertEqual(a.eval(),5)
        e._receive_midi((191,12,127));self.assertEqual(a.eval(),10)

    def test_new_request_during_commit_waits_for_later_pass(self):
        e,m,f,a,b,t1,t2,s,_=self.fixture();real=m.install
        def install(record,*args,**kw):
            result=real(record,*args,**kw)
            if record['track_name']=='B':f.request('custom',t1,'hardware')
            return result
        m.install=install;self.select_hw(e,m,t2);f.flush()
        self.assertEqual(m.track()['id'],t2);self.assertEqual(f.pending['track_id'],t1)
        f.flush();self.assertEqual(m.track()['id'],t1)

    def test_schema_rejects_duplicate_or_absolute_focus_and_normalizes_migration(self):
        e,m,f,a,b,t1,t2,s,_=self.fixture();before=copy.deepcopy(m.data)
        broken=copy.deepcopy(before);broken['records'][0]['tracks'][1]['plugins'][0]['focus_comp']=copy.deepcopy(broken['records'][0]['tracks'][0]['plugins'][0]['focus_comp'])
        with self.assertRaises(ValueError):m.validate(broken)
        broken=copy.deepcopy(before);broken['records'][0]['tracks'][0]['plugins'][0]['focus_comp']['path']='/absolute'
        with self.assertRaises(ValueError):m.validate(broken)
        broken=copy.deepcopy(before);broken['records'][0]['tracks'][0]['plugins'][0]['focus_comp']['path']='.././master'
        self.assertEqual(m.migrate(broken)['records'][0]['tracks'][0]['plugins'][0]['focus_comp']['path'],'../master')

    def test_unresolved_focus_ui_after_rename_does_not_unlink_live_handle(self):
        e,m,f,a,b,t1,t2,s,_=self.fixture()
        class Ref:
            name='Focuscomp';val='/master'
            def eval(self):return None
        e.ownerComp.par.Focuscomp=Ref();a.owner.path='/renamed'
        e.onParValueChange(e.ownerComp.par.Focuscomp,a.owner)
        self.assertEqual(m.plugin()['focus_comp'],dict(path='../renamed',state='bound'))
        self.assertEqual(e.ownerComp.par.Focuscomp.val,'/renamed')
        e.ownerComp.par.Focuscomp.val=''
        e.onParValueChange(e.ownerComp.par.Focuscomp,a.owner)
        self.assertIsNone(m.plugin()['focus_comp'])

    def test_button_actions_and_software_feedback_cannot_cross_fence(self):
        e,m,f,a,b,t1,t2,s,reset=self.fixture(pulse=True)
        toggle=test_assignment.AssignmentTests().parameter('Toggle','Enabled')
        toggle.owner=a.owner;a.owner.par.Enabled=toggle
        menu=test_assignment.AssignmentTests().parameter('Menu','Choice')
        menu.menuNames=['one','two'];menu.menuLabels=['One','Two'];menu.val='one'
        menu.owner=a.owner;a.owner.par.Choice=menu
        push=test_assignment.AssignmentTests().parameter('Pulse','Pushreset')
        push.owner=a.owner;a.owner.par.Pushreset=push
        e.AssignParameter('button',2,toggle);e.AssignParameter('button',3,menu,button_type='push')
        e.AssignParameter('button',4,push,button_type='push');self.ack(e)
        e._pending=b'';self.select_hw(e,m,t2);before=(reset.pulses,push.pulses,toggle.eval(),menu.eval(),e._host.tx)
        for cc in (20,21,22,23):
            for value in (127,127,0,127,0):e._receive_midi((191,cc,value))
        a.val=7;e.onControlChange(('knob',1),a)
        e._host.flush_display(time.monotonic()+1)
        self.assertEqual((reset.pulses,push.pulses,toggle.eval(),menu.eval(),e._host.tx),before)
        self.assertEqual(e._pending,b'');self.assertEqual(a.eval(),7)
        f.flush();self.ack(e);self.assertEqual((reset.pulses,push.pulses),before[:2])

    def test_failed_open_and_pipe_error_cancel_pending_session_intents(self):
        e,m,f,a,b,t1,t2,s,_=self.fixture();m.locked=True;self.select_hw(e,m,t2)
        e.ownerComp.par.Python=test_layouts.Par('/does/not/exist/python')
        with patch('RotoPythonExt.project',SimpleNamespace(folder='/tmp'),create=True),self.assertRaises(FileNotFoundError):e.Connect()
        self.assertIsNone(f.pending);self.assertFalse(m.locked);self.assertIs(e._layouts,m)
        e._host.connected=e._host.plugin=True;m.locked=True;self.select_hw(e,m,t2)
        child=Mock();child.poll.return_value=1;e._process=child
        with patch('RotoPythonExt.os.read',side_effect=OSError('broken pipe')),self.assertRaises(OSError):e.Tick()
        self.assertIsNone(f.pending);self.assertIsNone(e._process);self.assertFalse(m.locked)


if __name__ == '__main__':
    unittest.main()
