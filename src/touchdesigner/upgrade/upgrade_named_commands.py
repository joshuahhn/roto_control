"""Embed named commands in place after project, ownership and recovery checks.

Run install from live TD with exact expected_project and a new recovery .tox.
The existing owned Inspector is quiesced and restored; no nodes are rebuilt.
"""
import hashlib
from pathlib import Path

RUNTIME_NAMES = ('protocol', 'midi_queue', 'collection_protocol', 'free_learn',
                 'layouts', 'text_comp_follow', 'mix_runtime', 'RotoPythonExt')
SOURCE_PATHS = {name: 'code/py/roto_python/' + name + '.py' for name in RUNTIME_NAMES}
SOURCE_PATHS['serial_read_process'] = 'scripts/serial_read_process.py'


def _check_imports(controller):
    protocol = controller.op('protocol').module
    for name in RUNTIME_NAMES[1:]:
        module = controller.op(name).module
        if module.SysExCommand is not protocol.SysExCommand:
            raise RuntimeError('Named command import is stale: ' + name)
    collection = controller.op('collection_protocol').module
    if collection.Host is not protocol.Host:
        raise RuntimeError('Collection Host import is stale')
    for name in ('collection_protocol', 'free_learn'):
        module = controller.op(name).module
        if (module.learn_parameter_message is not protocol.learn_parameter_message
                or module.LearnParameter is not protocol.LearnParameter):
            raise RuntimeError('LEARN import is stale: ' + name)
    return protocol


def install(controller, source_dir, *, expected_project, recovery_path):
    name = project.name if project.name.endswith('.toe') else project.name + '.toe'
    current = (Path(project.folder)/name).resolve()
    if current != Path(expected_project).resolve():
        raise ValueError('Active project does not match expected_project')
    extension = controller.ext.RotoPythonExt
    if extension.ownerComp != controller:
        raise ValueError('Controller extension belongs to another component')
    hardware = getattr(extension, '_hardware_config', None)
    if extension._process is not None or hardware is not None and hardware.active:
        raise ValueError('Disconnect MIDI and finish Serial cleanup before installing')
    wrapper = controller.op('inspector')
    if wrapper is None or wrapper.op('owned_runtime') is None:
        raise ValueError('Existing owned Inspector is required')
    lifecycle = wrapper.op('owned_runtime').module
    _, model, views = lifecycle.validate(controller)
    root = Path(source_dir).resolve()
    sources = {controller.op(name): root/relative for name, relative in SOURCE_PATHS.items()}
    if None in sources or len(sources) != len(SOURCE_PATHS):
        raise ValueError('Required local command source DAT is missing')
    if any(node.OPType != 'textDAT' for node in sources):
        raise ValueError('Command sources must be existing local text DATs')
    texts = {node: path.read_text(encoding='utf-8') for node, path in sources.items()}
    for node, text in texts.items():
        compile(text, str(sources[node]), 'exec')
    recovery = Path(recovery_path).resolve()
    if recovery.exists() or recovery.suffix != '.tox' or not recovery.parent.is_dir():
        raise ValueError('Provide a new recovery .tox path in an existing directory')
    windows = [view.op(name) for view in views for name in ('window_main', 'window_editor')]
    if None in windows:
        raise ValueError('Owned Inspector windows are missing')
    opened = [window for window in windows if window.isOpen]
    controller.save(str(recovery))
    if not recovery.is_file() or not recovery.stat().st_size:
        raise RuntimeError('Recovery export did not produce a file')
    if getattr(extension, '_layouts', None) is not None:
        extension._layouts.capture(force=True)
    lifecycle.quiesce(controller)
    extension._cancel_inspector_refresh()
    for node, text in texts.items():
        node.par.syncfile = False; node.par.loadonstart = False; node.par.file = ''
        node.par.language = 'python'; node.text = text
    for name in RUNTIME_NAMES:
        controller.op(name).module
    controller.initializeExtensions(0)
    if controller.Applybinding() is False:
        raise RuntimeError('Controller binding restoration failed')
    protocol = _check_imports(controller)
    if protocol.SysExCommand.DAW_STARTED.message() != (240, 0, 34, 3, 2, 10, 1, 247):
        raise RuntimeError('Named command wire smoke failed')
    for node, text in texts.items():
        if node.text != text:
            raise RuntimeError('Installed command source differs: ' + node.path)
    wrapper.op('owned_runtime').module.initialize(controller)
    controller.ext.RotoPythonExt._publish_inspector(force=True)
    for window in opened:
        window.par.winopen.pulse()
    wrapper.op('owned_runtime').module.validate(controller)
    wrapper.unstore('owned_inspector_sources')
    return dict(project=str(current), controller=controller.path, recovery=str(recovery),
                source_paths={node.path: str(path) for node, path in sources.items()},
                hashes={node.path: hashlib.sha256(node.text.encode()).hexdigest() for node in sources},
                module_order=list(RUNTIME_NAMES), restored_windows=[window.path for window in opened])
