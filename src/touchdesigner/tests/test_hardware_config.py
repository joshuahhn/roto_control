"""Detached capture lifecycle and TD context fences, independent of MIDI I/O."""
import tests
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from hardware_config import HardwareConfig, ReadContext
import RotoPythonExt as runtime
import test_serial_read_process as wire
import test_layouts
from protocol import digest, SysExCommand


class Process:
    def __init__(self, ignore_terminate=False):
        read, write = os.pipe(); self.input = read; self.stdin = os.fdopen(write, 'wb', buffering=0)
        read, write = os.pipe(); self.stdout = os.fdopen(read, 'rb', buffering=0); self.output = write
        read, write = os.pipe(); self.stderr = os.fdopen(read, 'rb', buffering=0); self.errors = write
        os.set_blocking(self.input, False)
        self.returncode = None
        self.terminated = self.killed = 0
        self.ignore_terminate = ignore_terminate

    def poll(self): return self.returncode
    def terminate(self):
        self.terminated += 1
        if not self.ignore_terminate: self.returncode = -15
    def kill(self): self.killed += 1; self.returncode = -9
    def wait(self, timeout):
        if self.returncode is None: raise subprocess.TimeoutExpired('fixture', timeout)
        return self.returncode
    def receive(self): return json.loads(os.read(self.input, 16384))
    def emit(self, result, code=0):
        os.write(self.output, json.dumps(result).encode() + b'\n')
        os.close(self.output); self.output = None
        os.close(self.errors); self.errors = None
        self.returncode = code
    def close(self):
        for stream in (self.stdin, self.stdout, self.stderr):
            if not stream.closed: stream.close()
        for fd in (self.input, self.output, self.errors):
            if fd is not None:
                try: os.close(fd)
                except OSError: pass
        self.input = self.output = self.errors = None


def context(host=None, signature=('a',)):
    return ReadContext(host or object(), signature, dict(plugin_hash=wire.PH, controls=copy.deepcopy(wire.EXPECTED)),
                       dict(device_id='fixture', routing_key=('layout', 'track', 'device')))


def terminal(request):
    controls = [wire.worker.decode_control(bytes.fromhex(frame), expected, wire.PH)
                for frame, expected in zip(wire.FRAMES, request['controls'])]
    return dict(version=1, request_id=request['request_id'], serial_session_id=request['serial_session_id'], ok=True,
        snapshot=dict(controls=controls, provenance=dict(request_id=request['request_id'], serial_session_id=request['serial_session_id'],
            endpoint=request['port'], page_offset=0, observation='snapshot_only', worker_closed=True,
            physical_device=wire.PHYSICAL, firmware=dict(version='3.3.0'), started_at_utc='start', captured_at_utc='capture', observed_through_utc='capture')))


