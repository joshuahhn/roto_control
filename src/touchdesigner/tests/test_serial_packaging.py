"""Serial source installation and export sanitation at native TD boundaries."""
import tests
import copy
from pathlib import Path
from types import SimpleNamespace as S
import unittest
from unittest.mock import Mock
import upgrade_serial
import build_inspector
import export_component
import cleanup_network
from test_owned_inspector import Node, isolation_boundary, SOURCE


class SerialPackagingTests(unittest.TestCase):
    def fixture(self):
        controller = Node('controller')
        controller.storage = dict(mapping=['keep'], setting='/outside')
        layout = S(capture=Mock())
        follower = S(refresh_links=Mock())
        controller.ext.RotoPythonExt = S(_process=None, _layouts=layout, _follow=follower)
        controller.create = lambda kind, name: Node(name, controller, kind)
        for name in ('RotoPythonExt', 'layouts'):
            node = Node(name, controller, 'textDAT'); node.nodeX, node.nodeY = 123, -456
        controller.Applybinding = Mock(return_value=True)
        def initialized(index):
            for name in ('hardware_config', 'RotoPythonExt', 'layouts'):
                self.assertEqual(controller.op(name).text, (SOURCE/'code/py/roto_python'/f'{name}.py').read_text())
            self.assertEqual(controller.op('serial_read_process').text, (SOURCE/'scripts/serial_read_process.py').read_text())
        controller.initializeExtensions = Mock(side_effect=initialized)
        return controller

    def test_upgrade_embeds_exact_source_before_reinit_preserves_settings_and_existing_positions(self):
        controller = self.fixture(); before = copy.deepcopy(controller.storage)
        upgrade_serial.install(controller, SOURCE)
        self.assertEqual(controller.storage, before)
        self.assertEqual((controller.op('RotoPythonExt').nodeX, controller.op('RotoPythonExt').nodeY), (123, -456))
        self.assertEqual((controller.op('hardware_config').nodeX, controller.op('hardware_config').nodeY), (-800, -170))
        self.assertEqual((controller.op('serial_read_process').nodeX, controller.op('serial_read_process').nodeY), (-800, -340))
        controller.ext.RotoPythonExt._layouts.capture.assert_called_once_with(force=True)
        controller.initializeExtensions.assert_called_once_with(0); controller.Applybinding.assert_called_once()
        self.assertEqual(set(controller.storage), {'mapping', 'setting'})

    def test_upgrade_rejects_active_serial_or_midi_before_mutating(self):
        for target in ('serial', 'midi'):
            controller = self.fixture(); before = controller.op('RotoPythonExt').text
            if target == 'serial': controller.ext.RotoPythonExt._hardware_config = S(active=True)
            else: controller.ext.RotoPythonExt._process = object()
            with self.assertRaises(ValueError): upgrade_serial.install(controller, SOURCE)
            self.assertEqual(controller.op('RotoPythonExt').text, before)
            controller.initializeExtensions.assert_not_called()

    def test_source_checker_rejects_both_serial_module_and_worker_mismatch(self):
        for name in ('hardware_config', 'serial_read_process'):
            controller, _, required, internal = isolation_boundary()
            build_inspector._verify_runtime_sources(controller, SOURCE)
            controller.op(name).text = 'stale source'
            with self.assertRaises(ValueError): build_inspector._verify_runtime_sources(controller, SOURCE)

    def test_export_rejects_active_serial_before_copy_and_registration_clears_observation(self):
        controller = self.fixture(); extension = controller.ext.RotoPythonExt
        extension._hardware_config = S(active=True)
        controller.parent = Mock()
        with self.assertRaisesRegex(ValueError, 'Serial'): export_component.export(controller, '/tmp/unused-serial-export.tox')
        controller.parent.assert_not_called()
        Node('registration', controller, 'textDAT')
        export_component.reset_registration(controller)
        self.assertIsNone(extension._hardware_config)

    def test_cleanup_classifies_serial_sources_and_embedded_guide(self):
        root_names = [name for title, names, columns in cleanup_network.GROUPS[''] for name in names]
        self.assertIn('hardware_config', root_names); self.assertIn('serial_read_process', root_names)
        guides = [name for title, names, columns in cleanup_network.GROUPS['docs'] for name in names]
        self.assertIn('fn_serial_md', guides)

class UpgradeGuardTests(unittest.TestCase):
    def test_all_source_replacing_upgrades_reject_live_serial_before_mutation(self):
        import upgrade_controls
        import upgrade_layouts
        import upgrade_mix
        import upgrade_network
        for name, function, nested in (('controls', upgrade_controls.upgrade, True), ('layouts', upgrade_layouts.upgrade, False),
                                      ('mix', upgrade_mix.install, False), ('network', upgrade_network.upgrade, True)):
            controller = Mock()
            controller.ext.RotoPythonExt = S(_process=None, _hardware_config=S(active=True))
            parent = S(op=lambda name: controller)
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'Serial'):
                function(parent if nested else controller, SOURCE)
            controller.create.assert_not_called(); controller.appendCustomPage.assert_not_called()
