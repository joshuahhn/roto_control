"""External MIDI owner. Complete MIDI messages cross JSON-line pipes, not TD MIDI.

The parent owns lifetime: stdin EOF or SIGTERM closes both hardware ports.
"""

import argparse
import json
import os
import signal
import sys
import time

import mido


def emit(event):
    print(json.dumps(event), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="Roto-Control")
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()
    mido.set_backend("mido.backends.rtmidi")
    if args.list:
        emit({"inputs": mido.get_input_names(), "outputs": mido.get_output_names()})
        return
    if args.device not in mido.get_input_names() or args.device not in mido.get_output_names():
        raise RuntimeError(f"Exact MIDI input/output {args.device!r} unavailable")
    running = True

    def stop(*_):
        nonlocal running
        running = False

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    os.set_blocking(sys.stdin.fileno(), False)
    pending = b""
    with mido.open_input(args.device) as incoming, mido.open_output(args.device) as outgoing:
        emit({"ready": True})
        while running:
            for _ in range(256):
                message = incoming.poll()
                if message is None:
                    break
                emit({"midi": message.bytes()})
            try:
                chunk = os.read(sys.stdin.fileno(), 65536)
            except BlockingIOError:
                chunk = None
            if chunk == b"":
                break
            if chunk:
                pending += chunk
                if len(pending) > 262144:
                    raise ValueError("Parent command buffer exceeded limit")
                while b"\n" in pending:
                    line, pending = pending.split(b"\n", 1)
                    command = json.loads(line)
                    outgoing.send(mido.Message.from_bytes(command["midi"]))
            time.sleep(0.002)  # child process only; never blocks TD's cook thread


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        emit({"error": str(exc)})
        raise SystemExit(1) from exc
