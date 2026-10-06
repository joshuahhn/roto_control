"""Capture native callback bytes without any ROTO host or MIDI output."""
import json
import os
from pathlib import Path
import time


def onReceiveMIDI(dat, *args):
    if args and hasattr(args[0], 'byteData'):
        event = args[0]
        raw = list(event.byteData)
        description = str(event)
    elif len(args) >= 7:
        raw = list(args[6])
        description = str(args[1])
    else:
        raise ValueError('Unknown native MIDI callback signature')
    directory = os.environ.get('ROTO_NATIVE_PROBE_DIR')
    if directory:
        with (Path(directory) / 'td_events.jsonl').open('a') as stream:
            stream.write(json.dumps(dict(time=time.monotonic(), bytes=raw,
                                         description=description)) + '\n')
