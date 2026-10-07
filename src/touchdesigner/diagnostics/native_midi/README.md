# Native MIDI receive retest — 2026-10-07

TD 2025.33230 on macOS; a separate input-only TD process receives a unique virtual CoreMIDI source named `ROTO Native Probe`. Production ROTO parameters, protocol host, MIDI output and hardware ports are absent from the probe. An independent mido/rtmidi input listens to the same virtual source. This isolates native receive from the current ROTO adapter.

## Reproduction

The included `probe.tox` is inactive when opened normally. It arms only in the diagnostic process launched by this runner. It uses its own device table, rather than modifying the global mapper. The runner terminates only its owned TD process and closes its virtual ports.

From `src/touchdesigner`, using the MIDI venv:

```sh
.venv/bin/python diagnostics/native_midi/run_probe.py --probe diagnostics/native_midi/probe.tox --traffic ping --output /tmp/roto_native_ping_new
```

Use a new output directory for each attempt. Exit 0 requires exact reference and native bytes/order plus a responsive TD frame callback. Exit 1 reports a receive discrepancy or unresponsive process; inspect `result.json`, callback capture and the native sample before attributing a cause. `--traffic cc`, `--traffic sysex` and `--bytes-off` isolate traffic and the Bytes Column setting.

Rebuild the inactive tox through live TD with external `build_probe.py`: `build(explicit_parent, source_directory, destination)`. The builder removes its temporary COMP after export. Callback source and lifecycle source are embedded; the runner requires external Python with mido/python-rtmidi.

## Findings

- Two initial mixed captures each received all 35 SysEx and three CC packets, but TD emitted 35 extra three-byte messages not present in the reference. Separate End-of-System-Exclusive rows (`F7 00 00`) are excluded from the discrepancy count. Extra events include invalid SysEx, CC/Note and other messages; their bytes vary between runs. Both independent references exactly match the sender.
- CC-only: all three channel-16 CC packets arrive in order, with no extra messages; native frame capture remains responsive. This proves native CC input works in the tested condition, rather than all TD MIDI being unusable.
- SysEx-only, Bytes Column On and Off: neither run produced callback events or a post-traffic frame capture. These runs were terminated; no native samples were taken, so their unresponsiveness alone is not called a confirmed native crash.
- Minimal PING, Bytes Column On: one valid `F0 00 22 03 02 0A 02 F7` reaches the independent receiver exactly, but TD produces no callback and no frame response. The sampled native stack reaches CoreMIDI `PacketizerBase` destruction, `libMIDI.dylib +0x6b10`, `OSX_CrashHandler::abortHandler` and `sigwait`. See `evidence/ping_on/`.
- Minimal PING, Bytes Column Off: responsive in this attempt, with the correct PING plus one extra unsent three-byte event. The native DAT table also reports that extra event, independently of our raw-byte capture. Bytes Column Off is therefore not a valid fix for message integrity; the earlier 35-SysEx Bytes-Off run also lost frame response.

The input-only PING reproduces the same native stack reported in the earlier Issue 53 investigation. A Python ROTO binding/metadata callback is unnecessary for this trigger. The exact native defect, signal type and relationship between extra messages and the crash remain unconfirmed. A TD parser/buffer-lifetime defect is an inference from the native boundary, not a symbolicated vendor diagnosis.

Initial harness attempts had a malformed device table and could not open MIDI; they are excluded. The corrected table and refreshed mapper give no input warnings. The cached `/local/midi/midi_inputs` DAT still contains old default-project names, so the endpoint/table warning and independent packet capture are more informative than that cached list. All runs use the existing TD user profile; no clean-profile or firmware/hardware acceptance claim is made.

## Decision

Keep the production external MIDI backend. A native CC-only path cannot supply the complete SysEx handshake, metadata and mapping messages needed by this tool. Do not add a third user-facing backend mode before the native receive regression passes. The native probe remains available for testing another TD build or a vendor fix.

Official references: [MIDI In DAT](https://docs.derivative.ca/MIDI_In_DAT) documents raw Bytes Column, the callback and 14-bit consolidation; [MIDI Mapper](https://docs.derivative.ca/MIDI_Mapper_Dialog) documents device tables and discovery/restart behavior. Both are supported native APIs; the documentation does not establish a fix for this receive failure.

The 35-packet fixture is copied from the original Issue 53 capture in `nin-lab/td_projects/roto_control/scripts/phase8/diagnostics/issue53_report/no_usb/fixture_packets.txt`. It is historical traffic replay, not a new physical acceptance test.
