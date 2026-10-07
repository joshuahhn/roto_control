"""Native-height deltas preserve manual dimensions and closed-window state."""
from types import SimpleNamespace
from unittest import TestCase
from ui import InspectorView,MAPPING

class Par:
    def __init__(self,value=None,callback=lambda:None):self.val=value;self.callback=callback;self.pulses=0
    def eval(self):return self.val
    def pulse(self):self.pulses+=1;self.callback()

class Pars:
    def __init__(self,values):self.__dict__.update({n:Par(v) for n,v in values.items()})
    def __setattr__(self,name,value):
        self.__dict__[name].val=value
        callback=self.__dict__.get('_changed')
        if callback:callback(name)

class Window:
    def __init__(self):
        self.valid=True;self.isOpen=True;self.contentWidth=286;self.contentHeight=214
        self.x=508;self.y=236;self.height=246
        self.par=Pars(dict(winw=286,winh=214,winopen=None,justifyoffsetto=None,justifyh=None,justifyv=None,winoffsetx=508,winoffsety=236))
        self.width_history=[]
        self.par.winopen.callback=self.open
        self.par.__dict__['_changed']=lambda name:self.open() if self.isOpen and name in ('winw','winh','winoffsetx','winoffsety') else None
    def open(self):
        self.isOpen=True;self.contentWidth=self.par.winw.eval();self.contentHeight=self.par.winh.eval()
        self.width_history.append(self.contentWidth)
        self.height=self.contentHeight+32;self.x=self.par.winoffsetx.eval();self.y=self.par.winoffsety.eval()

class DeferredWindow(Window):
    """TD opening parameters update before its native geometry cache."""
    def open(self):pass
    def settle(self):super().open()

class PopupExpansionTests(TestCase):
    def setUp(self):
        self.v=InspectorView.__new__(InspectorView);v=self.v
        v._popup=Window();v._popup_extra=0;v._popup_size_pending=False;v._window_opens=0
        v._main=SimpleNamespace(isOpen=True,width=400,height=420,contentHeight=390,x=100,y=50)
        v.HideOtherViews=lambda:None
    def test_same_tick_section_changes_do_not_accumulate_stale_native_height(self):
        v=self.v;p=v._popup=DeferredWindow();corner=(p.x,p.y+p.height)
        for _ in range(20):
            for extra in (MAPPING,0,224,0,250,0,92,0):v._sync_popup_expansion(extra)
            p.settle()
            self.assertEqual((p.contentWidth,p.contentHeight),(286,214))
            self.assertEqual((p.x,p.y+p.height),corner)
        self.assertEqual(p.par.winopen.pulses,0)
    def test_close_before_native_resize_settles_retains_collapsed_height(self):
        v=self.v;p=v._popup=DeferredWindow()
        v._sync_popup_expansion(250);p.isOpen=False;v._sync_popup_expansion(0)
        self.assertEqual(p.par.winh.eval(),214)
    def test_reopen_before_collapsed_resize_settles_ignores_expanded_host_cache(self):
        v=self.v;p=v._popup=DeferredWindow();v._popup_host=SimpleNamespace(width=286,height=348)
        v._sync_popup_expansion(MAPPING);p.settle()
        v._sync_popup_expansion(0);p.isOpen=False
        v.OpenPopup()
        self.assertEqual(p.par.winh.eval(),214)
    def test_expand_collapse_keeps_width_and_top_left(self):
        v=self.v;p=v._popup;corner=(p.x,p.y+p.height)
        for _ in range(10):
            v._sync_popup_expansion(MAPPING)
            self.assertEqual((p.contentWidth,p.contentHeight),(286,348))
            self.assertEqual((p.x,p.y+p.height),corner)
            v._sync_popup_expansion(0)
            self.assertEqual((p.contentWidth,p.contentHeight),(286,214))
            self.assertEqual((p.x,p.y+p.height),corner)
        self.assertEqual(v._main.width,400)
    def test_repeated_layout_does_not_reopen_or_grow_window(self):
        v=self.v;p=v._popup;v._sync_popup_expansion(MAPPING)
        for _ in range(100):v._sync_popup_expansion(MAPPING)
        self.assertEqual(p.par.winopen.pulses,0)
        self.assertEqual(p.contentHeight,348)
    def test_section_changes_never_pulse_open_on_an_existing_window(self):
        v=self.v;p=v._popup
        for extra in (MAPPING,250,MAPPING,0):v._sync_popup_expansion(extra)
        self.assertEqual(p.par.winopen.pulses,0)

    def test_manual_expanded_resize_becomes_new_base(self):
        v=self.v;p=v._popup;v._sync_popup_expansion(MAPPING)
        p.contentWidth=320;p.contentHeight=388;p.height=420;p.y-=40
        corner=(p.x,p.y+p.height);v._sync_popup_expansion(0)
        self.assertEqual((p.contentWidth,p.contentHeight),(320,254))
        self.assertEqual((p.x,p.y+p.height),corner)
        v._sync_popup_expansion(MAPPING)
        self.assertEqual((p.contentWidth,p.contentHeight),(320,388))
    def test_manual_width_never_snaps_to_stale_opening_width_between_settings(self):
        v=self.v;p=v._popup
        # Manual native resize does not update Opening Width/Height parameters.
        p.contentWidth=376;p.contentHeight=300;p.height=332
        self.assertEqual(p.par.winw.eval(),286)
        corner=(p.x,p.y+p.height)
        for extra in (MAPPING,250,MAPPING,0):v._sync_popup_expansion(extra)
        self.assertTrue(p.width_history)
        self.assertEqual(set(p.width_history),{376})
        self.assertEqual((p.contentWidth,p.contentHeight),(376,300))
        self.assertEqual((p.x,p.y+p.height),corner)

    def test_closed_window_changes_use_pending_dimensions_without_opening(self):
        v=self.v;p=v._popup;v._sync_popup_expansion(MAPPING);p.isOpen=False
        v._sync_popup_expansion(0);v._sync_popup_expansion(MAPPING);v._sync_popup_expansion(0)
        self.assertEqual(p.par.winh.eval(),214)
        self.assertFalse(p.isOpen);self.assertEqual(p.par.winopen.pulses,0)
        v.OpenPopup();self.assertEqual((p.contentWidth,p.contentHeight),(286,214))
        self.assertFalse(v._popup_size_pending)
    def test_disconnect_removes_only_section_height_and_unsubscribes(self):
        v=self.v;p=v._popup;v._identity=12;v._model=SimpleNamespace(Unsubscribe=lambda *args:None)
        v.ownerComp=SimpleNamespace(op=lambda path:None)
        v._sync_popup_expansion(MAPPING);v.Disconnect()
        self.assertEqual(p.contentHeight,214);self.assertIsNone(v._model)
    def test_deleted_window_does_not_receive_resize(self):
        v=self.v;v._popup.valid=False;v._popup_extra=MAPPING;v._sync_popup_expansion(0)
        self.assertEqual(v._popup_extra,0);self.assertEqual(v._popup.par.winopen.pulses,0)
    def test_reopen_ignores_closed_window_cache_including_title_bar(self):
        v=self.v;p=v._popup;p.isOpen=False;p.contentHeight=246
        v._popup_host=SimpleNamespace(width=286,height=214)
        v.OpenPopup();self.assertEqual(p.contentHeight,214)
