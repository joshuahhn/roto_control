"""Explicit disposable native fixture entrypoints; importing never touches TD.

Execute with TD globals, PIN_SOURCE and RUN_PATH after combined source gates.
All toe/tox writes must use project.save/COMP.save in TD. No MIDI auto-connect.
"""
from pathlib import Path
import hashlib,json,shutil


def build_fixture(parent,source,python,execution_folder):
    if parent.children:raise ValueError('Use a new empty disposable fixture root')
    source=Path(source)
    # TD file-sync writes CRLF into source files. Never bind it to an immutable pin.
    execution=Path(execution_folder)
    shutil.copytree(source,execution)
    original_hashes={str(p.relative_to(source)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source.rglob('*') if p.is_file()}
    assert all(hashlib.sha256((execution/p).read_bytes()).hexdigest()==h for p,h in original_hashes.items())
    namespace=dict(globals())
    builder=source/'build_network.py'
    exec(compile(builder.read_text(),str(builder),'exec'),namespace)
    controller=namespace['build'](parent,str(execution))
    # The stock builder creates demo targets; this fixture intentionally starts empty.
    controller.ext.RotoPythonExt.BindControls([],group_id='ownership.fixture',_allow_empty=True)
    export_namespace=dict(globals())
    export_source=source/'export_component.py'
    exec(compile(export_source.read_text(),str(export_source),'exec'),export_namespace)
    export_namespace['reset_mapping_storage'](controller)
    controller.ext.RotoPythonExt._layouts=None
    controller.ext.RotoPythonExt._layout_ready=True
    controller.ext.RotoPythonExt._layout_manager()
    for child in tuple(parent.children):
        if child!=controller:child.destroy()
    controller.par.Python=python
    for dat in controller.findChildren(type=DAT):
        if hasattr(dat.par,'syncfile'):dat.par.syncfile=False
        if hasattr(dat.par,'loadonstart'):dat.par.loadonstart=False
        if hasattr(dat.par,'file'):dat.par.file=''
    assert controller.ext.RotoPythonExt._process is None
    fixture=source/'diagnostics/issue_9/native_owner_fixture.py'
    namespace=dict(globals(),__file__=str(fixture))
    exec(compile(fixture.read_text(),str(fixture),'exec'),namespace)
    evidence=namespace['run'](parent,controller)
    assert all(hashlib.sha256((source/p).read_bytes()).hexdigest()==h for p,h in original_hashes.items()),'Immutable source mirror changed'
    evidence['source_dir']=str(source)
    evidence['execution_dir']=str(execution)
    evidence['pin_unchanged_after_build']=True
    return controller,evidence


def record(name,evidence,folder):
    destination=Path(folder)/(name+'.json')
    if destination.exists():raise FileExistsError(destination)
    destination.write_text(json.dumps(evidence,indent=2,default=str)+'\n')
    return str(destination)


def source_equality(controller,source):
    source=Path(source)/'code/py/roto_python'
    result={}
    for path in source.glob('*.py'):
        dat=controller.op(path.stem)
        if dat is None:continue
        expected=path.read_text().replace('\r\n','\n');actual=dat.text.replace('\r\n','\n')
        assert actual==expected,path.name
        result[path.name]=hashlib.sha256(expected.encode()).hexdigest()
    assert all(n+'.py' in result for n in ('RotoPythonExt','layouts','free_learn','text_comp_follow'))
    return result
