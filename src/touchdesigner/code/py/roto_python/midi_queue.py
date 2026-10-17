"""Filter complete unsent MIDI frames, retaining any transmitted frame tail."""
import json


def discard(pending, predicate):
    kept = []
    for line in pending.splitlines(keepends=True):
        try:
            if not line.endswith(b'\n'):
                raise ValueError('Incomplete frame')
            message = json.loads(line)['midi']
        except (ValueError, KeyError, TypeError):
            kept.append(line)
            continue
        if not predicate(message):
            kept.append(line)
    return b''.join(kept)


def business_output(message):
    """Both modes own Track metadata, motor, text and meter output."""
    if len(message) == 3 and message[0] == 191:
        return True
    return (len(message) >= 8 and tuple(message[:5]) == (240, 0, 34, 3, 2)
            and (message[5] != 10 or message[6] not in (1, 3)))
