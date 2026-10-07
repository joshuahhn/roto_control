"""Run start/finish in separate TD turns to catch deferred write echoes."""
from pathlib import Path
from types import SimpleNamespace
import copy,json
m=op('/inspector_model');v=op('/inspector_below')
holder=op('/roto_control_python/base_inspector_value_verification')
phase=globals().get('phase','start')
if phase=='start':
    assert holder is None
    production=m.par.Controller.eval();holder=production.parent().create(baseCOMP,'base_inspector_value_verification')
    holder.viewer=True;holder.appendCustomPage('Fixture').appendFloat('Amount');holder.par.Amount=.37
    holder.store('production',production);holder.store('catalog',production.GetControlCatalog())
    holder.store('registry',copy.deepcopy(production.fetch('layout_registry')));holder.store('session',m.ext.InspectorModel.adapter.Session());holder.store('style',v.ext.InspectorView.style)
    clone=holder.copy(production,name='controller');clone.Disconnect();clone.par.Followcomp=False;clone.Applybinding()
    clone.SelectLayout(clone.CreateLayout('Live Value fixture'));id=clone.AssignParameter('knob',2,holder.par.Amount)['id']
    ext=clone.ext.RotoPythonExt;original=ext.SetValue;holder.store('writes',[])
    def capture(value,id=None):
        holder.fetch('writes').append((id,value));return original(value,id)
    ext.SetValue=capture
    assert ext._process is None
    m.par.Controller=clone;m.Sync();m.Flush();v.ext.InspectorView.style='below';v.Action('slot1')
    editor=v.ext.InspectorView._editors[0];field=editor.op('field_Value');callbacks=field.par.callbacks.eval().module
    v.Action('value_type');v.Action('value_type')
    assert not holder.fetch('writes') and holder.par.Amount.eval()==.37
    assert field.par.editmode.eval()=='editablecontinuous'
    assert not editor.op('cancel').par.display.eval() and not editor.op('apply').par.display.eval()
    callbacks.onValueChange(field,'.37','0');assert not holder.fetch('writes')
    callbacks.onFocus(field);callbacks.onTextEdit(SimpleNamespace(editText='.62'))
    assert holder.par.Amount.eval()==.62 and len(holder.fetch('writes'))==1
    callbacks.onTextEdit(SimpleNamespace(editText='.62'));assert len(holder.fetch('writes'))==1
    callbacks.onTextEdit(SimpleNamespace(editText='2'));assert len(holder.fetch('writes'))==1
    callbacks.onFocusEnd(field,dict(reason='enter'));assert v.op('base_draft').par.Value.eval()==.62
    clone.SetValue(.81,id);m.Sync();m.Flush()
    assert v.op('base_draft').par.Value.eval()==.81 and len(holder.fetch('writes'))==2
    callbacks.onValueChange(field,'.81','.62')
    assert len(holder.fetch('writes'))==2
elif phase=='finish':
    try:
        assert holder.par.Amount.eval()==.81 and len(holder.fetch('writes'))==2
        assert not m.Stats()['subscriber_errors']
        result=dict(numeric_type_cycle_no_deferred_write=True,continuous_user_callback_live_write=True,no_value_apply_cancel=True,
                    same_value_deduplicated=True,invalid_range_no_write=True,
                    software_value_follows_field=True,deferred_model_updates_no_echo=True)
    finally:
        production=holder.fetch('production');v.CloseEditor();v.ext.InspectorView.style=holder.fetch('style')
        m.par.Controller=production;m.Sync();m.Flush();holder.op('controller').Disconnect()
        assert production.GetControlCatalog()==holder.fetch('catalog')
        assert production.fetch('layout_registry')==holder.fetch('registry')
        assert m.ext.InspectorModel.adapter.Session()==holder.fetch('session')
        holder.destroy()
    result['production_catalog_registry_session_preserved']=True
    Path(project.folder+'/prototypes/inspector/live_value_verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
else:raise ValueError('Unknown phase')
print('Live Value phase:',phase)
