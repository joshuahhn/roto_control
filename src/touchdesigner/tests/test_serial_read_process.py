"""Read-only wire behavior against the measured firmware 3.3.0 PLUGIN records."""
import tests
import copy
import json
import os
from pathlib import Path
import plistlib
import select
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import Mock, patch
import serial_read_process as worker

FRAMES = ['a500774a21745a74143e000080427d382421520000003fff416d6f756e74000000000000004000ffff0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000', 'a500774a21745a74143e0000822b3f13485106007f456e61626c6564000000000000400d4601024f6666000000000000000000004f6e00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000', 'a500774a21745a74143e0100815d73776e117d0000003fff537465707300000000000000004000ffff0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000', 'a500774a21745a74143e020083130e3c1f28120000003fff4d6f64650000000000000000004001ffff03464952535400000000000000005345434f4e44000000000000005448495244000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000']
EXPECTED = [{'kind': 'knob', 'slot': 1, 'parameter_index': 128, 'parameter_hash': [66, 125, 56, 36, 33, 82], 'id': 'Amount'}, {'kind': 'button', 'slot': 1, 'parameter_index': 130, 'parameter_hash': [43, 63, 19, 72, 81, 6], 'id': 'Enabled'}, {'kind': 'knob', 'slot': 2, 'parameter_index': 129, 'parameter_hash': [93, 115, 119, 110, 17, 125], 'id': 'Steps'}, {'kind': 'knob', 'slot': 3, 'parameter_index': 131, 'parameter_hash': [19, 14, 60, 31, 40, 18], 'id': 'Mode'}]
PH = [119, 74, 33, 116, 90, 116, 20, 62]
PHYSICAL = {'IORegistryEntryID': 100, 'sessionID': 200, 'endpoint_registry_id': 101,
            'USB Serial Number': 'fixture', 'dialin_endpoint': '/dev/tty.fixture'}
FW = b'\xa5\x00\x03\x03\x00eaa37b0'
MODE = b'\xa5\x00\x01\x00'


def job():
    return dict(version=1, request_id='request1', serial_session_id='session1', port='/dev/cu.fixture',
                plugin_hash=list(PH), controls=copy.deepcopy(EXPECTED))


class FakePort:
    def __init__(self, replies=None, fragment=4096):
        self.replies = list(replies if replies is not None else [FW, MODE, *(bytes.fromhex(x) for x in FRAMES), MODE])
        self.fragment = fragment
        self.incoming = b''
        self.writes = []
        self.closed = False

    def write(self, packet, deadline):
        self.writes.append(packet)
        reply = self.replies.pop(0)
        if isinstance(reply, Exception): raise reply
        self.incoming += reply

    def read(self, timeout):
        result, self.incoming = self.incoming[:self.fragment], self.incoming[self.fragment:]
        return result

    def close(self): self.closed = True


