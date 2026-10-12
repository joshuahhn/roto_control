"""Portable interpreter resolution through the actual Connect call."""
from pathlib import Path
import sys
import runpy
import tempfile
from types import SimpleNamespace as S
import unittest
from unittest.mock import Mock, patch

SOURCE = next(p for p in Path(__file__).parents if p.name == 'touchdesigner')
sys.path.insert(0, str(SOURCE / 'code/py/roto_python'))
import RotoPythonExt as runtime


class PythonInterpreterTests(unittest.TestCase):
    def connect(self, value, folder):
        ext = runtime.RotoPythonExt.__new__(runtime.RotoPythonExt)
        ext._restore_pending = False
        ext._host = S(enabled=True)
        ext.Disconnect = Mock()
        ext._publish = Mock()
        ext.ownerComp = S(par=S(Python=S(eval=lambda: value),
                               Device=S(eval=lambda: 'Roto-Control')),
                          op=lambda name: S(text='# embedded helper'))
        with patch.object(runtime, 'project', S(folder=str(folder)), create=True), \
                patch.object(runtime.subprocess, 'Popen') as spawn, \
                patch.object(runtime.os, 'set_blocking'):
            ext.Connect()
            return spawn.call_args.args[0]

    def test_bare_command_uses_path_without_project_prefix(self):
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / 'python3'
            executable.touch()
            with patch('shutil.which', return_value=str(executable)) as lookup:
                command = self.connect('python3', '/unrelated/project')
            lookup.assert_called_once_with('python3')
            self.assertEqual(command[0], str(executable))
            self.assertEqual(command[1:4], ['-u', '-c', '# embedded helper'])

    def test_relative_venv_keeps_entrypoint_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            actual = folder / 'python-real'
            actual.touch()
            executable = folder / '.venv/bin/python'
            executable.parent.mkdir(parents=True)
            executable.symlink_to(actual)
            self.assertEqual(self.connect('.venv/bin/python', folder)[0], str(executable))

    def test_absolute_interpreter_remains_supported(self):
        with tempfile.NamedTemporaryFile() as executable:
            self.assertEqual(self.connect(executable.name, '/unrelated')[0], executable.name)

    def test_home_relative_interpreter(self):
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / 'python'
            executable.touch()
            with patch.dict('os.environ', HOME=directory):
                self.assertEqual(self.connect('~/python', '/unrelated')[0], str(executable))

    def test_missing_command_reports_interpreter_error(self):
        with patch('shutil.which', return_value=None), \
                self.assertRaisesRegex(FileNotFoundError, 'Python interpreter'):
            self.connect('missing-python', '/unrelated')

    def test_empty_interpreter_is_rejected(self):
        with self.assertRaisesRegex(FileNotFoundError, 'Python interpreter'):
            self.connect('', '/unrelated')

    def test_command_is_a_single_executable_without_shell_arguments(self):
        with patch('shutil.which', return_value=None), \
                self.assertRaises(FileNotFoundError):
            self.connect('python3 -u', '/unrelated')


class ExportInterpreterTests(unittest.TestCase):
    def test_old_embedded_runtime_reports_upgrade_before_creating_export(self):
        exporter = runpy.run_path(str(SOURCE / 'scripts/export_component.py'))
        controller = S(ext=S(RotoPythonExt=S(_process=None)),
                       op=lambda name: S(module=S()),
                       par=S(Python=S(eval=lambda: sys.executable)),
                       parent=Mock())
        exporter['export'].__globals__['project'] = S(folder='/tmp')
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / 'portable.tox'
            with self.assertRaisesRegex(ValueError, 'Upgrade.*runtime.*export'):
                exporter['export'](controller, destination)
            controller.parent.assert_not_called()
            self.assertFalse(destination.exists())

    def test_invalid_interpreter_stops_export_before_clone(self):
        exporter = runpy.run_path(str(SOURCE / 'scripts/export_component.py'))
        controller = S(ext=S(RotoPythonExt=S(_process=None)),
                       op=lambda name: S(module=runtime),
                       par=S(Python=S(eval=lambda: 'missing-python')),
                       parent=Mock())
        exporter['export'].__globals__['project'] = S(folder='/tmp')
        with tempfile.TemporaryDirectory() as directory, \
                patch('shutil.which', return_value=None):
            destination = Path(directory) / 'portable.tox'
            with self.assertRaisesRegex(FileNotFoundError, 'Python interpreter'):
                exporter['export'](controller, destination)
            controller.parent.assert_not_called()
            self.assertFalse(destination.exists())


if __name__ == '__main__':
    unittest.main()
