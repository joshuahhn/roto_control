"""Tests for the authoritative live adapter seam, with no TD or MIDI writes."""
import copy
import unittest
from live_model import ControllerCatalog, StaleDraft

KEY=('layout','track','device')

def state(value=.4):
    return dict(id='target',kind='knob',slot=2,label='Threshold',comp='/effect',parameter='Threshold',minimum=0.,maximum=1.,value=value,valid=True,mapped=True,connected=True,plugin=True,mode='value',parameter_style='Float')

class Adapter:
    def __init__(self):
        self.records={KEY:[state()]};self.active=KEY;self.session=1;self.learning=False;self.writes=[];self.pings=[];self.clears=[];self.accept_ping=True
    def Session(self):return self.session
    def Status(self):return dict(Connected=True,Learning=self.learning,Active=self.active)
    def ActiveContext(self):return self.active
    def Exists(self,key):return key in self.records
    def Read(self,key):return copy.deepcopy(self.records[key])
    def Choices(self,name,key):return [(KEY[('Layout','Track','Device').index(name)],name)]
    def Write(self,key,info,value):
        if key!=self.active:raise ValueError('Browse only')
        if self.learning:raise ValueError('Exit LEARN')
        self.writes.append((key,info['id'],value));self.records[key][0]['value']=value
    def Ping(self,key,info):
        self.pings.append((key,info['id']));return self.accept_ping
    def Clear(self,key,info):
        self.clears.append((key,info['id']))
        self.records[key]=[r for r in self.records[key] if r['id']!=info['id']]

