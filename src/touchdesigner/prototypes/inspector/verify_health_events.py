"""Run start/touch/definition/finish in separate TD turns to test native events.

No manual Sync/Inspect after touch or evaluation-mode mutation. The isolated
controller has no MIDI process; finish always restores the production adapter.
"""
from pathlib import Path
import copy
import json

model=op('/inspector_model');view=op('/inspector_below')
name='base_inspector_health_events'
holder=op('/roto_control_python/'+name)
phase=globals().get('phase','start')

if phase=='start':
    assert holder is None
    production=model.par.Controller.eval()
    holder=production.parent().create(baseCOMP,name)
    holder.appendCustomPage('Fixture').appendFloat('Amount');holder.par.Amount=.37
    holder.store('production',production)
    holder.store('before',production.GetControlCatalog())
    holder.store('registry',copy.deepcopy(production.fetch('layout_registry')))
    holder.store('session',model.ext.InspectorModel.adapter.Session())
    holder.store('style',view.ext.InspectorView.style)
    clone=holder.copy(production,name='controller');clone.Disconnect()
    clone.par.Followcomp=False;clone.Applybinding()
    clone.SelectLayout(clone.CreateLayout('Native event fixture'))
    state=clone.AssignParameter('knob',2,holder.par.Amount)
    clone.store('needs_relearn',())
    ext=clone.ext.RotoPythonExt;host=ext._host
    holder.store('packets',[])
    host.send=lambda packet:holder.fetch('packets').append(tuple(packet))
    host.connected=host.plugin=True;host.controls[('knob',2)].mapped=True
    host._sync();ext._publish();assert ext._process is None
    model.par.Controller=clone;model.Sync();model.Flush()
    view.ext.InspectorView.style='below';view.Action('slot1')
    holder.store('token',model.GetToken(model.ActiveContext(),1))
    assert model.Capabilities(model.ActiveContext(),1)['value']['enabled']
elif phase=='touch':
    clone=holder.op('controller');ext=clone.ext.RotoPythonExt
    ext._host.controls[('knob',2)].touched=True
    ext._host._sync();ext._publish()
elif phase=='definition':
    editor=view.op('container_scroll/container_content/editor_below')
    assert not editor.op('apply').par.enable.eval()
    assert not editor.op('clear').par.enable.eval()
    assert model.GetToken(model.ActiveContext(),1)==holder.fetch('token')
    clone=holder.op('controller');ext=clone.ext.RotoPythonExt
    ext._host.controls[('knob',2)].touched=False
    ext._host._sync();ext._publish()
    holder.par.Amount.expr='0.37'  # Same Value: the mode callback must invalidate cache.
elif phase=='finish':
    try:
        key=model.ActiveContext();cap=model.Capabilities(key,1)
        assert not cap['value']['enabled']
        assert 'CONSTANT or BIND' in cap['value']['reason'],dict(cap['value'])
        editor=view.op('container_scroll/container_content/editor_below')
        assert not editor.op('apply').par.enable.eval()
        assert model.GetToken(key,1)!=holder.fetch('token')
        assert holder.par.Amount.eval()==.37 and not holder.fetch('packets')
        result=dict(native_touch_callback=True,touch_keeps_token=True,
                    native_same_value_mode_callback=True,definition_expires_token=True,
                    no_manual_refresh_after_mutations=True,no_fixture_midi_or_value_writes=True)
    finally:
        production=holder.fetch('production');view.CloseEditor()
        view.ext.InspectorView.style=holder.fetch('style')
        model.par.Controller=production;model.Sync();model.Flush()
        holder.op('controller').Disconnect()
        assert production.GetControlCatalog()==holder.fetch('before')
        assert production.fetch('layout_registry')==holder.fetch('registry')
        assert model.ext.InspectorModel.adapter.Session()==holder.fetch('session')
        holder.destroy()
    result['production_session_registry_catalog_preserved']=True
    Path(project.folder+'/prototypes/inspector/health_events.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result))
else:raise ValueError('Unknown phase')
print('Native event phase:',phase)
