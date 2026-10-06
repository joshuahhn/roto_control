"""Layout isolation, transactional preflight and no parameter presets."""
import copy
import json
from types import SimpleNamespace
import unittest
import test_assignment
from controls import Controls
from collection_protocol import CollectionHost
from layouts import Layouts
from protocol import digest,sysex

class Par:
    def __init__(self,value):self.val=value;self.enable=True
    def eval(self):return self.val
class Pars:
    def __setattr__(self,name,value):
        old=self.__dict__.get(name)
        if isinstance(old,Par) and not isinstance(value,Par):old.val=value
        else:object.__setattr__(self,name,value)
class Table:
    numRows=1
    def row(self,index):return [SimpleNamespace(val='id')]
    def clear(self):pass
    def appendRow(self,row):pass

class LayoutTests(unittest.TestCase):
    def fixture(self):
        ext=test_assignment.AssignmentTests().fixture()
        p=test_assignment.AssignmentTests().parameter()
        ext._collection=Controls([dict(kind='knob',slot=1,id='original',parameter=p)])
        ext._host=CollectionHost(ext._send,ext._assign_control,list(ext._collection.specs()),'test')
        ext._host.connected=ext._host.plugin=True
        ext._restore_pending=ext._restoring=False;ext._layouts=None;ext._layout_dirty=False;ext._free_learner=None
        pars=Pars()
        for name,value in [('Value',.5),('Offerparameter',False),('Groupid','test'),('Setupmode','collection'),('Trackname','EFFECT'),('Pluginname','CUSTOM')]:setattr(pars,name,Par(value))
        ext.ownerComp.par=pars
        inspector=SimpleNamespace(store=lambda key,value:None)
        oldop=ext.ownerComp.op
        ext.ownerComp.op=lambda name:SimpleNamespace(par=SimpleNamespace(Speed=p),valid=p.owner.valid) if name=='../master' else Table() if name=='base_targets/targets' else inspector if name=='inspector' else oldop(name)
        manager=Layouts(ext);ext._layouts=manager
        return ext,manager,p

    def test_a_b_a_reads_actual_value_without_writes_or_pulse(self):
        ext,m,p=self.fixture();identity=ext._host.controls['knob',1].target_id
        b=m.create('B');m.select(b);self.assertEqual(ext.GetControlStates(),[])
        p.val=8
        m.select('custom')
        self.assertEqual(ext.GetValue('original'),8)
        self.assertEqual(ext._host.controls['knob',1].target_id,identity)
        self.assertFalse(ext._host.controls['knob',1].mapped)
        m.rename('custom','Renamed');self.assertEqual(m.record()['device_id'],'TD controls:test')
        self.assertEqual(p.eval(),8)

    def test_lock_learning_touch_preflight_and_callback_reject_atomic(self):
        ext,m,p=self.fixture();b=m.create('B');before=copy.deepcopy(m.data);host=ext._host
        for guard in ('locked','touched'):
            setattr(m,guard,True if guard=='locked' else {52})
            with self.assertRaises(ValueError):m.select(b)
            self.assertEqual(m.data,before);self.assertIs(ext._host,host)
            setattr(m,guard,False if guard=='locked' else set())
        ext._host.learning=True
        with self.assertRaises(ValueError):m.select(b)
        ext._host.learning=False
        with self.assertRaisesRegex(ValueError,'factory'):ext.BindCallback(id='cb',label='Callback',minimum=0,maximum=1,value=0,on_change=lambda e:None)
        self.assertEqual(m.data,before);self.assertIs(ext._host,host)

    def test_invalid_destination_reject_and_active_delete_uses_id(self):
        ext,m,p=self.fixture();b=m.create('B');original=copy.deepcopy(m.record())
        m.plugin(b)['targets']=[dict(original['targets'][0],minimum=-100)]
        with self.assertRaises(ValueError):m.select(b)
        self.assertEqual(m.data['active'],'custom')
        m.plugin(b)['targets']=[]
        ext.SetLayoutNames('NEW','CUSTOM')
        self.assertTrue(m.remove('custom'))
        self.assertEqual(m.data['active'],b);self.assertEqual(len(m.data['records']),1)
        with self.assertRaises(ValueError):m.remove(b)

    def test_missing_target_retained_after_active_deletion_switch_and_restore(self):
        ext,m,p=self.fixture();b=m.create('B');m.capture(force=True)
        p.owner.valid=False
        m.select(b);m.select('custom')
        self.assertEqual(ext.GetControlStates(),[])
        self.assertEqual(m.record()['targets'][0]['id'],'original')
        self.assertEqual(ext.GetControlCatalog()[0]['error'],'Target unavailable')
        m.restore();self.assertEqual(m.record()['targets'][0]['id'],'original')
        ext.RemoveControl('original');m.capture(force=True)
        self.assertEqual(m.record()['targets'],[])

    def test_offline_clear_all_reconciles_empty_from_scoped_removed_ack(self):
        ext,m,p=self.fixture();target=ext._host.controls['knob',1]
        packet=sysex(11,11,(0,target.index,*digest(target.target_id,6),0,0,0))
        ext._host.connected=ext._host.plugin=False
        ext.RemoveAllControls();m.capture(force=True)
        self.assertEqual(m.record()['targets'],[])
        m.restore();ext._host.connected=ext._host.plugin=True
        before=ext._pending
        self.assertTrue(m.receive(packet));self.assertTrue(m.confirmed)
        self.assertNotEqual(ext._pending,before)
        packets=[json.loads(line)['midi'] for line in ext._pending[len(before):].splitlines()]
        self.assertEqual(packets,[list(sysex(11,14,(0,0)))])

    def test_capacity_and_version_validation(self):
        ext,m,p=self.fixture()
        for i in range(7):m.create('Layout '+str(i))
        m.create('ninth Layout')
        self.assertEqual(len(m.data['records']),9)
        bad=copy.deepcopy(m.data);bad['version']=99
        with self.assertRaises(ValueError):Layouts.validate(bad)

    def test_reassign_cancels_removed_identity_and_late_ack_cannot_unmap(self):
        ext,m,p=self.fixture();target=ext._host.controls['knob',1]
        packet=sysex(11,11,(0,target.index,*digest(target.target_id,6),0,0,0))
        ext._host.connected=ext._host.plugin=False
        ext.RemoveAllControls();m.capture(force=True)
        ext.AssignParameter('knob',1,p);m.capture(force=True)
        ext._pending=b''
        self.assertFalse(m.receive(packet))
        self.assertEqual(ext._pending,b'')
        self.assertEqual(ext.ownerComp.fetch('pending_unmap_identities'),[])