class LiveModelTests(unittest.TestCase):
    def setUp(self):
        self.adapter=Adapter();self.model=ControllerCatalog(self.adapter);self.events=[]
        self.model.Subscribe('view',KEY,lambda *event:self.events.append(event))
    def test_real_slot_projection_and_readonly_shared_cache(self):
        rows=self.model.GetCatalog(KEY)
        self.assertEqual(rows[1]['Value'],.4);self.assertEqual(rows[0]['Destination'],'')
        self.assertIs(rows,self.model.GetCatalog(KEY))
        with self.assertRaises(TypeError):rows[1]['Value']=.2
    def test_event_sync_updates_values_without_changing_draft_revision(self):
        token=self.model.GetToken(KEY,1)
        self.adapter.records[KEY][0]['value']=.8;self.model.Sync();self.model.Flush()
        self.assertEqual(self.model.GetCatalog(KEY)[1]['Value'],.8)
        self.assertEqual(self.model.GetToken(KEY,1),token)
        self.assertEqual(len(self.events),1)
        for _ in range(100):self.model.Sync();self.model.Flush()
        self.assertEqual(len(self.events),1)
    def test_mapping_and_menu_changes_reject_old_tokens(self):
        for field,value in [('id','other'),('menu_names',['a','b'])]:
            token=self.model.GetToken(KEY,1)
            self.adapter.records[KEY][0][field]=value;self.model.Sync()
            draft=dict(self.model.GetCatalog(KEY)[1]);draft['Value']=.3
            with self.assertRaises(StaleDraft):self.model.Commit(KEY,1,draft,token)
        self.assertEqual(self.adapter.writes,[])
    def test_commit_goes_through_adapter_once_and_metadata_is_readonly(self):
        token=self.model.GetToken(KEY,1);draft=dict(self.model.GetCatalog(KEY)[1]);draft['Value']=.6
        self.model.Commit(KEY,1,draft,token)
        self.assertEqual(self.adapter.writes,[(KEY,'target',.6)])
        self.assertEqual(self.model.GetCatalog(KEY)[1]['Value'],.6)
        draft['Label']='rename'
        with self.assertRaises(ValueError):self.model.Commit(KEY,1,draft,self.model.GetToken(KEY,1))
        self.assertEqual(len(self.adapter.writes),1)
    def test_invalid_values_and_pulse_never_write(self):
        for value in [-1,2,float('nan'),float('inf')]:
            draft=dict(self.model.GetCatalog(KEY)[1]);draft['Value']=value
            with self.assertRaises(ValueError):self.model.Commit(KEY,1,draft,self.model.GetToken(KEY,1))
        self.adapter.records[KEY][0]['mode']='pulse';self.model.Sync()
        with self.assertRaises(ValueError):self.model.Commit(KEY,1,dict(self.model.GetCatalog(KEY)[1]),self.model.GetToken(KEY,1))
        self.assertEqual(self.adapter.writes,[])
    def test_session_fence_and_hardware_learn(self):
        token=self.model.GetToken(KEY,1);self.adapter.session+=1;self.adapter.learning=True
        self.model.Sync();self.model.Flush()
        self.assertNotEqual(token,self.model.GetToken(KEY,1));self.assertTrue(self.model.Learn)
        with self.assertRaises(ValueError):self.model.SetLearn(False)
    def test_browse_and_deleted_contexts_never_route_controller(self):
        other=('layout','track','other');self.adapter.records[other]=[state(.7)]
        row=self.model.GetCatalog(other)[1]
        self.assertEqual(self.adapter.active,KEY);self.assertEqual(row['Value'],.7)
        draft=dict(row);draft['Value']=.5
        with self.assertRaises(ValueError):self.model.Commit(other,1,draft,self.model.GetToken(other,1))
        del self.adapter.records[other];self.model.Sync()
        self.assertFalse(self.model.HasContext(other));self.assertEqual(self.adapter.writes,[])
    def test_bounded_source_and_eviction_cannot_revalidate_a_stale_draft(self):
        token=self.model.GetToken(KEY,1)
        for i in range(20):
            key=('layout','track','device'+str(i));self.adapter.records[key]=[state()];self.model.GetCatalog(key)
        self.assertLessEqual(len(self.model._source),4)
        self.assertLessEqual(len(self.model._info),4)
        self.assertLessEqual(len(self.model._cache),4)
        self.assertNotEqual(token,self.model.GetToken(KEY,1))
    def test_synthetic_traffic_and_restore_are_blocked(self):
        for call in [lambda:self.model.UpdateValues(KEY,{1:.1}),self.model.Snapshot,self.model.ResetDemo,lambda:self.model.Restore({})]:
            with self.assertRaises(ValueError):call()

    def test_ping_reoffers_forgotten_mapping_without_value_or_pulse_dispatch(self):
        self.adapter.learning=True
        self.adapter.records[KEY][0].update(mapped=False,mode='pulse',kind='button',slot=1)
        self.model.Sync();token=self.model.GetToken(KEY,8)
        self.assertTrue(self.model.Ping(KEY,8,token))
        self.assertEqual(self.adapter.pings,[(KEY,'target')]);self.assertEqual(self.adapter.writes,[])
        self.assertFalse(self.model.Info(KEY,8)['mapped'])  # Sending is not an ACK.
        self.assertEqual(self.adapter.records[KEY][0]['value'],.4)

    def test_ping_guards_and_rejection_do_not_report_success(self):
        with self.assertRaises(ValueError):self.model.Ping(KEY,1,self.model.GetToken(KEY,1))
        self.adapter.learning=True
        for field in ('connected','plugin','valid'):
            self.adapter.records[KEY][0][field]=False;self.model.Sync()
            with self.assertRaises(ValueError):self.model.Ping(KEY,1,self.model.GetToken(KEY,1))
            self.adapter.records[KEY][0][field]=True
        self.assertEqual(self.adapter.pings,[])
        self.adapter.accept_ping=False;self.model.Sync()
        with self.assertRaises(ValueError):self.model.Ping(KEY,1,self.model.GetToken(KEY,1))

    def test_clear_removes_only_selected_mapping_and_does_not_write_values(self):
        other=state(.7);other.update(id='other',slot=3)
        self.adapter.records[KEY].append(other);self.model.Sync()
        self.assertTrue(self.model.Clear(KEY,1,self.model.GetToken(KEY,1)))
        self.assertEqual(self.adapter.clears,[(KEY,'target')]);self.assertEqual(self.adapter.writes,[])
        self.assertEqual(self.adapter.records[KEY],[other]);self.assertEqual(self.model.Info(KEY,1),{})

    def test_clear_learn_touch_and_empty_slot_guards(self):
        self.adapter.learning=True
        with self.assertRaises(ValueError):self.model.Clear(KEY,1,self.model.GetToken(KEY,1))
        self.adapter.learning=False;self.adapter.records[KEY][0]['touched']=True
        with self.assertRaises(ValueError):self.model.Clear(KEY,1,self.model.GetToken(KEY,1))
        with self.assertRaises(ValueError):self.model.Clear(KEY,0,self.model.GetToken(KEY,0))
        self.assertEqual(self.adapter.clears,[])

    def test_ping_and_clear_fence_session_target_and_browse(self):
        other=('layout','track','other');self.adapter.records[other]=[state(.7)]
        self.adapter.learning=True
        for action in (self.model.Ping,self.model.Clear):
            token=self.model.GetToken(KEY,1);self.adapter.session+=1
            with self.assertRaises(StaleDraft):action(KEY,1,token)
            token=self.model.GetToken(KEY,1);self.adapter.records[KEY][0]['id']+='x'
            with self.assertRaises(StaleDraft):action(KEY,1,token)
            with self.assertRaises(ValueError):action(other,1,self.model.GetToken(other,1))
        self.assertEqual(self.adapter.pings,[]);self.assertEqual(self.adapter.clears,[])

if __name__=='__main__':unittest.main()
