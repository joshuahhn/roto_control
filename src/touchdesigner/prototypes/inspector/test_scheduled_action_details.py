"""Replay publication -> real installed DAT callback -> scheduled model ingress.

Fake TD DAT events/end-frame runner; no TD imports, manual Sync or native claim.
The unchanged targets/same-status details pattern comes from the recorded native
FAIL, native_scheduled_details.json (20261008T193240Z).
"""
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace as S
import sys
from unittest import TestCase
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SOURCE/'code/py/roto_python'))
sys.path.insert(0, str(SOURCE/'code/py/roto_python/inspector'))
sys.path.insert(0, str(SOURCE))
import test_action_presets as runtime_actions
from RotoPythonExt import RotoPythonExt
from controls import Actions
import inspector_data
import live_model
from live_model import ControllerCatalog, InspectorModel, TDControllerAdapter
from test_live_model import Adapter, KEY
from test_action_integration import action


class Pending:
    def __init__(self, callback): self.callback = callback; self.killed = False
    def kill(self): self.killed = True
    def fire(self):
        if not self.killed: self.callback()


class Frames:
    def __init__(self): self.pending = []; self.scripts = []
    def run(self, script, owner, **kwargs):
        assert kwargs == dict(endFrame=True)
        self.scripts.append(script)
        pending = Pending(lambda: exec(script, {}, dict(args=[owner])))
        self.pending.append(pending)
        return pending
    def drain(self):
        while self.pending:
            pending, self.pending = self.pending, []
            for item in pending: item.fire()


class Parameter:
    def __init__(self): self.val = False; self.expr = ''
    def __bool__(self): return bool(self.val)


class Parameters:
    def __init__(self): object.__setattr__(self, 'values', {})
    def __getattr__(self, name): return self.values.setdefault(name, Parameter())
    def __setattr__(self, name, value): getattr(self, name).val = value
    def __getitem__(self, name): return getattr(self, name)
    def __setitem__(self, name, value): setattr(self, name, value)


class Dat:
    def __init__(self, network):
        self.network = network; self.par = Parameters(); self._text = ''; self.changes = 0
    @property
    def text(self): return self._text
    @text.setter
    def text(self, value):
        if value == self._text: return
        self._text = value; self.changes += 1
        for observer in self.network.observers:
            if not observer.par.active or not observer.par.tablechange: continue
            parent = S(InspectorModel=self.network.model)
            watched = eval(observer.par.dat.expr, {}, dict(parent=parent))
            if watched is self:
                self.network.notifications.append(observer.name)
                namespace = dict(parent=parent)
                exec(observer.text, namespace)
                self.network.frames.pending.append(Pending(
                    lambda callback=namespace['onTableChange']: callback(self)))


class Network:
    def __init__(self):
        self.frames = Frames(); self.observers = []; self.nodes = {}; self.notifications = []
    def op(self, name): return self.nodes.get(name)
    def WatchOwners(self): return self.model.WatchOwners()
    def WatchPars(self): return self.model.WatchPars()
    def create(self, kind, name):
        dat = Dat(self); dat.name = name
        self.nodes[name] = dat; self.observers.append(dat); return dat
    def install(self, model):
        self.model = model
        # Execute the actual builder's observer configuration and callback text.
        # This excludes live attachment/geometry, not the notification seam.
        source = (SOURCE/'prototypes/inspector/build_live.py').read_text()
        start = source.index('# Existing controller catalog')
        stop = source.index('watch=m.op(', start)
        exec(compile(source[start:stop], 'build_live.py:observer-install', 'exec'),
             dict(m=self, datexecuteDAT=object()))
        self.nodes['controller_catalog'].par.active = True

    def parameter_changed(self, mode=False):
        """Replay the existing controller parameter watcher for guard cases."""
        source = (SOURCE/'prototypes/inspector/build_live.py').read_text()
        start = source.index('watch=m.op('); stop = source.index('config=m.op(', start)
        exec(compile(source[start:stop], 'build_live.py:parameter-watch-install', 'exec'),
             dict(m=self, parameterexecuteDAT=object()))
        watcher = self.nodes['controller_parameters']; watcher.par.active = True
        namespace = dict(parent=S(InspectorModel=self.model))
        exec(watcher.text, namespace)
        namespace['onModeChange' if mode else 'onValueChange'](None, None)