class SerialReadTests(unittest.TestCase):
    def capture(self, port=None, value=None):
        port = port or FakePort()
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.directory = temporary.name
        self.retirement = lambda p, d: worker.Retirement(p, d, self.directory)
        result = worker.capture(value or job(), inventory=lambda p: PHYSICAL,
                                open_port=lambda p, d: port, retirement_factory=self.retirement)
        return result, port

    def test_measured_fragmented_records_exact_get_sequence_and_closed_provenance(self):
        result, port = self.capture(FakePort(fragment=1))
        self.assertTrue(port.closed)
        self.assertEqual(port.writes, [bytes.fromhex('5a01010000'), bytes.fromhex('5a01020000'),
            bytes.fromhex('5a03090009') + bytes(PH) + b'\x00', bytes.fromhex('5a030a0009') + bytes(PH) + b'\x00',
            bytes.fromhex('5a03090009') + bytes(PH) + b'\x01', bytes.fromhex('5a03090009') + bytes(PH) + b'\x02', bytes.fromhex('5a01020000')])
        self.assertEqual([c['parameter_index'] for c in result['controls']], [128, 130, 129, 131])
        self.assertEqual(result['controls'][0]['maximum'], 16383)
        self.assertEqual(result['controls'][0]['haptics']['indent_positions'], [None, None])
        self.assertEqual(result['controls'][1]['button'], dict(mode='toggle', raw_mode=1, steps=2, led_on=13, led_off=70, labels=['Off', 'On']))
        self.assertEqual(result['controls'][3]['haptics']['labels'], ['FIRST', 'SECOND', 'THIRD'])
        self.assertEqual(result['provenance']['observation'], 'snapshot_only')
        self.assertTrue(result['provenance']['worker_closed'])
        self.assertEqual(list(Path(self.directory).iterdir()), [])

    def test_get_boundary_and_request_cannot_supply_writes(self):
        for command, payload in ((worker.SerialGet.MODE, b'\x00'), (worker.SerialGet.PLUGIN_KNOB_CONFIG, b'0' * 8), (worker.SerialGet.PLUGIN_KNOB_CONFIG, bytes(PH) + b'\x08')):
            with self.subTest(command=command), self.assertRaises(worker.ReadError): command.packet(payload)
        for key in ('opcode', 'raw', 'commands'):
            port = FakePort()
            with self.subTest(key=key), self.assertRaises(worker.ReadError): self.capture(port, dict(job(), **{key: [1, 4]}))
            self.assertEqual(port.writes, [])

    def test_each_ph_ci_full_eight_bit_mi_mh_mismatch_rejects(self):
        for offset in (2, 10, 12, 13):
            frame = bytearray.fromhex(FRAMES[0]); frame[offset] ^= 1
            port = FakePort([FW, MODE, frame])
            with self.subTest(offset=offset), self.assertRaises(worker.ReadError) as caught: self.capture(port)
            self.assertEqual(caught.exception.code, 'identity_mismatch')
            self.assertEqual(len(port.writes), 3); self.assertTrue(port.closed)

    def test_short_error_terminal_and_extra_bytes_retire(self):
        for reply in (b'\xa5\xfd', b'\xa5\xfd\xa5\x00'):
            port = FakePort([reply])
            with self.subTest(reply=reply), self.assertRaises(worker.ReadError) as caught: self.capture(port)
            self.assertEqual(caught.exception.code, 'device_error'); self.assertTrue(port.closed)
            self.assertEqual(len(port.writes), 1)
            self.assertEqual(bool(list(Path(self.directory).iterdir())), len(reply) > 2)

    def test_unrelated_midi_async_interleave_context_and_unknown_fail_closed(self):
        unrelated = b'\x5a\x02\x0b\x00\x03\x00\x00\x01'
        result, _ = self.capture(FakePort([unrelated + FW, MODE, *(bytes.fromhex(x) for x in FRAMES), MODE], fragment=1))
        self.assertEqual(len(result['controls']), 4)
        for frame in (b'\x5a\x01\x03\x00\x02\x01\x00', b'\x5a\x03\x05\x00\x00',
                      b'\x5a\x7f\x01\x00\x00', b'\x5a\x02\x0b\x00\x01\x00'):
            port = FakePort([frame + FW])
            with self.subTest(frame=frame), self.assertRaises(worker.ReadError) as caught: self.capture(port)
            self.assertEqual(caught.exception.code, 'context_changed'); self.assertTrue(port.closed)
            self.assertEqual(len(port.writes), 1)

    def test_oversize_unframed_and_trailing_replies_retire(self):
        for frame in (b'\x5a\x01\x03\xff\xff', b'\x00', b'x' * 9000, FW + b'\xa5\x00'):
            with self.subTest(frame=frame[:10]), self.assertRaises(worker.ReadError) as caught: self.capture(FakePort([frame], fragment=10000))
            self.assertEqual(caught.exception.code, 'protocol_error')
            self.assertTrue(list(Path(self.directory).iterdir()))

    def test_timeout_retirement_survives_new_owner_and_incarnation_recovers(self):
        port = FakePort([worker.ReadError('timeout', 'fixture timeout')])
        with self.assertRaises(worker.ReadError): self.capture(port)
        self.assertTrue(port.closed); self.assertEqual(len(port.writes), 1)
        late = FakePort([FW])
        with self.assertRaises(worker.ReadError) as caught:
            worker.capture(job(), inventory=lambda p: PHYSICAL, open_port=lambda p, d: late, retirement_factory=self.retirement)
        self.assertEqual(caught.exception.code, 'retired_session'); self.assertEqual(late.writes, [])
        new = dict(PHYSICAL, IORegistryEntryID=110, endpoint_registry_id=111, sessionID=210)
        result = worker.capture(job(), inventory=lambda p: new, open_port=lambda p, d: FakePort(), retirement_factory=self.retirement)
        self.assertEqual(result['provenance']['physical_device'], new)

    def test_partial_success_times_out_without_next_get(self):
        clock = [0.0]; port = FakePort([b'\xa5\x00\x03'])
        def read(timeout):
            clock[0] += timeout
            data, port.incoming = port.incoming, b''
            return data
        port.read = read
        with tempfile.TemporaryDirectory() as directory:
            retired = worker.Retirement('/dev/cu.fixture', PHYSICAL, directory)
            session = worker.ReadSession(port, retired, lambda: clock[0])
            with self.assertRaises(worker.ReadError) as caught: session.get(worker.SerialGet.FW_VERSION)
            self.assertEqual(caught.exception.code, 'timeout'); self.assertEqual(len(port.writes), 1)
            with self.assertRaises(worker.ReadError): worker.Retirement('/dev/cu.fixture', PHYSICAL, directory)

    def test_mode_page_gates_and_usb_replacement(self):
        for replies in ([FW, b'\xa5\x00\x01\x08'], [FW, b'\xa5\x00\x02\x00'],
                        [FW, MODE, *(bytes.fromhex(x) for x in FRAMES), b'\xa5\x00\x01\x08']):
            port = FakePort(replies)
            with self.assertRaises(worker.ReadError) as caught: self.capture(port)
            self.assertIn(caught.exception.code, ('unsupported_page', 'context_changed')); self.assertTrue(port.closed)
        identities = iter([PHYSICAL, dict(PHYSICAL, sessionID=300)])
        with tempfile.TemporaryDirectory() as directory, self.assertRaises(worker.ReadError) as caught:
            worker.capture(job(), inventory=lambda p: next(identities), open_port=lambda p, d: FakePort(),
                           retirement_factory=lambda p, d: worker.Retirement(p, d, directory))
        self.assertEqual(caught.exception.code, 'context_changed')

    def test_malformed_fields_unknown_and_plugin_top_indent_modes(self):
        for offset, value in ((19, 2), (24, 31), (36, 65), (37, 83), (39, 128), (41, 1)):
            frame = bytearray.fromhex(FRAMES[0]); frame[offset] = value
            with self.subTest(offset=offset), self.assertRaises(worker.ReadError): worker.decode_control(frame, EXPECTED[0], PH)
        for mode, label in ((2, 'plugin_top_indent'), (77, 'unknown')):
            frame = bytearray.fromhex(FRAMES[0]); frame[38] = mode
            control = worker.decode_control(frame, EXPECTED[0], PH)
            self.assertEqual(control['haptics']['mode'], label); self.assertEqual(control['haptics']['raw_mode'], mode)
            self.assertFalse(control['haptics']['physical_feel_verified'])

    def test_initial_orphan_bytes_retire_even_when_open_never_returns(self):
        with tempfile.TemporaryDirectory() as directory:
            def failed(p, d): raise worker.ReadError('protocol_error', 'orphan bytes')
            retired = lambda p, d: worker.Retirement(p, d, directory)
            with self.assertRaises(worker.ReadError):
                worker.capture(job(), inventory=lambda p: PHYSICAL, open_port=failed, retirement_factory=retired)
            with self.assertRaises(worker.ReadError): retired('/dev/cu.fixture', PHYSICAL)

    def test_inventory_uses_usb_ancestry_registry_ids_and_unsupported_backend(self):
        root = dict(PHYSICAL, IOObjectClass='IOUSBHostDevice', **{'USB Vendor Name': 'Melbourne Instruments', 'USB Product Name': 'Roto_Control'})
        root['IORegistryEntryChildren'] = [dict(IOCalloutDevice='/dev/cu.fixture', IODialinDevice='/dev/tty.fixture', IORegistryEntryID=101)]
        reply = subprocess.CompletedProcess([], 0, stdout=plistlib.dumps([root]), stderr=b'')
        with patch.object(worker.sys, 'platform', 'darwin'), patch.object(worker.subprocess, 'run', return_value=reply):
            physical = worker.physical_device('/dev/cu.fixture')
            self.assertEqual(physical['IORegistryEntryID'], 100); self.assertEqual(physical['endpoint_registry_id'], 101)
            with self.assertRaises(worker.ReadError): worker.physical_device('/dev/cu.wrong')
        with patch.object(worker.sys, 'platform', 'win32'), self.assertRaises(worker.ReadError) as caught: worker.physical_device('/dev/cu.fixture')
        self.assertEqual(caught.exception.code, 'unsupported_backend')

    def test_embedded_worker_invalid_input_has_no_checkout_dependency(self):
        for raw in ('{}', json.dumps(dict(job(), raw=[90, 1, 4])), 'x' * 17000):
            result = subprocess.run([sys.executable, '-I', '-u', '-c', Path(worker.__file__).read_text()], input=raw.encode(),
                                    capture_output=True, timeout=3, cwd=tempfile.gettempdir())
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['error']['code'], 'invalid_request')

    @unittest.skipUnless(os.name == 'posix', 'PTY transport requires POSIX')
    def test_real_subprocess_pty_fragmentation_and_termios_restoration(self):
        import pty
        import termios
        master, slave = pty.openpty(); path = os.ttyname(slave)
        original = termios.tcgetattr(slave)
        errors, packets = [], []
        def device():
            incoming = b''
            try:
                for reply in [FW, MODE, *(bytes.fromhex(x) for x in FRAMES), MODE]:
                    while len(incoming) < 5 or len(incoming) < 5 + int.from_bytes(incoming[3:5], 'big'):
                        if not select.select([master], [], [], 3)[0]: raise TimeoutError('PTY request did not arrive')
                        incoming += os.read(master, 4096)
                    length = 5 + int.from_bytes(incoming[3:5], 'big')
                    packets.append(incoming[:length]); incoming = incoming[length:]
                    for byte in reply: os.write(master, bytes((byte,)))
            except Exception as exc: errors.append(exc)
        thread = threading.Thread(target=device); thread.start()
        try:
            with tempfile.TemporaryDirectory() as directory:
                child = '''
fixture_request = json.loads(sys.argv[1])
fixture_physical = json.loads(sys.argv[2])
subprocess.run = lambda *args, **kwargs: subprocess.CompletedProcess([], 1, b'', b'')
result = capture(fixture_request, inventory=lambda p: fixture_physical,
    open_port=lambda p, d: PosixPort(sys.argv[3], d),
    retirement_factory=lambda p, d: Retirement(p, d, sys.argv[4]))
print(json.dumps(result))
'''
                source = Path(worker.__file__).read_text().rsplit("if __name__ == '__main__':", 1)[0] + child
                result = subprocess.run([sys.executable, '-I', '-u', '-c', source, json.dumps(job()), json.dumps(PHYSICAL), path, directory], capture_output=True, timeout=5)
                self.assertEqual(result.returncode, 0, result.stderr.decode()); self.assertEqual(len(json.loads(result.stdout)['controls']), 4)
            thread.join(timeout=3)
            self.assertFalse(thread.is_alive()); self.assertEqual(errors, []); self.assertEqual(len(packets), 7)
            restored = termios.tcgetattr(slave)
            # macOS marks canonical input pending after a raw-to-canonical transition.
            restored[3] &= ~getattr(termios, 'PENDIN', 0)
            original[3] &= ~getattr(termios, 'PENDIN', 0)
            self.assertEqual(restored, original)
        finally:
            os.close(master); os.close(slave)

