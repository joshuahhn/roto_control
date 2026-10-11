"""Targeted native fixture. Execute via live TD with __file__ and TD globals.

Only own fixture is mutated. Production main source/mappings are inventoried.
"""
from pathlib import Path
import hashlib
import json
import time

SOURCE = Path(__file__).resolve().parents[2]
RESULTS = SOURCE / 'diagnostics/validation/native_results'
ROOT = '/roto_clean_demo'
FIXTURE = ROOT + '/base_validation_fixture'


def snapshot(controller):
    nodes=[controller];sources={}
    while nodes:
        node=nodes.pop()
        if node.isCOMP:nodes.extend(node.children)
        if node.isDAT and getattr(node.par,'language',None) is not None and node.par.language.eval()=='python':
            sources[node.path[len(controller.path):]]=hashlib.sha256(node.text.encode()).hexdigest()
    return dict(sources=sources,registry=controller.GetLayoutRegistry(),catalog=controller.GetControlCatalog(),
                process=controller.ext.RotoPythonExt._process is not None)


def write(name,data):
    RESULTS.mkdir(parents=True,exist_ok=True)
    (RESULTS/(name+'.json')).write_text(json.dumps(data,indent=2,default=str)+'\n')


def start():
    assert project.name.startswith('cleaned_owned_inspector_review') and app.build=='2025.33230'
    parent_comp=op(ROOT);main=parent_comp.op('roto_python')
    assert main.ext.RotoPythonExt._process is None
    assert op(FIXTURE) is None
    write('main_before',snapshot(main))
    recovery=SOURCE.parents[1]/'native-recovery'/'owned_main_before_fixture.tox'
    assert not recovery.exists()
    main.save(str(recovery),createFolders=True)
    holder=parent_comp.create(baseCOMP,'base_validation_fixture')
    holder.viewer=True;holder.nodeX=900;holder.nodeY=-400
    holder.par.parentshortcut='ValidationFixture'
    namespace=dict(globals())
    path=SOURCE/'scripts/build_network.py'
    exec(compile(path.read_text(),str(path),'exec'),namespace)
    controller=namespace['build'](holder,SOURCE)
    assert controller.ext.RotoPythonExt._process is None
    print(json.dumps(dict(fixture=holder.path,controller=controller.path,recovery=str(recovery))))


def configure():
    holder=op(FIXTURE);controller=holder.op('roto_python')
    page=holder.appendCustomPage('Native Knobs')
    master=page.appendFloat('Master')[0];master.val=.37
    for i in range(8):
        name='K'+str(i+1)
        if i==1:
            par=page.appendInt(name)[0];par.min=par.normMin=0;par.max=par.normMax=10;par.val=4
        elif i==2:
            par=page.appendMenu(name)[0];par.menuNames=['a','b','c'];par.menuLabels=['A','B','C'];par.val=1
        else:
            par=page.appendFloat(name)[0];par.min=par.normMin=0;par.max=par.normMax=1;par.val=.37
        if i==0:par.bindExpr='me.par.Master'
        controller.AssignParameter('knob',i+1,par)
    finish_configure()


def finish_configure():
    holder=op(FIXTURE);controller=holder.op('roto_python')
    model=controller.op('inspector/inspector_model')
    commands=model.op('base_commands/InspectorCommands')
    assert commands.text==(SOURCE/'prototypes/inspector/commands.py').read_text()
    view=controller.op('inspector/inspector_below')
    assert view.op('ui').text==(SOURCE/'prototypes/inspector/ui.py').read_text()
    for parent_node,name in [(commands.parent(),'baseline_commands'),(view,'baseline_ui')]:
        dat=parent_node.create(textDAT,name);dat.par.language='python';dat.viewer=True
        dat.text=(RESULTS/(name+'.py')).read_text();dat.nodeX=-600;dat.nodeY=-1000
    model.Sync();model.Flush()
    write('configured',dict(key=model.ActiveContext(),catalog=controller.GetControlCatalog(),
            source_hashes={name:hashlib.sha256((SOURCE/'prototypes/inspector'/name).read_bytes()).hexdigest() for name in ('commands.py','ui.py')},
            errors=holder.errors(recurse=True),process=controller.ext.RotoPythonExt._process is not None))
    print(json.dumps(dict(configured=True,key=model.ActiveContext(),controls=len(controller.GetControlCatalog()))))


