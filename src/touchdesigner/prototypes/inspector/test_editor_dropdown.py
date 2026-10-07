"""Editor choices share inline selection, retain live/draft and stale guards."""
from types import SimpleNamespace
from unittest import TestCase
from context_menu import Dropdown
from editor_state import MappingDraft
from test_context_dropdown import MenuPar,Pars
from ui import InspectorView

class DraftPars(Pars):
    def __setitem__(self,name,value):getattr(self,name).val=value

class EditorDropdownTests(TestCase):
    def setUp(self):
        v=self.view=InspectorView.__new__(InspectorView)
        v._context=('L','T','D');v.selected=0;v._token=('token',1);v._menu_generation=0
        v._context_menu=None;v._menu_panel=None;v._menu_callback=None;v._menu_root=None
        self.schema=dict(kind='menu',reason='',names=('a','b','c'),labels=('Same','Same','C'))
        self.mapping_schema=dict(reason='',modes=('value','toggle'),inputs=('push','toggle'))
        v._model=SimpleNamespace(Inspect=lambda *a:None,ValueSchema=lambda *a:self.schema,GetCatalog=lambda *a:[dict(Value=1)],GetToken=lambda *a:v._token,MappingSchema=lambda *a:self.mapping_schema)
        v.IsLive=lambda:True
        v._draft=SimpleNamespace(par=DraftPars(**{n:MenuPar(x,[],[]) for n,x in [('Mapminimum',0),('Mapmaximum',1),('Mapmode','value'),('Mapinput','push')]}))
        v._mapping=MappingDraft();v._mapping.open=True;v._mapping.token=v._token
        v.ownerComp=SimpleNamespace(op=lambda name:None)
        self.anchor=None;self.checked=None;self.values=[]
        v.TypedValue=lambda value:self.values.append(value) or True
        def open_menu(items,callback,details,checked,anchor):
            v.CloseContextMenu();self.anchor=anchor;self.checked=checked
            v._context_menu=Dropdown(items,details,checked);v._menu_callback=callback;return True
        v.OpenEditorMenu=open_menu
    def test_value_same_labels_select_by_index_and_dispatch_live(self):
        v=self.view;self.assertTrue(v.OpenValueMenu())
        self.assertEqual(self.anchor,'value_menu');self.assertEqual(self.checked,['Same [1]'])
        self.assertTrue(v.SelectContextItem(0));self.assertEqual(self.values,[0]);self.assertIsNone(v._context_menu)
    def test_value_changed_schema_or_token_rejects_old_choice(self):
        v=self.view;v.OpenValueMenu();self.schema['labels']=('A','B','C')
        self.assertFalse(v.SelectContextItem(0));self.assertEqual(self.values,[])
        v.OpenValueMenu();v._token=('token',2)
        self.assertFalse(v.SelectContextItem(0));self.assertEqual(self.values,[])
    def test_new_mapping_menu_invalidates_old_value_callback(self):
        v=self.view;v.OpenValueMenu();old=v._context_menu
        v.OpenMappingChoice('mode')
        self.assertFalse(v.SelectValueMenu(dict(item=old.items[0],details=old.details)))
        self.assertEqual(self.values,[])
    def test_mode_and_hw_choices_change_only_mapping_draft(self):
        v=self.view
        for field,anchor,par in [('mode','choice_mode','Mapmode'),('button_type','choice_input','Mapinput')]:
            self.assertTrue(v.OpenMappingChoice(field));self.assertEqual(self.anchor,'container_mapping/'+anchor)
            self.assertTrue(v.SelectContextItem(1));self.assertEqual(v._draft.par[par].eval(),'toggle')
        self.assertEqual(self.values,[]);self.assertTrue(v._mapping.open)
    def test_mapping_closed_stale_token_or_generation_rejects_callback(self):
        v=self.view
        for change in (lambda:v._mapping.Close(),lambda:setattr(v,'_token',('token',2)),lambda:setattr(v,'_menu_generation',v._menu_generation+1)):
            v._mapping.open=True;v._mapping.token=v._token;v.OpenMappingChoice('mode');change()
            self.assertFalse(v.SelectContextItem(1))
        self.assertEqual(self.values,[])
    def test_fixed_single_choice_does_not_open(self):
        self.mapping_schema['modes']=('value',)
        self.assertFalse(self.view.OpenMappingChoice('mode'));self.assertIsNone(self.view._context_menu)
    def test_menu_close_clears_temporary_editor_and_window_space_once(self):
        v=self.view;v._menu_extra=164;v._menu_window_extra=164;layouts=[]
        v._editor_layout=lambda:layouts.append((v._menu_extra,v._menu_window_extra))
        v.CloseContextMenu();v.CloseContextMenu()
        self.assertEqual(layouts,[(0,0)])
    def test_popup_focus_and_outside_click_do_not_use_inspector_scope(self):
        v=self.view;main=object();popup=SimpleNamespace(panel=SimpleNamespace(focusselect=True))
        panel=SimpleNamespace(panel=SimpleNamespace(inside=False),par=SimpleNamespace(display=True),op=lambda name:SimpleNamespace(par=SimpleNamespace(text='',display=False)))
        v._menu_root=popup;v._menu_panel=panel;v._context_menu=Dropdown(('A',),{})
        v.ContextMenuFocusLost(main);v.ContextMenuOutsideClick(main);self.assertTrue(v.ContextMenuOpen())
        v.ContextMenuEscape();self.assertFalse(v.ContextMenuOpen())
        v._menu_root=popup;v._menu_panel=panel;v._context_menu=Dropdown(('A',),{})
        v.ContextMenuOutsideClick(popup);self.assertFalse(v.ContextMenuOpen())
