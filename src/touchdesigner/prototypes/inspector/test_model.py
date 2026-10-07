"""Core tests for shared state, cache bounds and hostile update sequences."""
import gc
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('inspector_catalog_model',Path(__file__).with_name('model.py'))
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
CatalogModel=module.CatalogModel
CONTEXTS=module.CONTEXTS
CTX=CONTEXTS[0]

class ModelTests(unittest.TestCase):
    def setUp(self):
        self.scheduled=[]
        self.model=CatalogModel(schedule=lambda:self.scheduled.append(True),capacity=2)

    def test_shared_read_only_catalog_and_lru(self):
        first=self.model.GetCatalog(CTX)
        self.assertIs(first,self.model.GetCatalog(CTX))
        with self.assertRaises(TypeError):first[1]['Value']=.2
        for context in CONTEXTS:self.model.GetCatalog(context)
        self.assertEqual(self.model.Stats()['cache_contexts'],2)
        self.assertEqual(first[1]['Value'],.45)
        self.assertEqual(self.model.GetCatalog(CTX)[1]['Value'],.45)

    def test_bursts_are_atomic_bounded_and_coalesced(self):
        events=[];self.model.Subscribe('a',CTX,lambda *x:events.append(x))
        for i in range(1000):self.model.UpdateValues(CTX,{1:i/1000})
        self.assertEqual(len(self.scheduled),1)
        self.assertEqual(self.model.Stats()['pending_slots'],1)
        self.model.Flush()
        self.assertEqual(len(events),1)
        self.assertEqual(self.model.GetCatalog(CTX)[1]['Value'],.999)
        for i in range(100):self.model.UpdateValues(CTX,{1:.999})
        self.assertFalse(self.model.Stats()['scheduled'])

    def test_invalid_batches_never_partially_write(self):
        for bad in [{1:.2,16:.3},{1:.2,2:float('nan')},{1:.2,2:2},{True:.2},{1:'x'},{1:float('inf')}]:
            with self.assertRaises(ValueError):self.model.UpdateValues(CTX,bad)
            self.assertEqual(self.model.GetCatalog(CTX)[1]['Value'],.45)
        self.assertFalse(self.model.Stats()['scheduled'])

    def test_context_isolation_and_generation_fence(self):
        other=CONTEXTS[1];events=[]
        self.model.Subscribe('other',other,lambda *x:events.append(x))
        self.model.UpdateValues(CTX,{1:.2});self.model.Flush()
        self.assertEqual(events,[])
        generation=self.model.Generation;self.model.Invalidate()
        with self.assertRaises(module.StaleDraft):self.model.UpdateValues(CTX,{1:.3},generation=generation)

    def test_revision_conflicts_do_not_clobber_mapping(self):
        token=self.model.GetToken(CTX,1)
        record=dict(self.model.GetCatalog(CTX)[1]);record['Label']='first'
        self.model.Commit(CTX,1,record,token)
        record['Label']='second'
        with self.assertRaises(module.StaleDraft):self.model.Commit(CTX,1,record,token)
        self.assertEqual(self.model.GetCatalog(CTX)[1]['Label'],'first')

    def test_live_value_does_not_invalidate_metadata_token(self):
        token=self.model.GetToken(CTX,1)
        self.model.UpdateValues(CTX,{1:.7})
        self.assertEqual(token,self.model.GetToken(CTX,1))

    def test_invalid_mapping_atomic_and_evicted_values_survive(self):
        token=self.model.GetToken(CTX,1)
        invalid=dict(self.model.GetCatalog(CTX)[1]);invalid['Maximum']=invalid['Minimum']
        with self.assertRaises(ValueError):self.model.Commit(CTX,1,invalid,token)
        self.model.UpdateValues(CTX,{1:.6})
        for c in CONTEXTS:self.model.GetCatalog(c)
        self.assertEqual(self.model.GetCatalog(CTX)[1]['Value'],.6)

    def test_subscriber_failure_and_dead_bound_method_are_isolated(self):
        class View:
            def callback(self,*args):pass
        view=View();self.model.Subscribe('dead',CTX,view.callback);del view;gc.collect()
        def broken(*args):raise RuntimeError('broken consumer')
        events=[];self.model.Subscribe('bad',CTX,broken);self.model.Subscribe('good',CTX,lambda *x:events.append(x))
        self.model.UpdateValues(CTX,{1:.3});self.model.Flush()
        self.assertEqual(len(events),1)
        self.assertEqual(self.model.Stats()['subscribers'],1)
        self.assertEqual(self.model.Stats()['subscriber_errors'],['broken consumer'])

    def test_reentrant_notification_is_not_lost(self):
        def callback(*args):self.model.UpdateValues(CTX,{2:.3})
        self.model.Subscribe('view',CTX,callback)
        self.model.UpdateValues(CTX,{1:.3});self.model.Flush()
        self.assertEqual(self.model.Stats()['pending_slots'],1)
        self.assertEqual(len(self.scheduled),2)
        self.model.Flush();self.assertFalse(self.model.Stats()['scheduled'])

    def test_restore_validates_and_invalidates_old_tokens(self):
        snapshot=self.model.Snapshot();token=self.model.GetToken(CTX,1)
        self.model.UpdateValues(CTX,{1:.3});self.model.Restore(snapshot)
        self.assertEqual(self.model.GetCatalog(CTX)[1]['Value'],.45)
        self.assertNotEqual(token,self.model.GetToken(CTX,1))
        broken=self.model.Snapshot();broken['rows'][CTX][1]['Value']=2
        with self.assertRaises(ValueError):self.model.Restore(broken)
        self.assertEqual(self.model.GetCatalog(CTX)[1]['Value'],.45)

    def test_old_extension_destruction_does_not_unsubscribe_replacement(self):
        events=[]
        class View:
            def callback(self,*args):events.append(self)
        old=View();new=View()
        self.model.Subscribe('same-comp',CTX,old.callback)
        self.model.Subscribe('same-comp',CTX,new.callback)
        self.model.Unsubscribe('same-comp',old.callback)
        self.model.UpdateValues(CTX,{1:.3});self.model.Flush()
        self.assertEqual(events,[new])
        self.model.Unsubscribe('same-comp',new.callback)
        self.assertEqual(self.model.Stats()['subscribers'],0)

    def test_shared_learn_and_shutdown(self):
        events=[];self.model.Subscribe('view',CTX,lambda *x:events.append(x))
        self.model.SetLearn(True);self.model.SetLearn(True);self.model.Flush()
        self.assertTrue(events[0][3]);self.assertTrue(self.model.Learn)
        self.model.Shutdown()
        with self.assertRaises(RuntimeError):self.model.GetCatalog(CTX)
        self.assertEqual(self.model.Stats()['subscribers'],0)

if __name__=='__main__':unittest.main()