class SerialBoundaryTests(unittest.TestCase):
    def test_observed_context_notification_between_replies_prevents_next_tx(self):
        for frame in (b'\x5a\x01\x03\x00\x02\x01\x00', b'\x5a\x7f\x00\x00\x00'):
            port = FakePort([FW + frame])
            with tempfile.TemporaryDirectory() as directory:
                with self.assertRaises(worker.ReadError):
                    worker.capture(job(), inventory=lambda p: PHYSICAL, open_port=lambda p, d: port,
                                   retirement_factory=lambda p, d: worker.Retirement(p, d, directory))
                self.assertEqual(len(port.writes), 1); self.assertTrue(port.closed)
                with self.assertRaises(worker.ReadError): worker.Retirement('/dev/cu.fixture', PHYSICAL, directory)

    def test_unrelated_async_between_replies_and_event_cap(self):
        frame = b'\x5a\x02\x0b\x00\x03\x00\x00\x00'
        for count, success in ((2, True), (65, False)):
            port = FakePort([FW + frame * count, MODE, *(bytes.fromhex(x) for x in FRAMES), MODE])
            with tempfile.TemporaryDirectory() as directory:
                call = lambda: worker.capture(job(), inventory=lambda p: PHYSICAL, open_port=lambda p, d: port,
                                   retirement_factory=lambda p, d: worker.Retirement(p, d, directory))
                if success: self.assertEqual(len(call()['controls']), 4)
                else:
                    with self.assertRaises(worker.ReadError) as caught: call()
                    self.assertEqual(caught.exception.code, 'protocol_error'); self.assertEqual(len(port.writes), 1)

    def test_busy_port_never_opens_or_sends_and_missing_port_reports_action(self):
        busy = subprocess.CompletedProcess([], 0, stdout=b'123\n', stderr=b'')
        with patch.object(worker.subprocess, 'run', return_value=busy), patch.object(worker.os, 'open') as opened:
            with self.assertRaises(worker.ReadError) as caught: worker.PosixPort('/dev/cu.fixture', PHYSICAL)
            self.assertEqual(caught.exception.code, 'port_busy'); opened.assert_not_called()
        free = subprocess.CompletedProcess([], 1, stdout=b'', stderr=b'')
        with patch.object(worker.subprocess, 'run', return_value=free), self.assertRaises(worker.ReadError) as caught:
            worker.PosixPort('/dev/cu.fixture-does-not-exist', PHYSICAL)
        self.assertEqual(caught.exception.code, 'port_unavailable')

