"""Add Serial Details in place after exact project and local ownership checks."""
from pathlib import Path


def install(controller, source_dir, *, expected_project, recovery_path):
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
    sources={controller.op('RotoPythonExt'):root/'code/py/roto_python/RotoPythonExt.py',
             wrapper.op('inspector_data'):root/'code/py/roto_python/inspector/inspector_data.py',
             wrapper.op('owned_runtime'):root/'code/py/roto_python/inspector/owned_runtime.py',
             model.op('live_model'):root/'prototypes/inspector/live_model.py',
             model.op('base_commands/parity'):root/'prototypes/inspector/parity.py'}
    editors=[]
    for view in views:
        sources[view.op('ui')]=root/'prototypes/inspector/ui.py'
        sources[view.op('parity')]=root/'prototypes/inspector/parity.py'
        popup=view.op('base_popup/editor_popup') or view.op('editor_popup')
        local=(view.op('container_scroll/container_content/editor_below'),popup.op('container_editor_content') if popup is not None else None)
        if None in local or tuple(view.ext.InspectorView._editors)!=local:
            raise ValueError('Inspector editors are not the current local components')
        editors.extend(local)
    if None in sources or len(editors)!=4:
        raise ValueError('Required local Inspector sources/editors are missing')
    texts={node:path.read_text(encoding='utf-8') for node,path in sources.items()}
    for node,text in texts.items():compile(text,str(sources[node]),'exec')
    namespace={'__name__':'inspector_hardware_builder'}
    path=root/'prototypes/inspector/build_parity.py'
    exec(compile(path.read_text(encoding='utf-8'),str(path),'exec'),namespace)
    parity={};exec((root/'prototypes/inspector/parity.py').read_text(encoding='utf-8'),parity)
    namespace['DETAIL_GROUPS']=parity['DETAIL_GROUPS']
    for editor in editors:
        if editor.op('container_details/container_readout/container_info') is None:
            raise ValueError('Existing Details content is missing')
    recovery=Path(recovery_path).resolve()
    if recovery.exists() or recovery.suffix!='.tox' or not recovery.parent.is_dir():
        raise ValueError('Provide a new recovery .tox path in an existing directory')
    windows=[view.op(name) for view in views for name in ('window_main','window_editor')]
    opened=[window for window in windows if window.isOpen]
    controller.save(str(recovery))
    if not recovery.is_file() or not recovery.stat().st_size:
        raise RuntimeError('Recovery export did not produce a file')
    if getattr(extension,'_layouts',None) is not None:extension._layouts.capture(force=True)
    lifecycle.quiesce(controller)
    extension._cancel_inspector_refresh()
    for node,text in texts.items():
        node.par.syncfile=False;node.par.loadonstart=False;node.par.file='';node.par.language='python'
        node.text=text
    for editor in editors:namespace['install_hardware_snapshot'](editor)
    controller.initializeExtensions(0)
    if controller.Applybinding() is False:raise RuntimeError('Controller binding restoration failed')
    wrapper.op('owned_runtime').module.initialize(controller)
    controller.ext.RotoPythonExt._publish_inspector(force=True)
    for window in opened:window.par.winopen.pulse()
    wrapper.op('owned_runtime').module.validate(controller)
    wrapper.unstore('owned_inspector_sources')
    return wrapper
