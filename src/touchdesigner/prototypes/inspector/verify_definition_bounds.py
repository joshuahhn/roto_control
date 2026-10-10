"""Native bounds setters and real K2 rejection/no-op, without hardware edits."""
from pathlib import Path
import json
c=op('/roto_control_python/roto_python');m=op('/inspector_model');v=op('/inspector_below')
before=c.GetControlCatalog();registry=c.fetch('layout_registry');pid=c.ext.RotoPythonExt._process.pid
name='base_definition_bounds_verification'
assert not op('/roto_control_python/'+name)
fixture=op('/roto_control_python').create(baseCOMP,name);fixture.viewer=True
fixture.nodeX=1750;fixture.nodeY=-1000
module=m.op('base_commands/definition_edit').module
try:
    page=fixture.appendCustomPage('Test')
    for style,name,value,default,maximum in (('Float','Amount',.375,.25,1),('Int','Count',2,1,8)):
        p=getattr(page,'append'+style)(name)[0]
        p.default=default;p.min=0;p.max=maximum;p.clampMin=p.clampMax=True;p.val=value
        info=dict(id=name,comp=fixture.path,parameter=name)
        ranges=((('fixture','track','device'),name,0.,float(maximum)),)
        draft=module.begin(info,lambda info:p,ranges)
        assert module.apply(info,draft,dict(normMin=-1,normMax=maximum+1,min=-1,max=maximum+1),lambda info:p,ranges)
        assert p.eval()==p.val==value and p.default==default
        assert (p.normMin,p.normMax,p.min,p.max)==(-1,maximum+1,-1,maximum+1)
        restore=module.begin(info,lambda info:p,ranges)
        assert module.apply(info,restore,draft['original'],lambda info:p,ranges)
        toggles=module.begin(info,lambda info:p,ranges)
        assert module.apply(info,toggles,dict(clampMin=False,clampMax=False),lambda info:p,ranges)
        assert not p.clampMin and not p.clampMax and p.eval()==value
        module.apply(info,module.begin(info,lambda info:p,ranges),toggles['original'],lambda info:p,ranges)
        assert p.clampMin and p.clampMax
    v.Action('slot1');v.Action('details_toggle')
    assert v.Action('definition_edit') is not False
    v.Action('definition_bounds')
    native=op('/roto_control_python/pixelSortV3').par.Lowthresh
    original=(native.min,native.max,native.clampMin,native.clampMax,native.eval())
    v.op('base_draft').par.Nativelimitmax='0.5'
    assert v.Action('definition_apply') is False
    assert 'Mapping' in v.ext.InspectorView._error
    assert (native.min,native.max,native.clampMin,native.clampMax,native.eval())==original
    v.op('base_draft').par.Nativelimitmax='1'
    assert v.Action('definition_apply') is not False  # Existing real bounds unchanged.
    assert v.op('window_editor').par.winh.eval()==402
finally:
    fixture.destroy()
assert c.GetControlCatalog()==before and c.fetch('layout_registry')==registry and c.ext.RotoPythonExt._process.pid==pid
assert m.Stats()['subscribers']==2
assert not any(o.errors(recurse=True) for o in (c,m,v,op('/inspector_popup')))
result=dict(native_float_int_bounds_setters=True,native_clamp_flag_setters=True,live_value_default_preserved=True,
    real_k2_mapping_range_rejection=True,real_k2_noop_apply=True,production_catalog_registry_process_preserved=True,
    fixture_removed=True,details_height=402,subscribers=2)
Path(project.folder+'/prototypes/inspector/definition_bounds_verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
