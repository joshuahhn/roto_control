"""Issue #9: owner identity, lifecycle, independent libraries and live values.

These are source/unit fixtures, not native TD or physical hardware evidence.
"""
import copy
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import test_assignment
import test_tag_devices
import test_comp_follow
from layouts import Layouts, OWNER_KEY
from protocol import digest, sysex
from export_component import reset_mapping_storage


class OwnerTests(unittest.TestCase):
    def fixture(self):
        e,m,f,a,b,*_=test_tag_devices.TagDeviceTests().fixture()
        comps=[a.owner,b.owner]
        old=e.ownerComp.op
        def lookup(path):
            absolute=os.path.normpath(e.ownerComp.path+'/'+path)
            found=next((c for c in comps if c.valid and c.path==absolute),None)
            return found if found is not None else old(path)
        e.ownerComp.op=lookup
        f.tag_sampler=lambda:tuple(comps)
        f.owner_candidates=lambda:list(comps)+list(f.handles.values())
        return e,m,f,a,b,comps

    def add(self,comps,path):
        p=test_tag_devices.TagDeviceTests().target(path)
        comps.append(p.owner)
        return p

    def test_idempotent_same_name_owner_and_custom_are_separate(self):
        e,m,f,a,b,comps=self.fixture()
        x=self.add(comps,'/one/Same');y=self.add(comps,'/two/Same')
        route=m.context()['key'];value=(x.eval(),y.eval())
        lx=e.RegisterComp(x.owner);ly=e.RegisterComp(y.owner)
        self.assertNotEqual(lx,ly);self.assertEqual(m.layout(lx)['name'],m.layout(ly)['name'])
        self.assertEqual(e.RegisterComp(x.owner),lx)
        self.assertEqual(e.LookupCompLayout(x.owner),lx)
        self.assertEqual(m.context()['key'],route);self.assertEqual((x.eval(),y.eval()),value)
        self.assertEqual(m.layout()['category'],'CUSTOM')
        self.assertEqual(len(m.track()['plugins']),2)
        m.rename(lx,'User label');x.owner.path='/moved/Same';x.owner.name='Renamed'
        self.assertEqual(e.RegisterComp(x.owner),lx)
        self.assertEqual(m.layout(lx)['name'],'User label')
        self.assertEqual(m.layout(lx)['owner']['path'],'../moved/Same')
        self.assertEqual(m.plugin(lx)['id'],m.layout(lx)['owner']['entry_plugin_id'])
        f.refresh_links();self.assertEqual(m.plugin(lx)['comp_name'],'Renamed')

    def test_roundtrip_rename_reparent_preserves_ids_links_and_offpage_library(self):
        e,m,f,a,b,comps=self.fixture();x=self.add(comps,'/Source');layout=e.RegisterComp(x.owner)
        e.SelectLayout(layout);assigned=e.AssignParameter('knob',1,x)
        m.capture(force=True);plugin=m.plugin();wire=plugin['device_id'];group=plugin['group_id']
        library=copy.deepcopy(e.ownerComp.fetch('page_targets'))
        library.append(dict(plugin['targets'][0],id='offpage',index=3,slot=2,identity='offpage'))
        e.ownerComp.store('page_targets',library);m.capture(force=True);x.owner.path='/moved/Renamed';x.owner.name='Renamed';f.refresh_links()
        self.assertEqual(m.plugin()['targets'][0]['comp'],'../moved/Renamed')
        self.assertEqual(m.plugin()['state']['page_targets'][1]['comp'],'../moved/Renamed')
        e.SelectLayout('custom');saved=e.GetLayoutRegistry();m2=Layouts(e);e._layouts=m2
        f.handles.clear();self.assertEqual(e.LookupCompLayout(x.owner),layout)
        e.SelectLayout(layout)
        self.assertEqual((m2.plugin()['device_id'],m2.plugin()['group_id']),(wire,group))
        self.assertEqual(e.GetControlState(assigned['id'])['value'],x.eval())
        self.assertEqual(m2.plugin()['state']['page_targets'][1]['id'],'offpage')
        self.assertEqual(saved['records'][1]['owner']['id'],m2.layout()['owner']['id'])

    def test_missing_same_path_replacement_cannot_dispatch_activate_or_recall(self):
        e,m,f,a,b,comps=self.fixture();x=self.add(comps,'/Source');layout=e.RegisterComp(x.owner)
        e.SelectLayout(layout);state=e.AssignParameter('knob',1,x);test_comp_follow.FollowTests().ack(e)
        self.assertTrue(e.GetControlState(state['id'])['mapped'])
        x.owner.valid=False;replacement=self.add(comps,'/Source')
        target=e._host.controls['knob',1]
        ack=sysex(11,11,(target.index>>7,target.index&127,*digest(target.target_id,6),0,0,0))
        e._receive_midi(ack);e._receive_midi((191,12,127));e._receive_midi((191,44,127))
        self.assertEqual(replacement.eval(),5);self.assertEqual(x.eval(),5)
        self.assertEqual(m.layout(layout)['owner']['state'],'missing')
        self.assertFalse(e.GetControlState(state['id'])['mapped'])
        with self.assertRaisesRegex(ValueError,'missing'):e.SelectLayout(layout)
        with self.assertRaisesRegex(ValueError,'missing'):e.SetValue(8,state['id'])
        self.assertIsNone(e.GetPluginTargets(layout)[0]['value'])
        self.assertIsNone(e.LookupCompLayout(replacement.owner))
        self.assertIsNone(replacement.owner.fetch(OWNER_KEY))

    def test_clone_conflict_latches_then_explicit_rekey_and_relink(self):
        e,m,f,a,b,comps=self.fixture();x=self.add(comps,'/Source');layout=e.RegisterComp(x.owner)
        clone=self.add(comps,'/Clone');token=x.owner.fetch(OWNER_KEY);clone.owner.store(OWNER_KEY,token)
        self.assertIsNone(e.LookupCompLayout(x.owner));self.assertIsNone(e.LookupCompLayout(clone.owner))
        self.assertEqual(m.layout(layout)['owner']['state'],'conflict')
        with self.assertRaisesRegex(ValueError,'conflict'):e.RegisterComp(clone.owner)
        clone_layout=e.RegisterComp(clone.owner,new_identity=True)
        self.assertNotEqual(clone.owner.fetch(OWNER_KEY),token)
        self.assertEqual(m.layout(layout)['owner']['state'],'conflict')
        self.assertEqual(e.RelinkLayoutOwner(layout,x.owner),layout)
        self.assertEqual(e.LookupCompLayout(x.owner),layout)
        self.assertEqual(e.LookupCompLayout(clone.owner),clone_layout)

    def test_token_only_duplicate_untagged_comp_is_detected(self):
        e,m,f,a,b,comps=self.fixture();x=self.add(comps,'/Source');layout=e.RegisterComp(x.owner)
        y=self.add(comps,'/Copy');y.owner.tags.clear();y.owner.store(OWNER_KEY,x.owner.fetch(OWNER_KEY))
        self.assertFalse(m.owner_ready(layout));self.assertEqual(m.layout(layout)['owner']['state'],'conflict')
        y.owner.valid=False
        self.assertFalse(m.owner_ready(layout))  # requires explicit acknowledgement of ambiguity

    def test_relink_rebases_all_variants_preserves_wire_and_target_identity(self):
        e,m,f,a,b,comps=self.fixture();x=self.add(comps,'/Source');layout=e.RegisterComp(x.owner)
        e.SelectLayout(layout);e.AssignParameter('knob',1,x);m.capture(force=True)
        prior=copy.deepcopy(m.plugin());e.SelectLayout('custom');x.owner.valid=False
        replacement=self.add(comps,'/Replacement')
        e.RelinkLayoutOwner(layout,replacement.owner);e.SelectLayout(layout)
        after=m.plugin();self.assertEqual(after['device_id'],prior['device_id'])
        self.assertEqual(after['targets'][0]['id'],prior['targets'][0]['id'])
        self.assertEqual(after['targets'][0]['identity'],prior['targets'][0]['identity'])
        self.assertEqual(after['targets'][0]['comp'],'../Replacement')
        self.assertIs(e._collection.bindings['knob',1].parameter,replacement)
        self.assertEqual(replacement.eval(),5)
        with self.assertRaisesRegex(ValueError,'another Layout'):e.RelinkLayoutOwner(layout,replacement.owner)

    def test_unregister_is_tombstone_and_never_deletes_comp_or_mapping(self):
        e,m,f,a,b,comps=self.fixture();x=self.add(comps,'/Source');layout=e.RegisterComp(x.owner)
        e.SelectLayout(layout);e.AssignParameter('knob',1,x);m.capture(force=True);saved=copy.deepcopy(m.plugin())
        with self.assertRaisesRegex(ValueError,'another Layout'):e.UnregisterLayoutOwner(layout)
        e.SelectLayout('custom');e.UnregisterLayoutOwner(layout)
        self.assertEqual(m.data['active'],'custom');self.assertTrue(x.owner.valid)
        self.assertEqual(m.plugin(layout),saved);self.assertEqual(m.layout(layout)['owner']['state'],'unregistered')
        self.assertEqual(f.sync_tags(force=True),[])
        with self.assertRaisesRegex(ValueError,'unregistered'):e.RegisterComp(x.owner)
        with self.assertRaisesRegex(ValueError,'Unregister'):e.RemoveLayout(layout)
        e.RelinkLayoutOwner(layout,x.owner);self.assertEqual(e.LookupCompLayout(x.owner),layout)
        self.assertEqual(m.plugin(layout),saved)

    def test_shared_parameter_live_values_and_range_assignment_library_are_independent(self):
        e,m,f,a,b,comps=self.fixture();layout=e.RegisterComp(a.owner)
        e.SelectLayout(layout);owned=e.AssignParameter('knob',1,a);e.ConfigureControl(owned['id'],minimum=2,maximum=8)
        m.capture(force=True);owned_plugin=copy.deepcopy(m.plugin())
        e.SelectLayout('custom');custom=m.plugin()['id'];original=m.plugin()['targets'][0]['id']
        e.SetValue(7,original)
        states=e.GetPluginTargets(layout)
        self.assertEqual((states[0]['value'],states[0]['value_source']),(7,'live'))
        self.assertEqual((states[0]['minimum'],states[0]['maximum']),(2,8))
        states[0]['maximum']=999  # detached snapshot
        self.assertEqual(m.plugin(layout),owned_plugin)
        e.SelectLayout(layout);self.assertEqual(e.GetValue(owned['id']),7)
        self.assertFalse(e.GetControlState(owned['id'])['mapped'])
        old=e._host.controls['knob',1];test_comp_follow.FollowTests().ack(e)
        e._receive_midi((191,12,127));e._receive_midi((191,44,127));self.assertEqual(a.eval(),8)
        self.assertEqual(e.GetPluginTargets('custom',plugin_id=custom)[0]['value'],8)
        self.assertEqual(m.plugin('custom')['targets'][0]['maximum'],10)
        e.RemoveControl(owned['id']);m.capture(force=True)
        self.assertEqual(m.plugin(layout)['targets'],[])
        e.SelectLayout('custom');self.assertEqual(e.GetValue(original),8)
        e._receive_midi(sysex(11,11,(old.index>>7,old.index&127,*digest(old.target_id,6),0,0,0)))
        self.assertFalse(e.GetControlState(original)['mapped'])

    def test_pulse_is_not_a_preset_on_selection_or_browse(self):
        e,m,f,a,b,comps=self.fixture();layout=e.RegisterComp(a.owner)
        pulse=test_assignment.AssignmentTests().parameter('Pulse','Reset');pulse.owner=a.owner;a.owner.par.Reset=pulse
        e.SelectLayout(layout);e.AssignParameter('button',1,pulse);e.SelectLayout('custom')
        target=e.GetPluginTargets(layout)[0];self.assertEqual(target['value_source'],'pulse');self.assertIsNone(target['value'])
        e.SelectLayout(layout);self.assertEqual(pulse.pulses,0)

    def test_same_owner_focus_variants_legal_but_unqualified_collision_rejected(self):
        e,m,f,a,b,comps=self.fixture();layout=e.RegisterComp(a.owner);track=m.track(layout)['id']
        variant=e.CreatePlugin(layout,track,'Variant')
        f.set_plugin_link(layout,track,variant,a.owner)
        self.assertEqual(m.plugin(layout,track,variant)['focus_comp']['owner_id'],m.layout(layout)['owner']['id'])
        m.save();e.SelectPlugin(layout,track,variant)
        self.assertEqual(f.resolve(a.owner),(layout,track,variant))
        snapshot=copy.deepcopy(m.data)
        m.plugin(layout,track,variant)['focus_comp'].pop('owner_id')
        with self.assertRaisesRegex(ValueError,'Duplicate Focus'):Layouts.validate(m.data)
        m.data=snapshot
        with self.assertRaisesRegex(ValueError,'owner Device'):f.set_plugin_link(layout,track,m.layout(layout)['owner']['entry_plugin_id'],b.owner)
        with self.assertRaisesRegex(ValueError,'Owner Device'):e.RemovePlugin(layout,track,m.layout(layout)['owner']['entry_plugin_id'])

    def test_legacy_upgrade_never_infers_owner_from_name_or_focus(self):
        e,m,f,a,b,comps=self.fixture();legacy=copy.deepcopy(m.data)
        legacy.pop('ownership_version');legacy.pop('revision')
        for layout in legacy['records']:layout.pop('category')
        e.ownerComp.store('layout_registry',legacy);upgraded=Layouts(e)
        self.assertEqual(upgraded.layout()['category'],'LEGACY');self.assertNotIn('owner',upgraded.layout())
        self.assertEqual(upgraded.plugin()['device_id'],legacy['records'][0]['tracks'][0]['plugins'][0]['device_id'])
        self.assertEqual(upgraded.plugin()['state'],legacy['records'][0]['tracks'][0]['plugins'][0]['state'])

    def test_revision_snapshot_is_detached_and_rejects_stale_plan(self):
        e,m,f,a,b,comps=self.fixture();snapshot=e.GetLayoutRegistry();rev=snapshot['revision']
        self.assertEqual(e.CheckLayoutRevision(rev),rev)
        snapshot['records'].clear();self.assertTrue(m.data['records'])
        e.RegisterComp(a.owner)
        with self.assertRaisesRegex(ValueError,'revision changed'):e.CheckLayoutRevision(rev)
        self.assertEqual(e.CheckLayoutRevision(e.GetLayoutRegistry()['revision']),m.data['revision'])

    def test_registration_and_relink_roll_back_on_observer_failure(self):
        e,m,f,a,b,comps=self.fixture();saved=e.GetLayoutRegistry()
        original=m.menu;calls=[0]
        def once():
            calls[0]+=1
            if calls[0]==1:raise ValueError('observer failure')
            return original()
        with patch.object(m,'menu',once):
            with self.assertRaisesRegex(ValueError,'observer'):e.RegisterComp(a.owner)
        self.assertIsNone(a.owner.fetch(OWNER_KEY));self.assertEqual(len(m.data['records']),len(saved['records']))
        layout=e.RegisterComp(a.owner);a.owner.valid=False;y=self.add(comps,'/New')
        m.refresh_owners();prior=copy.deepcopy(m.layout(layout));calls[0]=0
        with patch.object(m,'menu',once):
            with self.assertRaisesRegex(ValueError,'observer'):e.RelinkLayoutOwner(layout,y.owner)
        self.assertIsNone(y.owner.fetch(OWNER_KEY));self.assertEqual(m.layout(layout),prior)

    def test_generic_storage_reset_has_no_external_owner_side_effects(self):
        e,m,f,a,b,comps=self.fixture();e.RegisterComp(a.owner);token=a.owner.fetch(OWNER_KEY)
        store=copy.deepcopy(e.GetLayoutRegistry());storage={'layout_registry':store,OWNER_KEY:'clone-token'}
        clone=SimpleNamespace(store=lambda key,value:storage.__setitem__(key,value))
        reset_mapping_storage(clone)
        self.assertIsNone(storage['layout_registry']);self.assertIsNone(storage[OWNER_KEY])
        self.assertEqual(storage['page_targets'],[]);self.assertEqual(storage['parameter_assignments'],[])
        self.assertEqual(a.owner.fetch(OWNER_KEY),token);self.assertEqual(m.data['records'],store['records'])

    def test_missing_active_owner_reload_quarantines_then_requires_explicit_activate(self):
        e,m,f,a,b,comps=self.fixture();layout=e.RegisterComp(a.owner)
        e.SelectLayout(layout);state=e.AssignParameter('knob',1,a);m.capture(force=True)
        a.owner.valid=False
        reloaded=Layouts(e);e._layouts=reloaded;reloaded.restore()
        self.assertTrue(reloaded.quarantined);self.assertEqual(reloaded.context()['key'][0],layout)
        self.assertEqual(e.GetControlStates(),[])
        self.assertEqual(e.GetControlCatalog()[0]['value_source'],'unavailable')
        self.assertEqual(reloaded.plugin()['targets'][0]['id'],state['id'])
        a.owner.valid=True
        self.assertTrue(reloaded.owner_ready())
        self.assertTrue(reloaded.quarantined)  # repair never silently resumes dispatch
        e.SelectLayout(layout)
        self.assertFalse(reloaded.quarantined);self.assertEqual(e.GetValue(state['id']),5)
        self.assertFalse(e.GetControlState(state['id'])['mapped'])

    def test_rollback_failure_is_visible_paused_gated(self):
        from layouts import ActivationRollbackError
        e,m,f,a,b,comps=self.fixture()
        with patch.object(m,'menu',side_effect=ValueError('observer unavailable')):
            with self.assertRaises(ActivationRollbackError):e.RegisterComp(a.owner)
        self.assertTrue(f.paused);self.assertTrue(f.gated);self.assertEqual(f.status,'paused')
        self.assertIn('rollback failed',f.error);self.assertIsNone(a.owner.fetch(OWNER_KEY))

    def test_context_category_metadata_and_live_getters_do_not_select(self):
        e,m,f,a,b,comps=self.fixture();layout=e.RegisterComp(a.owner);route=m.context()['key']
        a.val=9
        self.assertEqual(e.GetValue(),9)
        metadata=next(r for r in e.GetLayouts() if r['id']==layout)
        self.assertEqual(metadata['category'],'COMP');self.assertFalse(metadata['active'])
        metadata['owner']['path']='../tampered'
        self.assertEqual(m.layout(layout)['owner']['path'],'../master')
        self.assertEqual(e.GetLayoutContext()['category'],'CUSTOM');self.assertEqual(m.context()['key'],route)
        self.assertTrue(e.ValidateLayoutRegistry(e.GetLayoutRegistry()))

    def test_owned_manual_activation_retains_lock_learn_touch_guards(self):
        for flag in ('locked','learning','touched'):
            with self.subTest(flag=flag):
                e,m,f,a,b,comps=self.fixture();layout=e.RegisterComp(a.owner);route=m.context()['key']
                setattr(m if flag=='locked' else e._host,flag,True)
                with self.assertRaises(ValueError):e.SelectLayout(layout)
                self.assertEqual(m.context()['key'],route);self.assertEqual(a.eval(),5)

    def test_explicit_relink_does_not_retarget_independent_custom_references(self):
        e,m,f,a,b,comps=self.fixture();layout=e.RegisterComp(a.owner)
        e.SelectLayout(layout);e.AssignParameter('knob',1,a);e.SelectLayout('custom')
        prior=copy.deepcopy(m.plugin());a.owner.valid=False;replacement=self.add(comps,'/Replacement')
        e.RelinkLayoutOwner(layout,replacement.owner)
        self.assertEqual(m.plugin(),prior)
        self.assertEqual(m.plugin(layout)['targets'][0]['comp'],'../Replacement')
        self.assertEqual(m.plugin()['targets'][0]['comp'],'../master')

    def test_ownership_mutations_wait_for_pending_gated_backlog_paused_or_opening(self):
        for flag in ('pending','gated','backlog','paused','opening'):
            with self.subTest(flag=flag):
                e,m,f,a,b,comps=self.fixture()
                if flag=='opening':e._process=object();e._host.plugin=False
                else:setattr(f,flag,True)
                with self.assertRaises(ValueError):e.RegisterComp(a.owner)
                self.assertIsNone(a.owner.fetch(OWNER_KEY));self.assertEqual(len(m.data['records']),1)

    def test_saved_missing_owner_does_not_disable_separate_legacy_callback_registration(self):
        e,m,f,a,b,comps=self.fixture();layout=e.RegisterComp(a.owner)
        e.SelectLayout(layout);e.AssignParameter('knob',1,a);m.capture(force=True)
        a.owner.valid=False;m.owner_ready();self.assertTrue(m.quarantined)
        m.legacy=True;events=[]
        e.BindControls([dict(kind='knob',slot=1,id='callback',minimum=0,maximum=10,value=5,on_change=events.append)],group_id='legacy')
        e.SetValue(6,'callback')
        self.assertEqual(e.GetValue('callback'),6);self.assertEqual(len(events),0)
        e._assign_control(('knob',1),.7);self.assertEqual(len(events),1)
        self.assertEqual(m.layout(layout)['owner']['state'],'missing')

    def test_cycle_uses_actual_shared_menu_value_before_dispatch(self):
        from test_menu import menu
        e,m,f,a,b,comps=self.fixture();layout=e.RegisterComp(a.owner)
        par=menu();par.owner=a.owner;a.owner.par.Speed=par
        e.SelectLayout(layout);state=e.AssignParameter('button',1,par)
        par.val='gamma'  # changed outside this binding before its deferred watcher
        e._assign_control(('button',1),1)
        self.assertEqual(par.eval(),'alpha')

    def test_nested_comp_inherited_storage_is_not_a_clone_or_reused_owner(self):
        e,m,f,a,b,comps=self.fixture();layout=e.RegisterComp(a.owner)
        child=self.add(comps,a.owner.path+'/child')
        test_tag_devices.persistent(child.owner,parent=a.owner)
        self.assertEqual(child.owner.fetch(OWNER_KEY),a.owner.fetch(OWNER_KEY))  # native default inheritance
        self.assertIsNone(child.owner.fetch(OWNER_KEY,search=False))
        self.assertTrue(m.owner_ready(layout));self.assertEqual(m.layout(layout)['owner']['state'],'bound')
        child_layout=e.RegisterComp(child.owner)
        self.assertNotEqual(child_layout,layout)
        self.assertNotEqual(child.owner.fetch(OWNER_KEY,search=False),a.owner.fetch(OWNER_KEY,search=False))
        self.assertEqual(e.LookupCompLayout(a.owner),layout)
        self.assertEqual(e.LookupCompLayout(child.owner),child_layout)

    def test_default_identity_inventory_traverses_components_only_once(self):
        from text_comp_follow import CompFollower
        e,m,f,a,b,comps=self.fixture();f.tag_sampler=f._tagged
        with patch.object(f,'_components',return_value=comps) as sampler:
            candidates=CompFollower.owner_candidates(f)
        self.assertEqual(sampler.call_count,1);self.assertIn(a.owner,candidates)

    def full_collection(self,e,m,a):
        specs=[]
        for kind in ('knob','button'):
            for slot in range(1,9):
                name=kind.capitalize()+str(slot)
                par=test_assignment.AssignmentTests().parameter('Float' if kind=='knob' else 'Toggle',name)
                par.owner=a.owner;setattr(a.owner.par,name,par)
                specs.append(dict(kind=kind,slot=slot,id=name,parameter=par))
        e.BindControls(specs,group_id=m.plugin()['group_id']);m.capture(force=True)

    def test_sixteen_slot_getter_observes_inventory_once_and_never_retains_a_timed_cache(self):
        e,m,f,a,b,comps=self.fixture();layout=e.RegisterComp(a.owner)
        e.SelectLayout(layout);self.full_collection(e,m,a)
        with patch.object(f,'owner_candidates',wraps=f.owner_candidates) as sampler:
            self.assertEqual(len(e.GetControlStates()),16)
            self.assertEqual(sampler.call_count,1)
            e.GetControlStates();self.assertEqual(sampler.call_count,2)

    def test_tick_read_and_nonwriting_midi_batch_share_one_inventory(self):
        e,m,f,a,b,comps=self.fixture();layout=e.RegisterComp(a.owner)
        e.SelectLayout(layout);self.full_collection(e,m,a)
        def batch():
            for _ in range(256):e._receive_midi((191,127,0))
            e.GetControlStates();e.GetControlCatalog()
        with patch.object(e,'_tick',batch),patch.object(f,'owner_candidates',wraps=f.owner_candidates) as sampler:
            e.Tick();self.assertEqual(sampler.call_count,1)

    def test_publish_nested_reads_share_inventory(self):
        from RotoPythonExt import RotoPythonExt
        e,m,f,a,b,comps=self.fixture();layout=e.RegisterComp(a.owner);e.SelectLayout(layout)
        def snapshots():
            e.GetControlStates();e.GetControlStates();e.GetControlCatalog()
        with patch.object(e,'_publish_state',snapshots),patch.object(f,'owner_candidates',wraps=f.owner_candidates) as sampler:
            RotoPythonExt._publish(e);self.assertEqual(sampler.call_count,1)

    def test_dispatch_rechecks_clone_inventory_even_inside_read_observation(self):
        e,m,f,a,b,comps=self.fixture();layout=e.RegisterComp(a.owner)
        e.SelectLayout(layout);e.AssignParameter('knob',1,a)
        with m.owner_observation():
            clone=self.add(comps,'/Clone');clone.owner.store(OWNER_KEY,a.owner.fetch(OWNER_KEY,search=False))
            e._assign_control(('knob',1),1)
        self.assertEqual(a.eval(),5);self.assertEqual(m.layout(layout)['owner']['state'],'conflict')
        self.assertTrue(m.quarantined)

    def test_deleted_or_unreadable_custom_parameter_is_unavailable_not_cached(self):
        for failure in ('deleted','read_error','nonfinite'):
            with self.subTest(failure=failure):
                e,m,f,a,b,comps=self.fixture()
                e.ownerComp.store('control_catalog',e.GetControlStates())
                if failure=='deleted':a.owner.valid=False
                elif failure=='read_error':a.eval=lambda:(_ for _ in ()).throw(RuntimeError('read failed'))
                else:a.eval=lambda:float('nan')
                state=e.GetControlState()
                self.assertEqual(state['value_source'],'unavailable');self.assertIsNone(state['value'])
                self.assertFalse(state['valid']);self.assertFalse(state['mapped'])
                self.assertIsNone(e.GetControlCatalog()[0]['value'])

    def test_missing_before_capture_preserves_latest_range_and_wire_identity(self):
        e,m,f,a,b,comps=self.fixture();layout=e.RegisterComp(a.owner);e.SelectLayout(layout)
        state=e.AssignParameter('knob',1,a);e.ConfigureControl(state['id'],minimum=2,maximum=8)
        identity=e._host.controls['knob',1].target_id
        a.owner.valid=False;m.capture(force=True)
        target=m.plugin()['targets'][0]
        self.assertEqual((target['minimum'],target['maximum'],target['identity']),(2,8,identity))

    def test_context_and_follow_reads_share_the_same_synchronous_inventory(self):
        e,m,f,a,b,comps=self.fixture();layout=e.RegisterComp(a.owner);e.SelectLayout(layout)
        with patch.object(f,'owner_candidates',wraps=f.owner_candidates) as sampler:
            with m.owner_observation():
                e.GetLayoutContext();f.context();e.GetControlCatalog()
            self.assertEqual(sampler.call_count,1)

    def test_revision_preflight_forces_fresh_inventory_within_read_batch(self):
        e,m,f,a,b,comps=self.fixture();layout=e.RegisterComp(a.owner)
        revision=e.GetLayoutRegistry()['revision']
        with m.owner_observation():
            clone=self.add(comps,'/Clone');clone.owner.store(OWNER_KEY,a.owner.fetch(OWNER_KEY,search=False))
            with self.assertRaisesRegex(ValueError,'revision changed'):e.CheckLayoutRevision(revision)
        self.assertEqual(m.layout(layout)['owner']['state'],'conflict')

    def test_inactive_library_nonfinite_or_unreadable_values_are_unavailable(self):
        for failure in ('nan','infinite','read_error','type_error'):
            with self.subTest(failure=failure):
                e,m,f,a,b,comps=self.fixture();layout=e.RegisterComp(a.owner)
                e.SelectLayout(layout);e.AssignParameter('knob',1,a);e.SelectLayout('custom')
                if failure in ('nan','infinite'):a.eval=lambda:float('nan' if failure=='nan' else 'inf')
                elif failure=='read_error':a.eval=lambda:(_ for _ in ()).throw(RuntimeError('read failed'))
                else:a.eval=lambda:object()
                target=e.GetPluginTargets(layout)[0]
                self.assertIsNone(target['value']);self.assertFalse(target['valid'])
                self.assertEqual(target['value_source'],'unavailable')


if __name__=='__main__':unittest.main()