class HardwareConfigTests(unittest.TestCase):
    def owner(self, ignore=False):
        process = Process(ignore); self.addCleanup(process.close)
        clock = [1.0]
        owner = HardwareConfig(spawn=Mock(return_value=process), clock=lambda: clock[0])
        self.addCleanup(lambda: owner.close('test cleanup'))
        return owner, process, context(), clock

    def start(self, owner, current):
        result = owner.read(current, port='/dev/cu.fixture', python=sys.executable, worker_source='fixture')
        self.assertEqual(result['status'], 'reading')
        owner.tick(current)
        return result

    def captured(self):
        owner, process, current, clock = self.owner()
        self.start(owner, current)
        process.emit(terminal(process.receive())); owner.tick(current)
        self.assertEqual(owner.snapshot(current)['status'], 'captured')
        return owner, process, current, clock

    def test_same_pending_refresh_deduplicates_and_other_port_returns_busy(self):
        owner, process, current, clock = self.owner()
        first = self.start(owner, current)
        second = owner.read(current, port='/dev/cu.fixture', python='ignored', worker_source='ignored')
        self.assertEqual(first, second); self.assertEqual(owner.spawn.call_count, 1)
        busy = owner.read(current, port='/dev/cu.other', python='ignored', worker_source='ignored')
        self.assertEqual(busy['error']['code'], 'busy'); self.assertEqual(owner.spawn.call_count, 1)
        first['status'] = 'changed'; self.assertEqual(owner.snapshot(current)['status'], 'reading')

    def test_closed_capture_deepcopy_and_known_context_invalidation(self):
        owner, process, current, clock = self.captured()
        result = owner.snapshot(current)
        self.assertFalse(owner.active); self.assertTrue(process.stdout.closed)
        self.assertEqual(result['snapshot']['context']['device_id'], 'fixture')
        result['snapshot']['controls'][0]['haptics']['labels'].append('wrong')
        self.assertEqual(owner.snapshot(current)['snapshot']['controls'][0]['haptics']['labels'], [])
        changed = context(current.host, ('b',))
        stale = owner.snapshot(changed)
        self.assertEqual(stale['status'], 'stale'); self.assertIsNotNone(stale['snapshot'])
        self.assertEqual(owner.snapshot(current)['status'], 'stale')

    def test_generation_aba_and_new_host_same_signature_discard_pending_result(self):
        for replacement in ('generation', 'host'):
            owner, process, current, clock = self.owner()
            self.start(owner, current); result = terminal(process.receive())
            if replacement == 'generation': owner.invalidate('A to B to A')
            else: owner.observe(context(signature=current.signature))
            process.emit(result); owner.tick(current)
            self.assertEqual(owner.snapshot(current)['status'], 'stale'); self.assertIsNone(owner.snapshot(current)['snapshot'])
            self.assertFalse(owner.active)

    def test_exit_before_complete_result_wrong_identity_and_nested_settings_fail(self):
        for mutation in ('request', 'control', 'haptic', 'button', 'macro', 'duplicate', 'stderr', 'crash'):
            owner, process, current, clock = self.owner()
            self.start(owner, current); event = terminal(process.receive())
            if mutation == 'request': event['request_id'] = 'other'
            elif mutation == 'control': event['snapshot']['controls'][0]['parameter_index'] = 1
            elif mutation == 'haptic': event['snapshot']['controls'][0]['haptics']['physical_feel_verified'] = True
            elif mutation == 'button': event['snapshot']['controls'][1]['button']['led_on'] = 99
            elif mutation == 'macro': event['snapshot']['controls'][0]['macro'] = 2
            elif mutation == 'duplicate': os.write(process.output, b'{}\n')
            elif mutation == 'stderr': os.write(process.errors, b'worker traceback')
            process.emit(event, 1 if mutation == 'crash' else 0); owner.tick(current)
            result = owner.snapshot(current)
            self.assertEqual(result['status'], 'error', mutation); self.assertIsNone(result['snapshot'], mutation)
            owner.tick(current); self.assertFalse(owner.active)

    def test_worker_error_isolated_and_parent_waits_for_exit_not_just_line(self):
        owner, process, current, clock = self.owner()
        self.start(owner, current); event = terminal(process.receive())
        os.write(process.output, json.dumps(event).encode() + b'\n'); owner.tick(current)
        self.assertEqual(owner.snapshot(current)['status'], 'reading')
        os.close(process.output); process.output = None; process.returncode = 0
        os.close(process.errors); process.errors = None
        owner.tick(current); self.assertEqual(owner.snapshot(current)['status'], 'captured')

    def test_deadline_terminate_kill_reap_and_idempotent_close(self):
        owner, process, current, clock = self.owner(ignore=True)
        self.start(owner, current); clock[0] = 30; owner.tick(current)
        self.assertEqual(owner.snapshot(current)['error']['code'], 'timeout'); self.assertEqual(process.terminated, 1)
        clock[0] += .3; owner.tick(current); self.assertEqual(process.killed, 1)
        owner.tick(current); self.assertFalse(owner.active)
        owner.close('again'); owner.close('again'); self.assertTrue(process.stdout.closed)

    def test_spawn_failure_and_invalid_port_return_status(self):
        owner, process, current, clock = self.owner()
        owner.spawn.side_effect = OSError('missing executable')
        self.assertEqual(owner.read(current, port='/dev/cu.fixture', python='none', worker_source='pass')['error']['code'], 'worker_error')
        self.assertFalse(owner.active)
        self.assertEqual(owner.read(current, port='COM3', python='none', worker_source='pass')['error']['code'], 'invalid_request')

    def test_real_subprocess_oversize_and_truncated_stdout_never_publish(self):
        for source in ("print('x'*70000)", "import sys; sys.stdout.write('{}')"):
            owner = HardwareConfig(); current = context()
            self.addCleanup(lambda o=owner: o.close('test cleanup'))
            owner.read(current, port='/dev/cu.fixture', python=sys.executable, worker_source=source)
            deadline = time.monotonic() + 3
            while owner.active and time.monotonic() < deadline:
                owner.tick(current)
                if owner.active:
                    streams = [s for s in (owner.job['process'].stdout, owner.job['process'].stderr) if not s.closed]
                    import select
                    select.select(streams, [], [], .05)
            self.assertFalse(owner.active); self.assertEqual(owner.snapshot(current)['status'], 'error')