class ScheduledActionDetailsTests(TestCase):
    def source_fixture(self, acknowledged=True):
        """Real Action recall/state/catalog/adapter, fake TD DAT/frame boundaries."""
        ext, manager, parameter, ignored = runtime_actions.ActionTests().fixture()
        ext.RemoveControl('original')
        provider = [dict(status='succeeded', error='', entries=[dict(actual_value=.72)])]
        recalls = []
        def recall(event):
            recalls.append(event); return deepcopy(provider[0])
        ext.RegisterAction('tool.preset.clean', 'Clean', recall, replace=True)
        ext.AssignAction(1, 'tool.preset.clean', id='mapping')
        if acknowledged:
            runtime_actions.ActionTests().ack(ext)
        else:
            ext._host.connected = ext._host.plugin = False
            ext._host._sync()
        ext._update_catalog()
        network = Network(); storage = {}
        nodes = {name: Dat(network) for name in ('targets', 'database', 'context_state')}
        nodes['title'] = S(par=S(text=''))
        nodes['inspector_data'] = S(module=inspector_data)
        controller = ext.ownerComp; old_op = controller.op
        inspector = S(id=7, parent=lambda: controller, op=nodes.get,
            fetch=lambda name, default=None: storage.get(name, default),
            store=lambda name, value: storage.__setitem__(name, value))
        controller.op = lambda name: inspector if name == 'inspector' else nodes.get(name[10:]) if name.startswith('inspector/') else old_op(name)
        controller.ext = S(RotoPythonExt=ext)
        for name in ('GetLayoutContext', 'GetLayouts', 'GetActions', 'GetControlStates',
                     'GetControlState', 'GetControlCatalog', 'GetPluginTargets'):
            setattr(controller, name, getattr(ext, name))
        controller.GetCompContext = lambda: dict(status='disabled')
        key = tuple(ext.GetLayoutContext()['key'])
        native = TDControllerAdapter(S(par=S(Controller=S(eval=lambda: controller))))
        adapter = Adapter(); adapter.controller = controller; adapter.active = key
        adapter.records = {key: []}; adapter.Read = native.Read
        observations = []
        @contextmanager
        def observation():
            observations.append(True)
            with manager.owner_observation(): yield
        adapter.Observation = observation
        model = InspectorModel.__new__(InspectorModel)
        model.ownerComp = network; model._queued_run = model._sync_run = None
        model.WatchOwners = lambda: []; model.WatchPars = lambda: ''
        ControllerCatalog.__init__(model, adapter, schedule=model._schedule_flush)
        events = [[], []]
        class View:
            def __init__(self, index): self.index = index; self.details = []
            def changed(self, *args):
                events[self.index].append(args)
                self.details.append(deepcopy(model.Info(key, 8)))
        network.views = [View(0), View(1)]  # retain actual WeakMethod recipients
        for index, view in enumerate(network.views): model.Subscribe(str(index), key, view.changed)
        model.GetCatalog(key); network.install(model)
        # TD-only output/custom-par publication is outside this source replay.
        # RecallAction still invokes its normal publisher automatically.
        ext._publish = ext._publish_inspector
        return network, ext, model, provider, recalls, nodes, events, observations, key

    def test_real_action_partial_error_and_clear_keep_assignment_token_scheduled(self):
        for acknowledged in (False, True):
            with self.subTest(acknowledged=acknowledged):
                self.verify_real_partial_chain(acknowledged)

    def verify_real_partial_chain(self, acknowledged):
        network, ext, model, provider, recalls, nodes, events, observations, key = self.source_fixture(acknowledged)
        with patch('RotoPythonExt.run', network.frames.run, create=True), \
             patch.object(live_model, 'run', network.frames.run, create=True):
            ext.RecallAction('tool.preset.clean'); network.frames.drain()
            token = model.GetToken(key, 8)
            for status, error in (('partial', 'native partial details'), ('succeeded', '')):
                for view in events: view.clear()
                observations.clear(); sync = model._sync_count
                for value in (.73, .74, .75):
                    provider[0] = dict(status=status, error=error, revision=4,
                        readback=dict(amount=value), entries=[dict(actual_value=value)])
                    ext.RecallAction('tool.preset.clean')
                actual = ext.GetControlState('mapping')
                self.assertEqual(actual['error'], 'partial: native partial details' if error else '')
                self.assertEqual(ext.GetControlCatalog()[0]['error'], actual['error'])
                self.assertTrue(actual['valid'] and actual['action_available'])
                self.assertEqual(actual['mapped'], acknowledged)
                self.assertEqual(actual['requires_relearn'], not acknowledged)
                network.frames.drain()
                self.assertEqual(model.Info(key, 8)['error'], actual['error'])
                self.assertEqual(model.Info(key, 8)['action_result']['readback'], dict(amount=.75))
                self.assertEqual(model._sync_count, sync + 1)
                self.assertEqual(observations, [True])
                for index, view in enumerate(events):
                    self.assertEqual(len(view), 1)
                    self.assertEqual(view[0][1:3], (1 << 8, 0))
                    detail = network.views[index].details[-1]
                    self.assertEqual(detail['error'], actual['error'])
                    self.assertEqual(detail['action_result']['status'], status)
                    self.assertEqual(detail['action_result']['readback'], dict(amount=.75))
                self.assertEqual(model.GetToken(key, 8), token)
                self.assertEqual(model.Health(key, 8)['code'], 'action_failed' if error else 'mapped' if acknowledged else 'relearn')
                self.assertEqual(model.adapter.writes, [])
                self.assertEqual(len(recalls), 1 + (3 if error else 6))

    def test_real_hardware_failure_fences_token_and_requires_fresh_repair_ack(self):
        network, ext, model, provider, recalls, nodes, events, observations, key = self.source_fixture()
        with patch('RotoPythonExt.run', network.frames.run, create=True), \
             patch.object(live_model, 'run', network.frames.run, create=True):
            ext.RecallAction('tool.preset.clean'); network.frames.drain()
            token = model.GetToken(key, 8)
            provider[0] = dict(status='partial', error='hardware partial')
            ext._receive_midi((191, 20, 127)); network.frames.drain()
            failed = ext.GetControlState('mapping')
            self.assertFalse(failed['valid'] or failed['mapped'])
            self.assertEqual(failed['mapping_error'], 'partial: hardware partial')
            self.assertEqual(failed['error'], failed['mapping_error'])
            self.assertNotEqual(model.GetToken(key, 8), token)
            with self.assertRaisesRegex(ValueError, 'Mapping changed'):
                model.Configure(key, 8, dict(button_type='toggle'), token)
            count = len(recalls)
            ext._receive_midi((191, 20, 0)); ext._receive_midi((191, 20, 127))
            self.assertEqual(len(recalls), count)
            ext.AssignAction(1, 'tool.preset.clean', id='mapping')
            self.assertFalse(ext.GetControlState('mapping')['mapped'])
            ext._receive_midi((191, 20, 127)); self.assertEqual(len(recalls), count)
            runtime_actions.ActionTests().ack(ext)
            self.assertEqual(len(recalls), count)
            repaired = ext.GetControlState('mapping')
            self.assertTrue(repaired['valid'] and repaired['mapped'])
            self.assertEqual(repaired['mapping_error'], '')
            self.assertEqual(repaired['error'], 'partial: hardware partial')  # no masked history
            network.frames.drain(); repaired_token = model.GetToken(key, 8)
            provider[0] = dict(status='succeeded', error='')
            ext._receive_midi((191, 20, 127)); network.frames.drain()
            self.assertEqual(len(recalls), count + 1)
            self.assertEqual(model.GetToken(key, 8), repaired_token)

    def test_true_action_definition_availability_and_mapping_error_expire_tokens(self):
        mutations = (dict(mapping_error='Owner quarantined', error='Owner quarantined'),
                     dict(valid=False), dict(action_available=False),
                     dict(action_id='preset.replacement'), dict(button_type='toggle'),
                     dict(definition_error='Descriptor changed'))
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                network, ext, model, records, nodes, events, scans = self.fixture()
                records[0]['mapping_error'] = ''
                with patch('RotoPythonExt.run', network.frames.run, create=True), \
                     patch.object(live_model, 'run', network.frames.run, create=True):
                    ext._publish_inspector(); network.frames.drain()
                    token = model.GetToken(KEY, 8)
                    records[0].update(mutation)
                    ext._publish_inspector()
                    if 'definition_error' in mutation: network.parameter_changed(mode=True)
                    network.frames.drain()
                    self.assertNotEqual(model.GetToken(KEY, 8), token)
                    with self.assertRaisesRegex(ValueError, 'Mapping changed'):
                        model.Configure(KEY, 8, dict(button_type='toggle'), token)
                    self.assertEqual(model.adapter.writes, [])

    def test_generic_errors_descriptors_and_unknown_action_provenance_remain_fenced(self):
        for kind in ('parameter', 'callback', 'action'):
            with self.subTest(kind=kind):
                network, ext, model, records, nodes, events, scans = self.fixture()
                records[0]['binding_type'] = kind  # no authoritative mapping_error
                with patch('RotoPythonExt.run', network.frames.run, create=True), \
                     patch.object(live_model, 'run', network.frames.run, create=True):
                    ext._publish_inspector(); network.frames.drain()
                    token = model.GetToken(KEY, 8)
                    records[0]['error'] = 'Unclassified target error'
                    ext._publish_inspector(); network.frames.drain()
                    self.assertNotEqual(model.GetToken(KEY, 8), token)
                    token = model.GetToken(KEY, 8)
                    records[0]['parameter_definition'] = ((1, '/effect', 'Value', 'Int'),)
                    ext._publish_inspector(); network.parameter_changed(mode=True); network.frames.drain()
                    self.assertNotEqual(model.GetToken(KEY, 8), token)
                    token = model.GetToken(KEY, 8)
                    model.adapter.session += 1
                    network.parameter_changed(); network.frames.drain()
                    self.assertNotEqual(model.GetToken(KEY, 8), token)

    def fixture(self):
        network = Network(); storage = {}; context = dict(key=KEY, label='Device',
            category='CUSTOM', locked=False)
        records = [action(action_result=dict(status='succeeded', error='',
                    entries=[dict(actual_value=.71)]))]
        nodes = {name: Dat(network) for name in ('targets', 'database', 'context_state')}
        nodes['title'] = S(par=S(text=''))
        nodes['inspector_data'] = S(module=inspector_data)
        controller = S(valid=True, GetLayoutContext=lambda: deepcopy(context),
            GetLayouts=lambda: [dict(id=KEY[0], name='Layout', category='CUSTOM')],
            GetCompContext=lambda: dict(status='disabled'),
            op=lambda name: nodes[name.split('/')[-1]])
        inspector = S(id=7, parent=lambda: controller, op=nodes.get,
            fetch=lambda name, default=None: storage.get(name, default),
            store=lambda name, value: storage.__setitem__(name, value))
        scans = []
        @contextmanager
        def observation():
            scans.append(True); yield
        ext = RotoPythonExt.__new__(RotoPythonExt)
        ext._actions = Actions(); network.recalls = []
        ext._actions.register('preset.clean', 'Clean', network.recalls.append)
        ext._actions.results['preset.clean'] = records[0]['action_result']
        controller.GetActions = ext.GetActions
        ext.ownerComp = S(valid=True, op=lambda name: inspector,
                          ext=S(RotoPythonExt=ext))
        ext._layouts = S(owner_observation=observation)
        ext.GetControlCatalog = lambda: deepcopy(records)
        adapter = Adapter(); adapter.controller = controller
        model_scans = []
        @contextmanager
        def model_observation():
            model_scans.append(True); yield
        adapter.records = {KEY: records}; adapter.Observation = model_observation
        network.model_scans = model_scans
        model = InspectorModel.__new__(InspectorModel)
        model.ownerComp = network; model._queued_run = model._sync_run = None
        model.WatchOwners = lambda: []; model.WatchPars = lambda: ''
        ControllerCatalog.__init__(model, adapter, schedule=model._schedule_flush)
        events = []; model.Subscribe('view', KEY, lambda *args: events.append(args))
        model.GetCatalog(KEY); network.install(model)
        return network, ext, model, records, nodes, events, scans

    def test_same_status_nested_details_reach_info_via_scheduled_ingress(self):
        network, ext, model, records, nodes, events, scans = self.fixture()
        with patch('RotoPythonExt.run', network.frames.run, create=True), \
             patch.object(live_model, 'run', network.frames.run, create=True):
            ext._publish_inspector(); network.frames.drain()
            token = model.GetToken(KEY, 8); sync = model._sync_count
            table = nodes['targets'].text
            records[0]['action_result']['entries'][0]['actual_value'] = .72
            ext._publish_inspector(); network.frames.drain()
            self.assertIn('0.72', nodes['database'].text)  # source publication passed
            self.assertEqual(nodes['targets'].text, table)  # no table/status signal
            self.assertGreater(model._sync_count, sync, 'Scheduled model Sync never ran')
            self.assertEqual(model.Info(KEY, 8)['action_result']['entries'][0]['actual_value'], .72)
            self.assertEqual(model.GetToken(KEY, 8), token)
            self.assertEqual(events[-1][1:3], (1 << 8, 0))
            self.assertEqual(model.adapter.writes, [])
            self.assertEqual(network.recalls, [])

    def test_burst_all_provider_details_coalesce_without_token_or_registry_churn(self):
        network, ext, model, records, nodes, events, scans = self.fixture()
        with patch('RotoPythonExt.run', network.frames.run, create=True), \
             patch.object(live_model, 'run', network.frames.run, create=True):
            ext._publish_inspector(); network.frames.drain()
            token = model.GetToken(KEY, 8); sync = model._sync_count
            metadata = nodes['context_state'].text; events.clear()
            network.model_scans.clear(); scripts = len(network.frames.scripts)
            result = records[0]['action_result']
            for value in (.72, .73, .74):
                result.update(status='partial', revision=4, error='partial detail',
                    readback=dict(amount=value), entries=[dict(actual_value=value)])
                ext._publish_inspector()
            network.frames.drain()
            self.assertEqual(model._sync_count, sync + 1)
            self.assertEqual(network.model_scans, [True])
            self.assertEqual(network.frames.scripts[scripts:].count('args[0]._flush_inspector()'), 1)
            self.assertEqual(network.frames.scripts[scripts:].count('args[0].SyncController()'), 1)
            self.assertEqual(model.Info(KEY, 8)['action_result'], result)
            self.assertEqual(model.GetToken(KEY, 8), token)
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0][1:3], (1 << 8, 0))
            # JSON diagnostics did not alter the registry/owner/routing snapshot.
            import json
            before = json.loads(metadata); after = json.loads(nodes['context_state'].text)
            self.assertEqual(before['layouts'], after['layouts'])
            self.assertEqual(before['routing'], after['routing'])
            network.frames.scripts.clear()
            ext._publish_inspector(); network.frames.drain()
            self.assertEqual(network.frames.scripts, [])
            self.assertEqual(model.adapter.writes, []); self.assertEqual(network.recalls, [])

    def test_offpage_inactive_result_notifies_without_publishing_slot_union(self):
        network, ext, model, records, nodes, events, scans = self.fixture()
        other = ('other-layout', 'other-track', 'other-device')
        ext._actions.register('preset.other', 'Other', network.recalls.append)
        result = dict(status='succeeded', error='', entries=[dict(actual_value=.81)])
        ext._actions.results['preset.other'] = result
        model.adapter.records[other] = [action(id='inactive-only', action_id='preset.other',
                                                action_result=result)]
        inactive_events = []
        model.Subscribe('inactive', other, lambda *args: inactive_events.append(args))
        with patch('RotoPythonExt.run', network.frames.run, create=True), \
             patch.object(live_model, 'run', network.frames.run, create=True):
            ext._publish_inspector(); network.frames.drain()
            active_token = model.GetToken(KEY, 8); inactive_token = model.GetToken(other, 8)
            table = nodes['targets'].text; database = nodes['database'].text
            events.clear(); inactive_events.clear()
            result['entries'][0]['actual_value'] = .82
            ext._publish_inspector(); network.frames.drain()
            self.assertEqual(nodes['targets'].text, table)
            self.assertEqual(nodes['database'].text, database)
            self.assertEqual(model.Info(other, 8)['action_result']['entries'][0]['actual_value'], .82)
            self.assertEqual(model.Info(KEY, 8)['id'], 'mapping')
            self.assertEqual(model.GetToken(KEY, 8), active_token)
            self.assertEqual(model.GetToken(other, 8), inactive_token)
            self.assertEqual(events, [])
            self.assertEqual(inactive_events[0][1:3], (1 << 8, 0))
            self.assertEqual(model.adapter.active, KEY)
            self.assertEqual(model.adapter.writes, []); self.assertEqual(network.recalls, [])

    def test_value_only_updates_do_not_churn_metadata_and_identity_still_expires_token(self):
        network, ext, model, records, nodes, events, scans = self.fixture()
        records.append(dict(action(kind='knob', slot=1, id='amount', binding_type='parameter',
            action_id=None, action_available=None, action_result=None, mode='value',
            parameter='Amount', comp='/consumer', value_source='live', value=.4)))
        with patch('RotoPythonExt.run', network.frames.run, create=True), \
             patch.object(live_model, 'run', network.frames.run, create=True):
            ext._publish_inspector(); network.frames.drain()
            token = model.GetToken(KEY, 8); metadata = nodes['context_state'].text
            records[1]['value'] = .5
            ext._publish_inspector(); network.frames.drain()
            self.assertEqual(nodes['context_state'].text, metadata)
            self.assertEqual(model.GetCatalog(KEY)[0]['Value'], .5)
            self.assertEqual(model.GetToken(KEY, 8), token)
            records[0]['action_id'] = 'preset.replacement'
            ext._publish_inspector(); network.frames.drain()
            self.assertNotEqual(model.GetToken(KEY, 8), token)
            self.assertEqual(model.adapter.writes, []); self.assertEqual(network.recalls, [])
