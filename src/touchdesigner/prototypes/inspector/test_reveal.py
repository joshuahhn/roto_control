"""Reveal navigates from Inspector windows without changing controller Follow."""
from types import SimpleNamespace
from unittest.mock import patch
import unittest
import live_model


class PaneList(list):
    def __init__(self, panes, current):
        super().__init__(panes)
        self.current = current


class RevealTests(unittest.TestCase):
    def setUp(self):
        self.follow = True
        self.controller = SimpleNamespace(GetCompContext=lambda: {'enabled': self.follow})
        self.selected = SimpleNamespace(selected=True)
        self.parent = SimpleNamespace(path='/', selectedChildren=(self.selected,))
        self.target = SimpleNamespace(valid=True, path='/effect',
                                      par=SimpleNamespace(Amount=object()),
                                      selectedChildren=(), parent=lambda: self.parent,
                                      nodeX=250, nodeY=0, nodeWidth=160, nodeHeight=130)
        self.homes = []
        self.pane = SimpleNamespace(open=True, type=SimpleNamespace(name='NETWORKEDITOR'),
                                    owner='/old', zoom=.1, home=self.home)
        self.ui = SimpleNamespace(panes=PaneList([self.pane], self.pane))
        self.adapter = live_model.TDControllerAdapter(SimpleNamespace(par=SimpleNamespace(
            Controller=SimpleNamespace(eval=lambda: self.controller))))
        self.info = dict(comp='/effect', parameter='Amount')

    def home(self, **kwargs):
        self.homes.append(kwargs)
        self.pane.zoom=.05

    def reveal(self):
        with patch.object(live_model, 'op', return_value=self.target, create=True), patch.object(live_model, 'ui', self.ui, create=True):
            return self.adapter.Reveal(self.info)

    def test_follow_on_navigates_and_clears_destination_selection(self):
        self.assertEqual(self.reveal(), '/effect')
        self.assertIs(self.pane.owner, self.parent)
        self.assertFalse(self.selected.selected)
        self.assertTrue(self.follow)
        self.assertEqual(self.homes, [])
        self.assertEqual(self.pane.zoom, 1.)
        self.assertEqual((self.pane.x,self.pane.y), (330.,65.))

    def test_popup_current_pane_falls_back_to_existing_network_editor(self):
        self.ui.panes.current = SimpleNamespace(open=True, type=SimpleNamespace(name='PANEL'))
        self.assertEqual(self.reveal(), '/effect')
        self.assertIs(self.pane.owner, self.parent)

    def test_no_editor_or_deleted_target_does_not_navigate(self):
        self.ui.panes = PaneList([], None)
        with self.assertRaisesRegex(ValueError, 'Network Editor'):
            self.reveal()
        self.ui.panes = PaneList([self.pane], self.pane)
        self.target.valid = False
        with self.assertRaisesRegex(ValueError, 'Target unavailable'):
            self.reveal()
        self.assertEqual(self.pane.owner, '/old')

    def test_follow_off_preserves_destination_selection(self):
        self.follow = False
        self.reveal()
        self.assertTrue(self.selected.selected)


if __name__ == '__main__':
    unittest.main()
