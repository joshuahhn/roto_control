# Optional Serial read-back feasibility

Status: first read-only integration implemented and hardware-read verified, 2026-10-18.
Tracks [issue #7](https://github.com/joshuahhn/roto_control/issues/7).
The [Serial API contract](../functions/serial.md) describes the implemented slice.
The investigation below records its grounding. Later integration evidence is at
the end of this document and in the latest HANDOFF entry.

## Reuse the old transport core

The user identifies `nin-lab/roto_control` as the unfinished Serial reference.
The local source is under `nin-lab/td_projects/roto_control/scripts/serial`, at
nin-lab commit `52a5f09a1381d66524de7f0d6ae9436ca6208343` with a clean working tree.
Its `roto_protocol.py` provides the command encoder and firmware/mode decoders.
`roto_queue.py` frames replies and asynchronous notifications with one command
outstanding. ZERROR's `code/py/roto_surface/RotoSerialRuntime.py` already adapts
that queue to a nonblocking, callback-based runtime outside native Serial DATs.

These are useful references, not acceptance of the whole unfinished plugin.
The old config parser handles MIDI setup payloads. Its 239-byte config layout
does not match the PLUGIN knob/switch replies verified below. Do not pass a
PLUGIN response into that parser, even though its minimum-length check can
accept the longer packet. The old extension also contains config writes,
presets, automatic reconnect and setup/session behavior outside this issue's
read-only scope.

The prototype imports the three reference files without modifying them and
disables Python bytecode writes. A send-boundary allowlist admits only firmware,
mode, PLUGIN knob GET and PLUGIN switch GET. It does not run old builders,
extensions, preset workflows or archived projects. Nine existing SerialRuntime
tests pass, covering fragmented frames, notifications, timeout invalidation,
partial sends and lifecycle behavior. That is scoped transport evidence.

## Serial identity can match the current MIDI host

The current host announces an eight-byte digest of the Plugin `device_id`.
Each control has a separate mapped parameter index and six-byte digest of its
complete wire identity. The digest uses SHA-1 bytes masked with `127`, not a
hexadecimal string. Saved Menu semantics and explicit parameter indices matter;
the display name, slot or current TD path alone cannot establish a match.

The [Serial API v1.3](../../../../docs/ROTO-CONTROL_SERIAL_API_v1.3.pdf),
sections 4.9 and 4.10, supplies the queried Plugin hash, control index, mapped
parameter index and mapped parameter hash in a successful reply. That allows
read-back to confirm the stored control against the current host definition.
The [SysEx API v1.6](../../../../docs/ROTO-CONTROL_SYSEX_API_v1.6.pdf),
sections 3.5 and 3.11, describes the corresponding Plugin/control identity
fields. The two transports use different packet layouts and index encodings.

The native port inventory identifies two CDC serial endpoints under the same
Melbourne Instruments Roto-Control USB device. On this machine,
`/dev/cu.usbmodem1101` answers firmware and mode GET. Firmware is 3.3.0,
commit `eaa37b0`; mode is PLUGIN and the page offset is zero.
`/dev/cu.usbmodem1103` gives no firmware reply within the bounded probe.
This result identifies the working endpoint in this session. It does not define
a permanent port suffix or the other endpoint's purpose.

## Actual stored control read-back

The reference encoder, queue and SerialRuntime complete six GETs on the Config
endpoint: firmware, mode and the four existing demo_A controls. The MIDI helper
stays disconnected. No START/END CONFIG UPDATE, SET, CLEAR, LEARN or firmware
commands are sent. Port settings are restored and file descriptors are closed.

All four replies match the requested Plugin hash, control index, mapped parameter
index and six-byte host parameter hash. Native read-back reports:

- Knob 1, Amount, mapped index 128: haptic mode 0, smooth, with both optional
  indent positions unused.
- Knob 2, Steps, mapped index 129: haptic mode 0, smooth. Its Int target does not
  imply physically stepped haptics.
- Knob 3, Mode, mapped index 131: haptic mode 1 and three steps, with the saved
  FIRST, SECOND and THIRD labels present in the raw response.
- Button 1, Enabled, mapped index 130: Toggle mode and two labels, Off and On.

The observed PLUGIN knob replies are 250 bytes, and the switch reply is 247
bytes, including header and status. Mapped indices 128..131 use two-byte
big-endian Serial values, independently of the SysEx two-seven-bit encoding.
The stored Button 1 hash matches the restored local definition in this read.
This does not resolve the separate MIDI recall/reconciliation discrepancy.

These are actual hardware configuration reads, not inferred Menu metadata or
sent haptic offers. No physical-feel comparison, centre/top-indent case or
custom-indent case is accepted here. The prior claim that the entire old plugin
is unfinished remains valid.

## Keep optional Serial failure separate from MIDI

The recommended first integration is an explicit-refresh read-only worker with
its own lifetime. This is an architectural recommendation, not measured
coexistence acceptance. The current MIDI child only accepts MIDI JSON commands;
its errors cause the parent to disconnect MIDI. Combining optional Serial into
that child would require changing both readiness and failure ownership.

Reuse the old framing and one-outstanding-command approach behind a small
read-only boundary. Add exact PLUGIN reply decoding, request and receive caps,
late-response/session invalidation and an allowlist that cannot initiate config
writes. Publish detected values separately from declared button adapters and
inferred target semantics. A refresh result must carry the physical device,
session, Plugin identity, control identity and freshness that produced it.
Disconnect, context changes and device replacement make results stale.

The present host cannot assume an absolute PLUGIN control page from every MIDI
page-change event. This prototype deliberately reads only the observed first
page. A future integration must obtain or verify the absolute Serial page and
the mapped identities before associating results with current Inspector slots.
It must not infer a new mapping or change mapped flags from a read-back result.

Production packaging needs a portable serial transport. The scratch probe uses
macOS POSIX termios because pyserial is absent from the current external Python.
No dependency is installed. Main-thread Serial I/O, background permanent polling
and automatic connection are not part of the recommended slice.

## Protocol ambiguities remain explicit

Rendered inspection of the published PDF confirms that MIDI knob GET lists two
payload fields while its CL line says one byte. GET PLUGIN also lists an extra
type field while its stated length accounts only for the hash, and labels the
response type inconsistently. The prototype avoids both ambiguous requests.
Firmware/mode and PLUGIN knob/switch GET layouts match the observed replies.

Replies have no echoed command ID or request sequence. A response begins with
header and status; an error can finish after two bytes. Thus a new command must
not consume a delayed reply from an expired request. The old runtime closes
its logical session on timeout; a production transport must also fence and
retire that physical session before accepting another request. The old queue's
pending and receive collections need explicit bounds at the new boundary.

The API calls haptic mode 2 centre-indent in the MIDI section and top-indent in
the PLUGIN section. Preserve the mode and provenance until its physical behavior
is checked. Do not silently merge those names into a verified physical claim.

## Evidence and limits

Scratch artifacts are under system temp `roto-7-serial-j0du7uf8`. They include
USB endpoint ancestry, MIDI identity snapshots, read-only probe scripts, exact
TX/RX captures, reference source hashes and preservation results. The probe is
an investigation instrument, not production code.

Fresh before/after snapshots preserve all 4,602 original nodes, 1,281 DAT hashes,
controller storage and static values. Only the same three live Low-signal
readbacks are normalized. TD remains on the saved #28 `.20` project, open and
disconnected with empty buffers and four local definitions. Nin-lab remains
clean. No saved project/export, mapping or audio routing is changed.

Remaining acceptance includes port contention and unplug/replug, active MIDI
coexistence, stale/wrong-identity replies, Inspector freshness, actual custom
indents and other pages. No frame-cost, latency or performance claim is made
from the single observed batch. Prove It Works changed the decision from
schema-only feasibility to demonstrated read-back for these four identities;
it does not establish complete integration.

## First integration acceptance

`ReadHardwareConfig(port=...)` and `GetHardwareConfig()` now expose a separate
one-shot worker. The worker embeds its stdlib macOS transport, permits four GET
forms, verifies USB ancestry and exact PH/CI/MI/MH, and closes before publication.
The transient owner returns detached status and historical snapshots. It does
not write the catalog, Layout registry, target values, or hardware configuration.
Timeout and uncertain framing leave a marker for that USB incarnation, including
across helper or extension restart. A new verified physical incarnation is the
recovery boundary. There is no Serial write API or automatic connection.

The final source suite passes 657 tests, including real subprocess/PTY transport,
malformed and stale responses, cleanup, value-only freshness, context ABA, and
packaging. Independent review found and reproduced a terminal pipe/exit race;
the EOF regression now passes. Native acceptance exposed repeated USB names on
interface nodes and a lazy MIX token initialization that cancelled the first
read. Both have regressions. A first read immediately after the final upgrade
captures all four original controls without a retry.

Native reads match the four records listed above, including Button 1. With MIDI
connected, the three currently reconciled knob definitions also capture, and
the MIDI process remains alive. A separate process holds the actual Config port;
the API returns `port_busy`, leaves that owner alone, and preserves the MIDI
process and its error. Releasing the holder permits another four-control read.
The four complete hardware records before and after these checks are equal.
The existing MIDI recall discrepancy temporarily removes Button 1 locally;
the original four local definitions are restored disconnected. This Serial
feature does not repair or claim acceptance of that separate behavior.

Disconnect invalidates a completed snapshot and reaps a pending worker. Extension
reinit starts at `never_read`. Save/export evidence is recorded separately in
HANDOFF. A later disconnected USB unplug/replug check confirms a new physical
incarnation and a fresh capture of the same four records. Empty successful USB
inventory now produces the actionable absent-device error; 659 source tests pass.
In-flight unplug, physical timeout-retirement recovery, Roto-Setup application
contention, other pages, Windows, and physical haptic feel remain unaccepted.
Port contention uses a real FD holder. The successful snapshot does not
continuously observe subsequent external edits or USB changes.
