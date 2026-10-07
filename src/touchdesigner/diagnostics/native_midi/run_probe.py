"""Compare native TD receive with independent rtmidi receive on a virtual source.

No hardware ports are opened. Run with the MIDI venv after exporting probe.tox.
The diagnostic TD process is owned, bounded and terminated by this runner.
"""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import subprocess
import time

import mido


def compare(expected, received):
    # TD may emit a separate End-of-System-Exclusive row for the F7 delimiter.
    messages = [packet for packet in received if packet not in ([0xF7], [0xF7, 0, 0])]
    wanted, actual = Counter(map(tuple, expected)), Counter(map(tuple, messages))
    return dict(exact_order=messages == expected,
                missing=[list(p) for p in (wanted - actual).elements()],
                unexpected=[list(p) for p in (actual - wanted).elements()],
                events=len(received))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--td', default='/Applications/TouchDesigner.app/Contents/MacOS/TouchDesigner')
    parser.add_argument('--probe', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--traffic', choices=['mixed', 'sysex', 'cc', 'ping'], default='mixed')
    parser.add_argument('--bytes-off', action='store_true')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    packets = [list(bytes.fromhex(line)) for line in
               Path(__file__).with_name('fixture_packets.txt').read_text().splitlines()]
    controls = [[0xBF, 12, 64], [0xBF, 44, 0], [0xBF, 20, 1]]
    if args.traffic == 'mixed':
        packets += controls
    elif args.traffic == 'cc':
        packets = controls
    elif args.traffic == 'ping':
        packets = packets[:1]
    process = None
    mido.set_backend('mido.backends.rtmidi')
    try:
        with mido.open_output('ROTO Native Probe', virtual=True) as outgoing:
            names = [name for name in mido.get_input_names() if 'ROTO Native Probe' in name]
            if len(names) != 1:
                raise RuntimeError('Unique diagnostic source not found: ' + repr(names))
            with mido.open_input(names[0]) as incoming:
                env = dict(os.environ, ROTO_NATIVE_PROBE_DIR=str(args.output.absolute()),
                           ROTO_NATIVE_PROBE_BYTES='0' if args.bytes_off else '1')
                with (args.output / 'td_stdout.log').open('w') as log:
                    process = subprocess.Popen([args.td, str(args.probe.absolute())], env=env,
                                               stdout=log, stderr=subprocess.STDOUT)
                    deadline = time.monotonic() + 35
                    while not (args.output / 'td_ready.json').exists():
                        if process.poll() is not None or time.monotonic() > deadline:
                            raise RuntimeError('Diagnostic TD did not become ready')
                        time.sleep(.1)
                    ready = json.loads((args.output / 'td_ready.json').read_text())
                    if ready['errors'] or ready['warnings']:
                        raise RuntimeError('Native probe could not open its input: ' + repr(ready))
                    time.sleep(.8)
                    for packet in packets:
                        outgoing.send(mido.Message.from_bytes(packet))
                        time.sleep(.01)
                    time.sleep(2)
                    (args.output / 'capture.request').touch()
                    deadline = time.monotonic() + 3
                    while not (args.output / 'td_capture.json').exists() and time.monotonic() < deadline:
                        time.sleep(.05)
                    if not (args.output / 'td_capture.json').exists():
                        with (args.output / 'native_sample.txt').open('w') as sample:
                            subprocess.run(['/usr/bin/sample', str(ready['pid']), '1'],
                                           stdout=sample, stderr=subprocess.STDOUT, timeout=8)
                    reference = [message.bytes() for message in incoming.iter_pending()]
                    event_file = args.output / 'td_events.jsonl'
                    events = [json.loads(line) for line in event_file.read_text().splitlines()] if event_file.exists() else []
                    native = [event['bytes'] for event in events]
                    result = dict(expected=packets, reference=reference,
                                  reference_exact=reference == packets,
                                  native=compare(packets, native),
                                  td=ready, traffic=args.traffic, bytes_column=not args.bytes_off,
                                  responsive=(args.output / 'td_capture.json').exists())
                    (args.output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
                    print(json.dumps(dict(reference_exact=result['reference_exact'],
                                          native_exact=result['native']['exact_order'],
                                          missing=len(result['native']['missing']),
                                          unexpected=len(result['native']['unexpected']),
                                          events=len(native), responsive=result['responsive'], td=ready)))
                    return 0 if result['reference_exact'] and result['native']['exact_order'] and result['responsive'] else 1
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)


if __name__ == '__main__':
    raise SystemExit(main())