class ExtensionHardwareTests(unittest.TestCase):
    def fixture(self):
        extension, manager, parameter = test_layouts.LayoutTests().fixture()
        extension._receive = b''; extension._process = None
        extension._hardware_config = HardwareConfig()
        extension._publish_inspector = Mock()
        return extension, manager, parameter

    def seed_capture(self, extension):
        owner = extension._hardware_owner()
        current, available = extension._hardware_context()
        self.assertTrue(available)
        owner.observe(current)
        owner.result.update(status='captured', snapshot=dict(marker='historical'))
        return owner

    def test_context_projection_distinguishes_slot_index_hash_without_value_reads(self):
        e, manager, parameter = self.fixture()
        c = e._host.controls['knob', 1]; c.index = 128
        current, available = e._hardware_context()
        self.assertTrue(available); self.assertEqual(current.manifest['controls'][0]['slot'], 1)
        self.assertEqual(current.manifest['controls'][0]['parameter_index'], 128)
        self.assertEqual(current.manifest['controls'][0]['parameter_hash'], list(digest(c.target_id, 6)))
        owner = self.seed_capture(e); before = current.signature
        parameter.val = 8
        self.assertEqual(e._hardware_context()[0].signature, before)
        self.assertEqual(e.GetHardwareConfig()['status'], 'captured')

    def test_real_binding_layout_install_identity_override_and_page_aba_fence(self):
        for action in ('binding', 'install', 'page', 'host'):
            e, manager, parameter = self.fixture(); owner = self.seed_capture(e)
            if action == 'binding':
                specs = [dict(kind='knob', slot=1, id='original', parameter=parameter)]
                e.BindControls(specs, group_id='test'); e.BindControls(specs, group_id='test')
            elif action == 'install':
                record = manager.record(); manager.capture(force=True); record = manager.record()
                manager.install(record); manager.install(record)
            elif action == 'page':
                manager.page_changed()
            else:
                e._host = copy.copy(e._host)
            self.assertEqual(e.GetHardwareConfig()['status'], 'stale', action)
            self.assertGreater(owner.generation, 0, action)

    def test_same_identity_hardware_context_events_stale_but_values_do_not(self):
        for message in (SysExCommand.SET_PLUGIN_MODE.message((0,)), SysExCommand.SET_DEVICE_LEARN.message((1,)), SysExCommand.ROTO_PAGE_LEFT.message(), SysExCommand.SET_MIXER_ALL_MODE.message()):
            e, manager, parameter = self.fixture(); owner = self.seed_capture(e)
            e._receive_midi(message)
            self.assertEqual(e.GetHardwareConfig()['status'], 'stale')
        e, manager, parameter = self.fixture(); self.seed_capture(e)
        e._receive_midi((191, 12, 1)); e._receive_midi((191, 44, 1))
        self.assertEqual(e.GetHardwareConfig()['status'], 'captured')

    def test_read_spawn_and_serial_error_leave_midi_and_saved_data_untouched(self):
        e, manager, parameter = self.fixture()
        process = Process(); self.addCleanup(process.close)
        owner = HardwareConfig(spawn=Mock(return_value=process)); e._hardware_config = owner
        before = copy.deepcopy(e.ownerComp.fetch('layout_registry'))
        midi = object(); e._process = midi; e._last_error = 'MIDI diagnostic'
        oldop = e.ownerComp.op
        e.ownerComp.op = lambda n: SimpleNamespace(text='embedded') if n == 'serial_read_process' else oldop(n)
        e.ownerComp.par.Python = SimpleNamespace(eval=lambda: sys.executable)
        with patch.object(runtime, 'project', SimpleNamespace(folder='/tmp'), create=True): result = e.ReadHardwareConfig(port='/dev/cu.fixture')
        self.assertEqual(result['status'], 'reading'); e._tick_hardware()
        request = process.receive()
        process.emit(dict(version=1, request_id=request['request_id'], serial_session_id=request['serial_session_id'], ok=False,
                          error=dict(code='port_busy', message='close Roto-Setup')))
        e._tick_hardware()
        self.assertEqual(e.GetHardwareConfig()['error']['code'], 'port_busy')
        self.assertIs(e._process, midi); self.assertEqual(e._last_error, 'MIDI diagnostic')
        self.assertEqual(e.ownerComp.fetch('layout_registry'), before); self.assertEqual(parameter.eval(), 5)
        owner.close('cleanup')

    def test_tick_finally_services_serial_when_midi_disconnected_or_fails(self):
        e, manager, parameter = self.fixture()
        e._restore_pending = False
        observed = []
        e._tick_hardware = lambda: observed.append('serial')
        e._tick = lambda: None
        e.Tick(); self.assertEqual(observed, ['serial'])
        def failed(): raise RuntimeError('MIDI failure')
        e._tick = failed
        with self.assertRaises(RuntimeError): e.Tick()
        self.assertEqual(observed, ['serial', 'serial'])

