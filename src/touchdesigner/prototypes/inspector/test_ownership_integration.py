"""Combined Inspector seam regressions; not native or physical evidence."""
from copy import deepcopy
from types import SimpleNamespace as S
from unittest import TestCase
from live_model import ControllerCatalog,TDControllerAdapter,project_records
from commands import semantic_fingerprint
from test_activation import ActivationAdapter,OTHER
from test_live_model import KEY,state

class RecoveryAdapter(ActivationAdapter):
    def __init__(self):
        super().__init__();self.quarantine=True;self.epoch=1;self.owner=dict(id='owner',path='../effect',state='bound',entry_plugin_id='device');self.recovered=True
    def Status(self):
        return dict(super().Status(),Legacy=False,Quarantined=self.quarantine,RoutingEpoch=self.epoch,ContextOwners={'layout':dict(category='COMP',owner=deepcopy(self.owner))})
    def Activate(self,key):
        super().Activate(key)
        if self.recovered:self.quarantine=False

class RecoveryTests(TestCase):
    def test_same_key_recovery_one_install_not_ack(self):
        a=RecoveryAdapter();m=ControllerCatalog(a)
        self.assertTrue(m.ActivationCapability(KEY)['recover']);self.assertFalse(m.Capabilities(KEY,1)['value']['enabled'])
        self.assertTrue(m.Activate(KEY,m.ActivationToken(KEY)));self.assertEqual(a.activations,[KEY])
        self.assertFalse(m.ActivationCapability(KEY)['enabled']);self.assertEqual(a.writes,[])
    def test_epoch_owner_drift_same_key_rejects_intent(self):
        for field in ('epoch','owner'):
            a=RecoveryAdapter();m=ControllerCatalog(a);token=m.ActivationToken(KEY)
            if field=='epoch':a.epoch+=1
            else:a.owner['id']='replacement'
            with self.assertRaisesRegex(ValueError,'session or routing'):m.Activate(KEY,token)
            self.assertEqual(a.activations,[])
    def test_unbound_owner_blocks_recovery_and_inactive_activation(self):
        for status in ('missing','conflict','unregistered'):
            a=RecoveryAdapter();a.owner['state']=status;m=ControllerCatalog(a)
            for key in (KEY,OTHER):
                self.assertFalse(m.ActivationCapability(key)['enabled'])
                with self.assertRaisesRegex(ValueError,'owner'):m.Activate(key,m.ActivationToken(key))
            self.assertEqual(a.activations,[])
    def test_completion_with_quarantine_is_failure(self):
        a=RecoveryAdapter();a.recovered=False;m=ControllerCatalog(a)
        with self.assertRaisesRegex(ValueError,'recover'):m.Activate(KEY,m.ActivationToken(KEY))
        self.assertTrue(m.Status['Quarantined'])
    def test_legacy_has_no_recovery(self):
        a=RecoveryAdapter();a.Status=lambda:dict(Active=KEY,Quarantined=True,Legacy=True)
        self.assertFalse(ControllerCatalog(a).ActivationCapability(KEY)['enabled'])

def registry():
    target=dict(id='one',kind='knob',slot=1,comp='../effect',parameter='Value',label='Value',minimum=0,maximum=1,identity='hash',value=.2)
    plugin=dict(id=KEY[2],plugin_name='Device',name_mode='comp',focus_comp=dict(path='../effect',state='bound'),targets=[target],state=dict(page_targets=[deepcopy(target)],control_catalog=[deepcopy(target)],needs_relearn=['one']))
    return dict(revision=1,records=[dict(id=KEY[0],name='Layout',category='COMP',owner=dict(id='owner',path='../effect',state='bound',entry_plugin_id=KEY[2]),tracks=[dict(id=KEY[1],name='Track',plugins=[plugin])])])

