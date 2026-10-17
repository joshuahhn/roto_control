import tests
import contextlib
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import verify_named_commands as check


class MigrationCheckTests(unittest.TestCase):
    def rejected(self, source, category, line=1):
        result = check.scan_source(source, 'code/example.py')
        self.assertTrue(any(x['category'] == category and x['line'] == line and x['path'] == 'code/example.py'
                            for x in result['findings']), result)
        return result

    def test_old_definitions_imports_qualified_and_bound_references(self):
        for source, category in [
            ('def sysex(group, command): pass', 'legacy_definitions'),
            ('from protocol import sysex as encode', 'legacy_imports'),
            ('import package.sysex as encode', 'legacy_imports'),
            ('packet = proto.sysex(10, 1)', 'legacy_calls'),
            ("packet = comp.op('protocol').module.sysex(10, 1)", 'legacy_calls'),
            ('encode = p.sysex', 'legacy_references'),
            ('request = host._command', 'legacy_references'),
            ('request = runtime.command', 'legacy_references'),
            ('class MixRuntime:\n    def command(self, group, command): pass', 'legacy_definitions'),
            ("getattr(protocol, 'sysex')", 'legacy_references'),
            ('from serial_read_process import COMMANDS as requests', 'legacy_imports'),
            ('request = worker._packet', 'legacy_references'),
        ]:
            with self.subTest(source=source):
                self.rejected(source, category, 2 if source.startswith('class ') else 1)

    def test_raw_dispatch_follows_renamed_identity_slots(self):
        for source, line in [
            ('if message[5] == 12: pass', 1),
            ('if message[6] in (1, 2): pass', 1),
            ('a, b = incoming[5:7]\nif a == 12: pass', 2),
            ('renamed = incoming[6]\nother = renamed\nif other in (1, 2): pass', 3),
            ('left, right = incoming[5], incoming[6]\nif (left, right) == (11, 1): pass', 2),
            ('if tuple(event[:5]) == HEADER and event[6] == 1: pass', 1),
            ('if message[5:7] == [10, 24]: pass', 1),
            ('if packet[5:9] == (12, 4, 0, 1): pass', 1),
            ("if frame[1:3] != b'\\x02\\x0b': pass", 1),
            ('if tuple(event[:7]) == (*HEADER, 11, 1): pass', 1),
            ('if raw.startswith(bytes((240, 0, 34, 3, 2, 11, 1))): pass', 1),
            ('command = SysExCommand((10, 1)).message()', 1),
            ('command = SysExCommand((SysExGroup.GENERAL, 1)).message()', 1),
            ('from protocol import SysExCommand as Command\nCommand((10, 1)).message()', 2),
            ('Command = p.SysExCommand\nAlias = Command\nAlias((SysExGroup.MIX, 9)).message()', 3),
            ('Command = p.SysExCommand\nCommand(dynamic_selector).message()', 2),
            ('packet = SerialGet((1, 2, 4)).packet()', 1),
            ('packet = worker.SerialGet((1, 2, 4)).packet()', 1),
            ('from serial_read_process import SerialGet as Get\nGet((1, 2, 4)).packet()', 2),
            ('Get = worker.SerialGet\nAlias = Get\nAlias((1, 2, 4)).packet()', 3),
        ]:
            with self.subTest(source=source): self.rejected(source, 'raw_dispatch', line)

    def test_raw_fixture_becomes_a_failure_only_at_output_or_encoder_boundary(self):
        fixture = 'expected = (240, 0, 34, 3, 2, 10, 1, 247)\n'
        self.assertEqual(check.scan_source(fixture + 'assert actual == expected')['findings'], [])
        self.rejected(fixture + 'queued = expected\nself._send(queued)', 'raw_send', 3)
        self.rejected('self._send((*HEADER, 12, 9, 247), mix=True)', 'raw_send')
        self.rejected('def encode(group, code):\n    return (*HEADER, group, code, 247)', 'raw_send', 2)

    def test_serial_selectors_follow_session_and_bound_get_aliases(self):
        for source, line in [
            ("session.get('mode')", 1),
            ("from serial_read_process import ReadSession as Reader\ns = Reader(port, retired)\ns.get('firmware')", 3),
            ("s = worker.ReadSession(port, retired)\nalias = s\nalias.get(c['kind'])", 3),
            ("s = worker.ReadSession(port, retired)\nget = s.get\nget(selector)", 3),
        ]:
            with self.subTest(source=source): self.rejected(source, 'serial_selectors', line)
        self.assertEqual(check.scan_source('''from serial_read_process import SerialGet as Get
session = ReadSession(port, retired)
selected = Get.PLUGIN_KNOB_CONFIG if kind == 'knob' else Get.PLUGIN_SWITCH_CONFIG
alias = session
read = alias.get
read(selected)
settings.get('mode')
''')['findings'], [])

    def test_literal_executable_aliases_and_dat_sources_are_scanned(self):
        for source in [
            'exec("proto.sysex(10, 1)")',
            'body = "proto." + "sysex(10, 1)"\nexec(body)',
            'BODY = "proto.sysex(10, 1)"\ndef install():\n    exec(BODY)',
            'body = dedent("    proto.sysex(10, 1)")\ncompile(body, "<native>", "exec")',
            'run("proto.sysex(10, 1)")',
            'dat.text = "if message[5] == 12: pass"',
        ]:
            with self.subTest(source=source):
                result = check.scan_source(source, 'build/example.py')
                self.assertEqual(len(result['snippets']), 1, result)
                self.assertTrue(result['findings'], result)
                self.assertIn(':snippet@', result['findings'][0]['path'])
                self.assertEqual(result['findings'][0]['line'], 1)
        result = check.scan_source('exec("this is ! invalid")')
        self.assertEqual(result['findings'][0]['category'], 'syntax')
        result = check.scan_source('exec(make_source())')
        self.assertEqual(len(result['dynamic']), 1)
        self.assertEqual(result['findings'], [])

    def test_named_apis_and_non_executable_fixture_strings_are_valid(self):
        result = check.scan_source('''from protocol import SysExCommand, SysExGroup
packet = SysExCommand.DAW_STARTED.message()
self._send(packet)
self.e._send(SysExCommand.NUM_SENDS.message((1,)), mix=True)
identity = SysExCommand.identify(message)
if identity is SysExCommand.SET_PLUGIN_MODE: pass
if message[5] == SysExGroup.MIX: pass
if data[0] == 12 or cc == 52: pass
expected = (240, 0, 34, 3, 2, 10, 1, 247)
assert actual == expected
scan_source("from protocol import sysex as encode")
label.par.text = "Hardware settings"
''')
        self.assertEqual(result['findings'], [])
        self.assertEqual(result['snippets'], [])

    def test_cli_exception_is_exact_and_never_exempts_its_file(self):
        path = 'diagnostics/runtime/layout_protocol_probe.py'
        source = "class Probe:\n    def command(self, line): pass\nprobe.command(line.decode('ascii'))\n"
        self.assertEqual(check.scan_source(source, path)['findings'], [])
        self.assertEqual(len(check.scan_source(source, path)['cli_exclusions']), 2)
        self.assertTrue(check.scan_source(source + 'other.command(12, 9)', path)['findings'])
        self.assertTrue(check.scan_source(source, 'other.py')['findings'])

    def test_negative_boundary_and_corrupt_dat_exclusions_are_exact(self):
        path = 'tests/test_named_commands.py'
        function = 'test_serial_named_requests_keep_their_wire_and_response_lengths'
        source = "def " + function + "(self):\n    with self.assertRaisesRegex(TypeError, 'SerialGet'):\n        session.get(selector)\n"
        result = check.scan_source(source, path)
        self.assertEqual(result['findings'], [])
        self.assertEqual(len(result['text_fixtures']), 1)
        self.assertTrue(check.scan_source(source.replace('TypeError', 'ValueError'), path)['findings'])
        self.assertTrue(check.scan_source(source, 'tests/other.py')['findings'])
        source = "def test_required_runtime_and_helper_source_mismatch_stops_packaging(self):\n    dat.text = 'wrong runtime'\n    other.text = 'proto.sysex(10, 1)'\n"
        result = check.scan_source(source, 'tests/test_owned_inspector.py')
        self.assertEqual(len(result['text_fixtures']), 1)
        self.assertTrue(result['findings'])

    def test_cli_reports_nonzero_with_locations_and_zero_for_named_source(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            for name in check.ROOTS: (root/name).mkdir()
            path = root/'code/example.py'
            path.write_text('from protocol import sysex as encode\n')
            output = io.StringIO()
            with contextlib.redirect_stdout(output): self.assertEqual(check.main(['--root', str(root)]), 1)
            self.assertIn('code/example.py:1: legacy_imports', output.getvalue())
            path.write_text('packet = SysExCommand.DAW_STARTED.message()\n')
            report = root/'report.json'
            with contextlib.redirect_stdout(io.StringIO()): self.assertEqual(check.main(['--root', str(root), '--json', str(report)]), 0)
            value = json.loads(report.read_text())
            self.assertTrue(value['zero']); self.assertEqual(value['files'], 1)
            self.assertTrue(all(total == 0 for total in value['categories'].values()))
            self.assertEqual(value['roots'], list(check.ROOTS))