class CompletionRaceTests(unittest.TestCase):
    owner = HardwareConfigTests.owner
    start = HardwareConfigTests.start

    def test_exit_observed_after_eagain_defers_until_both_pipes_drained(self):
        owner, process, current, clock = self.owner()
        self.start(owner, current); request = process.receive()
        original = process.poll
        fired = []
        def finish_during_poll():
            if not fired:
                fired.append(True); process.emit(terminal(request))
            return original()
        process.poll = finish_during_poll
        owner.tick(current)
        self.assertEqual(owner.snapshot(current)['status'], 'reading')
        owner.tick(current)
        self.assertEqual(owner.snapshot(current)['status'], 'captured')
        self.assertFalse(owner.active)

    def test_closed_stdout_late_stderr_is_drained_before_publication(self):
        owner, process, current, clock = self.owner()
        self.start(owner, current); request = process.receive()
        os.write(process.output, json.dumps(terminal(request)).encode() + b'\n')
        os.close(process.output); process.output = None
        original = process.poll
        fired = []
        def finish_during_poll():
            if not fired:
                fired.append(True); os.write(process.errors, b'late failure')
                os.close(process.errors); process.errors = None; process.returncode = 0
            return original()
        process.poll = finish_during_poll
        owner.tick(current); self.assertEqual(owner.snapshot(current)['status'], 'reading')
        owner.tick(current); self.assertEqual(owner.snapshot(current)['status'], 'error')

    def test_dead_child_with_inherited_open_pipes_still_has_deadline(self):
        owner, process, current, clock = self.owner()
        self.start(owner, current); process.returncode = 0
        owner.tick(current); self.assertEqual(owner.snapshot(current)['status'], 'reading')
        clock[0] = 30; owner.tick(current)
        self.assertEqual(owner.snapshot(current)['error']['code'], 'timeout')
        owner.tick(current); self.assertFalse(owner.active)

