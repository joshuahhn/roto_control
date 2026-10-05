"""Catalog data survives disconnect; removed slots cannot recall or auto-offer."""
from types import SimpleNamespace
import unittest
import test_api
import controls
import binding
import collection_protocol
from protocol import sysex,digest

class CatalogRemovalTests(unittest.TestCase):
    def fixture(self):
        ext=test_api.ApiTests().collection()
        ext._restore_pending=ext._restoring=False
        ext._mirror=lambda value:None
        watchers={}
        def watch(name):
            return watchers.setdefault(name,SimpleNamespace(par=SimpleNamespace(active=True,op=SimpleNamespace(expr='',val=''),pars='')))
        def op(name):
            if name in ('controls','collection_protocol','binding'):return SimpleNamespace(module={'controls':controls,'collection_protocol':collection_protocol,'binding':binding}[name])
            if name=='base_targets/targets':return SimpleNamespace(numRows=1)
            return watch(name)
        ext.ownerComp.op=op
        ext.ownerComp.ops=lambda pattern:list(watchers.values())
        ext.ownerComp.par=SimpleNamespace(Value=SimpleNamespace(enable=True),Offerparameter=SimpleNamespace(enable=True))
        return ext
    def test_catalog_disconnect_and_deleted_destination(self):
        ext=self.fixture();test_api.ApiTests().ready(ext)
        ext._update_catalog();before=ext.GetControlCatalog()
        ext._host.stop();ext._update_catalog();after=ext.GetControlCatalog()
        self.assertEqual(before[0]['value'],after[0]['value'])
        self.assertTrue(after[0]['last_mapped']);self.assertFalse(after[0]['mapped'])
        after[0]['value']=99;self.assertNotEqual(ext.GetControlCatalog()[0]['value'],99)
    def test_offline_remove_blocks_stale_ack_and_replays_unmap(self):
        ext=self.fixture();host=ext._host;old=host.controls['button',8]
        old_identity=old.target_id
        ext.RemoveControl('reset');ext._update_catalog()
        self.assertEqual([s['id'] for s in ext.GetControlCatalog()],['speed'])
        self.assertFalse(ext.ownerComp.op('base_targets/watch_button8').par.active)
        sent=[];host.send=sent.append
        host.start();host.receive(sysex(10,12));host.receive(sysex(11,1,(0,)))
        self.assertIn(sysex(11,14,(1,7)),sent)
        sent.clear();host.receive(sysex(11,11,(0,15,*digest(old_identity,6),1,7,0)))
        self.assertEqual(sent,[])
        with self.assertRaises(ValueError):host.offer_parameter(('button',8))
        with self.assertRaises(ValueError):ext.SetValue(1,id='reset')
    def test_saved_hook_cannot_restore_removed_id(self):
        ext=self.fixture();specs=[dict(kind='button',slot=8,id='reset',label='Reset',mode='pulse',on_change=lambda e:None)]
        ext.RemoveControl('reset');ext._restoring=True
        ext.BindControls(specs,group_id='test')
        self.assertEqual(ext.GetControlStates(),[])
        self.assertIn(('button',8),ext._host.pending_unmaps)
        # Explicit public registration opts the target back in.
        ext._restoring=False;ext.BindControls(specs,group_id='test')
        self.assertEqual(ext.GetControlStates()[0]['id'],'reset')
        self.assertNotIn(('button',8),ext._host.pending_unmaps)
    def test_removed_single_binding_restore_stays_empty(self):
        import binding
        ext=self.fixture();ext._collection=None
        ext._binding=binding.Binding('single','Single',0,10,4,on_change=lambda event:None)
        from protocol import Host
        ext._host=Host(lambda message:None,lambda value:None,.4)
        self.assertEqual(ext.RemoveAllControls(),('single',))
        self.assertEqual(ext.GetControlStates(),[])
        ext._restoring=True
        ext.BindCallback(id='single',label='Single',minimum=0,maximum=10,value=4,on_change=lambda event:None)
        self.assertEqual(ext.GetControlStates(),[])
        self.assertIn(('knob',1),ext._host.pending_unmaps)

    def test_clear_all_keeps_empty_collection(self):
        ext=self.fixture();self.assertEqual(ext.RemoveAllControls(),('speed','reset'))
        ext._update_catalog();self.assertEqual(ext.GetControlCatalog(),[])
        self.assertEqual(ext.GetControlStates(),[])
        self.assertEqual(ext._host.controls,{})

if __name__=='__main__':unittest.main()
