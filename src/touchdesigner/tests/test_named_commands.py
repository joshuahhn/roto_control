import tests
import json
from pathlib import Path
import unittest
from unittest.mock import Mock
from protocol import Host, SysExCommand, SysExGroup
from midi_queue import business_output
from mix_runtime import MixRuntime
from text_comp_follow import CompFollower
import serial_read_process as worker
import test_mix


class NamedCommandTests(unittest.TestCase):
    def test_encoding_keeps_exact_integer_wire_bytes_and_payload_validation(self):
        self.assertEqual(SysExCommand.DAW_STARTED.message(), (240, 0, 34, 3, 2, 10, 1, 247))
        packet = SysExCommand.PARAM_VALUES.message(iter((0, 127)))
        self.assertEqual(packet, (240, 0, 34, 3, 2, 10, 24, 0, 127, 247))
        self.assertTrue(all(type(value) is int for value in packet))
        for data in ((128,), (-1,), (True,), (1.0,)):
            with self.subTest(data=data), self.assertRaisesRegex(ValueError, 'seven-bit integers'):
                SysExCommand.DAW_STARTED.message(data)
        for selector in ((10, 1), 10, 'DAW_STARTED', object()):
            with self.subTest(selector=selector), self.assertRaises((AttributeError, TypeError)):
                SysExCommand.message(selector)

    def test_identify_preserves_identity_equality_without_framing_validation(self):
        for frame in ((9, 9, 9, 9, 9, 10, 1), (240, 0, 34, 3, 2, 10, True, 0),
                      (240, 0, 34, 3, 2, 10, 1.0, 128, 247)):
            self.assertIs(SysExCommand.identify(frame), SysExCommand.DAW_STARTED)
        for frame in ((), (240, 0, 34, 3, 2, 10), (240, 0, 34, 3, 2, [], 1),
                      (240, 0, 34, 3, 2, 10, []), (240, 0, 34, 3, 2, 10, {}),
                      (240, 0, 34, 3, 2, 12, 127, 247)):
            self.assertIsNone(SysExCommand.identify(frame))
        self.assertEqual(SysExGroup.MIX, 12)

    def test_serial_named_requests_keep_their_wire_and_response_lengths(self):
        for command, payload, expected, size in (
            (worker.SerialGet.FW_VERSION, b'', '5a01010000', 12),
            (worker.SerialGet.MODE, b'', '5a01020000', 4),
            (worker.SerialGet.PLUGIN_KNOB_CONFIG, bytes(range(8)) + b'\x07', '5a03090009000102030405060707', 250),
            (worker.SerialGet.PLUGIN_SWITCH_CONFIG, bytes(range(8)) + b'\x07', '5a030a0009000102030405060707', 247),
        ):
            self.assertEqual(command.packet(payload), bytes.fromhex(expected))
            self.assertEqual(command.response_size, size)
        transport, retirement = Mock(), Mock()
        session = worker.ReadSession(transport, retirement)
        for selector in ('firmware', (1, 1, 12), 1, object()):
            with self.subTest(selector=selector), self.assertRaisesRegex(TypeError, 'SerialGet'):
                session.get(selector)
        transport.write.assert_not_called(); retirement.arm.assert_not_called()

    def test_unknown_mix_group_still_resets_the_plugin_host(self):
        host = Host(lambda packet: None, lambda value: None)
        host.connected = host.plugin = host.mapped = host.learning = True
        host.receive((240, 0, 34, 3, 2, 12, 127, 247))
        self.assertTrue(host.connected)
        self.assertFalse(host.plugin or host.mapped or host.learning)

    def test_pinned_loose_filters_and_mix_ownership_are_unchanged(self):
        baseline = json.loads((Path(__file__).parent/'fixtures/named_commands_loose.json').read_text())
        for name, case in baseline['cases'].items():
            with self.subTest(case=name):
                packet = tuple(case['frame'])
                actual = {}
                for function in (business_output, CompFollower.context_output, MixRuntime.feedback_output):
                    actual[function.__qualname__] = function(packet)
                for active in (False, True):
                    extension, mix, *_ = test_mix.MixTests().fixture()
                    mix.active = active; mix.view = ('all', (0, 0, 0, 0)); before = mix.epoch
                    answer = mix.receive(packet, now=1)
                    actual['receive_' + str(active)] = dict(answer=answer, active=mix.active,
                        returning=mix.returning, view=mix.view, family=mix.family,
                        epoch_delta=mix.epoch-before, pending=extension._pending.decode())
                self.assertEqual(json.loads(json.dumps(actual)), case['expected'])