class USBAncestryRegressionTests(unittest.TestCase):
    def test_config_and_interface_descriptions_cannot_replace_physical_usb_ancestor(self):
        endpoint = dict(IOCalloutDevice='/dev/cu.fixture', IODialinDevice='/dev/tty.fixture', IORegistryEntryID=101)
        interface = dict(IOObjectClass='IOUSBHostInterface', IORegistryEntryID=103,
                         **{'USB Product Name': 'Roto-Control', 'USB Vendor Name': 'Melbourne Instruments'},
                         IORegistryEntryChildren=[endpoint])
        config = dict(interface, IOObjectClass='IOUSBHostInterface', IORegistryEntryID=102,
                      IORegistryEntryChildren=[interface])
        root = dict(PHYSICAL, IOObjectClass='IOUSBHostDevice',
                    **{'USB Product Name': 'Roto_Control', 'USB Vendor Name': 'Melbourne Instruments'},
                    IORegistryEntryChildren=[config])
        reply = subprocess.CompletedProcess([], 0, stdout=plistlib.dumps([root]), stderr=b'')
        with patch.object(worker.sys, 'platform', 'darwin'), patch.object(worker.subprocess, 'run', return_value=reply):
            identity = worker.physical_device('/dev/cu.fixture')
        self.assertEqual(identity['IORegistryEntryID'], 100)
        self.assertEqual(identity['sessionID'], 200)
        self.assertEqual(identity['endpoint_registry_id'], 101)


class EmptyUSBInventoryTests(unittest.TestCase):
    def assert_inventory_refuses_serial_open(self, stdout, expected_code):
        inventory = subprocess.CompletedProcess([], 0, stdout=stdout, stderr=b'')
        port = FakePort()
        opened = Mock(return_value=port)
        retired = Mock()
        with patch.object(worker.sys, 'platform', 'darwin'), patch.object(worker.subprocess, 'run', return_value=inventory):
            with self.assertRaises(worker.ReadError) as caught:
                worker.capture(job(), open_port=opened, retirement_factory=retired)
        self.assertEqual(caught.exception.code, expected_code)
        opened.assert_not_called(); retired.assert_not_called()
        self.assertEqual(port.writes, [])
        return caught.exception

    def test_successful_empty_ioreg_output_reports_absent_device_without_open(self):
        error = self.assert_inventory_refuses_serial_open(b'', 'wrong_device')
        self.assertIn('absent', str(error))
        self.assertIn('/dev/cu.', str(error))

    def test_successful_nonempty_malformed_ioreg_output_remains_inventory_error_without_open(self):
        error = self.assert_inventory_refuses_serial_open(b'not a plist', 'usb_inventory')
        self.assertIn('Cannot verify Roto USB ancestry', str(error))