class RenameTests(TestCase):
    def fixture(self):
        a=ActivationAdapter();a.registry=registry();a.calls=[];a.Registry=lambda:deepcopy(a.registry);m=ControllerCatalog(a)
        c=S(GetLayoutRegistry=a.Registry,CheckLayoutRevision=lambda revision:a.calls.append(('check',revision)),RenameLayout=lambda id,name:a.calls.append(('layout',id,name)),RenameTrack=lambda *args:a.calls.append(('track',)+args),RenamePlugin=lambda *args:a.calls.append(('device',)+args))
        native=TDControllerAdapter(S(par=S(Controller=S(eval=lambda:c))))
        native.Status=a.Status;native.Session=a.Session;native.ActiveContext=a.ActiveContext;native.ActivationReason=lambda:a.reason
        a.Rename=native.Rename
        return a,m,native
    def test_value_traffic_keeps_draft_and_checks_fresh_revision(self):
        a,m,n=self.fixture();draft=m.PrepareRename(KEY,'Layout');a.registry['revision']=42;p=a.registry['records'][0]['tracks'][0]['plugins'][0]
        p['targets'][0]['value']=.9;p['state']['control_catalog'].append(dict(id='observation'));p['state']['needs_relearn']=[]
        m.Rename(KEY,'New',draft);self.assertEqual(a.calls,[('check',42),('layout','layout','New')])
    def test_structure_owner_policy_and_library_drift_reject(self):
        for field in ('owner','name','parent','identity','library','policy','focus'):
            a,m,n=self.fixture();draft=m.PrepareRename(KEY,'Layout');l=a.registry['records'][0];p=l['tracks'][0]['plugins'][0]
            if field=='owner':l['owner']['path']='../other'
            elif field=='name':l['name']='Other'
            elif field=='parent':l['tracks'][0]['id']='other'
            elif field=='identity':p['targets'][0]['identity']='new'
            elif field=='library':p['state']['page_targets'][0]['maximum']=2
            elif field=='policy':p['name_mode']='manual'
            else:p['focus_comp']['state']='missing'
            with self.assertRaises(ValueError):m.Rename(KEY,'New',draft)
            self.assertEqual(a.calls,[])
    def test_linked_device_opt_out_explicit(self):
        a,m,n=self.fixture()
        with self.assertRaisesRegex(ValueError,'opt-out'):m.Rename(KEY,'New',m.PrepareRename(KEY,'Device'))
        self.assertEqual(a.calls,[]);m.Rename(KEY,'New',m.PrepareRename(KEY,'Device',manual=True))
        self.assertEqual(a.calls,[('check',1),('device',)+KEY+('New',)])
    def test_capture_session_drift_blocks_cas_and_write(self):
        a,m,n=self.fixture();draft=m.PrepareRename(KEY,'Layout');old=n.controller.GetLayoutRegistry
        def capture():a.session+=1;return old()
        n.controller.GetLayoutRegistry=capture
        with self.assertRaisesRegex(ValueError,'session'):m.Rename(KEY,'New',draft)
        self.assertEqual(a.calls,[])
    def test_guard_freshly_checked(self):
        a,m,n=self.fixture();draft=m.PrepareRename(KEY,'Layout');a.reason='Exit LEARN'
        with self.assertRaisesRegex(ValueError,'LEARN'):m.Rename(KEY,'New',draft)
        self.assertEqual(a.calls,[])

