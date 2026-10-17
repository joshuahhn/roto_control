import tests
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace as S
import unittest
from unittest.mock import Mock, patch
import protocol
import upgrade_named_commands as upgrade

SOURCE = Path(__file__).resolve().parents[1]


class Dat:
    def __init__(self, name, module=None):
        self.path = '/controller/' + name
        self.OPType = 'textDAT'; self.text = 'before ' + name; self.module = module
        self.par = S(syncfile=True, loadonstart=True, file='external.py', language='python')


class UpgradeTests(unittest.TestCase):
    def fixture(self, directory):
        events = []; windows = []
        for index in range(4):
            windows.append(S(path='/view/window' + str(index), isOpen=index in (0, 3),
                             par=S(winopen=S(pulse=Mock(side_effect=lambda: events.append('open'))))))
        views = [S(op=lambda name, i=i: windows[i*2 + (name == 'window_editor')]) for i in range(2)]
        lifecycle = S(validate=Mock(return_value=(None, object(), views)),
                      quiesce=Mock(side_effect=lambda c: events.append('quiesce')),
                      initialize=Mock(side_effect=lambda c: events.append('inspector')))
        marker = {'build': 'previous full build'}
        wrapper = S(op=lambda name: S(module=lifecycle), storage={'owned_inspector_sources': marker, 'user': [1, 2]})
        wrapper.unstore = lambda key: wrapper.storage.pop(key, None)
        modules = {name: S(SysExCommand=protocol.SysExCommand) for name in upgrade.RUNTIME_NAMES}
        modules['protocol'] = protocol
        modules['collection_protocol'] = S(SysExCommand=protocol.SysExCommand, Host=protocol.Host,
            LearnParameter=protocol.LearnParameter, learn_parameter_message=protocol.learn_parameter_message)
        modules['free_learn'] = S(SysExCommand=protocol.SysExCommand,
            LearnParameter=protocol.LearnParameter, learn_parameter_message=protocol.learn_parameter_message)
        dats = {name: Dat(name, modules.get(name)) for name in upgrade.SOURCE_PATHS}
        controller = S(path='/controller', op=lambda name: wrapper if name == 'inspector' else dats.get(name))
        extension = S(ownerComp=controller, _process=None, _hardware_config=None, _layouts=None,
                      _cancel_inspector_refresh=Mock(), _publish_inspector=Mock())
        controller.ext = S(RotoPythonExt=extension)
        controller.initializeExtensions = Mock(side_effect=lambda index: events.append('extensions'))
        controller.Applybinding = Mock(side_effect=lambda: events.append('binding'))
        def save(path):
            self.assertTrue(all(dat.text == 'before ' + name for name, dat in dats.items()))
            self.assertEqual(events, [])
            Path(path).write_bytes(b'recovery of original component'); events.append('recovery')
        controller.save = Mock(side_effect=save)
        return controller, dats, wrapper, lifecycle, windows, events

    def test_preflight_rejects_wrong_project_owner_transports_and_missing_local_nodes(self):
        for failure in ('project', 'owner', 'midi', 'serial', 'source', 'inspector'):
            with self.subTest(failure=failure), TemporaryDirectory() as directory:
                controller, dats, wrapper, lifecycle, windows, events = self.fixture(directory)
                expected = Path(directory)/'expected.toe'
                if failure == 'owner': controller.ext.RotoPythonExt.ownerComp = object()
                if failure == 'midi': controller.ext.RotoPythonExt._process = object()
                if failure == 'serial': controller.ext.RotoPythonExt._hardware_config = S(active=True)
                if failure == 'source': dats.pop('protocol')
                if failure == 'inspector': lifecycle.validate.side_effect = ValueError('Foreign Inspector owner')
                with patch.object(upgrade, 'project', S(folder=directory, name='expected'), create=True):
                    with self.assertRaises(ValueError):
                        upgrade.install(controller, SOURCE,
                            expected_project=expected if failure != 'project' else expected.with_name('other.toe'),
                            recovery_path=Path(directory)/'new.tox')
                controller.save.assert_not_called(); controller.initializeExtensions.assert_not_called()
                self.assertEqual(events, [])
                self.assertTrue(all(dat.text == 'before ' + name for name, dat in dats.items()))

    def test_new_recovery_precedes_source_mutation_and_original_windows_and_storage_survive(self):
        with TemporaryDirectory() as directory:
            controller, dats, wrapper, lifecycle, windows, events = self.fixture(directory)
            identities = {name: id(dat) for name, dat in dats.items()}
            with patch.object(upgrade, 'project', S(folder=directory, name='expected'), create=True):
                result = upgrade.install(controller, SOURCE, expected_project=Path(directory)/'expected.toe',
                                         recovery_path=Path(directory)/'new.tox')
            self.assertEqual(events, ['recovery', 'quiesce', 'extensions', 'binding', 'inspector', 'open', 'open'])
            self.assertEqual(result['restored_windows'], [windows[0].path, windows[3].path])
            self.assertEqual(result['module_order'], list(upgrade.RUNTIME_NAMES))
            self.assertEqual(len(result['hashes']), 9)
            self.assertEqual(wrapper.storage, {'user': [1, 2]})
            self.assertEqual(identities, {name: id(dat) for name, dat in dats.items()})
            for name, dat in dats.items():
                self.assertEqual(dat.text, (SOURCE/upgrade.SOURCE_PATHS[name]).read_text())
                self.assertEqual(dat.par.file, '')
                self.assertFalse(dat.par.syncfile or dat.par.loadonstart)
            controller.Applybinding.assert_called_once_with()
            self.assertEqual(lifecycle.validate.call_count, 2)

    def test_existing_or_failed_recovery_stops_before_quiescing_or_writing_sources(self):
        for failure in ('existing', 'empty'):
            with self.subTest(failure=failure), TemporaryDirectory() as directory:
                controller, dats, wrapper, lifecycle, windows, events = self.fixture(directory)
                recovery = Path(directory)/'new.tox'
                if failure == 'existing': recovery.write_bytes(b'older recovery')
                else: controller.save.side_effect = lambda path: Path(path).write_bytes(b'')
                with patch.object(upgrade, 'project', S(folder=directory, name='expected'), create=True):
                    with self.assertRaises((ValueError, RuntimeError)):
                        upgrade.install(controller, SOURCE, expected_project=Path(directory)/'expected.toe', recovery_path=recovery)
                lifecycle.quiesce.assert_not_called(); controller.initializeExtensions.assert_not_called()
                self.assertTrue(all(dat.text == 'before ' + name for name, dat in dats.items()))

    def test_stale_import_or_final_validation_failure_preserves_recovery_and_build_marker(self):
        for failure in ('enum', 'learn', 'validation'):
            with self.subTest(failure=failure), TemporaryDirectory() as directory:
                controller, dats, wrapper, lifecycle, windows, events = self.fixture(directory)
                if failure == 'enum': dats['midi_queue'].module.SysExCommand = object()
                if failure == 'learn': dats['free_learn'].module.learn_parameter_message = object()
                if failure == 'validation': lifecycle.validate.side_effect = [(None, object(), [S(op=lambda name: windows[0])]), ValueError('Final validation')]
                recovery = Path(directory)/'new.tox'
                with patch.object(upgrade, 'project', S(folder=directory, name='expected'), create=True):
                    with self.assertRaises((ValueError, RuntimeError)):
                        upgrade.install(controller, SOURCE, expected_project=Path(directory)/'expected.toe', recovery_path=recovery)
                self.assertTrue(recovery.read_bytes())
                self.assertEqual(wrapper.storage['owned_inspector_sources'], {'build': 'previous full build'})
