"""Repeated runtime publication skips only identical optional UI projections."""
import copy
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import patch
import test_api
sys.path.insert(0,str(Path(__file__).parent/'code/py/roto_python/inspector'))
import inspector_data

class Scheduled:
    def __init__(self,owner):self.owner=owner;self.killed=False
    def kill(self):self.killed=True
    def fire(self):
        if not self.killed:self.owner._flush_inspector()

class InspectorPublicationTests(unittest.TestCase):
    def setUp(self):
        self.ext=test_api.ApiTests().collection();self.calls=[];self.storage={}
        self.ext._restore_pending=False
        self.context=dict(key=('layout','track','device'),label='Device',locked=False)
        self.focus=dict(status='disabled')
        controller=SimpleNamespace(GetLayoutContext=lambda:copy.deepcopy(self.context),
                                   GetCompContext=lambda:dict(self.focus))
        self.module=SimpleNamespace(refresh=self.refresh,
            projection_signature=getattr(inspector_data,'projection_signature',None))
        self.inspector=SimpleNamespace(id=7,parent=lambda:controller,
            fetch=lambda key,default=None:self.storage.get(key,default),
            store=lambda key,value:self.storage.update({key:value}),
            op=lambda name:SimpleNamespace(module=self.module) if name=='inspector_data' else SimpleNamespace(par=SimpleNamespace(text='')))
        self.ext.ownerComp.op=lambda name:self.inspector
    def refresh(self,inspector,states):self.calls.append(copy.deepcopy(states))
    def test_identical_publications_render_once_but_changed_value_and_ack_render(self):
        for _ in range(20):self.ext._publish_inspector()
        self.assertEqual(len(self.calls),1)
        self.ext._collection.bindings['knob',2].write(8,'software');self.ext._publish_inspector()
        self.assertEqual(len(self.calls),2)
        self.ext._host.controls['knob',2].mapped=True;self.ext._publish_inspector()
        self.assertEqual(len(self.calls),3)
    def test_page_confirmation_action_context_and_follow_changes_render(self):
        self.ext._publish_inspector()
        for name,value in [('selected_page','/effect'),('pending_clear',dict(id='speed')),
                           ('action_status','Invalid range')]:
            self.storage[name]=value;self.ext._publish_inspector()
        self.storage['pending_clear']['id']='reset';self.ext._publish_inspector()
        self.context['label']='Renamed';self.ext._publish_inspector()
        self.focus['status']='gated';self.ext._publish_inspector()
        self.assertEqual(len(self.calls),7)
    def test_failed_render_retries_and_module_or_operator_replacement_invalidates(self):
        original=self.module.refresh
        def broken(*args):raise ValueError('broken')
        self.module.refresh=broken;self.ext._publish_inspector()
        self.assertEqual(self.storage['refresh_error'],'broken')
        self.module.refresh=original;self.ext._publish_inspector();self.ext._publish_inspector()
        self.assertEqual(len(self.calls),1)
        self.inspector.id=8;self.ext._publish_inspector();self.assertEqual(len(self.calls),2)
        self.module.refresh=lambda *args:original(*args)
        self.ext._publish_inspector();self.assertEqual(len(self.calls),3)
    def test_manual_refresh_forces_render_and_cached_catalog_avoids_eager_live_scan(self):
        self.ext._publish_inspector();self.ext._publish_inspector(force=True);self.assertEqual(len(self.calls),2)
        self.ext._publish_inspector();self.assertEqual(len(self.calls),2)
        catalog=[dict(id='saved')];self.ext.ownerComp.store('control_catalog',catalog)
        self.ext.GetControlStates=lambda: (_ for _ in ()).throw(AssertionError('eager live scan'))
        detached=self.ext.GetControlCatalog();detached[0]['id']='changed'
        self.assertEqual(catalog[0]['id'],'saved')

    def test_burst_queues_one_owned_callback_and_projects_latest_authoritative_state(self):
        queued=[]
        signatures=[];original=self.module.projection_signature
        def signature(*args):signatures.append(None);return original(*args)
        self.module.projection_signature=signature
        def schedule(script,owner,**kwargs):
            pending=Scheduled(owner);queued.append(pending);return pending
        with patch('RotoPythonExt.run',schedule,create=True):
            for value in range(8):
                self.ext._collection.bindings['knob',2].write(value,'software')
                self.ext._update_catalog();self.ext._publish_inspector()
                self.assertEqual(self.ext.GetControlCatalog()[0]['value'],value)
            self.assertEqual(len(queued),1);self.assertEqual(self.calls,[])
            self.assertEqual(len(signatures),1)
            queued[0].fire()
            self.assertEqual(len(signatures),2)
            self.assertEqual(len(self.calls),1);self.assertEqual(self.calls[0][0]['value'],7)
            self.assertIsNone(self.ext._inspector_refresh_run)
            self.ext._publish_inspector();self.assertEqual(len(queued),1)
            self.ext._collection.bindings['knob',2].write(8,'software');self.ext._update_catalog()
            self.ext._publish_inspector();self.ext._publish_inspector(force=True)
            self.assertTrue(queued[-1].killed);queued[-1].fire()
            self.assertEqual(len(self.calls),2)

    def test_cancelled_or_replaced_extension_cannot_project_late(self):
        queued=[]
        def schedule(script,owner,**kwargs):
            pending=Scheduled(owner);queued.append(pending);return pending
        with patch('RotoPythonExt.run',schedule,create=True):
            self.ext._publish_inspector();self.ext._cancel_inspector_refresh()
            self.assertTrue(queued[0].killed);queued[0].fire();self.assertEqual(self.calls,[])
            self.ext._publish_inspector()
            self.ext.ownerComp.ext=SimpleNamespace(RotoPythonExt=object())
            queued[-1].fire();self.assertEqual(self.calls,[])
            self.assertIsNone(self.ext._inspector_refresh_run)
