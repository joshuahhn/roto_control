"""One event-driven watcher per registered hardware control."""
def key():
    name = me.name.removeprefix('watch_')
    return ('knob' if name.startswith('knob') else 'button', int(name[-1]))


def onValueChange(par, prev):
    parent.RotoPython.ext.RotoPythonExt.onControlChange(key(), par)


def onPulse(par):
    parent.RotoPython.ext.RotoPythonExt.onControlChange(key(), par, pulse=True)
