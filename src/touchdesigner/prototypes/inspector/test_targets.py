"""Behavior at discovery/command seams; no TD or MIDI dependencies."""
from unittest import TestCase
from target_catalog import TargetService
from live_model import ControllerCatalog, StaleDraft
from test_live_model import Adapter, KEY, state


class Source:
    def __init__(self):self.session=1;self.scans=0;self.revision=0;self.reason='';self.exists=True
    def Scope(self,scope):return scope
    def Session(self):return self.session
    def row(self,index=0):return dict(owner_id=1,path='/effect',name='P'+str(index),label='Parameter',style='Float',reason=self.reason,fingerprint=(self.revision,))
    def Units(self,scope,kind):
        self.scans+=1
        for i in range(1000):yield self.row(i)
    def Resolve(self,path,name,kind):
        if not self.exists:raise ValueError('Target disappeared')
        return 'native parameter',self.row()


class Pending:
    def __init__(self,callback):self.callback=callback;self.dead=False
    def kill(self):self.dead=True
    def fire(self):
        if not self.dead:self.callback()


class TargetTests(TestCase):
    def setUp(self):
        self.source=Source();self.pending=[];self.events=[]
        def schedule(callback):
            p=Pending(callback);self.pending.append(p);return p
        self.catalog=TargetService(self.source,schedule,limit=4096)
    def drain(self):
        while self.pending:self.pending.pop(0).fire()
    def start(self,identity='view',scope='/effect',refresh=False):
        self.catalog.Start(identity,scope,'knob',lambda *r:self.events.append(r),refresh)
    def test_discovery_cooperates_then_reuses_shared_snapshot(self):
        self.start();self.assertLessEqual(self.catalog.Stats()['pending'],1)
        self.assertEqual(self.events,[]);self.drain()
        self.assertEqual(len(self.events[0][0]),1000)
        self.start('second');self.assertEqual(self.source.scans,1)
        self.assertEqual(self.catalog.Stats()['jobs'],0)
        self.assertEqual(self.events[0],self.events[1])
    def test_cancel_and_replacement_suppress_old_results(self):
        self.start();self.catalog.Cancel('view');self.drain();self.assertEqual(self.events,[])
        self.start();self.start(scope='/different');self.drain()
        self.assertEqual(len(self.events),1)
    def test_cache_total_entries_and_pages_are_bounded(self):
        for i in range(35):self.start(scope=str(i));self.drain()
        stats=self.catalog.Stats();self.assertLessEqual(stats['pages'],32);self.assertLessEqual(stats['entries'],4096)
    def test_truncated_results_are_explicit(self):
        self.catalog.limit=200;self.start();self.drain()
        self.assertEqual(len(self.events[0][0]),200);self.assertTrue(self.events[0][1])
    def test_session_change_cancels_inflight_without_caching(self):
        self.start();self.source.session+=1;self.drain()
        self.assertIn('session changed',self.events[0][2]);self.assertEqual(self.catalog.Stats()['pages'],0)
    def test_handles_revalidate_definition_readonly_missing_kind_and_reset(self):
        self.start();self.drain();handle=self.events[0][0][0]['handle']
        self.assertEqual(self.catalog.Resolve(handle,'knob'),'native parameter')
        self.source.revision=1
        with self.assertRaisesRegex(ValueError,'definition changed'):self.catalog.Resolve(handle,'knob')
        self.source.revision=0;self.source.reason='Read only'
        with self.assertRaisesRegex(ValueError,'Read only'):self.catalog.Resolve(handle,'knob')
        self.source.reason='';self.source.exists=False
        with self.assertRaisesRegex(ValueError,'disappeared'):self.catalog.Resolve(handle,'knob')
        self.source.exists=True
        with self.assertRaisesRegex(ValueError,'expired'):self.catalog.Resolve(handle,'button')
        self.catalog.Reset()
        with self.assertRaisesRegex(ValueError,'expired'):self.catalog.Resolve(handle,'knob')
    def test_max_two_jobs_and_callback_failures_are_contained(self):
        self.start('a');self.start('b')
        with self.assertRaisesRegex(ValueError,'busy'):self.start('c')
        self.catalog.Cancel('a');self.catalog.Cancel('b')
        self.catalog.Start('bad','/effect','knob',lambda *r:(_ for _ in ()).throw(RuntimeError('bad view')))
        self.drain();self.assertEqual(self.catalog.Stats()['errors'],('bad view',))


class AssignAdapter(Adapter):
    def __init__(self):super().__init__();self.assigns=[]
    def Assign(self,key,slot,handle):
        self.assigns.append((key,slot,handle));record=state();record.update(slot=slot+1,id='assigned')
        self.records[key]=[r for r in self.records[key] if r['slot']!=slot+1]+[record]
        return dict(id='assigned',message='Assigned')


class TypedCommandTests(TestCase):
    def setUp(self):self.adapter=AssignAdapter();self.model=ControllerCatalog(self.adapter)
    def commit(self,value):
        row=dict(self.model.GetCatalog(KEY)[1]);row['Value']=value
        return self.model.Commit(KEY,1,row,self.model.GetToken(KEY,1))
    def test_empty_slot_assignment_and_learn_do_not_require_previous_registration(self):
        self.adapter.learning=True;self.model.Sync()
        self.assertTrue(self.model.Capabilities(KEY,0)['assign']['enabled'])
        self.model.Assign(KEY,0,'handle',self.model.GetToken(KEY,0))
        self.assertEqual(self.model.Info(KEY,0)['id'],'assigned');self.assertEqual(self.adapter.writes,[])
    def test_assignment_is_fenced_by_context_touch_and_stale_token(self):
        other=('layout','track','other');self.adapter.records[other]=[]
        with self.assertRaises(ValueError):self.model.Assign(other,0,'handle',self.model.GetToken(other,0))
        self.adapter.records[KEY][0]['touched']=True;self.model.Sync()
        with self.assertRaises(ValueError):self.model.Assign(KEY,1,'handle',self.model.GetToken(KEY,1))
        self.adapter.records[KEY][0]['touched']=False;token=self.model.GetToken(KEY,0);self.adapter.session+=1
        with self.assertRaises(StaleDraft):self.model.Assign(KEY,0,'handle',token)
        self.assertEqual(self.adapter.assigns,[])
    def test_integer_menu_toggle_reject_fractional_values_and_invalid_choices(self):
        r=self.adapter.records[KEY][0]
        for style,mode,maximum in [('Int','value',7),('Menu','value',2),('Toggle','toggle',1)]:
            r.update(parameter_style=style,mode=mode,maximum=maximum,menu_names=['a','b','c'],menu_labels=['A','B','C']);self.model.Sync()
            with self.assertRaises(ValueError):self.commit(.5)
            self.commit(1)
        r.update(parameter_style='Menu',mode='value',maximum=5);self.model.Sync()
        with self.assertRaisesRegex(ValueError,'unavailable'):self.commit(3)
        r.update(parameter_style='Toggle',mode='toggle',maximum=5);self.model.Sync()
        with self.assertRaisesRegex(ValueError,'0 or 1'):self.commit(2)
    def test_pulse_schema_remains_readonly(self):
        self.adapter.records[KEY][0].update(parameter_style='Pulse',mode='pulse');self.model.Sync()
        schema=self.model.ValueSchema(KEY,1);self.assertEqual(schema['kind'],'pulse');self.assertIn('Pulse',schema['reason'])
        with self.assertRaises(ValueError):self.commit(1)
        self.assertEqual(self.adapter.writes,[])
