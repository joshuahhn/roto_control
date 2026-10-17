"""Install the MIX source slice on a disconnected, otherwise current controller.

Call install(controller, source_dir) in native TD after making a recovery .tox.
This does not rebuild Inspector, create audio processing or connect hardware.
"""
from pathlib import Path


def install(controller, source_dir):
    extension = controller.ext.RotoPythonExt
    if extension._process is not None:
        raise ValueError('Disconnect before MIX upgrade')
    source = Path(source_dir) / 'code/py/roto_python'
    names = ('midi_queue', 'mix_descriptor', 'mix_runtime', 'RotoPythonExt', 'lifecycle_callbacks')
    texts = {name: (source / (name + '.py')).read_text(encoding='utf-8') for name in names}
    if getattr(extension, '_layouts', None) is not None:
        extension._layouts.capture(force=True)
    if getattr(extension, '_follow', None) is not None:
        extension._follow.refresh_links()
    for index, name in enumerate(names):
        node = controller.op(name)
        if node is None:
            node = controller.create('textDAT', name)
            node.nodeX, node.nodeY = -600, -170 * (index + 1)
        node.viewer = True
        node.par.language = 'python'
        node.par.syncfile = False; node.par.loadonstart = False; node.par.file = ''
        node.text = texts[name]
    nodes = [controller.op(name) for name in names[:3]]
    groups = [n for n in controller.ops('*', includeUtility=True)
              if n.OPType == 'annotateCOMP' and n.fetch('roto_network_group', False)
              and n.par.Titletext.eval() == 'MIX']
    group = groups[0] if groups else controller.create('annotateCOMP', 'annotate_mix')
    for duplicate in groups[1:]:
        duplicate.destroy()
    group.store('roto_network_group', True)
    # Annotate's initialization script chooses its own name; set it afterward.
    group.name = 'annotate_mix'
    group.viewer = True
    group.par.Mode = 'annotate'; group.par.Titletext = 'MIX'
    group.utility = False
    group.nodeX = min(n.nodeX for n in nodes) - 25
    group.nodeY = min(n.nodeY for n in nodes) - 25
    group.nodeWidth = max(n.nodeX + n.nodeWidth for n in nodes) - group.nodeX + 25
    group.nodeHeight = max(n.nodeY + n.nodeHeight for n in nodes) - group.nodeY + 60
    controller.initializeExtensions(0)
    if controller.Applybinding() is False:
        raise RuntimeError('MIX upgrade binding restore failed')
    return controller
