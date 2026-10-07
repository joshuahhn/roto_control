"""Execute in live TD to export an inactive input-only probe for a NEW process."""
from pathlib import Path


def build(parent_comp, source_dir, destination):
    source = Path(source_dir)
    if parent_comp.op('base_native_midi_probe') is not None:
        raise ValueError('Existing native probe must be removed first')
    base = parent_comp.create(baseCOMP, 'base_native_midi_probe')
    base.viewer = base.display = True
    base.par.parentshortcut = 'NativeMidiProbe'
    base.nodeX, base.nodeY = 2400, 0
    try:
        for name, kind, x, y in (
            ('devices', tableDAT, 0, 0),
            ('midi_callbacks', textDAT, 175, -125),
            ('midi_in', midiinDAT, 175, 0),
            ('lifecycle', executeDAT, 350, -125),
        ):
            node = base.create(kind, name)
            node.viewer = True
            node.nodeX, node.nodeY = x, y
        base.op('devices').clear()
        base.op('devices').appendRow(['id', 'indevice', 'outdevice', 'definition', 'channel'])
        base.op('devices').appendRow(['1', 'ROTO Native Probe', 'None', '', '1'])
        incoming = base.op('midi_in')
        incoming.par.active = False
        incoming.par.device = 'devices'
        incoming.par.id = '1'
        incoming.par.value14 = False
        incoming.par.filter = False
        incoming.par.bytes = True
        incoming.par.callbacks = 'midi_callbacks'
        incoming.par.maxlines = 256
        for name in ('midi_callbacks', 'lifecycle'):
            dat = base.op(name)
            dat.par.language = 'python'
            dat.text = (source / (name + '.py')).read_text()
        base.op('lifecycle').par.framestart = True
        base.save(str(destination))
        return str(destination)
    finally:
        base.destroy()