class LifecycleTests(unittest.TestCase):
    fixture = ExtensionHardwareTests.fixture
    seed_capture = ExtensionHardwareTests.seed_capture

    def test_disconnect_and_destroy_same_identity_invalidate_and_reap_optional_child(self):
        for action in ('disconnect', 'destroy'):
            extension, manager, parameter = self.fixture()
            process = Process(ignore_terminate=True); self.addCleanup(process.close)
            owner = HardwareConfig(spawn=Mock(return_value=process)); extension._hardware_config = owner
            current, available = extension._hardware_context()
            owner.read(current, port='/dev/cu.fixture', python=sys.executable, worker_source='fixture')
            if action == 'disconnect': extension.Disconnect()
            else: extension.onDestroyTD()
            self.assertFalse(owner.active); self.assertEqual(process.killed, 1)
            self.assertEqual(extension.GetHardwareConfig()['status'], 'stale')
            self.assertEqual(parameter.eval(), 5)

    def test_unsupported_parent_platform_returns_action_before_spawning(self):
        import hardware_config
        spawn = Mock(); owner = HardwareConfig(spawn=spawn)
        with patch.object(hardware_config.sys, 'platform', 'win32'):
            result = owner.read(context(), port='/dev/cu.fixture', python='unused', worker_source='unused')
        self.assertEqual(result['error']['code'], 'unsupported_backend'); spawn.assert_not_called()

    def test_unavailable_owner_and_pending_backlog_fail_closed_without_start(self):
        extension, manager, parameter = self.fixture()
        follower = SimpleNamespace(gated=False, paused=False, pending=None, backlog=True, token=(0, 0))
        extension._follow = follower
        self.assertFalse(extension._hardware_context()[1])
        follower.backlog = False; follower.paused = True
        self.assertFalse(extension._hardware_context()[1])
        follower.paused = False
        self.assertTrue(extension._hardware_context()[1])

class ValueFreshnessTests(unittest.TestCase):
    fixture = ExtensionHardwareTests.fixture
    seed_capture = ExtensionHardwareTests.seed_capture

    def test_buffered_value_input_and_callback_dispatch_do_not_stale_capture(self):
        extension, manager, parameter = self.fixture()
        owner = self.seed_capture(extension)
        signature = extension._hardware_context()[0].signature
        extension._receive = b'{"midi":[191,44,1]}\n'
        extension._receive_midi((191, 12, 1)); extension._receive_midi((191, 44, 1))
        extension._dispatching = True
        self.assertFalse(extension._hardware_context()[1])
        self.assertEqual(extension._hardware_context()[0].signature, signature)
        self.assertEqual(extension.GetHardwareConfig()['status'], 'captured')
        extension._dispatching = False; extension._receive = b''
        self.assertEqual(extension.GetHardwareConfig()['status'], 'captured')

class LazyMixStartupTests(unittest.TestCase):
    fixture = ExtensionHardwareTests.fixture

    def test_first_tick_lazy_mix_initialization_keeps_pending_serial_read(self):
        extension, manager, parameter = self.fixture()
        process = Process(); self.addCleanup(process.close)
        owner = HardwareConfig(spawn=Mock(return_value=process)); extension._hardware_config = owner
        self.addCleanup(lambda: owner.close('test cleanup'))
        extension._mix = None
        current, available = extension._hardware_context()
        owner.read(current, port='/dev/cu.fixture', python=sys.executable, worker_source='fixture')
        ingress = extension._ingress_token()
        extension.Tick()
        self.assertIsNotNone(extension._mix)
        self.assertNotEqual(extension._ingress_token(), ingress)
        self.assertEqual(extension.GetHardwareConfig()['status'], 'reading')
        self.assertEqual(process.terminated, 0)
        extension._mix_mode_boundary()
        self.assertEqual(extension.GetHardwareConfig()['status'], 'stale')
        self.assertEqual(process.terminated, 1)

    def test_serial_fingerprint_keeps_follower_connection_and_routing_boundaries(self):
        extension, manager, parameter = self.fixture()
        extension._follow = SimpleNamespace(gated=False, paused=False, pending=None, backlog=False, token=(2, 3))
        owner = extension._hardware_owner()
        owner.observe(extension._hardware_context()[0])
        owner.result.update(status='captured', snapshot={'historical': True})
        extension._follow.token = (2, 4)
        self.assertEqual(extension.GetHardwareConfig()['status'], 'stale')
