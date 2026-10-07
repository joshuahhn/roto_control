"""Dropdown opening never cycles; selection is ID-based and stale-safe."""
from types import SimpleNamespace
from unittest import TestCase
from live_model import ControllerCatalog
from test_live_model import Adapter,KEY,state
from ui import InspectorView
from context_menu import Dropdown

class MenuPar:
    def __init__(self,value,names,labels):self.val=value;self.menuNames=names;self.menuLabels=labels
    def eval(self):return self.val

class Pars(SimpleNamespace):
    def __getitem__(self,name):return getattr(self,name)

class DropdownTests(TestCase):
    def setUp(self):
        self.adapter=Adapter();self.other=('layout','track','other');self.adapter.records[self.other]=[state()]
        self.adapter.Choices=lambda name,key:[('device','Same name'),('other','Same name')] if name=='Device' else [(key[0 if name=='Layout' else 1],name)]
        model=ControllerCatalog(self.adapter);model.GetCatalog(KEY)
        self.view=InspectorView.__new__(InspectorView);v=self.view
        v._model=model;v._context=KEY;v._menu_generation=0;v._follow_routing=True
        v._context_menu=None
        v.ownerComp=SimpleNamespace(par=Pars(**{n:MenuPar(KEY[i],['device','other'] if n=='Device' else [KEY[i]],['Same name','Same name'] if n=='Device' else [n]) for i,n in enumerate(('Layout','Track','Device'))}))
        v.Key=lambda:tuple(getattr(v.ownerComp.par,n).eval() for n in ('Layout','Track','Device'))
        v.ConfigureMenus=lambda key:None;v.OnContext=lambda:None
        panel=SimpleNamespace(y=200,par=SimpleNamespace(y=MenuPar(200,[],[])),op=lambda path:SimpleNamespace(par=SimpleNamespace(text='',display=False)))
        v.ownerComp.op=lambda name:panel
        self.opened=[];v._render_context_menu=lambda:self.opened.append(v._context_menu)
        def open_menu(items,callback,details,checked,host,anchor):
            v.CloseContextMenu();v._menu_panel=panel;v._menu_callback=callback
            v._context_menu=Dropdown(items,details,checked);v._render_context_menu();return True
        v.OpenInlineMenu=open_menu
    def test_all_three_header_buttons_open_dropdown_without_cycling(self):
        for name in ('Device','Layout','Track'):
            self.assertTrue(self.view.Action('context_'+name));self.assertEqual(self.view.Key(),KEY)
            self.assertEqual(self.opened[-1].details['name'],name)
        self.assertEqual(self.adapter.active,KEY)
    def test_duplicate_labels_resolve_correct_id_and_keep_hardware_route(self):
        self.view.OpenContextMenu('Device');menu=self.opened[-1]
        self.assertEqual(menu.items,('Same name (1)','Same name (2)'))
        self.assertTrue(self.view.SelectContextItem(1))
        self.assertIsNone(self.view._context_menu)
        self.assertEqual(self.view.Key(),self.other);self.assertFalse(self.view._follow_routing)
        self.assertEqual(self.adapter.active,KEY);self.assertEqual(self.adapter.writes,[])
    def test_stale_menu_after_session_change_or_new_menu_is_ignored(self):
        self.view.OpenContextMenu('Device');menu=self.opened[-1]
        self.adapter.session+=1;self.view._model.Sync()
        self.assertFalse(self.view.SelectContextMenu(dict(item=menu.items[1],details=menu.details)))
        self.view.OpenContextMenu('Device');menu=self.opened[-1];self.view.OpenContextMenu('Track')
        self.assertFalse(self.view.SelectContextMenu(dict(item=menu.items[1],details=menu.details)))
        self.assertEqual(self.view.Key(),KEY)
    def test_removed_registry_context_does_not_raise_in_menu_callback(self):
        self.view.OpenContextMenu('Device');menu=self.opened[-1]
        def removed(*args):raise ValueError('Context was removed')
        self.adapter.Choices=removed
        self.assertFalse(self.view.SelectContextItem(1))
        self.assertEqual(self.view.Key(),KEY)

class IndependentEditorTests(TestCase):
    def view(self,opened):
        class Par:
            def __init__(self,value=None):self.value=value;self.expr=None
            def eval(self):return self.value
            def pulse(self):pass
        v=InspectorView.__new__(InspectorView)
        v._main=SimpleNamespace(isOpen=True,contentWidth=400,width=400,contentHeight=390,height=420,x=100,y=50)
        v._popup=SimpleNamespace(isOpen=opened,contentWidth=286,contentHeight=214,x=508,y=236,
            par=SimpleNamespace(**{name:Par(value) for name,value in [('winw',286),('winh',214),('winopen',None),('justifyoffsetto',None),('justifyh',None),('justifyv',None),('winoffsetx',None),('winoffsety',None)]}))
        v.HideOtherViews=lambda:None;v._window_opens=0
        return v
    def test_open_editor_retains_own_size_and_position_when_inspector_changes(self):
        v=self.view(True);v.OpenPopup()
        self.assertEqual((v._popup.par.winw.eval(),v._popup.par.winh.eval()),(286,214))
        self.assertEqual(v._window_opens,0)
        self.assertIsNone(v._popup.par.winoffsetx.value)
    def test_reopen_uses_editor_dimensions_instead_of_inspector_dimensions(self):
        v=self.view(False);v.OpenPopup()
        self.assertEqual((v._popup.par.winw,v._popup.par.winh),(286,214))
        self.assertEqual(v._popup.par.winoffsetx,508)
        self.assertEqual(v._window_opens,1)
