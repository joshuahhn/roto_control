"""Runtime control paths work after removing the outer Control parameters."""
from types import SimpleNamespace
import unittest

import test_catalog_removal
from test_layouts import Par
from RotoPythonExt import RotoPythonExt


class InternalControlTests(unittest.TestCase):
    def fixture(self):
        ext = test_catalog_removal.CatalogRemovalTests().fixture()
        ext.ownerComp.par = SimpleNamespace()
        backing = Par(.5)
        old_op = ext.ownerComp.op
        ext.ownerComp.op = lambda name: SimpleNamespace(par=SimpleNamespace(Manualvalue=backing)) if name == 'base_state' else old_op(name)
        ext._mirror = RotoPythonExt._mirror.__get__(ext)
        return ext, backing

    def test_collection_registration_and_removal_without_outer_control_page(self):
        ext, backing = self.fixture()
        ext.BindControls([dict(kind='knob', slot=1, id='speed', minimum=0,
                              maximum=10, value=5, on_change=lambda event: None)], group_id='test')
        ext.SetValue(8, id='speed')
        self.assertEqual(ext.GetValue('speed'), 8)
        self.assertEqual(backing.eval(), .8)
        ext.RemoveControl('speed')
        self.assertEqual(ext.GetControlStates(), [])

    def test_internal_mirror_callback_does_not_write_target_twice(self):
        ext, backing = self.fixture()
        ext._mirror(.75)
        backing.name = 'Manualvalue'
        ext.SetValue = lambda value: self.fail('Mirror callback must not dispatch')
        ext.onParValueChange(backing, .5)
        self.assertEqual(backing.eval(), .75)
        self.assertIsNone(ext._mirror_expected)


if __name__ == '__main__':
    unittest.main()
