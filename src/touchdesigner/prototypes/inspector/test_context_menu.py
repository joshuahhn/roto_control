from types import SimpleNamespace
from unittest import TestCase
from context_menu import Dropdown,capacity_for,placement_for,editor_space_for
from context_callbacks import header_callback_source

class DropdownTests(TestCase):
    def test_editor_always_has_room_below_for_bounded_rows(self):
        for bottom in (36,38,66,170,300):
            for count in (1,2,8,17,127):
                extra,capacity=editor_space_for(bottom,count)
                height=4+24*min(count,capacity)+(24 if count>capacity else 0)
                self.assertGreaterEqual(bottom+extra,height+4)
                self.assertLessEqual(capacity,4)
        self.assertEqual(editor_space_for(36,8),(92,4))
        self.assertEqual(editor_space_for(66,2),(0,2))
    def test_existing_tall_window_shows_full_menu_without_extra_window_space(self):
        self.assertEqual(editor_space_for(36,8,200),(164,8))
        self.assertEqual(editor_space_for(36,8,199),(92,4))
        self.assertEqual(editor_space_for(66,2,66),(0,2))
    def test_editor_menu_fits_above_or_below_without_window_growth(self):
        for bottom,top,height,count in [(36,58,178,8),(72,98,312,2),(40,64,178,127),(250,274,428,127)]:
            direction,capacity=placement_for(bottom,top,height,count)
            space=bottom if direction=='below' else height-top
            menu_height=4+24*min(count,capacity)+(24 if count>capacity else 0)
            self.assertLessEqual(menu_height+2,space)
        self.assertEqual(placement_for(36,58,178,8),('above',3))
        self.assertEqual(placement_for(72,98,312,2),('below',2))
    def test_menu_rows_and_footer_fit_below_header_at_compact_heights(self):
        for bottom in (54,74,98,132,200,320):
            for count in (1,2,3,8,17,127):
                capacity=capacity_for(bottom,count)
                height=4+24*min(count,capacity)+(24 if count>capacity else 0)
                self.assertLessEqual(height+2,bottom)
                self.assertGreaterEqual(capacity,1);self.assertLessEqual(capacity,8)
    def test_pool_scrolls_to_checked_item_and_stays_bounded(self):
        state=Dropdown(tuple(str(i) for i in range(127)),{},('126',))
        self.assertEqual(state.rows(),tuple(str(i) for i in range(119,127)))
        self.assertEqual(state.count_label(),'120–127 / 127')
        self.assertFalse(state.move(8));self.assertTrue(state.move(-200));self.assertEqual(state.first,0)
        self.assertEqual(state.item(7),'7')
    def test_paging_preserves_callback_details_and_checks(self):
        details=dict(context=('L','T','D'),generation=3)
        state=Dropdown(tuple(str(i) for i in range(9)),details,('0',))
        self.assertTrue(state.move(8));self.assertEqual(state.rows(),tuple(str(i) for i in range(1,9)))
        self.assertIs(state.details,details);self.assertEqual(state.checked,frozenset(('0',)))
        for slot in (-1,8,'0',True):
            with self.assertRaises(ValueError):state.item(slot)
    def test_small_menu_has_no_spare_rows(self):
        state=Dropdown(('A','B'),{},('B',))
        self.assertEqual(state.rows(),('A','B'));self.assertFalse(state.move(1));self.assertEqual(state.count_label(),'1–2 / 2')
    def test_header_release_inside_opens_each_dropdown_without_timer(self):
        opened=[];panel=SimpleNamespace(inside=True);main=SimpleNamespace(isOpen=True)
        owner=SimpleNamespace(op=lambda n:SimpleNamespace(panel=panel),ext=SimpleNamespace(InspectorView=SimpleNamespace(_main=main)),OpenContextMenu=opened.append)
        for name in ('Device','Layout','Track'):
            scope=dict(parent=SimpleNamespace(InspectorDemo=owner));exec(header_callback_source(name),scope)
            callback=scope['onOnToOff'];callback(None);panel.inside=False;callback(None);panel.inside=True
            main.isOpen=False;callback(None);main.isOpen=True
        self.assertEqual(opened,['Device','Layout','Track'])
