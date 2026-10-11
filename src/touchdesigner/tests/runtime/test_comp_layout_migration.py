"""#11 source fixtures: explicit classification, atomic variants, offline CAS.

Mock protocol evidence only; native save/load and physical recall are separate.
"""
import copy
import builtins
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace, ModuleType
from unittest.mock import patch

import test_layout_owners
import test_comp_follow
import test_assignment
import layout_migration as migration
import layouts
from layouts import Layouts, FIELDS, DEFAULTS, ActivationRollbackError
from protocol import digest


class MigrationTests(unittest.TestCase):
    def fixture(self):
        e, m, f, a, b, comps = test_layout_owners.OwnerTests().fixture()
        # Mirror native local OP storage, retaining the fixture's existing data.
        storage = e.ownerComp.fetch.__closure__[0].cell_contents
        e.ownerComp.storage = storage
        oldop = e.ownerComp.op
        layout_dat=SimpleNamespace(module=layouts, valid=True, isDAT=True, name='layouts', parent=lambda:e.ownerComp)
        e.ownerComp.op = lambda n: (SimpleNamespace(module=migration) if n == 'layout_migration'
                                   else layout_dat if n == 'layouts' else oldop(n))
        focus=SimpleNamespace(val='')
        focus.eval=lambda:next((c for c in comps if c.valid and c.path==focus.val),None)
        e.ownerComp.par.Focuscomp=focus
        m.layout()['category'] = 'LEGACY'; m.save()
        la = e.RegisterComp(a.owner); lb = e.RegisterComp(b.owner)
        e._host.connected = e._host.plugin = False
        f.session_boundary(); e._pending = b''
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        path = Path(self.temp.name) / 'recovery.json'
        return e, m, f, a, b, la, lb, path

    def decision(self, m, la, plugin_id=None):
        key = next(k for k in migration.records(m.data) if k[0] == 'custom' and
                   (plugin_id is None or k[2] == plugin_id))
        return dict(source=list(key), decision='move', owner_layout_id=la,
                    owner_id=m.layout(la)['owner']['id'],
                    evidence=dict(kind='user-confirmed-ownership', reference='isolated fixture registration'))

    def plan(self, e, rows, entries=None):
        return e.PlanCompLayoutMigration('fixture-migration', rows, entries=entries)

    def apply(self, e, plan, path):
        return e.ApplyCompLayoutMigration(plan, recovery_path=path)

    def dat_local_helper(self, e):
        # Real helper source in an isolated DAT namespace: sibling DATs exist,
        # but TouchInit's standalone Python import cannot find 'layouts'.
        helper=ModuleType('fixture_layout_migration_DAT')
        imports=[]
        def dat_import(name,*args,**kwargs):
            if name=='layouts':
                imports.append(name)
                raise ModuleNotFoundError("No module named 'layouts'",name='layouts')
            return builtins.__import__(name,*args,**kwargs)
        helper.__dict__['__builtins__']=dict(vars(builtins),__import__=dat_import)
        source=Path(migration.__file__).read_text()
        exec(compile(source,'/fixture/controller/layout_migration','exec'),helper.__dict__)
        oldop=e.ownerComp.op
        e.ownerComp.op=lambda name:SimpleNamespace(module=helper) if name=='layout_migration' else oldop(name)
        return imports

    def test_public_plan_with_dat_local_layouts_without_standalone_import(self):
        e,m,f,a,b,la,lb,path=self.fixture()
        self.assertIs(e.ownerComp.op('layouts').module.Layouts,type(m))
        imports=self.dat_local_helper(e)
        before=e.GetLayoutRegistry()
        plan=self.plan(e,[self.decision(m,la)])
        self.assertEqual(len(plan['manifest']),len(migration.records(before)))
        self.assertEqual(e.GetLayoutRegistry(),before); self.assertFalse(path.exists())
        self.assertEqual((a.eval(),b.eval()),(5,5)); self.assertEqual(imports,[])

    def test_dat_local_apply_and_failed_recovery_use_installed_shared_exception(self):
        for fail_restore in (False,True):
            with self.subTest(fail_restore=fail_restore):
                e,m,f,a,b,la,lb,path=self.fixture(); imports=self.dat_local_helper(e)
                plan=self.plan(e,[self.decision(m,la)]); before=e.GetLayoutRegistry()
                if fail_restore:
                    with patch.object(e,'_publish',side_effect=RuntimeError('publication failure')):
                        with self.assertRaises(layouts.ActivationRollbackError) as caught:self.apply(e,plan,path)
                    self.assertIs(type(caught.exception),e.ownerComp.op('layouts').module.ActivationRollbackError)
                    self.assertTrue(f.paused and f.gated)
                    recovery=migration.decode(json.loads(path.read_text())['recovery'])
                    self.assertEqual(recovery['registry'],before)
                else:
                    self.assertTrue(self.apply(e,plan,path)['changed'])
                    self.assertEqual(m.plugin()['id'],plan['route'][2])
                    self.assertFalse(self.apply(e,plan,path)['changed'])
                self.assertEqual(imports,[]); self.assertEqual((a.eval(),b.eval()),(5,5))

    def test_dat_local_dependency_fails_closed_for_plan_and_apply(self):
        class Unreadable:
            valid=True; isDAT=True; name='layouts'
            def __init__(self,owner):self.owner=owner
            def parent(self):return self.owner
            @property
            def module(self):raise RuntimeError('DAT compilation failure')
        for defect in ('missing','foreign','invalid','not_dat','unreadable','other_class','bad_constants'):
            with self.subTest(defect=defect):
                e,m,f,a,b,la,lb,path=self.fixture(); self.dat_local_helper(e)
                plan=self.plan(e,[self.decision(m,la)]); before=e.GetLayoutRegistry()
                dat=e.ownerComp.op('layouts')
                if defect=='missing':dat=None
                elif defect=='foreign':dat.parent=lambda:SimpleNamespace()
                elif defect=='invalid':dat.valid=False
                elif defect=='not_dat':dat.isDAT=False
                elif defect=='unreadable':dat=Unreadable(e.ownerComp)
                else:
                    dat.module=SimpleNamespace(Layouts=layouts.Layouts,FIELDS=layouts.FIELDS,
                                               DEFAULTS=layouts.DEFAULTS,ActivationRollbackError=layouts.ActivationRollbackError)
                    if defect=='other_class':dat.module.Layouts=type('ForeignLayouts',(),{})
                    else:dat.module.DEFAULTS=()
                oldop=e.ownerComp.op
                e.ownerComp.op=lambda name:dat if name=='layouts' else oldop(name)
                for call in (lambda:self.plan(e,[self.decision(m,la)]),lambda:self.apply(e,plan,path)):
                    with self.assertRaisesRegex(ValueError,'same-controller layouts DAT'):call()
                    self.assertEqual(m.data,before); self.assertFalse(path.exists())
                    self.assertFalse(m.mutating); self.assertEqual((a.eval(),b.eval()),(5,5))

    def test_plan_lists_every_record_without_classifying_names_or_links(self):
        e,m,f,a,b,la,lb,path = self.fixture()
        before = e.GetLayoutRegistry(); route = m.context()['key']; pending = e._pending
        p = self.plan(e, [])
        self.assertEqual(len(p['manifest']), len(migration.records(before)))
        self.assertTrue(all(r['decision'] == 'retain' and r['source'] == r['destination'] for r in p['manifest']))
        self.assertEqual(p['result'], before); self.assertEqual(m.context()['key'], route)
        self.assertEqual(e._pending, pending); self.assertFalse(path.exists())
        self.assertFalse(self.apply(e, p, path)['changed']); self.assertFalse(path.exists())

    def action_fixture(self):
        e,m,f,a,b,la,lb,path = self.fixture()
        events = []
        e.RegisterAction('migration.demo.clean.v1', 'Clean', events.append)
        state = e.AssignAction(1, 'migration.demo.clean.v1', id='saved.action.mapping')
        e._action_registry().results['migration.demo.clean.v1'] = dict(
            status='partial', error='prior readback', details={'readback': .7})
        return e,m,f,a,b,la,lb,path,events,state

    def test_action_relocation_preserves_runtime_result_bindings_and_saved_identity(self):
        e,m,f,a,b,la,lb,path,events,state = self.action_fixture()
        result = e.GetActionState('migration.demo.clean.v1')
        registry = e._actions; collection = e._collection
        binding = collection.bindings['button',1]; target = e._host.controls['button',1]
        before = e.GetLayoutRegistry(); row = self.decision(m,la)
        plan = self.plan(e,[row]); self.apply(e,plan,path)
        self.assertIs(e._actions,registry); self.assertIs(e._collection,collection)
        self.assertIs(collection.bindings['button',1],binding)
        self.assertIs(e._host.controls['button',1],target)
        self.assertEqual(e.GetActionState('migration.demo.clean.v1'),result)
        self.assertEqual(e.GetControlState(state['id'])['action_result'],result['result'])
        saved = next(t for t in m.plugin()['targets'] if t.get('action_id'))
        original = next(t for t in migration.records(before)[tuple(row['source'])][2]['targets'] if t.get('action_id'))
        self.assertEqual(saved,original); self.assertEqual(saved['id'],state['id'])
        self.assertFalse(self.apply(e,plan,path)['changed'])
        self.assertEqual(events,[]); self.assertEqual((a.eval(),b.eval()),(5,5))

    def test_dangling_offpage_action_survives_relocation_reload_and_manual_custom(self):
        e,m,f,a,b,la,lb,path,events,state = self.action_fixture()
        row=self.decision(m,la); m.capture(force=True)
        action=copy.deepcopy(next(t for t in m.plugin()['targets'] if t.get('action_id')))
        manual=e.CreateLayout('Manual Actions'); e.SelectLayout(manual)
        e.AssignAction(1,'migration.demo.clean.v1',id='manual.action.mapping'); m.capture(force=True)
        retained=copy.deepcopy(m.layout(manual))
        source=m.plugin(*row['source'])
        offpage=dict(action,id='offpage.action',index=123,identity='offpage.action.wire',action_id='missing.provider.v1')
        source['state']['page_targets'].append(offpage); m.save()
        plan=self.plan(e,[row]); self.apply(e,plan,path)
        dest=next(r['destination'] for r in plan['manifest'] if r['source']==row['source'])
        self.assertEqual(m.layout(manual),retained)
        self.assertIn(offpage,m.plugin(*dest)['state']['page_targets'])
        self.assertFalse(next(t for t in e.GetPluginTargets(*dest) if t['id']==offpage['id'])['action_available'])
        saved=e.GetLayoutRegistry(); self.assertEqual(Layouts.migrate(saved),saved)
        m2=Layouts(e); e._layouts=m2; m2.restore(); e.SelectPlugin(*dest)
        self.assertEqual(e.GetControlState(state['id'])['action_id'],action['action_id'])
        self.assertEqual(events,[]); self.assertEqual((a.eval(),b.eval()),(5,5))

    def test_action_result_and_full_recovery_survive_failed_migration_publication(self):
        e,m,f,a,b,la,lb,path,events,state = self.action_fixture()
        plan=self.plan(e,[self.decision(m,la)])
        before=e.GetLayoutRegistry(); result=e.GetActionState('migration.demo.clean.v1')
        registry=e._actions; binding=e._collection.bindings['button',1]
        publish=e._publish; calls=[]
        def fail_once():
            calls.append(1)
            if len(calls)==1: raise RuntimeError('injected migration publish failure')
            return publish()
        with patch.object(e,'_publish',fail_once):
            with self.assertRaisesRegex(RuntimeError,'injected migration'): self.apply(e,plan,path)
        restored=e.GetLayoutRegistry(); restored['revision']=before['revision']
        self.assertEqual(restored,before); self.assertIs(e._actions,registry)
        self.assertIs(e._collection.bindings['button',1],binding)
        self.assertEqual(e.GetActionState('migration.demo.clean.v1'),result)
        recovery=migration.decode(json.loads(path.read_text())['recovery'])
        self.assertEqual(recovery['registry'],before)
        self.assertEqual(events,[]); self.assertEqual((a.eval(),b.eval()),(5,5))

    def test_invalid_action_reference_is_rejected_without_repair_or_recall(self):
        for bad in ({'action_id':''},{'kind':'knob','slot':2},{'mode':'value'},{'parameter':'Amount'}):
            with self.subTest(bad=bad):
                e,m,f,a,b,la,lb,path,events,state=self.action_fixture()
                row=self.decision(m,la); e.SelectLayout(la)
                source=m.plugin(*row['source'])
                next(t for t in source['targets'] if t.get('action_id')).update(bad); m.save()
                with self.assertRaises(ValueError):self.plan(e,[row])
                self.assertFalse(path.exists()); self.assertEqual(events,[])

    def test_mixed_track_two_owners_reuses_original_id_only_once(self):
        e,m,f,a,b,la,lb,path = self.fixture()
        before = e.GetLayoutRegistry(); original = m.track()['id']
        rows = [self.decision(m, la), self.decision(m, lb, m.track()['plugins'][1]['id'])]
        plan = self.plan(e, rows); host = e._host; collection = e._collection
        state = {k: copy.deepcopy(e.ownerComp.fetch(k, d)) for k,d in zip(FIELDS, DEFAULTS)}
        result = self.apply(e, plan, path)
        self.assertTrue(result['changed']); self.assertTrue(path.is_file())
        self.assertEqual(sum(t['id'] == original for l in m.data['records'] for t in l['tracks']), 1)
        self.assertIs(e._host, host); self.assertIs(e._collection, collection)
        self.assertEqual(m.plugin()['id'], rows[0]['source'][2]); self.assertEqual(m.data['active'], la)
        self.assertEqual(e._pending, b''); self.assertEqual((a.eval(), b.eval()), (5,5))
        for k,d in zip(FIELDS, DEFAULTS): self.assertEqual(e.ownerComp.fetch(k,d),state[k])
        for row in plan['manifest']:
            old = migration.records(before)[tuple(row['source'])][2]
            actual = migration.records(m.data)[tuple(row['destination'])][2]
            qualified = copy.deepcopy(old)
            if row['decision'] == 'move':
                qualified['focus_comp']['owner_id'] = m.layout(row['destination'][0])['owner']['id']
            self.assertEqual(actual, qualified)
            self.assertEqual(list(digest(actual['device_id'],8)), row['device_wire_hash'])

    def test_mixed_track_retained_records_keep_original_track_and_context(self):
        e,m,f,a,b,la,lb,path = self.fixture()
        original = m.track()['id']; route = m.context()['key']; pa = m.plugin()['id']
        row = self.decision(m, lb, m.track()['plugins'][1]['id'])
        before_a = copy.deepcopy(m.plugin())
        plan = self.plan(e,[row]); self.apply(e,plan,path)
        self.assertEqual(m.context()['key'],route); self.assertEqual(m.plugin('custom',original,pa),before_a)
        moved = next(r for r in plan['manifest'] if r['decision']=='move')
        self.assertNotEqual(moved['destination'][1], original)

    def test_same_owner_cross_layout_variants_qualify_without_merge_or_unlink(self):
        e,m,f,a,b,la,lb,path = self.fixture()
        first = self.decision(m,la)
        second_layout = e.CreateLayout('Variant')
        e.SelectLayout(second_layout); state = e.AssignParameter('knob',1,a)
        f.set_plugin_link(second_layout,m.track()['id'],m.plugin()['id'],a.owner)
        e.RenamePlugin(second_layout,m.track()['id'],m.plugin()['id'],'MANUAL')
        m.layout()['category']='LEGACY'; m.capture(force=True)
        second_key = list(m.context()['key']); second_plugin = copy.deepcopy(m.plugin())
        e.SelectLayout('custom'); e._pending=b''
        second = dict(first, source=second_key)
        plan=self.plan(e,[first,second],entries={la:second_key[2]})
        self.apply(e,plan,path)
        self.assertEqual(m.layout(la)['owner']['entry_plugin_id'],second_key[2])
        variants=[p for t in m.layout(la)['tracks'] for p in t['plugins'] if p['id'] in (first['source'][2],second_key[2])]
        self.assertEqual(len(variants),2)
        self.assertEqual(variants[1]['name_mode'],'manual'); self.assertEqual(variants[1]['plugin_name'],'MANUAL')
        self.assertEqual(variants[1]['targets'],second_plugin['targets'])
        self.assertTrue(all(p['focus_comp']['owner_id']==first['owner_id'] for p in variants))
        # Composed #10 v5 selects the owner's saved qualified Device; #11 alone
        # used the older unique-link policy. Migration preserves both variants.
        owner=m.layout(la)
        saved_track=m.track(la)
        saved_plugin=m.plugin(la,saved_track['id'])
        self.assertEqual(f.resolve(a.owner),(la,saved_track['id'],saved_plugin['id']))
        moved = next(r for r in plan['manifest'] if r['source']==second_key)
        e.SelectPlugin(*moved['destination']); self.assertEqual(e.GetValue(state['id']),5)
        self.assertEqual(f.resolve(a.owner),tuple(moved['destination']))

    def test_custom_reference_to_same_parameter_stays_independent(self):
        e,m,f,a,b,la,lb,path=self.fixture()
        custom=e.CreateLayout('User'); e.SelectLayout(custom); assigned=e.AssignParameter('knob',1,a)
        e.ConfigureControl(assigned['id'],minimum=1,maximum=9); m.capture(force=True)
        user=copy.deepcopy(m.layout(custom)); e.SelectLayout('custom')
        plan=self.plan(e,[self.decision(m,la)]); self.apply(e,plan,path)
        self.assertEqual(m.layout(custom),user)
        self.assertEqual(e.GetPluginTargets(custom)[0]['value'],5)
        invalid=dict(self.decision(m,la),source=[custom,user['tracks'][0]['id'],user['tracks'][0]['plugins'][0]['id']])
        with self.assertRaisesRegex(ValueError,'CUSTOM'):e.PlanCompLayoutMigration('custom-rejected',[invalid])

    def test_missing_evidence_unlinked_mismatched_owner_fail_before_recovery(self):
        for bad in ('evidence','unlinked','mismatch'):
            with self.subTest(bad=bad):
                e,m,f,a,b,la,lb,path=self.fixture(); row=self.decision(m,la)
                if bad=='evidence':row.pop('evidence')
                if bad=='unlinked':m.plugin()['focus_comp']=None; m.save()
                if bad=='mismatch':row.update(owner_layout_id=lb,owner_id=m.layout(lb)['owner']['id'])
                before=e.GetLayoutRegistry()
                with self.assertRaises(ValueError):self.plan(e,[row])
                self.assertEqual(m.data,before); self.assertFalse(path.exists())

    def test_clone_conflict_and_missing_owner_fail_closed(self):
        for condition in ('missing','clone'):
            with self.subTest(condition=condition):
                e,m,f,a,b,la,lb,path=self.fixture(); row=self.decision(m,la)
                if condition=='missing':a.owner.valid=False
                else:
                    twin=SimpleNamespace(**vars(a.owner)); f.owner_candidates=lambda:[a.owner,b.owner,twin]
                    twin.path='/copy'
                with self.assertRaises(ValueError):self.plan(e,[row])
                self.assertFalse(path.exists())

    def test_all_nine_state_fields_and_128_offpage_definitions_are_preserved(self):
        e,m,f,a,b,la,lb,path=self.fixture(); row=self.decision(m,la); pid=row['source'][2]
        e.SelectLayout(la)  # source is inactive; preserve deliberately rich saved state
        plugin=m.plugin(*row['source']); seed=copy.deepcopy(plugin['targets'][0])
        library=[dict(seed,id='page.'+str(i),index=128+i,identity='page-wire.'+str(i),slot=i%8+1) for i in range(127)]
        library.append(seed)
        plugin['state'].update(page_targets=library,removed_controls=['deleted'],needs_relearn=('pending',),
                               pending_unmaps=[('button',8)],pending_unmap_identities=[{'id':'deleted','index':17,'identity':'gone'}],
                               control_overrides={'original':{'minimum':2,'maximum':8}},
                               control_catalog=[{'id':'original','value':7,'mapped':True}],
                               parameter_assignments=[seed],assignment_device_id={'group_id':plugin['group_id'],'device_id':plugin['device_id']})
        m.save();before=copy.deepcopy(plugin);plan=self.plan(e,[row]);self.apply(e,plan,path)
        dest=next(x['destination'] for x in plan['manifest'] if x['source']==row['source'])
        after=m.plugin(*dest)
        self.assertEqual(after['state'],before['state']);self.assertEqual(len(after['state']['page_targets']),128)
        for t in after['state']['page_targets']:
            original=next(x for x in before['state']['page_targets'] if x['id']==t['id'])
            self.assertEqual(digest(t['identity'],6),digest(original['identity'],6))

    def test_library_collision_or_callback_schema_is_never_repaired_by_relearn(self):
        for bad in ('index','hash','callback'):
            with self.subTest(bad=bad):
                e,m,f,a,b,la,lb,path=self.fixture();row=self.decision(m,la);e.SelectLayout(la)
                plugin=m.plugin(*row['source']);seed=copy.deepcopy(plugin['targets'][0])
                if bad=='callback':seed.update(id='callback',index=123,identity='callback');seed.pop('comp')
                else:seed.update(id='extra',index=seed['index'] if bad=='index' else 123,
                                 identity=seed['identity'] if bad=='hash' else 'unique')
                plugin['state']['page_targets'].append(seed);m.save()
                with self.assertRaises(ValueError):self.plan(e,[row])
                self.assertFalse(path.exists())

    def test_repeat_apply_reload_upgrade_preserves_edits_and_no_new_records(self):
        e,m,f,a,b,la,lb,path=self.fixture();row=self.decision(m,la);plan=self.plan(e,[row])
        self.apply(e,plan,path);raw=path.read_bytes();saved=e.GetLayoutRegistry()
        self.assertFalse(self.apply(e,plan,path)['changed']);self.assertEqual(path.read_bytes(),raw)
        self.assertEqual(e.GetLayoutRegistry(),saved)
        self.assertEqual(Layouts.migrate(saved),saved)
        m2=Layouts(e);e._layouts=m2;f.handles.clear();m2.restore()
        dest=next(r['destination'] for r in plan['manifest'] if r['source']==row['source'])
        m2.plugin(*dest)['plugin_name']='EDITED';m2.plugin(*dest)['name_mode']='manual';m2.save()
        edited=e.GetLayoutRegistry()
        self.assertFalse(self.apply(e,plan,path)['changed']);self.assertEqual(e.GetLayoutRegistry(),edited)

    def test_reusing_migration_id_with_changed_decision_rejected(self):
        e,m,f,a,b,la,lb,path=self.fixture();row=self.decision(m,la);p=self.plan(e,[row]);self.apply(e,p,path)
        with self.assertRaisesRegex(ValueError,'another request'):e.PlanCompLayoutMigration('fixture-migration',[])

    def test_stale_plan_and_modified_candidate_rejected(self):
        for bad in ('revision','candidate'):
            with self.subTest(bad=bad):
                e,m,f,a,b,la,lb,path=self.fixture();p=self.plan(e,[self.decision(m,la)])
                if bad=='revision':e.CreateLayout('New')
                else:p['result']['records'][0]['name']='hidden edit'
                before=e.GetLayoutRegistry()
                with self.assertRaisesRegex(ValueError,'Stale'):self.apply(e,p,path)
                self.assertEqual(m.data,before);self.assertFalse(path.exists())

    def test_revision_change_inside_serialized_transaction_is_rejected(self):
        e,m,f,a,b,la,lb,path=self.fixture();p=self.plan(e,[self.decision(m,la)])
        original=m.refresh_owners
        def during(*args,**kwargs):
            original(*args,**kwargs)
            if m.mutating:m.data['revision']+=1
        with patch.object(m,'refresh_owners',during):
            with self.assertRaisesRegex(ValueError,'inside migration'):self.apply(e,p,path)
        self.assertFalse(path.exists());self.assertFalse(m.mutating)

    def test_existing_recovery_path_is_not_overwritten(self):
        e,m,f,a,b,la,lb,path=self.fixture();p=self.plan(e,[self.decision(m,la)])
        path.write_text('previous recovery');before=e.GetLayoutRegistry()
        with self.assertRaises(FileExistsError):self.apply(e,p,path)
        self.assertEqual(path.read_text(),'previous recovery');self.assertEqual(m.data,before)

    def test_recovery_contains_complete_storage_registry_context_and_hook(self):
        e,m,f,a,b,la,lb,path=self.fixture();e.ownerComp.store('user_backup',{'bytes':b'x','tuple':(1,2)})
        oldop=e.ownerComp.op
        e.ownerComp.op=lambda n:SimpleNamespace(text='hook preserved') if n=='registration' else oldop(n)
        p=self.plan(e,[self.decision(m,la)]);before=e.GetLayoutRegistry();self.apply(e,p,path)
        recovery=json.loads(path.read_text())
        self.assertEqual(recovery['source_fingerprint'],migration.fingerprint(before))
        payload=recovery['recovery']['value']
        self.assertIn('user_backup',payload['storage']['value']);self.assertIn('registration',payload['sources']['value'])
        self.assertIn('selected_track',payload['context']['value'])

    def test_opaque_recovery_storage_fails_without_lossy_copy_or_commit(self):
        e,m,f,a,b,la,lb,path=self.fixture();e.ownerComp.store('opaque',object())
        p=self.plan(e,[self.decision(m,la)]);before=e.GetLayoutRegistry()
        with self.assertRaisesRegex(ValueError,'Unsupported recovery'):self.apply(e,p,path)
        self.assertFalse(path.exists());self.assertEqual(m.data,before)

    def test_commit_or_observer_failure_restores_registry_materialized_context(self):
        for seam in ('save','menu','publish'):
            with self.subTest(seam=seam):
                e,m,f,a,b,la,lb,path=self.fixture();p=self.plan(e,[self.decision(m,la)])
                before=e.GetLayoutRegistry();storage=copy.deepcopy(e.ownerComp.storage);route=m.context()['key']
                target=m if seam!='publish' else e;name=seam if seam!='publish' else '_publish'
                original=getattr(target,name);calls=[0]
                def once(*args,**kwargs):
                    if m.mutating:
                        calls[0]+=1
                        if calls[0]==1:raise ValueError('injected '+seam)
                    return original(*args,**kwargs)
                with patch.object(target,name,once):
                    with self.assertRaisesRegex(ValueError,'injected'):self.apply(e,p,path)
                actual=copy.deepcopy(m.data);actual['revision']=before['revision']
                self.assertEqual(actual,before);self.assertGreater(m.data['revision'],before['revision'])
                self.assertEqual(m.context()['key'],route)
                for key,value in storage.items():
                    if key!='layout_registry':self.assertEqual(e.ownerComp.storage[key],value)
                self.assertTrue(path.exists());self.assertFalse(m.mutating)

    def test_failed_rollback_pauses_gates_and_reports_actual_failure(self):
        e,m,f,a,b,la,lb,path=self.fixture();p=self.plan(e,[self.decision(m,la)])
        with patch.object(m,'menu',side_effect=ValueError('unavailable observer')):
            with self.assertRaises(ActivationRollbackError):self.apply(e,p,path)
        self.assertTrue(f.paused);self.assertTrue(f.gated);self.assertIn('rollback failed',f.error)
        self.assertTrue(path.exists());self.assertFalse(m.mutating)

    def test_disconnected_learning_touch_lock_callback_and_routing_guards(self):
        for condition in ('connected','process','learning','touch','locked','dispatch','pending','gated','paused','backlog','legacy'):
            with self.subTest(condition=condition):
                e,m,f,a,b,la,lb,path=self.fixture();row=self.decision(m,la)
                if condition=='connected':e._host.connected=True
                elif condition=='process':e._process=object()
                elif condition=='learning':e._host.learning=True
                elif condition=='touch':m.touched={1}
                elif condition=='locked':m.locked=True
                elif condition=='dispatch':e._dispatching=True
                elif condition=='legacy':m.legacy=True
                else:setattr(f,condition,True)
                with self.assertRaises(ValueError):self.plan(e,[row])
                self.assertFalse(path.exists())

    def test_layout_selection_live_value_and_matching_recall_survive_migration(self):
        e,m,f,a,b,la,lb,path=self.fixture();row=self.decision(m,la);plan=self.plan(e,[row])
        wire=e._host.controls['knob',1].target_id;self.apply(e,plan,path)
        destination=next(r['destination'] for r in plan['manifest'] if r['source']==row['source'])
        e.SelectLayout(lb);a.val=7;e.SelectPlugin(*destination)
        self.assertEqual(e.GetValue(),7);self.assertEqual(e._host.controls['knob',1].target_id,wire)
        self.assertFalse(e.GetControlState()['mapped'])
        e._host.connected=e._host.plugin=True;test_comp_follow.FollowTests().ack(e)
        self.assertTrue(e.GetControlState()['mapped'])
        e._receive_midi((191,12,127));e._receive_midi((191,44,127));self.assertEqual(a.eval(),10)

    def test_unlinked_ambiguous_and_explicit_retain_are_preserved_in_place(self):
        e,m,f,a,b,la,lb,path=self.fixture();pa=m.plugin()['id'];pb=m.track()['plugins'][1]['id']
        m.plugin('custom',m.track()['id'],pb)['focus_comp']=None;m.save()
        retain=dict(source=list(m.context()['key']),decision='retain',reason='user manual variant, ownership unknown')
        p=self.plan(e,[retain]);self.assertEqual(p['result'],e.GetLayoutRegistry())
        self.assertTrue(all(r['source']==r['destination'] for r in p['manifest']))

    def test_unknown_registry_version_and_capacity_fail_without_writes(self):
        e,m,f,a,b,la,lb,path=self.fixture();row=self.decision(m,la)
        broken=copy.deepcopy(e.GetLayoutRegistry());broken['version']=99
        with self.assertRaises(ValueError):migration.build_plan(m,broken,'x',[row])
        p=self.plan(e,[row]);p['result']['records'][0]['tracks'][0]['plugins']*=128
        with self.assertRaises(ValueError):self.apply(e,p,path)
        self.assertFalse(path.exists())

    def test_pulse_selection_migration_and_recovery_never_execute_actions(self):
        e,m,f,a,b,la,lb,path=self.fixture()
        pulse=test_assignment.AssignmentTests().parameter('Pulse','Reset')
        pulse.owner=a.owner;a.owner.par.Reset=pulse
        e.AssignParameter('button',1,pulse);m.capture(force=True)
        row=self.decision(m,la);p=self.plan(e,[row]);self.apply(e,p,path)
        dest=next(r['destination'] for r in p['manifest'] if r['source']==row['source'])
        e.SelectLayout(lb);e.SelectPlugin(*dest)
        self.assertEqual(pulse.pulses,0);self.assertEqual(a.eval(),5)
        self.assertIsNone(next(t for t in e.GetPluginTargets(la,dest[1],dest[2]) if t['mode']=='pulse')['value'])

    def test_recovery_codec_roundtrips_types_without_executing_data(self):
        value={'x':(1,2),'data':b'\x00\xff','set':{'b','a'},'nested':[{'type':'dict','value':'user-data'}]}
        self.assertEqual(migration.decode(json.loads(json.dumps(migration.encode(value)))),value)

    def test_parameter_draft_and_local_storage_survive_failed_commit(self):
        e,m,f,a,b,la,lb,path=self.fixture()
        par=SimpleNamespace(name='Layoutname',val='unsaved draft',expr='',bindExpr='',enable=True,
                            menuNames=[],menuLabels=[])
        e.ownerComp.customPars=[par];e.ownerComp.par.Layoutname=par
        p=self.plan(e,[self.decision(m,la)])
        original=m.menu;calls=[0]
        def fail_once():
            calls[0]+=1
            original()
            if calls[0]==1:raise ValueError('draft failure')
        with patch.object(m,'menu',fail_once):
            with self.assertRaisesRegex(ValueError,'draft failure'):self.apply(e,p,path)
        self.assertEqual(par.val,'unsaved draft')

    def test_removed_completed_variant_is_reported_without_resurrection(self):
        e,m,f,a,b,la,lb,path=self.fixture();p=self.plan(e,[self.decision(m,la)])
        self.apply(e,p,path)
        row=next(r for r in p['manifest'] if r['decision']=='move')
        track=m.track(*row['destination'][:2]);track['plugins']=[]
        before=copy.deepcopy(m.data)
        with self.assertRaises(ValueError):self.apply(e,p,path)
        self.assertEqual(m.data,before)

    def test_unrelated_missing_conflicted_or_unregistered_owner_is_retained(self):
        for state in ('missing','conflict','unregistered'):
            with self.subTest(state=state):
                e,m,f,a,b,la,lb,path=self.fixture();row=self.decision(m,la)
                if state=='missing':b.owner.valid=False
                elif state=='conflict':m.layout(lb)['owner']['state']='conflict';m.save()
                else:e.UnregisterLayoutOwner(lb)
                p=self.plan(e,[row]);before=copy.deepcopy(m.layout(lb))
                preserved={k:copy.deepcopy(v[2]) for k,v in migration.records(m.data).items() if k!=tuple(row['source'])}
                self.assertTrue(self.apply(e,p,path)['changed'])
                self.assertEqual(m.layout(lb),before);self.assertEqual(m.layout(lb)['owner']['state'],state)
                self.assertNotIn(before['owner']['entry_plugin_id'],f.handles)
                for key,value in preserved.items():
                    self.assertEqual(m.plugin(*key),value)

    def test_explicit_saved_active_variant_is_distinct_from_entry_and_routing(self):
        e,m,f,a,b,la,lb,path=self.fixture()
        second=m.track()['plugins'][1]['id'];row=self.decision(m,lb,second)
        entry=m.layout(lb)['owner']['entry_plugin_id'];route=m.context()['key']
        p=e.PlanCompLayoutMigration('active-policy',[row],active_variants={lb:second})
        change=next(c for c in p['selection_changes'] if c['layout_id']==lb)
        self.assertEqual(change['after'][1],second);self.assertEqual(change['reason'],'explicit active variant')
        self.apply(e,p,path)
        self.assertEqual(m.layout(lb)['owner']['entry_plugin_id'],entry)
        self.assertEqual(m.plugin(lb)['id'],second);self.assertEqual(m.context()['key'],route)

    def test_entry_selection_alone_does_not_choose_saved_active_follow_variant(self):
        e,m,f,a,b,la,lb,path=self.fixture();pid=m.track()['plugins'][1]['id'];row=self.decision(m,lb,pid)
        initial=m.plugin(lb)['id']
        p=e.PlanCompLayoutMigration('entry-only',[row],entries={lb:pid});self.apply(e,p,path)
        self.assertEqual(m.layout(lb)['owner']['entry_plugin_id'],pid);self.assertEqual(m.plugin(lb)['id'],initial)

    def test_saved_active_policy_cannot_silently_replace_current_bindings(self):
        e,m,f,a,b,la,lb,path=self.fixture();row=self.decision(m,la)
        with self.assertRaisesRegex(ValueError,'replace routing'):
            e.PlanCompLayoutMigration('invalid-active',[row],active_variants={la:m.layout(la)['owner']['entry_plugin_id']})
        self.assertFalse(path.exists())

    def test_native_mode_compensation_and_op_valued_settings(self):
        from enum import Enum
        class Mode(Enum):
            CONSTANT=0
            EXPRESSION=1
        class NativePar:
            name='Layoutname';expr="'draft'";bindExpr='';enable=True;menuNames=[];menuLabels=[]
            mode=Mode.EXPRESSION
            def __init__(self):self._val='unsaved'
            @property
            def val(self):return self._val
            @val.setter
            def val(self,value):self._val=value;self.mode=Mode.CONSTANT
        e,m,f,a,b,la,lb,path=self.fixture();p=NativePar()
        a.owner.isOP=True
        focus=SimpleNamespace(name='Focuscomp',val=a.owner,expr='',bindExpr='',enable=True,
                              mode=Mode.CONSTANT,eval=lambda:a.owner)
        e.ownerComp.customPars=[p,focus];e.ownerComp.par.Layoutname=p;e.ownerComp.par.Focuscomp=focus
        plan=self.plan(e,[self.decision(m,la)])
        real=m.menu;calls=[0]
        def once():
            calls[0]+=1;real()
            if calls[0]==1:raise ValueError('native mode failure')
        with patch.object(m,'menu',once):
            with self.assertRaisesRegex(ValueError,'native mode failure'):self.apply(e,plan,path)
        self.assertEqual(p.val,'unsaved');self.assertEqual(p.mode,Mode.EXPRESSION)
        recovery=migration.decode(json.loads(path.read_text())['recovery'])
        self.assertEqual(recovery['parameters']['Focuscomp']['val'],a.owner.path)
        self.assertEqual(recovery['parameters']['Layoutname']['mode'],'EXPRESSION')

    def test_recovery_durability_failure_leaves_original_and_partial_attempt(self):
        e,m,f,a,b,la,lb,path=self.fixture();p=self.plan(e,[self.decision(m,la)])
        before=e.GetLayoutRegistry()
        with patch.object(migration.os,'fsync',side_effect=OSError('fixture fsync failure')):
            with self.assertRaisesRegex(OSError,'fsync failure'):self.apply(e,p,path)
        self.assertEqual(m.data,before);self.assertTrue(path.exists());self.assertFalse(m.mutating)

    def test_recovery_rejects_native_binary_filename(self):
        e,m,f,a,b,la,lb,path=self.fixture();p=self.plan(e,[self.decision(m,la)])
        wrong=path.with_suffix('.tox')
        with self.assertRaisesRegex(ValueError,'not a native binary'):self.apply(e,p,wrong)
        self.assertFalse(wrong.exists())

    def test_migration_preserves_follow_observation_and_saved_active_policy(self):
        e,m,f,a,b,la,lb,path=self.fixture();baseline=((1,100,'/'),a.owner.id,a.owner.path)
        f.baseline=baseline;f.scope=('custom',False);f.observed_comp=a.owner.path
        p=self.plan(e,[self.decision(m,la)]);self.apply(e,p,path)
        self.assertEqual(f.baseline,baseline);self.assertEqual(f.scope,(la,False))
        self.assertEqual(f.observed_comp,a.owner.path);self.assertEqual(m.plugin(la)['id'],p['route'][2])
        recovery=migration.decode(json.loads(path.read_text())['recovery'])
        self.assertEqual(recovery['context']['follower']['baseline'],baseline)
        self.assertEqual(recovery['context']['host']['connected'],False)

    def test_fresh_intent_during_failed_commit_keeps_ingress_fence_until_flush(self):
        e,m,f,a,b,la,lb,path=self.fixture();p=self.plan(e,[self.decision(m,la)])
        route=m.context()['key'];epoch=f.routing_epoch;real=m.menu;calls=[0]
        def once():
            calls[0]+=1;real()
            if calls[0]==1:
                f.request(lb,m.track(lb)['id'],'td',b.owner,m.plugin(lb)['id'])
                raise ValueError('failure after fresh intent')
        with patch.object(m,'menu',once):
            with self.assertRaisesRegex(ValueError,'fresh intent'):self.apply(e,p,path)
        self.assertEqual(m.context()['key'],route)
        self.assertEqual(f.pending['layout_id'],lb);self.assertEqual(f.pending['source'],'td')
        self.assertTrue(f.gated);self.assertGreater(f.routing_epoch,epoch)
        self.assertFalse(e.GetControlState()['mapped']);self.assertEqual(e._pending,b'')

    def test_mode_only_follow_scope_is_preserved_for_future_root_composition(self):
        e,m,f,a,b,la,lb,path=self.fixture();f.scope=False;f.baseline=('existing-pane-selection',)
        p=self.plan(e,[self.decision(m,la)]);self.apply(e,p,path)
        self.assertIs(f.scope,False);self.assertEqual(f.baseline,('existing-pane-selection',))


if __name__ == '__main__':
    unittest.main()