def benchmark():
    holder=op(FIXTURE);c=holder.op('roto_python');model=c.op('inspector/inspector_model').ext.InspectorModel
    candidate=model._commands
    baseline=c.op('inspector/inspector_model/base_commands/baseline_commands').module.CommandService(model)
    key=model.ActiveContext();values=[holder.par['K'+str(i+1)].eval() for i in range(8)]
    timings={};counts={}
    try:
        for explicit in (False,True):
            mode='explicit' if explicit else 'default';timings[mode]={'before':[],'after':[]}
            for trial in range(12):
                for name,service in [('before',baseline),('after',candidate)] if trial%2==0 else [('after',candidate),('before',baseline)]:
                    model._commands=service
                    selected=[(key,i,model.GetToken(key,i)) for i in range(8)] if explicit else []
                    before=model.Stats()['sync_calls'];started=time.perf_counter()
                    intent=model.SnapshotIntent(key,selected)
                    elapsed=(time.perf_counter()-started)*1000
                    timings[mode][name].append(elapsed)
                    counts[mode+'_'+name]=model.Stats()['sync_calls']-before
                    assert len(intent['capture_tokens'])==8
        model._commands=candidate
        intent=model.SnapshotIntent(key)
        before=[holder.par['K'+str(i+1)].eval() for i in range(8)]
        record=model.SnapshotCommand('save',intent,'Native validation')
        assert len(record['entries'])==8
        assert [holder.par['K'+str(i+1)].eval() for i in range(8)]==before
        # Unsynced native bound definition change must expire the pending dialog.
        pending=model.SnapshotIntent(key)
        old=holder.par.K8.max;holder.par.K8.max=2
        try:
            try:model.SnapshotCommand('save',pending,'Must not save')
            except ValueError:rejected=True
            else:raise AssertionError('Stale native definition accepted')
        finally:holder.par.K8.max=old
        assert len(c.GetSnapshots())==1
        # Current value changes remain captureable without rewinding values.
        intent=model.SnapshotIntent(key);holder.par.K8.val=.7
        model.SnapshotCommand('save',intent,'Fresh values')
        assert holder.par.K8.eval()==.7 and len(c.GetSnapshots())==2
        holder.par.K8.val=values[7]
        summaries={}
        for mode,variants in timings.items():
            summaries[mode]={}
            for name,samples in variants.items():
                ordered=sorted(samples)
                summaries[mode][name]=dict(median_ms=(ordered[5]+ordered[6])/2,p95_ms=ordered[-1],samples=len(samples))
        result=dict(native=True,physical=False,project=project.name,build=app.build,counts=counts,timings=timings,
                    summary=summaries,save_no_value_writes=True,stale_native_definition_rejected=rejected,
                    value_only_confirmation=True,process=c.ext.RotoPythonExt._process is not None)
        write('snapshot_benchmark',result);print(json.dumps(result))
    finally:model._commands=candidate


def clear_checks():
    holder=op(FIXTURE);c=holder.op('roto_python');model=c.op('inspector/inspector_model').ext.InspectorModel
    view_node=c.op('inspector/inspector_below');view=view_node.ext.InspectorView
    old_action=view_node.op('baseline_ui').module.InspectorView.Action
    candidate=model._commands
    baseline=c.op('inspector/inspector_model/base_commands/baseline_commands').module.CommandService(model)
    results={}
    try:
        for name,service,action in [('before',baseline,old_action),('after',candidate,type(view).Action)]:
            model._commands=service
            c.AssignParameter('knob',8,holder.par.K8);model.Sync();model.Flush()
            view.CloseEditor();assert action(view,'slot7')
            id=model.Info(model.ActiveContext(),7)['id']
            assert action(view,'clear')
            assert any(r['id']==id for r in c.GetControlCatalog())
            before=model.Stats()['sync_calls'];start=time.perf_counter()
            assert action(view,'clear')
            results[name]=dict(syncs=model.Stats()['sync_calls']-before,elapsed_ms=(time.perf_counter()-start)*1000)
            assert not any(r['id']==id for r in c.GetControlCatalog())
            assert not action(view,'clear')
        model._commands=candidate
        c.AssignParameter('knob',8,holder.par.K8);model.Sync();model.Flush()
        view.CloseEditor();view.Action('slot7');assert view.Action('clear')
        id=model.Info(model.ActiveContext(),7)['id']
        # Actual native model/command, controlled runtime touch injection.
        host=c.ext.RotoPythonExt._host;control=host.controls[('knob',8)]
        control.touched=True;host._sync();c.ext.RotoPythonExt._publish()
        try:
            assert not view.Action('clear')
            assert any(r['id']==id for r in c.GetControlCatalog())
        finally:control.touched=False;host._sync();c.ext.RotoPythonExt._publish()
        results['touch_between_clicks_rejected']=True
        view.CloseEditor();model.Sync();model.Flush()
        c.op('inspector/owned_runtime').module.open_inspector(c)
        assert view_node.op('window_main').isOpen
        write('clear_checks',dict(native=True,physical=False,results=results,errors=holder.errors(recurse=True)))
        print(json.dumps(results))
    finally:model._commands=candidate


