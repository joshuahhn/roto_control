"""Cross-owner routing uses actual source allocation; no native/physical claim."""
import copy
import json
import time
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import test_assignment
import test_comp_follow
import test_layout_owners
from layouts import Layouts, OWNER_KEY
from protocol import sysex, digest
from text_comp_follow import CompFollower


class OwnerFollowTests(unittest.TestCase):
    def fixture(self):
        e,m,f,a,b,comps = test_layout_owners.OwnerTests().fixture()
        f.tag_sampler = lambda: ()
        la = e.RegisterComp(a.owner); lb = e.RegisterComp(b.owner)
        reset = test_assignment.AssignmentTests().parameter('Pulse', 'Reset')
        reset.owner = a.owner; a.owner.par.Reset = reset
        e.SelectLayout(la); e.AssignParameter('knob',1,a)
        e.AssignParameter('button',1,reset,button_type='push')
        e.SelectLayout(lb); e.AssignParameter('knob',1,b)
        e.SelectLayout(la)
        sample = [((1,100,'/'),(a.owner,))]
        f.sampler = lambda: sample[0]
        f.scope = None; f.invalidate(); f.observe(force=True)
        self.ack(e); e._pending = b''
        return e,m,f,a,b,la,lb,sample,reset,comps

    def ack(self,e):
        test_comp_follow.FollowTests().ack(e)

    def follow(self,f,s,comp,flush=True):
        s[0] = (s[0][0],(comp,)); f.observe(force=True)
        if flush: f.flush()

    def test_cross_layout_a_b_a_live_values_ids_library_and_announcement_scope(self):
        e,m,f,a,b,la,lb,s,reset,_ = self.fixture()
        before = {l:copy.deepcopy(m.plugin(l)) for l in (la,lb)}
        b.val = 7
        self.follow(f,s,b.owner)
        self.assertEqual(m.context()['key'],(lb,m.track(lb)['id'],m.plugin(lb)['id']))
        self.assertEqual(e.GetValue(),7); self.assertFalse(e.GetControlState()['mapped'])
        self.assertEqual((e.ownerComp.par.Trackname.eval(),e.ownerComp.par.Pluginname.eval()),
                         (m.track()['name'],m.plugin()['plugin_name']))
        packets = [json.loads(line)['midi'] for line in e._pending.splitlines()]
        self.assertTrue(packets)
        details = [p for p in packets if p[5:7] == [11,5]]
        self.assertTrue(details)
        self.assertTrue(all(p[8:16] == list(digest(m.plugin()['device_id'],8)) for p in details))
        self.ack(e); self.follow(f,s,a.owner)
        self.assertEqual(m.data['active'],la)
        self.assertEqual(reset.pulses,0); self.assertEqual((a.eval(),b.eval()),(5,7))
        for l in (la,lb):
            p = m.plugin(l)
            for field in ('id','group_id','device_id','targets'):
                self.assertEqual(p[field],before[l][field])
            self.assertEqual(p['state']['page_targets'],before[l]['state']['page_targets'])
        installed = Mock(wraps=m.install); m.install = installed
        for _ in range(3): f.observe(force=True); f.flush()
        installed.assert_not_called()

    def test_saved_qualified_variant_wins_without_entry_or_order_fallback(self):
        e,m,f,a,b,la,lb,s,_,_ = self.fixture()
        track = e.CreateTrack(lb,'Variant')
        variant = e.CreatePlugin(lb,track,'Manual')
        e.SetPluginComp(lb,track,variant,b.owner)
        e.RenamePlugin(lb,track,variant,'Manual')
        e.SelectPlugin(lb,track,variant); assigned = e.AssignParameter('knob',2,b)
        e.SelectLayout(la)
        f.observe(force=True)  # linking intentionally establishes a new baseline
        entry = m.layout(lb)['owner']['entry_plugin_id']
        self.assertNotEqual(variant,entry)
        self.follow(f,s,b.owner)
        self.assertEqual(m.context()['key'],(lb,track,variant))
        self.assertEqual(e.GetValue(assigned['id']),5)
        self.assertEqual(m.plugin()['name_mode'],'manual')
        self.follow(f,s,a.owner); self.follow(f,s,b.owner)
        self.assertEqual(m.plugin()['id'],variant)
        # An unlinked saved choice is an explicit failure, not an empty entry fallback.
        empty = e.CreatePlugin(lb,track,'Unlinked')
        e.SelectPlugin(lb,track,empty); e.SelectLayout(la)
        self.follow(f,s,a.owner); self.follow(f,s,b.owner)
        self.assertEqual(m.data['active'],la)
        self.assertIn('qualified',f.error); self.assertIsNone(f.pending)

    def test_custom_reference_and_legacy_link_do_not_override_bound_owner(self):
        e,m,f,a,b,la,lb,s,_,_ = self.fixture()
        custom = copy.deepcopy(m.layout('custom'))
        e.SelectLayout('custom'); self.assertEqual(m.layout()['category'],'CUSTOM')
        self.assertEqual(f.resolve(a.owner),(la,m.track(la)['id'],m.plugin(la)['id']))
        e.SelectComp(b.owner); self.assertEqual(m.data['active'],lb)
        self.assertEqual(m.layout('custom')['tracks'],custom['tracks'])
        c = test_layout_owners.OwnerTests().add([], '/Unregistered')
        e.SelectLayout('custom'); e.SetPluginComp('custom',m.track()['id'],m.plugin()['id'],c.owner)
        with self.assertRaisesRegex(ValueError,'bound owner'): e.SelectComp(c.owner)
        self.assertEqual(m.data['active'],'custom')

    def test_guards_latest_intent_fence_recall_and_no_pulse_replay(self):
        for guard in ('locked','learning','backlog','opening'):
            with self.subTest(guard=guard):
                e,m,f,a,b,la,lb,s,reset,_ = self.fixture()
                if guard == 'locked': m.locked = True
                elif guard == 'learning': e._host.learning = True
                elif guard == 'opening': e._process = Mock(); e._host.plugin = False
                self.follow(f,s,b.owner,flush=False); f.flush(backlog=guard == 'backlog')
                self.assertEqual(m.data['active'],la)
                self.assertEqual(f.pending['layout_id'],lb)
                self.assertEqual(f.gated,guard != 'locked')
                if guard == 'locked':
                    e._receive_midi((191,12,127)); e._receive_midi((191,44,127))
                    self.assertEqual(a.eval(),10)
                m.locked = False; m.touched.clear(); e._host.touched = False
                e._host.learning = False; e._host.plugin = True; e._process = None
                if guard == 'locked': f.unlocked()
                for packet in ((191,12,127),(191,44,127),(191,20,127),(191,20,0)):
                    e._receive_midi(packet)
                self.ack(e); self.assertEqual(reset.pulses,0)
                f.flush(); self.assertEqual(m.data['active'],lb)
                self.assertFalse(e.GetControlState()['mapped'])
                e._receive_midi((191,44,127)); self.assertEqual(b.eval(),5)
                self.ack(e); e._receive_midi((191,12,127)); e._receive_midi((191,44,127))
                self.assertEqual(b.eval(),10); self.assertEqual(reset.pulses,0)

    def test_mixed_td_hardware_intents_both_orders_and_locked_sel_exception(self):
        for last in ('td','hardware'):
            e,m,f,a,b,la,lb,s,_,_ = self.fixture()
            other = e.CreateTrack(la,'Other')
            m.locked = True
            self.follow(f,s,b.owner,flush=False)
            e._receive_midi(sysex(10,9,(0,1)))
            if last == 'td':
                self.follow(f,s,a.owner,flush=False); self.follow(f,s,b.owner,flush=False)
            m.locked = False; f.unlocked(); f.flush()
            self.assertEqual(m.data['active'],lb if last == 'td' else la)
            if last == 'hardware': self.assertEqual(m.track()['id'],other)
        e,m,f,a,b,la,lb,s,_,_ = self.fixture()
        variant = e.CreatePlugin(la,m.track()['id'],'Variant')
        e.SetPluginComp(la,m.track()['id'],variant,a.owner)
        m.locked = True; self.follow(f,s,b.owner,flush=False)
        e._receive_midi(sysex(11,7,(1,))); f.flush()
        self.assertTrue(m.locked); self.assertEqual(m.plugin()['id'],variant)
        self.assertEqual(m.data['active'],la)

    def test_manual_cross_layout_choice_and_browse_reads_do_not_replay_selection(self):
        e,m,f,a,b,la,lb,s,_,_ = self.fixture()
        route = m.context()['key']; registry = e.GetLayoutRegistry()
        e.GetPlugins(lb); e.GetPluginTargets(lb); e.GetLayouts()
        self.assertEqual(m.context()['key'],route)
        self.assertEqual(e.GetLayoutRegistry(),registry)
        self.follow(f,s,b.owner); e.SelectLayout('custom')
        for _ in range(3): f.observe(force=True); f.flush()
        self.assertEqual(m.data['active'],'custom'); self.assertIsNone(f.pending)
        self.follow(f,s,a.owner); self.assertEqual(m.data['active'],la)

    def test_cancel_off_zero_multiple_pane_exit_and_missing_pending(self):
        for reason in ('off','zero','multiple','pane','missing'):
            with self.subTest(reason=reason):
                e,m,f,a,b,la,lb,s,_,_ = self.fixture()
                self.follow(f,s,b.owner,flush=False); self.assertTrue(f.gated)
                if reason == 'off': e.ownerComp.par.Followcomp.val = False
                elif reason == 'zero': s[0] = (s[0][0],())
                elif reason == 'multiple': s[0] = (s[0][0],(a.owner,b.owner))
                elif reason == 'pane': s[0] = (None,())
                else: b.owner.valid = False
                f.observe(force=True); f.flush()
                self.assertIsNone(f.pending); self.assertEqual(m.data['active'],la)
                self.assertFalse(f.gated); self.assertFalse(e.GetControlState()['mapped'])

    def test_owner_clone_unregistered_and_replacement_cannot_fallback_to_custom(self):
        for failure in ('clone','unregistered','replacement','token_removed'):
            with self.subTest(failure=failure):
                e,m,f,a,b,la,lb,s,_,comps = self.fixture()
                self.follow(f,s,b.owner,flush=False)
                if failure == 'clone':
                    clone = test_layout_owners.OwnerTests().add(comps,'/Clone')
                    clone.owner.store(OWNER_KEY,b.owner.fetch(OWNER_KEY))
                elif failure == 'unregistered': m.layout(lb)['owner']['state'] = 'unregistered'; m.save()
                elif failure == 'replacement':
                    b.owner.valid = False
                    replacement = test_layout_owners.OwnerTests().add(comps,b.owner.path)
                    s[0] = (s[0][0],(replacement.owner,))
                else: b.owner.store(OWNER_KEY,None)
                f.flush(); self.assertEqual(m.data['active'],la); self.assertIsNone(f.pending)
                self.assertEqual((a.eval(),b.eval()),(5,5))
                self.assertFalse(e.GetControlState()['mapped'])

    def test_pending_destination_revalidated_and_origin_scope_not_reinterpreted(self):
        e,m,f,a,b,la,lb,s,_,_ = self.fixture()
        variant = e.CreatePlugin(lb,m.track(lb)['id'],'Variant')
        e.SetPluginComp(lb,m.track(lb)['id'],variant,b.owner)
        f.observe(force=True)
        self.follow(f,s,b.owner,flush=False)
        m.track(lb)['active_plugin'] = variant; m.save()
        f.flush(); self.assertEqual(m.data['active'],la)
        self.assertIn('expired',f.error)
        # Source context drift without the common manual-selection callback is stale.
        f.request(lb,m.track(lb)['id'],'td',b.owner,variant)
        m.data['active'] = 'custom'; m.save()
        f.flush(); self.assertEqual(m.data['active'],'custom')
        self.assertIn('context expired',f.error); self.assertIsNone(f.pending)

    def test_disconnect_generation_cancels_cross_layout_then_fresh_offline_follow(self):
        e,m,f,a,b,la,lb,s,_,_ = self.fixture()
        self.follow(f,s,b.owner,flush=False); token = f.token
        e.Disconnect(); self.assertIsNone(f.pending); self.assertNotEqual(f.token,token)
        f.observe(force=True); f.flush(); self.assertEqual(m.data['active'],la)
        e._receive_midi(sysex(10,9,(0,0)),token); self.assertIsNone(f.pending)
        self.follow(f,s,a.owner); self.follow(f,s,b.owner)
        self.assertEqual(m.data['active'],lb); self.assertIsNone(e._process)
        self.assertFalse(e._host.connected)

    def test_failed_activation_rolls_back_and_failed_rollback_pauses_without_retry(self):
        for broken_rollback in (False,True):
            e,m,f,a,b,la,lb,s,_,_ = self.fixture()
            real = m.install; calls = []
            def install(record,*args,**kwargs):
                calls.append(record['id'])
                if record['id'] == lb or broken_rollback: raise RuntimeError('cross-owner failure')
                return real(record,*args,**kwargs)
            m.install = install; e.Disconnect = Mock()
            self.follow(f,s,b.owner)
            for _ in range(3): f.flush()
            self.assertEqual(m.data['active'],la); self.assertEqual(calls,[lb,la])
            self.assertEqual(f.paused,broken_rollback); self.assertEqual(f.gated,broken_rollback)
            self.assertIsNone(f.pending); e.Disconnect.assert_not_called()
            self.assertFalse(e.GetControlState()['mapped'])
            m.install = real; f.repair(); f.observe(force=True); f.flush()
            self.assertEqual(m.data['active'],la)

    def test_new_intent_during_cross_layout_commit_retains_fence_and_next_pass(self):
        e,m,f,a,b,la,lb,s,_,_ = self.fixture()
        real = m.install; installed = []
        def install(record,*args,**kwargs):
            installed.append(record['id']); result = real(record,*args,**kwargs)
            if record['id'] == lb:
                f.request(la,m.track(la)['id'],'td',a.owner,m.plugin(la)['id'])
            return result
        m.install = install; self.follow(f,s,b.owner)
        self.assertEqual(installed,[lb]); self.assertEqual(m.data['active'],lb)
        self.assertTrue(f.gated); self.assertEqual(f.pending['layout_id'],la)
        self.ack(e); self.assertFalse(e.GetControlState()['mapped'])
        f.flush(); self.assertEqual(installed,[lb,la]); self.assertEqual(m.data['active'],la)
        self.assertFalse(f.gated); self.assertFalse(e.GetControlState()['mapped'])

    def test_fresh_intent_during_successful_rollback_keeps_restored_target_fenced(self):
        e,m,f,a,b,la,lb,s,reset,_ = self.fixture()
        real = m.install; installed = []; failed = [False]
        def install(record,*args,**kwargs):
            installed.append(record['id'])
            if record['id'] == lb and not failed[0]:
                failed[0] = True; raise RuntimeError('first activation failed')
            result = real(record,*args,**kwargs)
            if record['id'] == la:
                f.request(lb,m.track(lb)['id'],'td',b.owner,m.plugin(lb)['id'])
            return result
        m.install = install; self.follow(f,s,b.owner)
        self.assertEqual(installed,[lb,la]); self.assertEqual(m.data['active'],la)
        self.assertTrue(f.gated); self.assertEqual(f.pending['layout_id'],lb)
        self.assertIn('first activation failed',f.error)
        self.ack(e)
        for packet in ((191,12,127),(191,44,127),(191,20,127),(191,20,0)):
            e._receive_midi(packet)
        self.assertFalse(e.GetControlState()['mapped'])
        self.assertEqual((a.eval(),b.eval(),reset.pulses),(5,5,0))
        f.flush(); self.assertEqual(installed,[lb,la,lb]); self.assertEqual(m.data['active'],lb)
        self.assertFalse(f.gated); self.assertIsNone(f.pending)
        self.assertFalse(e.GetControlState()['mapped'])
        self.ack(e); e._receive_midi((191,12,127)); e._receive_midi((191,44,127))
        self.assertEqual((a.eval(),b.eval()),(5,10))

    def test_real_tick_partial_line_old_mapping_cannot_cross_layout(self):
        e,m,f,a,b,la,lb,s,_,_ = self.fixture()
        old = e._host.controls['knob',1]
        mapping = sysex(11,11,(old.index>>7,old.index&127,*digest(old.target_id,6),0,0,0))
        def line(message): return (json.dumps({'midi':message})+'\n').encode()
        tail = line(mapping); split = len(tail)//2
        packet = line((191,12,127))*257 + tail[:split]
        child = Mock(); child.poll.return_value = None
        e._process = child; e._transport_ready = True; e._started_at = time.monotonic()
        e._trace_control_midi = Mock(); s[0] = (s[0][0],(b.owner,)); f.next_sample = 0
        with patch('RotoPythonExt.os.read',side_effect=[packet,BlockingIOError]),patch('RotoPythonExt.os.write',side_effect=lambda fd,data:len(data)):
            e.Tick()
        self.assertEqual(m.data['active'],la); self.assertTrue(f.gated)
        with patch('RotoPythonExt.os.read',side_effect=BlockingIOError),patch('RotoPythonExt.os.write',side_effect=lambda fd,data:len(data)):
            e.Tick()
        self.assertEqual(m.data['active'],lb)
        with patch('RotoPythonExt.os.read',side_effect=[tail[split:],BlockingIOError]),patch('RotoPythonExt.os.write',side_effect=lambda fd,data:len(data)):
            e.Tick()
        self.assertIs(e._collection.bindings['knob',1].parameter,b)
        self.assertFalse(e.GetControlState()['mapped']); self.assertEqual((a.eval(),b.eval()),(5,5))

    def test_reload_saved_variant_baseline_rename_reparent_and_explicit_enable(self):
        e,m,f,a,b,la,lb,s,_,comps = self.fixture()
        variant = e.CreatePlugin(lb,m.track(lb)['id'],'Variant')
        e.SetPluginComp(lb,m.track(lb)['id'],variant,b.owner)
        e.SelectPlugin(lb,m.track(lb)['id'],variant); e.AssignParameter('knob',1,b)
        e.SelectLayout(la); before = copy.deepcopy(m.plugin(lb))
        b.owner.path = '/moved/Renamed'; b.owner.name = 'Renamed'
        e.GetLayoutRegistry(); e._layouts = m = Layouts(e)
        f = e._follow = CompFollower(e,lambda:s[0]); f.owner_candidates = lambda:list(comps)
        f.tag_sampler = lambda:(); m.restore()
        s[0] = (s[0][0],(b.owner,)); f.observe(force=True); f.flush()
        self.assertEqual(m.data['active'],la); self.assertIsNone(f.pending)
        e.ownerComp.par.Followcomp.val = False; f.observe(force=True)
        e.ownerComp.par.Followcomp.val = True; f.observe(force=True,explicit=True); f.flush()
        self.assertEqual(m.plugin()['id'],variant)
        self.assertEqual(m.plugin()['device_id'],before['device_id'])
        self.assertEqual(m.plugin()['targets'][0]['identity'],before['targets'][0]['identity'])
        self.assertEqual(m.plugin()['targets'][0]['comp'],'../moved/Renamed')
        self.assertEqual(b.eval(),5)

    def test_returned_owner_quarantine_needs_explicit_activation_not_follow(self):
        e,m,f,a,b,la,lb,s,_,_ = self.fixture()
        a.owner.valid = False; f.refresh_links(); self.assertTrue(m.quarantined)
        a.owner.valid = True; f.refresh_links()
        self.assertEqual(m.layout(la)['owner']['state'],'bound')
        with self.assertRaisesRegex(ValueError,'Explicitly Activate'): e.SelectComp(a.owner)
        self.assertTrue(m.quarantined); self.assertFalse(e.GetControlState()['mapped'])
        e.SelectPlugin(la,m.track()['id'],m.plugin()['id']); self.assertFalse(m.quarantined)
        self.assertFalse(e.GetControlState()['mapped'])

    def test_diagnostics_detached_pending_layout_owner_and_policy(self):
        e,m,f,a,b,la,lb,s,_,_ = self.fixture()
        m.locked = True; self.follow(f,s,b.owner,flush=False)
        c = e.GetCompContext()
        self.assertEqual(c['pending_layout_id'],lb)
        self.assertEqual(c['pending_owner_id'],m.layout(lb)['owner']['id'])
        self.assertEqual(c['follow_destination_policy'],'saved_active_owner_qualified_device')
        c['owner']['state'] = 'missing'
        self.assertEqual(m.layout(la)['owner']['state'],'bound')

    def test_startup_pane_return_mixed_selection_and_callback_mode_baselines(self):
        e,m,f,a,b,la,lb,s,_,_ = self.fixture()
        f.invalidate(); s[0] = (s[0][0],(b.owner,)); f.observe(force=True); f.flush()
        self.assertEqual(m.data['active'],la)
        top = SimpleNamespace(valid=True,isCOMP=False,id=30,path='/top')
        for selected in ((),(b.owner,top),(a.owner,b.owner)):
            s[0] = (s[0][0],selected); f.observe(force=True); f.flush()
            self.assertEqual(m.data['active'],la)
        s[0] = (None,()); f.observe(force=True)
        s[0] = ((2,200,'/other-pane'),(b.owner,)); f.observe(force=True); f.flush()
        self.assertEqual(m.data['active'],la)
        m.legacy = True; f.observe(force=True); self.assertEqual(f.status,'unavailable')
        m.legacy = False; f.observe(force=True); f.flush()
        self.assertEqual(m.data['active'],la)
        f.observe(force=True,explicit=True); f.flush(); self.assertEqual(m.data['active'],lb)

    def test_cross_owner_open_and_child_failure_cancel_without_replaying(self):
        for failure in ('open','child'):
            e,m,f,a,b,la,lb,s,_,_ = self.fixture()
            m.locked = True; self.follow(f,s,b.owner,flush=False); old = f.token
            if failure == 'open':
                import test_layouts
                e.ownerComp.par.Python = test_layouts.Par('/does/not/exist/python')
                with patch('RotoPythonExt.project',SimpleNamespace(folder='/tmp'),create=True),self.assertRaises(FileNotFoundError):
                    e.Connect()
            else:
                child = Mock(); child.poll.return_value = 1
                e._process = child; e._transport_ready = True; e._started_at = time.monotonic()
                with patch('RotoPythonExt.os.read',side_effect=BlockingIOError),self.assertRaises(RuntimeError): e.Tick()
            self.assertIsNone(f.pending); self.assertNotEqual(f.token,old)
            self.assertFalse(m.locked); self.assertIsNone(e._process)
            e._host.connected = e._host.plugin = True
            f.observe(force=True); f.flush(); self.assertEqual(m.data['active'],la)

    def test_stale_owner_identity_with_same_destination_is_rejected(self):
        e,m,f,a,b,la,lb,s,_,_ = self.fixture()
        self.follow(f,s,b.owner,flush=False)
        # Simulate a detached replacement/install that preserves L/T/D IDs.
        token = 'owner.replacement'; b.owner.store(OWNER_KEY,token)
        owner = m.layout(lb)['owner']; owner['id'] = token
        m.plugin(lb)['focus_comp']['owner_id'] = token; m.save()
        f.flush(); self.assertEqual(m.data['active'],la)
        self.assertIn('expired',f.error); self.assertIsNone(f.pending)

    def test_same_source_latest_return_requires_new_matching_recall(self):
        e,m,f,a,b,la,lb,s,reset,_ = self.fixture()
        self.follow(f,s,b.owner,flush=False); self.follow(f,s,a.owner,flush=False)
        e._receive_midi((191,20,127)); f.flush()
        self.assertEqual(m.data['active'],la); self.assertEqual(reset.pulses,0)
        self.assertFalse(e.GetControlState()['mapped'])
        self.ack(e); e._receive_midi((191,20,127)); self.assertEqual(reset.pulses,1)

    def test_inspector_adapter_projects_commit_and_expires_old_activate_token(self):
        import sys
        from pathlib import Path
        sys.path.insert(0,str(Path(__file__).parent/'prototypes/inspector'))
        from live_model import TDControllerAdapter, ControllerCatalog
        e,m,f,a,b,la,lb,s,_,_ = self.fixture()
        class Controller:
            ext = SimpleNamespace(RotoPythonExt=e)
            path = e.ownerComp.path
            def op(self,path):
                if path=='inspector':return SimpleNamespace(fetch=lambda key,default=None:default,store=lambda key,value:None)
                return e.ownerComp.op(path)
            def __getattr__(self,name): return getattr(e,name)
            @property
            def State(self):
                return dict(Connected=e._host.connected,Learning=e._host.learning,
                    Touched=e._host.touched,Bindingvalid=True,Lasterror=e._last_error)
        c = Controller()
        wrapper = SimpleNamespace(par=SimpleNamespace(Controller=SimpleNamespace(eval=lambda:c)),op=lambda name:None)
        adapter = TDControllerAdapter(wrapper)
        # Native definition inspection is a separate gate; projection/routing is real source.
        adapter._definitions = lambda rows,key:rows
        model = ControllerCatalog(adapter)
        ka = m.context()['key']; kb = (lb,m.track(lb)['id'],m.plugin(lb)['id'])
        token = model.ActivationToken(kb); preview = model.GetCatalog(kb)
        self.assertEqual(m.context()['key'],ka); self.assertEqual(preview[0]['Value'],5)
        self.follow(f,s,b.owner); model.Sync(); model.Flush()
        self.assertEqual(model.Status['Active'],kb); self.assertEqual(model.ActiveContext(),kb)
        self.assertFalse(model.Info(kb,0)['mapped'])
        self.assertEqual(model.Status['ContextOwners'][lb]['owner']['id'],m.layout(lb)['owner']['id'])
        with self.assertRaises(ValueError): model.Activate(kb,token)
        # Browsing A remains a detached view; it cannot redirect active B writes.
        model.GetCatalog(ka)
        with self.assertRaisesRegex(ValueError,'Browse only'): adapter.Write(ka,model.Info(ka,0),8)
        self.assertEqual(m.context()['key'],kb); self.assertEqual((a.eval(),b.eval()),(5,5))
        self.ack(e); model.Sync(); self.assertTrue(model.Info(kb,0)['mapped'])


if __name__ == '__main__': unittest.main()
