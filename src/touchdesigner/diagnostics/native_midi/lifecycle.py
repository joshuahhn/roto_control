"""Arm only in the explicitly launched diagnostic process; never in production."""
import json
import os
from pathlib import Path
import time


def onFrameStart(frame):
    directory = os.environ.get('ROTO_NATIVE_PROBE_DIR')
    if not directory:
        return
    directory = Path(directory)
    if parent().fetch('probe_ready', False):
        if (directory / 'capture.request').exists() and not (directory / 'td_capture.json').exists():
            incoming = parent().op('midi_in')
            (directory / 'td_capture.json').write_text(json.dumps(dict(
                table=incoming.text, errors=incoming.errors(), warnings=incoming.warnings())))
        return
    started = parent().fetch('probe_started', None)
    if started is None:
        ui.openMIDIDeviceMapper()
        parent().store('probe_started', time.monotonic())
        return
    if time.monotonic() - started < 1:
        return
    incoming = parent().op('midi_in')
    incoming.par.bytes = os.environ.get('ROTO_NATIVE_PROBE_BYTES', '1') == '1'
    incoming.par.active = True
    incoming.cook(force=True)
    (directory / 'td_ready.json').write_text(json.dumps(dict(
        pid=os.getpid(), build=app.build, version=app.version,
        inputs=op('/local/midi/midi_inputs').text,
        device=parent().op('devices').text,
        errors=incoming.errors(), warnings=incoming.warnings())))
    parent().store('probe_ready', True)
