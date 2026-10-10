"""Disposable native setters plus production UI draft/no-op Apply/cancel checks."""
from pathlib import Path
import json
c=op('/roto_control_python/roto_python');m=op('/inspector_model');v=op('/inspector_below')
before=c.GetControlCatalog();registry=c.fetch('layout_registry');pid=c.ext.RotoPythonExt._process.pid
name='base_definition_edit_verification'
assert not op('/roto_control_python/'+name)
fixture=op('/roto_control_python').create(baseCOMP,name);fixture.viewer=True
fixture.nodeX=1750;fixture.nodeY=-1000
try:
    page=fixture.appendCustomPage('Test')
    floats=page.appendFloat('Amount',label='Fixture amount');p=floats[0]
    p.default=.25;p.val=.375;p.min=0;p.max=1;p.clampMin=p.clampMax=True
    q=page.appendInt('Count',label='Fixture count')[0];q.default=1;q.val=2;q.min=0;q.max=8;q.clampMin=q.clampMax=True
    module=m.op('base_commands/definition_edit').module
    for par,label,value in ((p,'Renamed amount',.5),(q,'Renamed count',3)):
        info=dict(id='fixture',comp=fixture.path,parameter=par.name)
        old=par.eval();mode=par.mode;group=[p.name for p in par.parGroup]
        draft=module.begin(info,lambda i:par)
        assert module.apply(info,draft,dict(label=label,default=value),lambda i:par)
        assert par.label==label and par.default==value and par.eval()==old and par.mode==mode
        assert [p.name for p in par.parGroup]==group
        restore=module.begin(info,lambda i:par)
        assert module.apply(info,restore,draft['original'],lambda i:par)
        stale=module.begin(info,lambda i:par);par.default=value
        try:module.apply(info,stale,dict(label='Stale',default=value),lambda i:par)
        except ValueError:pass
        else:raise AssertionError('Stale native draft accepted')
    v.Action('slot1');v.Action('details_toggle')
    height=v.op('window_editor').par.winh.eval()
    assert v.Action('definition_edit') is not False
    assert v.Action('definition_apply') is not False  # Real K2 no-op; no metadata mutation.
    assert v.Action('definition_edit') is not False
    v.op('base_draft').par.Nativelabel='Discarded draft'
    v.op('base_draft').par.Nativedefault='0.5'
    v.Action('definition_cancel')
    assert v.ext.InspectorView._definition_draft is None
    assert v.op('window_editor').par.winh.eval()==height==402
    assert not v.op('base_draft').par.Nativelabel.eval()
finally:
    fixture.destroy()
assert c.GetControlCatalog()==before and c.fetch('layout_registry')==registry and c.ext.RotoPythonExt._process.pid==pid
assert m.Stats()['subscribers']==2
assert not any(o.errors(recurse=True) for o in (c,m,v,op('/inspector_popup')))
result=dict(native_float_int_setters=True,live_value_mode_identity_preserved=True,native_stale_draft_rejected=True,
    production_ui_noop_apply_cancel=True,production_catalog_registry_process_preserved=True,details_height=402,fixture_removed=True,subscribers=2)
Path(project.folder+'/prototypes/inspector/definition_edit_verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
