"""Native Style selection and preview stay separate from live Value input."""
from types import SimpleNamespace
from unittest import TestCase
from ui import InspectorView,DEFINITION_FIELDS,STYLE_FIELDS
from test_definition_bounds import DraftPars
from test_style_migration import native
import definition_edit
import style_migration
from test_parameter_definition import INFO
from test_live_model import KEY

class Pars(DraftPars):
    def __setattr__(self,key,value):self[key]=value

class StyleViewTests(TestCase):
    def view(self):
        p=native();d=definition_edit.begin(INFO,lambda i:p);d['style_snapshot']=style_migration.begin(p)
        view=InspectorView.__new__(InspectorView)
        view._definition_draft=d;view._context=KEY;view.selected=1;view._token=('token',)
        view._definition_scope=(KEY,1,view._token);view._menu_generation=1;view._details_open=True
        values={name:str(d['original'][key]) if not key.startswith('clamp') else d['original'][key] for key,name in DEFINITION_FIELDS}
        values['Nativestyle']='Float';view._draft=SimpleNamespace(par=Pars(values));view.calls=[]
        view._model=SimpleNamespace(Stats=lambda:dict(generation=1),GetToken=lambda *a:view._token,
            PreviewStyle=lambda *a:dict(style='Int',value=3,mappings=2))
        view.Key=lambda:KEY;view._update_details=lambda:None;view.CloseContextMenu=lambda:None
        view._set_error=lambda text:view.calls.append(text)
        return view

    def details(self,view):
        return dict(generation=1,model_generation=1,context=KEY,slot=1,token=view._token)

    def test_one_selection_updates_only_local_style_and_preview(self):
        view=self.view()
        self.assertTrue(view.SelectDefinitionStyle(dict(item='Int',details=self.details(view))))
        self.assertEqual(view._definition_patch()['style'],'Int')
        self.assertEqual(view._style_preview['value'],3)
        self.assertEqual(view._menu_generation,2)
        self.assertEqual(view.calls,[])
        self.assertFalse(view.SelectDefinitionStyle(dict(item='Float',details=self.details(view))))

    def test_stale_session_or_token_rejects_selection(self):
        for field,value in [('model_generation',2),('token',('other',)),('slot',2)]:
            view=self.view();details=self.details(view);details[field]=value
            self.assertFalse(view.SelectDefinitionStyle(dict(item='Int',details=details)))
            self.assertEqual(view._definition_patch()['style'],'Float')

    def test_apply_carries_approved_value_then_resets_input_type(self):
        view=self.view();view._draft.par.Nativestyle='Int';view._style_preview=dict(value=3,style='Int')
        patches=[];view._model.ApplyDefinition=lambda *args:patches.append(args[-1]) or True
        view._capture_definition=lambda:None;view._update_editor=lambda **kw:None;view._editors=[]
        view._value_type='float'
        self.assertIsNot(view.Action('definition_apply'),False)
        self.assertEqual(patches[0]['style_value'],3)
        self.assertIsNone(view._value_type);self.assertIsNone(view._definition_draft)
        self.assertEqual(view._draft.par.Nativestyle.eval(),'')
        self.assertIn('Needs re-LEARN',view.calls[-1])

    def test_apply_without_valid_preview_is_rejected(self):
        view=self.view();view._draft.par.Nativestyle='Int';view._style_preview=dict(reason='Would lose decimals')
        self.assertFalse(view.Action('definition_apply'))
        self.assertIsNotNone(view._definition_draft)
        self.assertIn('preview',view.calls[-1])
