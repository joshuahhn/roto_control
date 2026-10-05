"""Observe Pulse actions without extra controller custom parameters."""
def onPulse(par):
    state = parent.ControlsDemo.op('pulse_events')
    state[par.name, 'count'] = int(state[par.name, 'count']) + 1