def export_fixture():
    holder=op(FIXTURE);c=holder.op('roto_python')
    c.op('inspector/owned_runtime').module.quiesce(c)
    for name in ('inspector_below','inspector_popup'):
        view=c.op('inspector/'+name)
        view.op('window_main').par.winclose.pulse();view.op('window_editor').par.winclose.pulse()
    path=RESULTS/'validated_fixture.tox'
    assert not path.exists()
    holder.save(str(path),createFolders=True)
    write('fixture_artifact',dict(path=str(path),bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    print(json.dumps(dict(exported=str(path))))


def reload_fixture():
    parent_comp=op(ROOT)
    loaded=parent_comp.loadTox(str(RESULTS/'validated_fixture.tox'))
    assert loaded!=op(FIXTURE)
    loaded.nodeX=900;loaded.nodeY=-650;loaded.viewer=True
    c=loaded.op('roto_python');m=c.op('inspector/inspector_model').ext.InspectorModel
    c.op('inspector/owned_runtime').module.validate(c)
    assert m.adapter.controller==c and c.ext.RotoPythonExt._process is None
    assert c.op('inspector/inspector_model/base_commands/InspectorCommands').text==(SOURCE/'prototypes/inspector/commands.py').read_text()
    assert c.op('inspector/inspector_below/ui').text==(SOURCE/'prototypes/inspector/ui.py').read_text()
    assert len(c.GetSnapshots())==2
    key=m.ActiveContext();candidate=m._commands
    baseline=c.op('inspector/inspector_model/base_commands/baseline_commands').module.CommandService(m)
    samples={'before':[],'after':[]}
    try:
        for trial in range(12):
            for name,service in [('before',baseline),('after',candidate)] if trial%2==0 else [('after',candidate),('before',baseline)]:
                m._commands=service;token=m.GetToken(key,0)
                started=time.perf_counter();intent=m.SnapshotIntent(key,[(key,0,token)])
                samples[name].append((time.perf_counter()-started)*1000)
                assert len(intent['capture_tokens'])==1
        m._commands=candidate
        assert len(c.GetSnapshots())==2
        result=dict(native=True,physical=False,path=loaded.path,source_parity=True,local_ownership=True,
                    snapshots_restored=2,disconnected=not c.op('base_state').par.Connected.eval(),errors=loaded.errors(recurse=True),
                    one_knob_samples_ms=samples,one_knob_median_ms={name:(sorted(v)[5]+sorted(v)[6])/2 for name,v in samples.items()})
        write('reload_fixture',result);print(json.dumps(result))
    finally:m._commands=candidate


def finish():
    main=op(ROOT+'/roto_python')
    before=json.loads((RESULTS/'main_before.json').read_text())
    after=json.loads(json.dumps(snapshot(main),default=str))
    assert after==before,'Original main controller changed'
    fixtures=[n for n in op(ROOT).children if n.name.startswith('base_validation_fixture')]
    assert len(fixtures)==2
    for holder in fixtures:
        c=holder.op('roto_python')
        assert c.ext.RotoPythonExt._process is None
        c.op('inspector/owned_runtime').module.quiesce(c)
        c.Disconnect()
        for name in ('inspector_below','inspector_popup'):
            view=c.op('inspector/'+name)
            view.op('window_main').par.winclose.pulse();view.op('window_editor').par.winclose.pulse()
        holder.destroy()
    assert not any(n.name.startswith('base_validation_fixture') for n in op(ROOT).children)
    assert json.loads(json.dumps(snapshot(main),default=str))==before
    main.op('inspector/owned_runtime').module.open_inspector(main)
    for pane in ui.panes:
        if pane.type=='NETWORKEDITOR':pane.owner=op(ROOT)
    write('finish',dict(native=True,main_preserved=True,fixtures_removed=True,main_inspector_open=True,
                        project=project.name,errors=op(ROOT).errors(recurse=True)))
    print(json.dumps(dict(main_preserved=True,fixtures_removed=True,project=project.name)))