class LibraryTests(TestCase):
    def adapter(self,current,library,catalog=None):
        manager=S(plugin=lambda *k:dict(targets=library[:1]),quarantined=False)
        c=S(path='/controller',op=lambda path:None,GetPluginTargets=lambda *k:deepcopy(library),GetControlStates=lambda:deepcopy(current),GetControlCatalog=lambda:deepcopy(catalog or current),GetLayoutContext=lambda:dict(key=KEY),ext=S(RotoPythonExt=S(_layout_manager=lambda:manager)))
        a=TDControllerAdapter(S(par=S(Controller=S(eval=lambda:c))));a._definitions=lambda rows,key:rows
        return a
    def test_library_slot_collision_does_not_overwrite_current_binding(self):
        live=state();old=dict(live,id='offpage',value=.8);a=self.adapter([live],[live,old],[live,dict(old,valid=False,value=None)])
        rows=a.Library(KEY);self.assertEqual(len(rows),2);self.assertEqual(len({r['library_key'] for r in rows}),2)
        self.assertTrue(all(not r['mapped'] for r in rows));self.assertEqual([r['id'] for r in a.Read(KEY)],['target'])
        self.assertEqual(project_records(a.Read(KEY))[0][1]['Value'],.4)
        rows[0]['label']='changed';self.assertEqual(a.Library(KEY)[0]['label'],'Threshold')
    def test_inactive_preview_projects_only_last_slots_not_library_union(self):
        live=state();old=dict(live,id='offpage',slot=4);a=self.adapter([live],[live,old]);rows=a.Read(OTHER)
        self.assertEqual(len(a.Library(OTHER)),2);self.assertEqual([r['id'] for r in rows],['target'])
        self.assertFalse(rows[0]['mapped']);self.assertEqual(rows[0]['projection'],'last-saved preview')
    def test_pulse_unavailable_never_claim_live_mapping(self):
        a=self.adapter([],[dict(state(),mode='pulse',value=1),dict(state(),id='missing',value=None,valid=False)])
        rows=a.Library(OTHER);self.assertIsNone(rows[0]['value']);self.assertIsNone(rows[1]['value']);self.assertFalse(rows[1]['valid'])
        self.assertTrue(all(not r['mapped'] and not r['connected'] for r in rows))
    def test_quarantine_preview_unavailable_until_recovery(self):
        a=self.adapter([state()],[state()]);a.controller.GetLayoutContext=lambda:dict(key=KEY,quarantined=True)
        a.controller.ext.RotoPythonExt._layout_manager().quarantined=True
        row=a.Read(KEY)[0];self.assertFalse(row['valid']);self.assertFalse(row['mapped']);self.assertIsNone(row['value'])

    def test_active_projection_scans_live_parameters_once(self):
        a=self.adapter([state()],[state()]);calls=[]
        a.controller.GetControlStates=lambda:calls.append('scan') or [state()]
        def catalog():raise AssertionError('Catalog would rescan current native parameters')
        a.controller.GetControlCatalog=catalog
        self.assertEqual(a.Read(KEY)[0]['value'],.4);self.assertEqual(calls,['scan'])


class OwnershipDisplayTests(TestCase):
    def test_categories_use_metadata_not_display_names(self):
        from parity import ownership_label,detail_groups
        self.assertEqual(ownership_label(dict(category='LEGACY',name='CUSTOM')),'Legacy-unclassified')
        self.assertEqual(ownership_label(dict(category='CUSTOM')),'CUSTOM')
        metadata=dict(category='COMP',owner=dict(path='../Source',state='missing'))
        self.assertIn('missing',ownership_label(metadata))
        groups=detail_groups({},dict(label='Invalid'),dict(ViewingOwner=metadata,RoutingOwner=metadata,Quarantined=True),{},('L','T','D'),('L','T','D'),('T','D'),False)
        technical=dict((label,value) for label,value,size in groups[-1][1])
        self.assertIn('missing',technical['Viewing']);self.assertIn('Needs Activate',technical['Owner / Follow'])

class PulsePresentationTests(TestCase):
    def test_active_pulse_masks_numeric_without_disabling_health(self):
        from test_live_model import Adapter
        a=Adapter();a.records[KEY][0].update(mode='pulse',value_source='pulse',value=0)
        m=ControllerCatalog(a);info=m.Info(KEY,1)
        self.assertFalse(info['available']);self.assertTrue(info['valid']);self.assertTrue(info['mapped'])
        self.assertEqual(m.ValueText(KEY,1),'Pulse');self.assertEqual(m.Health(KEY,1)['code'],'mapped')
        self.assertIn('Pulse',m.Capabilities(KEY,1)['value']['reason'])
    def test_layout_choices_distinguish_categories_by_id(self):
        c=S(GetLayoutContext=lambda:dict(legacy=False),GetLayouts=lambda:[dict(id='a',name='Same',category='COMP'),dict(id='b',name='Same',category='CUSTOM'),dict(id='c',name='CUSTOM')])
        a=TDControllerAdapter(S(par=S(Controller=S(eval=lambda:c))))
        self.assertEqual(a.Choices('Layout',KEY),[('a','COMP · Same'),('b','CUSTOM · Same'),('c','Legacy · CUSTOM')])
