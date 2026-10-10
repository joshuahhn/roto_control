"""Authorized one-batch physical fixture; execute in TD, never auto-connect.

Baseline recovery project must be loaded, original controller disconnected.
Only source installation and explicitly disposable owned A/B banks are prepared.
"""
from pathlib import Path
from types import SimpleNamespace
import json,hashlib


def prepare(folder):
    folder=Path(folder);package=folder/'candidate/v6';pin=package/'src/touchdesigner'
    manifest=json.loads((package/'manifest.json').read_text())
    for section in ('sources','changed_files'):
        for path,digest in manifest[section].items():assert hashlib.sha256((package/path).read_bytes()).hexdigest()==digest,path
    baseline=json.loads((folder/'live_baseline.json').read_text())
    c=op(baseline['controller']);assert c.ext.RotoPythonExt._process is None
    assert tuple(c.GetLayoutContext()['key'])==tuple(baseline['routing']['key'])
    assert op('/roto_control_python/base_physical_test') is None
    namespace=dict(globals());upgrade=pin/'upgrade_layouts.py'
    exec(compile(upgrade.read_text(),str(upgrade),'exec'),namespace)
    namespace['upgrade'](c,pin)
    # Force native extension initialization before using the additive API.
    c.initializeExtensions(0)
    model=op('/inspector_model');model.op('InspectorModel').text=(pin/'prototypes/inspector/model.py').read_text()
    for view in (op('/inspector_below'),op('/inspector_popup')):view.op('ui').text=(pin/'prototypes/inspector/ui.py').read_text()
    builder=pin/'prototypes/inspector/build_live.py'
    namespace=dict(globals(),controller_path=c.path,project=SimpleNamespace(folder=str(pin)))
    exec(compile(builder.read_text(),str(builder),'exec'),namespace)
    e=c.ext.RotoPythonExt;manager=e._layout_manager()
    original=tuple(c.GetLayoutContext()['key'])
    assert original==tuple(baseline['routing']['key'])
    holder=c.parent().create(baseCOMP,'base_physical_test');holder.viewer=True;holder.nodeX=1200;holder.nodeY=250
    keys={};targets={}
    for index,name in enumerate(('physical_a','physical_b')):
        comp=holder.create(baseCOMP,name);comp.viewer=True;comp.nodeX=index*175;comp.nodeY=0
        page=comp.appendCustomPage('Physical fixture');amount=page.appendFloat('Amount',label='A Amount' if index==0 else 'B Amount')[0]
        amount.default=2;amount.min=amount.normMin=0;amount.max=amount.normMax=7;amount.clampMin=amount.clampMax=True;amount.val=3 if index==0 else 5
        layout=c.RegisterComp(comp);c.RenameLayout(layout,'PHYSICAL A' if index==0 else 'PHYSICAL B')
        track=manager.track(layout);key=(layout,track['id'],manager.layout(layout)['owner']['entry_plugin_id'])
        c.SelectPlugin(*key);targets[name]=[c.AssignParameter('knob',1,amount)['id']]
        if index==0:
            choice=page.appendMenu('Choice',label='Menu Choice')[0];choice.menuNames=['one','two','three'];choice.menuLabels=['FIRST','SECOND','THIRD'];choice.default='two';choice.val='two'
            targets[name].append(c.AssignParameter('knob',2,choice)['id'])
        keys[name]=key
    c.SelectPlugin(*keys['physical_a'])
    model.RefreshDefinitions();model.Sync();model.Flush()
    view=op('/inspector_below').ext.InspectorView;view._follow_routing=True;view.Refresh();view.Show()
    view.ownerComp.par.Presentation='popup';view.Action("slot0")
    sources={}
    for path in (pin/'code/py/roto_python').rglob('*.py'):
        dat=c.op(str(path.relative_to(pin/'code/py/roto_python').with_suffix('')))
        if dat:
            actual=dat.text.replace('\r\n','\n');assert actual==path.read_text().replace('\r\n','\n'),dat.path
            sources[dat.path]=dict(source=str(path.relative_to(package)),source_raw=hashlib.sha256(path.read_bytes()).hexdigest(),native_normalized=hashlib.sha256(actual.encode()).hexdigest())
    for dat,path in [(model.op('live_model'),pin/'prototypes/inspector/live_model.py'),(model.op('base_commands/InspectorCommands'),pin/'prototypes/inspector/commands.py')]+[(v.op('ui'),pin/'prototypes/inspector/ui.py') for v in (op('/inspector_below'),op('/inspector_popup'))]:
        actual=dat.text.replace('\r\n','\n');assert actual==path.read_text().replace('\r\n','\n'),dat.path
        sources[dat.path]=dict(source=str(path.relative_to(package)),source_raw=hashlib.sha256(path.read_bytes()).hexdigest(),native_normalized=hashlib.sha256(actual.encode()).hexdigest())
    for section in ('sources','changed_files'):
        for path,digest in manifest[section].items():assert hashlib.sha256((package/path).read_bytes()).hexdigest()==digest,path
    record=dict(pin=manifest['patch_sha256'],controller=c.path,initial_route=original,owned_keys=keys,targets=targets,installed=sources,raw_pin_after='PASS',exclusive_process=None,holder=holder.path,production_parameters_unchanged=True)
    (folder/'physical_prepared_v6.json').write_text(json.dumps(record,indent=2,default=str)+'\n')
    holder.store('prepared',record)
    return record


