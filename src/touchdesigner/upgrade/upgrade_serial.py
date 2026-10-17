"""Install read-only Serial capture into an otherwise current disconnected controller.

Call install(controller, source_dir) after retaining a recovery .tox.
Mappings, settings, registration hooks and parameter values remain intact.
"""
from pathlib import Path


def install(controller, source_dir):
    extension = controller.ext.RotoPythonExt
    hardware = getattr(extension, '_hardware_config', None)
    if extension._process is not None or hardware is not None and hardware.active:
        raise ValueError('Disconnect MIDI and finish or disconnect Serial before upgrading')
    root = Path(source_dir).resolve()
    paths = {name: root/'code/py/roto_python'/f'{name}.py'
             for name in ('hardware_config', 'RotoPythonExt', 'layouts')}
    paths['serial_read_process'] = root/'scripts/serial_read_process.py'
    texts = {name: path.read_text(encoding='utf-8') for name, path in paths.items()}
    for name, text in texts.items():
        compile(text, str(paths[name]), 'exec')
    if getattr(extension, '_layouts', None) is not None:
        extension._layouts.capture(force=True)
    if hardware is not None:
        hardware.close('Serial source upgraded')
    if getattr(extension, '_follow', None) is not None:
        extension._follow.refresh_links()
    positions = {'hardware_config': (-800, -170), 'serial_read_process': (-800, -340)}
    for name, text in texts.items():
        node = controller.op(name)
        if node is None:
            node = controller.create('textDAT', name)
            if name in positions:
                node.nodeX, node.nodeY = positions[name]
        node.par.language = 'python'
        node.par.syncfile = False; node.par.loadonstart = False; node.par.file = ''
        node.text = text
        node.viewer = True
    controller.initializeExtensions(0)
    if controller.Applybinding() is False:
        raise RuntimeError('Serial upgrade binding restoration failed')
    return controller