class MultiTrackTests(unittest.TestCase):
    fixture=LayoutTests.fixture

    def packets(self,ext):
        return [tuple(json.loads(line)['midi']) for line in ext._pending.splitlines()]

    def test_v1_migration_keeps_each_layout_and_all_wire_state(self):
        ext,m,p=self.fixture()
        a=copy.deepcopy(m.record());b=copy.deepcopy(a)
        b.update(id='other',name='Other',device_id='old.device',group_id='old.group')
        a['state']['pending_unmaps']=[('knob',2)]
        a['state']['removed_controls']=['deleted']
        old=dict(version=1,active='other',records=[a,b]);before=copy.deepcopy(old)
        new=Layouts.migrate(old);Layouts.validate(new)
        self.assertEqual(old,before)
        self.assertEqual(new['active'],'other')
        for old_record,new_layout in zip(old['records'],new['records']):
            self.assertEqual((new_layout['id'],new_layout['name']),(old_record['id'],old_record['name']))
            self.assertEqual(len(new_layout['tracks']),1)
            plugin=new_layout['tracks'][0]['plugins'][0]
            for field in ('device_id','group_id','targets','state','plugin_name'):
                self.assertEqual(plugin[field],old_record[field])
        self.assertEqual(Layouts.migrate(new),new)

    def test_tracks_same_plugin_name_independent_recall_and_clear(self):
        ext,m,p=self.fixture();a=m.track()['id'];a_device=m.plugin()['device_id']
        b=ext.CreateTrack('custom','VISUAL');ext.SelectTrack('custom',b)
        self.assertNotEqual(m.plugin()['device_id'],a_device)
        self.assertEqual(m.plugin()['plugin_name'],'CUSTOM')
        self.assertEqual(ext.GetControlStates(),[])
        assigned=ext.AssignParameter('knob',1,p)
        ext.RemoveAllControls();m.capture(force=True)
        ext.SelectTrack('custom',a)
        self.assertEqual(ext.GetControlState()['id'],'original')
        self.assertEqual(m.plugin()['device_id'],a_device)
        ext.SelectTrack('custom',b)
        self.assertEqual(ext.GetControlStates(),[])
        self.assertIn(assigned['id'],m.plugin()['state']['removed_controls'])

    def test_track_page_is_not_selection_and_current_track_only_plugin_list(self):
        ext,m,p=self.fixture();original=m.track()['id'];ids=[original]
        for n in range(8):ids.append(ext.CreateTrack('custom','TRACK'+str(n)))
        ext._pending=b'';host=ext._host
        self.assertTrue(m.receive(sysex(10,6,(0,8))))
        self.assertIs(ext._host,host);self.assertEqual(m.track()['id'],original)
        packets=self.packets(ext)
        self.assertEqual([packet[6] for packet in packets],[4,5,7,8])
        self.assertEqual(packets[1][7:9],(0,8))
        self.assertEqual(packets[2][7:9],(0,8))
        ext._pending=b'';m.receive(sysex(10,9,(0,8)))
        self.assertEqual(m.track()['id'],ids[8]);packets=self.packets(ext)
        self.assertFalse(any(packet[5:7]==(12,4) for packet in packets)) # no Track echo
        plugins=[packet for packet in packets if packet[5:7]==(11,5)]
        self.assertEqual(len(plugins),1);self.assertEqual(plugins[0][7],0)
        self.assertEqual(plugins[0][8:16],digest(m.plugin()['device_id'],8))
        self.assertIn(sysex(11,8,(0,0,0)),packets)

    def test_host_track_select_and_reconnect_announce_saved_track(self):
        ext,m,p=self.fixture();b=m.create_track('custom','VISUAL')
        ext._pending=b'';m.select_track('custom',b)
        self.assertTrue(any(packet[5:9]==(12,4,0,1) for packet in self.packets(ext)))
        m.capture(force=True);data=copy.deepcopy(m.data)
        replacement=Layouts(ext);ext._layouts=replacement;replacement.restore()
        self.assertEqual(replacement.data,data)
        ext._pending=b'';ext._host.receive(sysex(10,12))
        packets=self.packets(ext)
        self.assertIn(sysex(10,4,(0,2)),packets)
        self.assertTrue(any(packet[5:9]==(12,4,0,1) for packet in packets))

    def test_lock_keeps_routing_track_and_unlock_follows_selected(self):
        ext,m,p=self.fixture();a=m.track()['id'];b=m.create_track('custom','VISUAL');host=ext._host
        m.receive(sysex(11,13,(1,)))
        with self.assertRaisesRegex(ValueError,'Unlock'):ext.SelectTrack('custom',b)
        ext._pending=b'';m.receive(sysex(10,9,(0,1)))
        self.assertIs(ext._host,host);self.assertEqual(m.track()['id'],a)
        self.assertEqual(ext.GetLayoutContext()['selected_track_id'],b)
        self.assertEqual(ext._pending,b'')
        m.receive(sysex(11,13,(0,)))
        self.assertEqual(m.track()['id'],b);self.assertFalse(m.confirmed)

    def test_invalid_page_index_and_plugin_index_never_switch_layout(self):
        ext,m,p=self.fixture();m.create('Other');before=copy.deepcopy(m.data);host=ext._host
        ext._pending=b''
        for packet in (sysex(10,9,(127,127)),sysex(10,9,(0,)),sysex(10,6,(0,1)),sysex(11,7,(1,)),sysex(11,4,(8,))):
            self.assertTrue(m.receive(packet))
        self.assertEqual(m.data,before);self.assertIs(ext._host,host);self.assertEqual(ext._pending,b'')

    def test_rename_and_reorder_do_not_change_identity(self):
        ext,m,p=self.fixture();a=m.track()['id'];b=m.create_track('custom','VISUAL')
        before=copy.deepcopy(m.plugin());ext.RenameTrack('custom',a,'RENAMED')
        self.assertEqual(m.plugin(),before);self.assertEqual(ext.GetTracks()[0]['name'],'RENAMED')
        m.layout()['tracks'].reverse();m.save();m.announce_tracks()
        self.assertEqual(m.plugin()['device_id'],before['device_id'])
        returned=ext.GetTracks();returned[0]['name']='MUTATED'
        self.assertEqual(m.track('custom',b)['name'],'VISUAL')

    def test_last_track_guard_and_inactive_layout_edit(self):
        ext,m,p=self.fixture();b=m.create('Other');t=m.track(b)['id'];host=ext._host
        with self.assertRaisesRegex(ValueError,'last Track'):ext.RemoveTrack(b,t)
        t2=ext.CreateTrack(b,'SECOND');ext.RemoveTrack(b,t)
        self.assertEqual(m.layout(b)['active_track'],t2)
        self.assertEqual(m.data['active'],'custom');self.assertIs(ext._host,host)

    def test_stale_ack_and_cc_do_not_route_unconfirmed_destination(self):
        ext,m,p=self.fixture();target=ext._host.controls['knob',1]
        stale=sysex(11,11,(0,target.index,*digest(target.target_id,6),0,0,0))
        b=m.create_track('custom','VISUAL');m.select_track('custom',b)
        ext.AssignParameter('knob',1,p);m.capture(force=True)
        value=p.eval()
        ext._host.receive(stale)
        ext._host.receive((191,12,127));ext._host.receive((191,44,127))
        self.assertFalse(ext._host.controls['knob',1].mapped);self.assertEqual(p.eval(),value)

    def test_failed_install_rolls_back_registry_and_leaves_controls_unmapped(self):
        ext,m,p=self.fixture();b=m.create_track('custom','VISUAL');previous=copy.deepcopy(m.data)
        original=ext.BindControls;failed=[]
        def fail_once(*args,**kwargs):
            if not failed:failed.append(True);raise RuntimeError('fixture install failure')
            return original(*args,**kwargs)
        ext.BindControls=fail_once
        with self.assertRaisesRegex(RuntimeError,'fixture'):m.select_track('custom',b)
        self.assertEqual(m.data,previous);self.assertFalse(ext._host.controls['knob',1].mapped)
        self.assertTrue(ext._host.connected and ext._host.plugin)
        self.assertEqual(ext.GetControlState()['id'],'original')

    def test_pulse_never_fires_on_switch_or_restore(self):
        ext,m,p=self.fixture();a=m.track()['id'];pulse=test_assignment.AssignmentTests().parameter('Pulse','Reset')
        oldop=ext.ownerComp.op
        ext.ownerComp.op=lambda name:SimpleNamespace(par=SimpleNamespace(Speed=p,Reset=pulse),valid=True) if name=='../master' else oldop(name)
        ext.AssignParameter('button',1,pulse);m.capture(force=True)
        b=m.create_track('custom','VISUAL');m.select_track('custom',b);m.select_track('custom',a);m.restore()
        self.assertEqual(pulse.pulses,0)

    def test_pending_output_discard_preserves_partial_json_frame(self):
        ext,m,p=self.fixture();b=m.create_track('custom','VISUAL')
        ext._host.connected=ext._host.plugin=False
        ext._pending=b'44, 0]}\n{"midi": [191, 12, 127]}\n'
        m.select_track('custom',b)
        self.assertEqual(ext._pending,b'44, 0]}\n')

    def test_invalid_nested_registry_rejected(self):
        ext,m,p=self.fixture();b=m.create_track('custom','VISUAL')
        for mutation in ('device','track','active','plugins'):
            bad=copy.deepcopy(m.data);tracks=bad['records'][0]['tracks']
            if mutation=='device':tracks[1]['plugins'][0]['device_id']=tracks[0]['plugins'][0]['device_id']
            elif mutation=='track':tracks[1]['id']=tracks[0]['id']
            elif mutation=='active':bad['records'][0]['active_track']='missing'
            else:tracks[0]['plugins']=[]
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):Layouts.validate(bad)

    def test_deferred_display_callback_does_not_overwrite_pending_track_menu(self):
        ext,m,p=self.fixture();a=m.track()['id'];b=m.create_track('custom','VISUAL')
        ext.ownerComp.par.Track=Par(a);ext.ownerComp.par.Track.name='Track'
        ext.ownerComp.par.Trackname.name='Trackname';m.select_track('custom',b)
        ext.ownerComp.par.Track=a
        ext.onParValueChange(ext.ownerComp.par.Trackname,'EFFECT')
        self.assertEqual(ext.ownerComp.par.Track.eval(),a)
        ext.onParValueChange(ext.ownerComp.par.Track,b)
        self.assertEqual(m.track()['id'],a)
