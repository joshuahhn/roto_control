# Independent MIX view mappings

Status: design with an initial [analysis source slice](../functions/mix.md),
2026-10-17. The user selected independent MIX assignments,
then clarified the intended flow through Layer Mix, analysis and audio examples.
Selection means choosing an object, not requiring the physical SEL key:
touch selects an item and FUNC opens its details. This document does not describe
the acceptance status of every runtime feature; the linked source contract
records the implemented subset and remaining hardware checks.

The [interactive scenarios](mix-view-mappings.html) show the intended objects and
details without connecting to TD or MIDI. They are not a verified native screen.
The proposed [TD → ROTO contract v1](mix-style-contract.md) standardizes only the
three requested styles: `layers`, `analysis` and `audio`.
Audio refinement is explicitly deferred to [issue #26](https://github.com/joshuahhn/roto_control/issues/26);
it is not the first implementation target.

## User scenarios and revised model

The user's intended hierarchy is tool/source → item → its detail parameters:

| Tool/source | Selectable item | Detail controls | Read-only feedback |
| --- | --- | --- | --- |
| Layer Mix TOP | Input/layer 1, 2, … | Opacity, Brightness, Black Level, Gamma, Operation, Swap | Layer opacity |
| audioAnalysis | Low, Mid, High | Threshold, Gain, Add, Smooth, Active | That band's explicitly chosen level |
| audioAnalysis | Kick | Threshold, Active | Pre-threshold low-band level and real kick output |
| Audio file/input | One audio source | Gain, Mute | Audio level, initially interpreted as RMS VU |

The user confirmed touch + FUNC. Audio Level is currently interpreted as a
measurement, with Gain writable and Mute a toggle, rather than a second gain
control. That interpretation remains open to correction.

Eight visible MIX slots can reference different item types. For example, two
Layer Mix inputs, Low/Mid/High/Kick, file audio and input audio fit one overview.
These are illustrative entries, not assignments or a requirement to fill all
slots. The examples do not authorize a new group-selector framework, network
construction or automatic switching with PLUGIN Device selection.

The overview target is an item's useful primary control: layer Opacity, band
Threshold or audio Gain. Touch selects the item without writing that primary
control; FUNC exposes the item's details. Each detail records its real label,
target identity, type and value semantics. Float, Menu and Toggle are distinct;
read-only Level/trigger feedback is not a writable control. Operation is a menu
and Swap is a separate toggle. Preserve the complete current menu choices;
do not impose a 16-entry detent limit or promise unverified MIX haptics.

Native Level/Pan/Send are view addresses at the hardware adapter boundary, not
the TD domain categories. A detail binding and its overview binding share target
identity. No duplicate parameter definition or saved value is needed. The exact
native address/label presentation must be proved with one focused item before
the complete editor is implemented.

## Scope and evidence

MIX configuration is independent of the current PLUGIN Layout/Track/Device.
An audio channel, a Layer Mix layer or an analysis control can occupy a slot.
Selecting a TD COMP or a PLUGIN Device does not replace these slots.

Official authority is the [integration guidance](../../../../docs/integration-guidance.md),
[SysEx API v1.6](../../../../docs/ROTO-CONTROL_SYSEX_API_v1.6.pdf), sections 4.1–4.11
and Appendix B, and the [user manual](https://www.melbourneinstruments.com/s/ROTO-UserManual-V1-1-4-April2025.pdf),
printed pages 8–9. The local [Ableton reference](../../../ableton/ROTO_CONTROL.py)
provides implementation examples, not a replacement for the specification.

Physical evidence on firmware 3.3.0 / API 1.6 covers MIX Level input, touch,
motor feedback, native meters, real audio sources and actual Kick output.
The later Low Focus probe passed four combined name/value texts, first-meter
placement and one Gain input/motor route. Other SEL Pan/Send routes and multi-item
selection remain unverified. See [initial trigger acceptance](../../HANDOFF.md#actual-kick-output-acceptance-and-mix-configuration-decision--2026-10-17)
and [Low Focus acceptance](../../HANDOFF.md#low-mix-focus-prototype-and-deferred-audio-issue--2026-10-17).

Source inspection used the clean Track-color worktree at `0ac1ada`, with runtime
source `0254000`. The root checkout remains dirty at `1cb09d9`; its older runtime
must not replace the saved controller. Implementation should start in a separate
worktree from the then-current fork main, preserving the live project and all
existing root changes.

## Slot projection onto native views

Save one ordered collection of eight MIX slots pointing to selected items. Each
item has a stable identity, name/color, typed details, an overview target and one
independent meter source. The adapter explicitly maps the item's targets to
native Level/Pan/Send or button addresses as supported. Each writable target owns
its identity and value semantics. A missing function stays unassigned; it never
falls back to Level or another slot.
An optional read-only trigger source and detection-enabled parameter support the
analysis indicator without hardcoding audioAnalysis internals into MIX routing.

The hardware retains its native function names. Pan and Send are not freely
renamed TD banks. Official SHOW CONTROL VALUE supports text, and SEND TRACK NAMES
supports send labels, but that does not establish replacement of every native
Volume/Pan heading or FUNC button behavior. A scoped probe must check whether
Opacity/Brightness/etc. can be presented clearly enough. Do not call a screen
finished merely because the right value appears beneath a misleading heading.

SEL keeps its native view behavior. It is not the requested item-picker, and
cross-item secondary-function views are optional rather than the main workflow.
The main flow is overview → touch item → FUNC details. The table below describes
native addresses, not a final user-facing detail layout.

| Hardware view | Knob `n`, numbered 1–8 | Meter source |
| --- | --- | --- |
| All Tracks / Level | Slot `n` → Level | Slot `n` meter |
| All Tracks / Pan | Slot `n` → Pan | Slot `n` meter |
| All Tracks / Send `s` | Slot `n` → Send `s` | Slot `n` meter |
| FUNC / Track Focus, first page | Selected slot → Level, Pan, Send A–F across knobs 1–8 | Selected slot meter at meter 1, proposed reference-compatible behavior |
| Track Focus, next page | Selected slot → Send G–L on knobs 1–6; knobs 7–8 unassigned | Same selected slot meter at meter 1 |

All Tracks button function is selected independently through SEL: button `n`
addresses that slot's On/Off, Solo or Arm target. Wire switch mode 0 is called
Mute in the API; the manual presents track activation as On/Off. Define and test
the boolean polarity explicitly rather than assuming a parameter named Mute.
Changing a view, touching a knob or selecting a slot must not toggle a target.

The production Low/Mid check establishes overview press/release as CC20 127/0.
Only native On/Off maps to analyzer Active. Solo/Arm remain unassigned. Active
True uses native Mute-off feedback 0; Active False uses 127. Press duplicates and
release cannot toggle twice, and state feedback is reconfirmed after release.
Track Focus Button 2 instead selects Mid via Track selection, with no CC21
press/release. Keep Focus buttons as item selectors, with no business toggle or
PLUGIN fallback. The native Toggle and source tests cover the new Active route;
use dated HANDOFF evidence for its physical acceptance.

The same target object is projected into either view. Editing it in All Tracks
therefore changes what FUNC exposes, without copying bindings or storing a second
set of parameter values. View changes read current TD values for motor recall;
they do not restore a value snapshot.

Touch selection follows validated hardware selection messages. Do not derive
selected slot from every touch: hardware LOCK can suppress touch-based selection.
MIX selected slot and PLUGIN selected/routing contexts remain separate.

## Concrete uses

| MIX slot example | Level target | Other functions | Independent meter |
| --- | --- | --- | --- |
| Audio | An explicitly chosen gain parameter/stage | Mute with retained Gain; Level is feedback | `demo_au_file_null` stereo RMS or `demo_au_devin_null` mono RMS |
| Layer | An explicitly chosen Layer Mix layer opacity | Brightness, Black Level, Gamma, Operation menu, Swap toggle | Scalar readback of that layer's opacity, 0..1 |
| Low / Mid / High | The selected band's Threshold | Gain, Add, Smooth, Active | An explicitly chosen band-level source |
| Kick analysis | `audioAnalysis.Kickthresh`, 0..0.6 | `Kickactive` toggle | Pre-threshold low-band level; actual public `out1['kick']` is separate trigger feedback |

These are configuration examples, not assignments made to the project. Do not
infer an audio gain target from an audio CHOP, create a Layer Mix network, or
enable Kick detection/output automatically. Existing user audio nodes and the
threshold `0.26174693279619116` remain unchanged during this design work.

Read-only TD inspection confirmed Low/Mid/High each expose writable `*thresh`,
`*gain`, `*add`, `*smooth`, `*active`, with read-only Low/Mid/High outputs. Kick
exposes Kickthresh/Kickactive and read-only Kickdetection. Do not assume every
analysis item has the same detail list or that an output is pre-threshold.

The installed Layer Mix TOP documentation confirms per-layer Opacity, Brightness
and Levels are enabled through Setup, and per-layer Operation/Swap requires the
Operation setting to be Per Layer. Do not turn those flags on or change the
global composite operation just to expose controls. Disabled/missing parameters
are unavailable until intentionally configured. Resolve actual layer parameters
and detect layer/input changes before admitting a new touch to write them.

Live source inspection found `audiofilein1.volume`, but no Volume/Gain/Mute
parameter on the immediate `audiodevin1` source. Receiving audio and metering it
does not create gain or mute. An explicit downstream gain/mute stage is a possible
shared solution, requiring its own small network design. Mute preserves the Gain
setting and does not stop file playback or microphone capture. Meter before/after
that stage must be chosen and labelled; post-stage is a proposal, not an applied
routing change.

## Meter and trigger behavior

Meter configuration records the CHOP/channel source, stereo/mono or scalar/RMS
interpretation, and a range independent of every control range. Audio RMS may use
dBFS; analysis and opacity use an explicit linear scale. Mono duplicates into the
stereo bars. An invalid/missing source clears its bars instead of retaining a
previous slot's values, and does not disable a separately valid knob target.

SEL changes the control function, not the source of any slot's meter. Track Focus
uses the selected slot's source; the first-meter-only placement follows the
Ableton reference and still needs hardware acceptance. Native bars on every Focus
control screen are not promised. Pan/Send meter visibility also needs acceptance.

The yellow/red transition points are global across MIX meters (`0C 0B`), with
red greater than yellow. They cannot represent eight independent analysis
threshold markers. Keep global points stable; a threshold is shown as target
text, and optional K0/K1 comes from actual public trigger output. A disabled
detector reports disabled, not a fabricated K0 result. A short display hold can
make an observed pulse visible without changing detection or audio processing.

Do not implement DAW solo/mute mixing rules merely because a TD boolean is mapped
under Solo or On/Off. A meter remains a measurement of its explicit source.
For example, disabling Kick detection need not hide the pre-threshold signal.

## Protocol and view routing

`0C 01 <AM KM SM SI>` reports All Tracks/channel family, knob function, button
function and send index. `0C 02 <CI>` reports Track Focus control offset.
Both are FROM ROTO only; the host must not send them to force a view. Use
`0C 09` to request MIX refresh and accept validated readback before routing.
Track selection and shared General messages need mode-aware dispatch too.

For Track Focus, API section 4.2 defines `CI` as an offset in multiples of eight:
`00`, `08`, `10` hexadecimal. Project the ordered function list
`[Level, Pan, Send A, ..., Send L]` at `CI + physical_knob_index`.
Section 4.8 explicitly says `CI=08` starts its send names at index `06`.
The inspected Ableton formula instead treats its stored value as a page number;
do not copy that formula blindly. Capture actual second-page readback once before
enabling that page. Until accepted, unsupported offsets have no business routing.

Send count and Send names are shared view metadata. Announce only the needed send
range, pad requested name blocks as specified, and retain holes as unassigned
functions. Do not silently substitute Send A for an unavailable Send. The initial
model needs no extra track banks, grouping or Master/Return targets. Recognize
those requests and suspend business routing rather than aliasing them to slots.

On every mode/view/selection or configuration change:

1. Invalidate the previous routing generation, incomplete CC pairs, deferred
   motor values and queued feedback that belongs to that generation. Preserve
   session traffic and any already transmitted frame tail.
2. Validate the actual view and the referenced slot/function, publish its current
   metadata/value, and activate only after the relevant ingress backlog is drained.
3. Require release and a fresh touch after a transition before knob writes.
   A motor CC echo or an old touch cannot select/write the new target.

Missing targets, changed parameter identity/mode, stale sessions, malformed CC
pairs and unsupported views produce no parameter write. Reuse the existing
managed MIDI process and session protections. MIX does not need PLUGIN LEARN/ACK;
do not fake PLUGIN mapping readiness to admit MIX input. Re-entering PLUGIN must
restore its Track/Device metadata and existing recall/ACK path before input resumes.

## Small implementation boundary

Keep saved slot data separate from transient view/touch/session state. A small MIX
adapter should own view decoding, pure slot/function projection, MIX CC pairing
and feedback. Reuse existing parameter identity/conversion code where its contract
fits. The extension supplies TD resolution, the existing MIDI connection and Tick.
Keep PLUGIN Layouts/FreeLearner behavior in their current managers.

The entry seam needs mutually exclusive MIX/PLUGIN business dispatch, including
the shared General Track messages and Track metadata. Existing Follow/owner
fences govern PLUGIN; an unrelated PLUGIN Focus failure must not redefine MIX
targets. MIX still validates its own explicit targets, session and ingress epoch.

Continuous feedback needs bounded, coalesced meter updates, initially 10 Hz, with
no catch-up stream of obsolete samples. If queue filtering must be shared, extract
only the small existing frame-preserving queue operations; managers still choose
what to discard. No generic event bus, transport rewrite or second MIDI owner.

The TD editor needs one eight-item overview plus a selected-item detail editor and
meter settings. Avoid exposing 8×14 targets as hundreds of outer parameters.
Show real detail labels and types, keeping native address translation in the
adapter. No generic profile framework or automatic node building is needed.
Saved configuration/reload must
not connect hardware, restore target values or enable audio. Generic tox stays
disconnected with eight unassigned slots and no user paths.

## Delivery slices and checks

1. Completed bounded proof: Low Focus shows readable Threshold/Gain/Add/Smooth
   text and its first meter; Gain alone passed touch input and motor restore.
   This supports proceeding with analysis source integration. It does not accept
   every detail type or the multi-item selection path.
2. Implement and test saved item configuration and pure view projection.
   Cover SEL Level/Pan/Send, independent button mode, FUNC shared targets,
   `CI=08` → Send G, gaps, invalid selection and unsupported channel families.
3. Integrate one slot with Level and one Send target, independent meter, then
   test first-page FUNC routing. Check fresh-touch/echo rejection, transition
   queues, stale ingress, session restart and PLUGIN restoration. Unassigned Pan
   must never control the Level target. Preserve existing wrong-target, stale-ACK,
   persistence and exactly-once regressions.
4. Run affected native configuration/callback and save/reload checks. Physically
   verify SEL/FUNC target identity, motor recall, meter ownership and normal
   PLUGIN return. Resolve actual Focus button semantics and second-page `CI`
   before enabling those routes; unsupported cases remain visibly unavailable.
5. Complete the eight-slot editor, repeat only newly affected checks, then save /
   export through live TD with recovery copies, generic tox/receipt and a scoped
   PR. Layer opacity remains a separate concrete configuration/acceptance slice.

Runtime implementation follows the repository's scoped-test policy and final
runtime discovery run. This documentation-only design needs link/consistency
review and `git diff --check`, with no TD connection, hardware action or artifact
re-embedding. No implementation or PR was created by this design step.