def resume(folder):
    """Continue after preserved UI-method typo; never rebuild or enroll again."""
    folder=Path(folder);package=folder/"candidate/v6";pin=package/"src/touchdesigner"
    manifest=json.loads((package/"manifest.json").read_text())
    baseline=json.loads((folder/"live_baseline.json").read_text())
    original=tuple(baseline["routing"]["key"])
    c=op(baseline["controller"]);assert c.ext.RotoPythonExt._process is None
    holder=c.parent().op("base_physical_test");assert holder
    manager=c.ext.RotoPythonExt._layout_manager();keys={};targets={}
    for name in ("physical_a","physical_b"):
        layout=c.LookupCompLayout(holder.op(name));assert layout
        track=manager.track(layout);key=(layout,track["id"],manager.layout(layout)["owner"]["entry_plugin_id"])
        keys[name]=key;targets[name]=[r["id"] for r in c.GetPluginTargets(*key)]
    assert tuple(c.GetLayoutContext()["key"])==keys["physical_a"]
    model=op("/inspector_model");view=op("/inspector_below").ext.InspectorView
    view.Refresh();view.Show();view.Action("slot0")
    sources={}
    for path in (pin/'code/py/roto_python').rglob('*.py'):
        dat=c.op(str(path.relative_to(pin/'code/py/roto_python').with_suffix('')))
        if dat:
            actual=dat.text.replace('\r\n','\n');assert actual==path.read_text().replace('\r\n','\n'),dat.path
            sources[dat.path]=dict(source=str(path.relative_to(package)),source_raw=hashlib.sha256(path.read_bytes()).hexdigest(),native_normalized=hashlib.sha256(actual.encode()).hexdigest())
    for dat,path in [(model.op('live_model'),pin/'prototypes/inspector/live_model.py'),(model.op('base_commands/InspectorCommands'),pin/'prototypes/inspector/commands.py')]+[(v.op('ui'),pin/'prototypes/inspector/ui.py') for v in (op('/inspector_below'),op('/inspector_popup'))]:
        actual=dat.text.replace('\r\n','\n');assert actual==path.read_text().replace('\r\n','\n'),dat.path
        sources[dat.path]=dict(source=str(path.relative_to(package)),source_raw=hashlib.sha256(path.read_bytes()).hexdigest(),native_normalized=hashlib.sha256(actual.encode()).hexdigest())
    for section in ('sources','changed_files'):
        for path,digest in manifest[section].items():assert hashlib.sha256((package/path).read_bytes()).hexdigest()==digest,path
    record=dict(pin=manifest['patch_sha256'],controller=c.path,initial_route=original,owned_keys=keys,targets=targets,installed=sources,raw_pin_after='PASS',exclusive_process=None,holder=holder.path,production_parameters_unchanged=True)
    (folder/'physical_prepared_v6.json').write_text(json.dumps(record,indent=2,default=str)+'\n')
    holder.store('prepared',record)
    return record
