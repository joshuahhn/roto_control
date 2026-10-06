"""Independent Device selection, wire banks and preserved mapping identities."""
import copy
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import test_comp_follow
import test_delete_popup
from layouts import Layouts, VERSION
from protocol import sysex, digest


class DeviceTests(unittest.TestCase):
    def fixture(self, pulse=False):
        e,m,f,a,b,t1,t2,s,reset=test_comp_follow.FollowTests().fixture(pulse)
        pa=m.plugin('custom',t1)['id'];pb=m.plugin('custom',t2)['id']
        m.track('custom',t1)['plugins'].append(m.plugin('custom',t2))
        m.layout()['tracks']=[m.track('custom',t1)]
        m.save();m.menu();f.observe(force=True)
        return e,m,f,a,b,t1,pa,pb,s,reset

    def ack(self,e):test_comp_follow.FollowTests().ack(e)

    def hw(self,e,index):e._receive_midi(sysex(11,7,(index,)))

    def test_same_track_a_b_a_reads_values_preserves_ids_and_libraries(self):
        e,m,f,a,b,t,pa,pb,s,_=self.fixture()
        initial=copy.deepcopy(m.plugin()['state']['page_targets']);wire=e._host.controls['knob',1].target_id
        self.assertEqual(len(e.GetPlugins()),2)
        e.SelectPlugin('custom',t,pb);self.assertEqual(e.GetValue(),5)
        self.assertEqual(m.track()['id'],t);self.assertEqual(m.plugin()['id'],pb)
        b.val=7;e.SelectPlugin('custom',t,pa)
        self.assertEqual(e._host.controls['knob',1].target_id,wire)
        self.assertEqual(m.plugin()['state']['page_targets'],initial)
        self.assertEqual((a.eval(),b.eval()),(5,7))
        e.SelectPlugin('custom',t,pb);e.RemoveAllControls();m.capture(force=True)
        self.assertEqual(m.plugin()['targets'],[])
        e.SelectPlugin('custom',t,pa);self.assertEqual(e._host.controls['knob',1].target_id,wire)

    def test_comp_follow_changes_plugin_without_changing_track(self):
        e,m,f,a,b,t,pa,pb,s,_=self.fixture()
        s[0]=(s[0][0],(b.owner,));f.observe(force=True)
        self.assertEqual(f.pending['plugin_id'],pb);f.flush()
        self.assertEqual((m.track()['id'],m.plugin()['id']),(t,pb))
        e.SelectComp(a.owner);self.assertEqual(m.plugin()['id'],pa)
        self.assertEqual(e.GetCompContext()['focus_comp'],m.plugin()['focus_comp'])

    def test_same_batch_backlog_split_knob_and_pulse_are_fenced(self):
        e,m,f,a,b,t,pa,pb,s,reset=self.fixture(True)
        e._receive_midi((191,12,127));self.hw(e,1)
        self.assertTrue(f.gated)
        for packet in ((191,44,127),(191,20,127),(191,12,127)):
            e._receive_midi(packet)
        self.ack(e);f.flush(backlog=True)
        self.assertEqual(m.plugin()['id'],pa)
        self.assertEqual((a.eval(),b.eval(),reset.pulses),(5,5,0))
        f.flush();self.assertEqual(m.plugin()['id'],pb)
        e._receive_midi((191,44,127));self.assertEqual(b.eval(),5)
        self.ack(e);e._receive_midi((191,44,127));self.assertEqual(b.eval(),5)
        e._receive_midi((191,12,127));self.assertEqual((a.eval(),b.eval()),(5,10))

    def test_locked_explicit_plugin_selection_keeps_lock_and_track_browse(self):
        e,m,f,a,b,t,pa,pb,s,_=self.fixture()
        other=m.create_track('custom','Other')
        e._receive_midi(sysex(11,13,(1,)))
        e._receive_midi(sysex(10,9,(0,1)))
        self.assertFalse(f.gated);self.assertEqual(m.selected_track,other)
        self.hw(e,1);self.assertTrue(f.gated);f.flush()
        self.assertTrue(m.locked);self.assertEqual(m.plugin()['id'],pb)
        self.assertEqual(m.track()['id'],t);self.assertEqual(m.selected_track,other)
        with self.assertRaises(ValueError):e.SelectPlugin('custom',t,pa)
        self.ack(e);e._receive_midi((191,12,127));e._receive_midi((191,44,127))
        self.assertEqual((a.eval(),b.eval()),(5,10))
        e._receive_midi(sysex(11,13,(0,)));f.flush()
        self.assertEqual(m.track()['id'],other)

    def test_locked_plugin_still_waits_for_learn_touch_and_latest_intent(self):
        e,m,f,a,b,t,pa,pb,s,_=self.fixture()
        e._receive_midi(sysex(11,13,(1,)));e._receive_midi((191,52,127))
        e._receive_midi(sysex(11,9,(1,)));self.hw(e,1);f.flush()
        self.assertEqual(m.plugin()['id'],pa)
        self.hw(e,0);e._receive_midi((191,52,0));f.flush()
        self.assertIsNotNone(f.pending)
        e._receive_midi(sysex(11,9,(0,)));f.flush()
        self.assertEqual(m.plugin()['id'],pa);self.assertFalse(e.GetControlState()['mapped'])
        self.ack(e);self.assertTrue(e.GetControlState()['mapped'])

    def test_device_bank_browse_not_selection_and_ninth_select(self):
        e,m,f,a,b,t,pa,pb,s,_=self.fixture()
        ids=[pa,pb]+[e.CreatePlugin('custom',t,'DEV'+str(i)) for i in range(2,9)]
        e._pending=b'';e._receive_midi(sysex(11,4,(8,)))
        import json
        packets=[json.loads(line)['midi'] for line in e._pending.splitlines()]
        self.assertIn(list(sysex(11,2,(9,))),packets)
        self.assertIn(list(sysex(11,3,(8,))),packets)
        details=[p for p in packets if p[5:7]==[11,5]]
        self.assertEqual([p[7] for p in details],[8])
        self.assertEqual(m.plugin()['id'],pa);self.assertIsNone(f.pending);self.assertFalse(f.gated)
        self.hw(e,0);f.flush();self.assertEqual(m.plugin()['id'],ids[8])
        self.assertEqual(e._host.plugin_index,8)
        self.assertEqual(e.GetControlStates(),[])
        before=copy.deepcopy(m.data);epoch=f.token
        for packet in (sysex(11,4,(7,)),sysex(11,4,(16,)),sysex(11,7,(1,)),sysex(11,7,(8,))):e._receive_midi(packet)
        self.assertEqual(m.data,before);self.assertEqual(f.token,epoch)

    def test_rename_comp_name_is_metadata_only_and_layout_independent(self):
        e,m,f,a,b,t,pa,pb,s,_=self.fixture()
        wire=e._host.controls['knob',1].target_id;identity=m.plugin()['device_id']
        a.owner.name='pixelSortV3';f.refresh_links()
        self.assertEqual(e.GetPlugins()[0]['name'],'pixelSortV3')
        m.rename('custom','Another Layout')
        a.owner.name='a_very_long_tool_name';f.refresh_links()
        self.assertEqual(m.plugin()['plugin_name'],'a_very_long_')
        self.assertEqual(m.plugin()['comp_name'],'a_very_long_tool_name')
        self.assertEqual(e._host.controls['knob',1].target_id,wire)
        self.assertEqual(m.plugin()['device_id'],identity);self.assertTrue(e.GetControlState()['mapped'])
        e.RenamePlugin('custom',t,pa,'MANUAL');a.owner.name='new';f.refresh_links()
        self.assertEqual(m.plugin()['plugin_name'],'MANUAL')
        e.SetPluginComp('custom',t,pa,a.owner);self.assertEqual(m.plugin()['plugin_name'],'new')

    def test_v2_focus_moves_without_merge_or_identity_changes(self):
        e,m,f,a,b,t,pa,pb,s,_=self.fixture()
        # Build a genuine v2 baseline: exactly one Plugin in each Track.
        old=copy.deepcopy(m.data);old['version']=2
        track=old['records'][0]['tracks'][0];second=copy.deepcopy(track)
        second.update(id='second',name='B',plugins=[track['plugins'].pop()],active_plugin=pb)
        old['records'][0]['tracks'].append(second)
        for item in old['records'][0]['tracks']:
            p=item['plugins'][0];item['focus_comp']=p.pop('focus_comp');p.pop('name_mode');p.pop('comp_name',None)
        before=copy.deepcopy(old);new=Layouts.migrate(old);Layouts.validate(new)
        self.assertEqual(old,before);self.assertEqual(new['version'],VERSION)
        self.assertEqual(Layouts.migrate(new),new);self.assertEqual(len(new['records'][0]['tracks']),2)
        for oldtrack,newtrack in zip(old['records'][0]['tracks'],new['records'][0]['tracks']):
            plugin=newtrack['plugins'][0]
            self.assertEqual(plugin['focus_comp'],oldtrack['focus_comp']);self.assertNotIn('focus_comp',newtrack)
            for key,value in oldtrack['plugins'][0].items():self.assertEqual(plugin[key],value)

    def test_linked_comp_rename_rebases_active_and_inactive_target_libraries(self):
        e,m,f,a,b,t,pa,pb,s,_=self.fixture()
        old_a=copy.deepcopy(m.plugin()['targets']);old_b=copy.deepcopy(m.plugin('custom',t,pb)['targets'])
        variant=e.CreatePlugin('custom',t,'VARIANT')
        m.plugin('custom',t,variant)['targets']=copy.deepcopy(old_a)
        m.plugin('custom',t,variant)['state']['page_targets']=copy.deepcopy(old_a)
        a.owner.path='/renamed_a';b.owner.path='/renamed_b';f.refresh_links()
        for pid,old,path in ((pa,old_a,'../renamed_a'),(pb,old_b,'../renamed_b')):
            plugin=m.plugin('custom',t,pid)
            self.assertEqual(plugin['targets'][0]['comp'],path)
            self.assertEqual(plugin['state']['page_targets'][0]['comp'],path)
            self.assertEqual(plugin['targets'][0]['identity'],old[0]['identity'])
            self.assertEqual(plugin['targets'][0]['id'],old[0]['id'])
        self.assertEqual(e.ownerComp.fetch('parameter_assignments')[0]['comp'],'../renamed_a')
        self.assertEqual(e.ownerComp.fetch('page_targets')[0]['comp'],'../renamed_a')
        self.assertEqual(m.plugin('custom',t,variant)['targets'][0]['comp'],'../renamed_a')
        self.assertEqual(m.plugin('custom',t,variant)['state']['page_targets'][0]['identity'],old_a[0]['identity'])

    def test_integrated_tick_partial_mapping_cannot_recall_previous_device(self):
        from unittest.mock import Mock
        import json,time
        e,m,f,a,b,t,pa,pb,s,_=self.fixture()
        child=Mock();child.poll.return_value=None;e._process=child;e._transport_ready=True
        e._started_at=time.monotonic();e._trace_control_midi=Mock()
        def line(message):return (json.dumps({'midi':message})+'\n').encode()
        old=e._host.controls['knob',1]
        tail=line(sysex(11,11,(old.index>>7,old.index&127,*digest(old.target_id,6),0,0,0)))
        split=len(tail)//2
        packet=line(sysex(11,7,(1,)))+line((191,12,127))+line((191,44,127))*255+tail[:split]
        with patch('RotoPythonExt.os.read',side_effect=[packet,BlockingIOError]),patch('RotoPythonExt.os.write',side_effect=lambda fd,data:len(data)):e.Tick()
        self.assertEqual(m.plugin()['id'],pa);self.assertTrue(f.gated)
        with patch('RotoPythonExt.os.read',side_effect=BlockingIOError),patch('RotoPythonExt.os.write',side_effect=lambda fd,data:len(data)):e.Tick()
        self.assertEqual(m.plugin()['id'],pb)
        with patch('RotoPythonExt.os.read',side_effect=[tail[split:],BlockingIOError]),patch('RotoPythonExt.os.write',side_effect=lambda fd,data:len(data)):e.Tick()
        self.assertIs(e._collection.bindings['knob',1].parameter,b)
        self.assertFalse(e.GetControlState()['mapped']);self.assertEqual((a.eval(),b.eval()),(5,5))

    def test_session_end_discards_locked_plugin_and_offline_follow_works(self):
        e,m,f,a,b,t,pa,pb,s,_=self.fixture()
        e._receive_midi(sysex(11,13,(1,)));e._receive_midi((191,52,127));self.hw(e,1)
        e.Disconnect();self.assertIsNone(f.pending)
        e._host.connected=e._host.plugin=True;f.flush();self.assertEqual(m.plugin()['id'],pa)
        e.Disconnect();f.observe(force=True);s[0]=(s[0][0],(b.owner,));f.observe(force=True);f.flush()
        self.assertEqual(m.plugin()['id'],pb);self.assertIsNone(e._process)

    def test_failure_rolls_back_plugin_and_preserves_transport(self):
        e,m,f,a,b,t,pa,pb,s,_=self.fixture()
        original=m.install
        def fail(record,*args,**kw):
            if record['device_id']==m.plugin('custom',t,pb)['device_id']:raise RuntimeError('Device fixture')
            return original(record,*args,**kw)
        with patch.object(m,'install',side_effect=fail):
            self.hw(e,1);f.flush()
        self.assertEqual(m.plugin()['id'],pa);self.assertIn('Device fixture',f.error)
        self.assertTrue(e._host.connected);self.assertFalse(e.GetControlState()['mapped'])
        self.assertEqual((a.eval(),b.eval()),(5,5))

    def test_latest_td_and_hardware_device_intent_wins_once(self):
        for last in ('td','hardware_plugin'):
            with self.subTest(last=last):
                e,m,f,a,b,t,pa,pb,s,_=self.fixture()
                e._receive_midi(sysex(11,13,(1,)))
                s[0]=(s[0][0],(b.owner,));f.observe(force=True)
                self.hw(e,0)
                if last=='td':
                    s[0]=(s[0][0],(a.owner,));f.observe(force=True)
                    s[0]=(s[0][0],(b.owner,));f.observe(force=True)
                e._receive_midi(sysex(11,13,(0,)))
                with patch.object(m,'install',wraps=m.install) as install:
                    f.flush();f.flush();self.assertLessEqual(install.call_count,1)
                self.assertEqual(m.plugin()['id'],pb if last=='td' else pa)

    def test_device_capacity_and_invalid_crud_are_atomic(self):
        e,m,f,a,b,t,pa,pb,s,_=self.fixture()
        for i in range(125):e.CreatePlugin('custom',t,'D'+str(i))
        before=copy.deepcopy(m.data)
        with self.assertRaisesRegex(ValueError,'capacity'):e.CreatePlugin('custom',t,'extra')
        with self.assertRaises(ValueError):e.SelectPlugin('custom',t,'unknown')
        with self.assertRaises(ValueError):e.SetPluginComp('custom',t,pb,a.owner)
        self.assertEqual(m.data,before)

    def test_rename_when_follow_off_keeps_identity_and_deferred_learn_name(self):
        e,m,f,a,b,t,pa,pb,s,_=self.fixture()
        e.ownerComp.par.Followcomp.val=False;e._host.learning=True
        identity=m.plugin()['device_id'];a.owner.name='NewName'
        f.observe(force=True);self.assertNotEqual(m.plugin()['plugin_name'],'NewName')
        e._host.learning=False;f.observe(force=True)
        self.assertEqual(m.plugin()['plugin_name'],'NewName')
        self.assertEqual(m.plugin()['device_id'],identity)

    def test_plugin_rollback_failure_pauses_until_explicit_repair(self):
        e,m,f,a,b,t,pa,pb,s,_=self.fixture()
        original=m.install
        with patch.object(m,'install',side_effect=RuntimeError('broken activation')):
            self.hw(e,1);f.flush()
        self.assertTrue(f.paused);self.assertTrue(f.gated);self.assertTrue(e._host.connected)
        self.assertEqual(m.plugin()['id'],pa);f.repair();f.flush()
        self.assertFalse(f.paused);self.assertFalse(f.gated);self.assertFalse(e.GetControlState()['mapped'])

    def test_delete_popup_expires_on_plugin_switch_and_last_device_guard(self):
        e,m,requests=test_delete_popup.DeletePopupTests().fixture();t=m.track()['id']
        original=m.plugin()['id'];other=e.CreatePlugin('custom',t,'Other')
        e.onParPulse(SimpleNamespace(name='Deleteplugin'));details=requests[-1]
        e.SelectPlugin('custom',t,other)
        e._on_delete_choice(dict(details=details,item=details['item']))
        self.assertEqual(len(m.track()['plugins']),2)
        e.SelectPlugin('custom',t,original);e.onParPulse(SimpleNamespace(name='Deleteplugin'))
        details=requests[-1];e._on_delete_choice(dict(details=details,item='Cancel'))
        self.assertEqual(len(m.track()['plugins']),2)
        e.onParPulse(SimpleNamespace(name='Deleteplugin'));details=requests[-1]
        e._on_delete_choice(dict(details=details,item=details['item']))
        self.assertEqual(m.plugin()['id'],other)
        with self.assertRaisesRegex(ValueError,'last Device'):e.RemovePlugin('custom',t,other)


if __name__=='__main__':unittest.main()
