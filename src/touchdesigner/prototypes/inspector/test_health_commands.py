"""Health/capability correctness and command fences over authoritative snapshots."""
from unittest import TestCase
from live_model import ControllerCatalog, StaleDraft, TDControllerAdapter
from types import SimpleNamespace
from test_live_model import Adapter, KEY, state

class HealthCommandsTests(TestCase):
    def setUp(self):
        self.adapter=Adapter();self.model=ControllerCatalog(self.adapter)
        self.model.GetCatalog(KEY)
    def update(self,**changes):
        self.adapter.records[KEY][0].update(changes);self.model.Sync()
    def test_destination_is_not_an_ack_and_health_priority_is_explicit(self):
        self.assertEqual(self.model.Health(KEY,0)['code'],'unassigned')
        self.assertEqual(self.model.Health(KEY,1)['code'],'mapped')
        self.update(mapped=False);self.assertEqual(self.model.Health(KEY,1)['code'],'pending')
        self.assertTrue(self.model.GetCatalog(KEY)[1]['Destination'])
        self.update(mapped=True,connected=False);self.assertEqual(self.model.Health(KEY,1)['code'],'saved')
        self.update(requires_relearn=True);self.assertEqual(self.model.Health(KEY,1)['code'],'relearn')
        self.update(valid=False,error='Deleted target');health=self.model.Health(KEY,1)
        self.assertEqual(health['code'],'invalid');self.assertEqual(health['detail'],'Deleted target')
    def test_inactive_saved_mapping_never_claims_an_ack(self):
        other=('layout','track','other');self.adapter.records[other]=[state()]
        self.assertTrue(self.model.Info(other,1)['mapped'])
        self.assertEqual(self.model.Health(other,1)['code'],'saved')
        for action in ('value','ping','clear'):
            self.assertFalse(self.model.Capabilities(other,1)[action]['enabled'])
        self.assertEqual(self.adapter.active,KEY)
    def test_capabilities_clear_invalid_targets_but_do_not_write_or_offer_them(self):
        self.update(valid=False,value=None,error='Target missing')
        caps=self.model.Capabilities(KEY,1)
        self.assertFalse(caps['value']['enabled']);self.assertFalse(caps['ping']['enabled'])
        self.assertTrue(caps['clear']['enabled'])
        with self.assertRaises(TypeError):caps['clear']['enabled']=False
        self.assertEqual(self.adapter.writes,[]);self.assertEqual(self.adapter.pings,[])
    def test_learn_and_touch_capabilities_match_execution_guards(self):
        token=self.model.GetToken(KEY,1)
        self.adapter.learning=True;self.model.Sync()
        caps=self.model.Capabilities(KEY,1)
        self.assertTrue(caps['ping']['enabled']);self.assertFalse(caps['value']['enabled']);self.assertFalse(caps['clear']['enabled'])
        self.adapter.learning=False;self.update(touched=True)
        self.assertFalse(self.model.Capabilities(KEY,1)['value']['enabled'])
        draft=dict(self.model.GetCatalog(KEY)[1]);draft['Value']=.6
        with self.assertRaises(ValueError):self.model.Commit(KEY,1,draft,token)
        self.assertEqual(self.adapter.writes,[])
    def test_runtime_health_and_touch_notify_without_expiring_value_draft(self):
        events=[];self.model.Subscribe('view',KEY,lambda *args:events.append(args))
        token=self.model.GetToken(KEY,1)
        for fields in [dict(mapped=False),dict(touched=True),dict(touched=False,connected=False),dict(requires_relearn=True),dict(requires_relearn=False)]:
            self.update(**fields);self.model.Flush()
            self.assertEqual(self.model.GetToken(KEY,1),token)
            self.assertEqual(events[-1][1],2);self.assertEqual(events[-1][2],0)
        self.assertEqual(len(events),5)
    def test_adapter_and_native_definition_changes_expire_old_commands(self):
        for field,value in [('button_type','push'),('binding_type','callback'),('parameter_definition',(('owner','Threshold','Float','BIND'),))]:
            token=self.model.GetToken(KEY,1);self.update(**{field:value})
            with self.assertRaises(StaleDraft):self.model.Clear(KEY,1,token)
        self.assertEqual(self.adapter.clears,[])
    def test_definition_error_blocks_value_and_ping_while_allowing_cleanup(self):
        self.update(definition_error='Target or bind master must use CONSTANT or BIND mode')
        self.adapter.learning=True;self.model.Sync()
        token=self.model.GetToken(KEY,1)
        with self.assertRaises(ValueError):self.model.Ping(KEY,1,token)
        self.assertEqual(self.model.Health(KEY,1)['code'],'invalid')
        self.adapter.learning=False;self.model.Sync()
        self.assertTrue(self.model.Capabilities(KEY,1)['clear']['enabled'])
        self.assertEqual(self.adapter.pings,[])
    def test_unchanged_sync_and_capability_reads_do_not_notify_or_write(self):
        events=[];self.model.Subscribe('view',KEY,lambda *args:events.append(args))
        for _ in range(100):
            self.model.Sync();self.model.Health(KEY,1);self.model.Capabilities(KEY,1);self.model.Flush()
        self.assertEqual(events,[]);self.assertEqual(self.adapter.writes,[])
    def test_invalid_inactive_target_does_not_hide_other_saved_targets(self):
        broken=state();broken['id']='broken'
        healthy=state(.7);healthy.update(id='healthy',slot=3)
        par=SimpleNamespace(name='Threshold',owner=SimpleNamespace(path='/effect',valid=True),style='Float')
        class Manager:
            def plugin(self,*key):return dict(targets=[broken,healthy])
            def resolve(self,record):
                target=record['targets'][0]
                if target['id']=='broken':raise ValueError('Readonly target')
                return [dict(target,parameter=par)],[]
        controller=SimpleNamespace(ext=SimpleNamespace(RotoPythonExt=SimpleNamespace(_layout_manager=Manager)),
                                   op=lambda path:SimpleNamespace(path='/effect',module=SimpleNamespace(parameter_value=lambda p:.7)))
        owner=SimpleNamespace(par=SimpleNamespace(Controller=SimpleNamespace(eval=lambda:controller)))
        adapter=TDControllerAdapter(owner);adapter.ActiveContext=lambda:KEY
        adapter._definitions=lambda records,key:records
        rows=adapter.Read(('layout','track','inactive'))
        by_id={row['id']:row for row in rows}
        self.assertFalse(by_id['broken']['valid']);self.assertEqual(by_id['broken']['error'],'Readonly target')
        self.assertTrue(by_id['healthy']['valid']);self.assertEqual(by_id['healthy']['value'],.7)
        self.assertFalse(by_id['healthy']['mapped'])
