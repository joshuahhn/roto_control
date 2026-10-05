"""Behavior checks at the complete MIDI-message / parameter interface."""

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parent / "code/py/roto_python"))
from protocol import Host, digest, sysex


class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.sent, self.assigned = [], []
        self.host = Host(self.sent.append, self.assigned.append)

    def ready(self):
        self.host.start()
        self.host.receive(sysex(10, 2))
        self.host.receive(sysex(10, 12))
        self.host.receive(sysex(11, 1, (0,)))

    def map(self):
        self.ready()
        self.host.receive(sysex(11, 11, (0, 0, *digest("Value", 6), 0, 0, 0)))

    def test_compact_numeric_display_preserves_value(self):
        self.map()
        value = 0.123456789
        self.host.parameter_changed(value)
        self.assertEqual(self.host.value, round(value * 16383) / 16383)
        display = self.sent[-1]
        self.assertEqual(bytes(display[9:-1]).rstrip(b"\0"), b"0.123")
        from protocol import format_number
        self.assertEqual(format_number(1.2348), "1.235")
        self.assertEqual(format_number(7.0), "7")
        self.assertEqual(format_number(-0.0001), "0")

    def test_handshake_and_parameter_offer_bytes(self):
        self.ready()
        self.assertEqual(self.sent[:2], [(240, 0, 34, 3, 2, 10, 1, 247),
                                       (240, 0, 34, 3, 2, 10, 3, 1, 247)])
        self.assertFalse(self.host.offer_parameter())
        self.host.receive(sysex(11, 9, (1,)))
        self.assertTrue(self.host.offer_parameter())
        self.assertEqual(self.sent[-1][5:9], (11, 10, 0, 0))
        self.assertEqual(len(self.sent[-1]), 34)

    def test_value_edit_offers_once_per_learn_session(self):
        self.ready()
        self.host.parameter_changed(0.2)
        before = len(self.sent)
        self.host.receive(sysex(11, 9, (1,)))
        self.host.parameter_changed(0.3)
        self.host.parameter_changed(0.4)
        self.assertEqual(len(self.sent), before + 1)
        self.assertEqual(self.sent[-1][5:7], (11, 10))
        self.host.receive(sysex(11, 9, (1,)))  # Duplicate event is not a new session.
        self.host.parameter_changed(0.5)
        self.assertEqual(len(self.sent), before + 1)
        self.host.receive(sysex(11, 9, (0,)))
        self.host.parameter_changed(0.6)
        self.assertEqual(len(self.sent), before + 1)
        self.host.receive(sysex(11, 9, (1,)))
        self.host.parameter_changed(0.7)
        self.assertEqual(len(self.sent), before + 2)

    def test_hardware_input_does_not_offer_during_learn(self):
        self.map()
        self.host.receive(sysex(11, 9, (1,)))
        before = len(self.sent)
        self.host.receive((191, 12, 32))
        self.host.receive((191, 44, 0))
        self.host.parameter_changed(self.assigned[-1])
        self.assertEqual(len(self.sent), before)
        self.host.parameter_changed(0.7)
        self.assertEqual(self.sent[before][5:7], (11, 10))

    def test_pulse_offer_counts_but_remains_repeatable(self):
        self.ready()
        self.host.receive(sysex(11, 9, (1,)))
        self.assertTrue(self.host.offer_parameter())
        before = len(self.sent)
        self.host.parameter_changed(0.7)
        self.assertEqual(len(self.sent), before)
        self.assertTrue(self.host.offer_parameter())
        self.assertEqual(len(self.sent), before + 1)

    def test_mapping_required_before_writing_parameter(self):
        self.ready()
        self.host.receive((191, 12, 64))
        self.host.receive((191, 44, 0))
        self.assertEqual(self.assigned, [])
        self.host.receive(sysex(11, 11, (0, 0, *digest("Value", 6), 0, 1, 0)))
        self.assertFalse(self.host.mapped)

    def test_connected_advertises_track_context_before_plugin(self):
        self.host.start()
        self.host.receive(sysex(10, 12))
        commands = [(message[5], message[6]) for message in self.sent]
        # Official _return_tracks + selected-track callback startup sequence.
        self.assertEqual(commands[1:], [(10, 4), (10, 5), (10, 7), (10, 8), (12, 4)])

    def test_mapping_returns_parameter_details_before_motor_feedback(self):
        self.map()
        self.assertEqual(self.sent[-4][5:7], (11, 10))

    def test_touch_displays_value_without_moving_motor(self):
        self.map()
        before = len(self.sent)
        self.host.receive((191, 52, 127))
        self.assertEqual(len(self.sent), before + 1)
        self.assertEqual(self.sent[-1][5:7], (10, 24))

    def test_input_display_is_coalesced_without_motor_echo(self):
        self.map()
        before = len(self.sent)
        self.host.receive((191, 12, 32))
        self.host.receive((191, 44, 0))
        self.host.parameter_changed(self.assigned[-1])
        self.host.flush_display(1.0)
        self.assertEqual(len(self.sent), before + 1)
        self.assertEqual(self.sent[-1][5:7], (10, 24))
        self.host.receive((191, 12, 64))
        self.host.receive((191, 44, 0))
        self.host.parameter_changed(self.assigned[-1])
        self.host.flush_display(1.01)
        self.assertEqual(len(self.sent), before + 1)
        self.host.flush_display(1.1)
        self.assertEqual(len(self.sent), before + 2)

    def test_14bit_input_requires_both_halves_and_suppresses_echo(self):
        self.map()
        before = len(self.sent)
        self.host.receive((191, 44, 27))
        self.assertEqual(self.assigned, [])
        self.host.receive((191, 12, 80))
        value = (80 * 128 + 27) / 16383
        self.assertEqual(self.assigned, [value])
        self.host.parameter_changed(value)
        self.assertEqual(len(self.sent), before)
        self.host.parameter_changed(0.25)
        self.assertEqual(self.sent[-3:-1], [(191, 12, 32), (191, 44, 0)])

    def test_touch_defers_motor_until_release(self):
        self.map()
        self.host.receive((191, 52, 127))
        before = len(self.sent)
        self.host.parameter_changed(0.75)
        self.assertEqual(len(self.sent), before)
        self.host.receive((191, 52, 0))
        self.assertEqual(self.sent[-3:-1], [(191, 12, 95), (191, 44, 127)])

    def test_bad_sysex_and_reconnect_do_not_keep_mapping(self):
        self.map()
        self.host.receive((240, 0, 34, 3, 2, 10, 2, 128, 247))
        self.host.receive((240, 0, 34, 3, 2, 10, 2))
        self.assertEqual(self.host.rejected, 2)
        self.host.stop()
        self.host.parameter_changed(0.2)
        self.assertFalse(self.host.mapped)
        self.assertFalse(self.host.connected)

    def test_physical_gesture_supersedes_deferred_motor_value(self):
        self.map()
        self.host.receive((191, 52, 127))
        self.host.parameter_changed(0.75)
        before = len(self.sent)
        self.host.receive((191, 12, 32))
        self.host.receive((191, 44, 0))
        self.host.parameter_changed(self.assigned[-1])
        self.host.receive((191, 52, 0))
        self.assertEqual(len(self.sent), before)


if __name__ == "__main__":
    unittest.main()
