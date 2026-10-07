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
    def __setattr__(self,name,value):self.__dict__[name].val=value

class Window:
    def __init__(self):
        self.valid=True;self.isOpen=True;self.contentWidth=286;self.contentHeight=214
        self.x=508;self.y=236;self.height=246
        self.par=Pars(dict(winw=286,winh=214,winopen=None,justifyoffsetto=None,justifyh=None,justifyv=None,winoffsetx=508,winoffsety=236))
        self.par.winopen.callback=self.open
    def open(self):
        self.isOpen=True;self.contentWidth=self.par.winw.eval();self.contentHeight=self.par.winh.eval()
        self.height=self.contentHeight+32;self.x=self.par.winoffsetx.eval();self.y=self.par.winoffsety.eval()

class PopupExpansionTests(TestCase):
    def setUp(self):
        self.v=InspectorView.__new__(InspectorView);v=self.v
        v._popup=Window();v._popup_extra=0;v._popup_size_pending=False;v._window_opens=0
        v._main=SimpleNamespace(isOpen=True,width=400,height=420,contentHeight=390,x=100,y=50)
        v.HideOtherViews=lambda:None
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
        self.assertEqual(p.par.winopen.pulses,1)
        self.assertEqual(p.contentHeight,348)
    def test_manual_expanded_resize_becomes_new_base(self):
        v=self.v;p=v._popup;v._sync_popup_expansion(MAPPING)
        p.contentWidth=320;p.contentHeight=388;p.height=420;p.y-=40
        corner=(p.x,p.y+p.height);v._sync_popup_expansion(0)
        self.assertEqual((p.contentWidth,p.contentHeight),(320,254))
        self.assertEqual((p.x,p.y+p.height),corner)
        v._sync_popup_expansion(MAPPING)
        self.assertEqual((p.contentWidth,p.contentHeight),(320,388))
    def test_closed_window_changes_use_pending_dimensions_without_opening(self):
        v=self.v;p=v._popup;v._sync_popup_expansion(MAPPING);p.isOpen=False
        v._sync_popup_expansion(0);v._sync_popup_expansion(MAPPING);v._sync_popup_expansion(0)
        self.assertEqual(p.par.winh.eval(),214)
        self.assertFalse(p.isOpen);self.assertEqual(p.par.winopen.pulses,1)
        v.OpenPopup();self.assertEqual((p.contentWidth,p.contentHeight),(286,214))
        self.assertFalse(v._popup_size_pending)
    def test_disconnect_removes_only_section_height_and_unsubscribes(self):
        v=self.v;p=v._popup;v._identity=12;v._model=SimpleNamespace(Unsubscribe=lambda *args:None)
        v._sync_popup_expansion(MAPPING);v.Disconnect()
        self.assertEqual(p.contentHeight,214);self.assertIsNone(v._model)
    def test_deleted_window_does_not_receive_resize(self):
        v=self.v;v._popup.valid=False;v._popup_extra=MAPPING;v._sync_popup_expansion(0)
        self.assertEqual(v._popup_extra,0);self.assertEqual(v._popup.par.winopen.pulses,0)
    def test_reopen_ignores_closed_window_cache_including_title_bar(self):
        v=self.v;p=v._popup;p.isOpen=False;p.contentHeight=246
        v._popup_host=SimpleNamespace(width=286,height=214)
        v.OpenPopup();self.assertEqual(p.contentHeight,214)
