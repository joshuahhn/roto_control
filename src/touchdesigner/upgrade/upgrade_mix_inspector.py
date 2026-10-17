import hashlib
from pathlib import Path

CONTROLLER_SOURCES=('mix_runtime','RotoPythonExt')
INSPECTOR_SOURCES=('inspector_data','owned_runtime')


def install(controller,source_dir,*,expected_project,recovery_path):
    name=project.name if project.name.endswith('.toe') else project.name+'.toe'
    current=(Path(project.folder)/name).resolve()
    if current!=Path(expected_project).resolve():
        raise ValueError('Active project does not match expected_project')
    extension=controller.ext.RotoPythonExt
    if extension.ownerComp!=controller:raise ValueError('Controller extension belongs to another component')
    hardware=getattr(extension,'_hardware_config',None)
    if extension._process is not None or hardware is not None and hardware.active:
        raise ValueError('Disconnect MIDI and finish Serial cleanup before installing')
    wrapper=controller.op('inspector')
    if wrapper is None or wrapper.op('owned_runtime') is None:
        raise ValueError('Existing owned Inspector is required')
    lifecycle=wrapper.op('owned_runtime').module
    _,model,views=lifecycle.validate(controller)
    root=Path(source_dir).resolve()
    sources={controller.op(name):root/'code/py/roto_python'/f'{name}.py' for name in CONTROLLER_SOURCES}
    sources.update({wrapper.op(name):root/'code/py/roto_python/inspector'/f'{name}.py' for name in INSPECTOR_SOURCES})
    sources[model.op('live_model')]=root/'prototypes/inspector/live_model.py'
    for view in views:sources[view.op('ui')]=root/'prototypes/inspector/ui.py'
    if None in sources or len(sources)!=7 or any(node.OPType!='textDAT' for node in sources):
        raise ValueError('Required local MIX Inspector source DAT is missing or has wrong type')
    texts={node:path.read_text(encoding='utf-8') for node,path in sources.items()}
    for node,text in texts.items():compile(text,str(sources[node]),'exec')
    helper_path=root/'build/build_mix_inspector.py'
    helper={};exec(compile(helper_path.read_text(encoding='utf-8'),str(helper_path),'exec'),helper)
    for view in views:helper['validate'](view)
    windows=[view.op(name) for view in views for name in ('window_main','window_editor')]
    if None in windows or any(window.OPType!='windowCOMP' for window in windows):
        raise ValueError('Owned Inspector windows are missing or have wrong type')
    opened=[window for window in windows if window.isOpen]
    recovery=Path(recovery_path).resolve()
    if recovery.exists() or recovery.suffix!='.tox' or not recovery.parent.is_dir():
        raise ValueError('Provide a new recovery .tox path in an existing directory')
    controller.save(str(recovery))
    if not recovery.is_file() or not recovery.stat().st_size:
        raise RuntimeError('Recovery export did not produce a file')
    if getattr(extension,'_layouts',None) is not None:extension._layouts.capture(force=True)
    lifecycle.quiesce(controller);extension._cancel_inspector_refresh()
    for node,text in texts.items():
        node.par.syncfile=False;node.par.loadonstart=False;node.par.file=''
        node.par.language='python';node.text=text
    for view in views:helper['install'](view)
    runtime=controller.op('mix_runtime').module
    controller_module=controller.op('RotoPythonExt').module
    if controller_module.MixRuntime is not runtime.MixRuntime or controller_module.inspection is not runtime.inspection:
        raise RuntimeError('MIX runtime import is stale')
    controller.initializeExtensions(0)
    if controller.Applybinding() is False:raise RuntimeError('Controller binding restoration failed')
    wrapper.op('owned_runtime').module.initialize(controller)
    controller.ext.RotoPythonExt._publish_inspector(force=True)
    wrapper.op('owned_runtime').module.validate(controller)
    for node,text in texts.items():
        if node.text!=text:raise RuntimeError('Installed MIX Inspector source differs: '+node.path)
    for view in views:
        if type(view.ext.InspectorView) is not view.op('ui').module.InspectorView:
            raise RuntimeError('MIX Inspector view extension is stale')
        helper['validate'](view)
    if type(model.ext.InspectorModel) is not model.op('live_model').module.InspectorModel:
        raise RuntimeError('MIX Inspector model extension is stale')
    for window in opened:window.par.winopen.pulse()
    wrapper.unstore('owned_inspector_sources')
    return dict(project=str(current),controller=controller.path,recovery=str(recovery),
                source_paths={node.path:str(path) for node,path in sources.items()},
                hashes={node.path:hashlib.sha256(node.text.encode()).hexdigest() for node in sources},
                restored_windows=[window.path for window in opened])
