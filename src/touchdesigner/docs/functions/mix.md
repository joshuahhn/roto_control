# Independent MIX analysis

This slice implements saved Low/Mid descriptions on an independent eight-slot
MIX page, float input and native meter feedback. Source tests, native TD checks
and scoped hardware acceptance cover touch selection, FUNC details, sustained
captions, Mid Gain input/motor return and normal PLUGIN restoration. The generic
tox includes this slice with no MIX assignments; the checked-in demo project
retains its separate older receipt. See [dated evidence](../../HANDOFF.md#mix-lowmid-hardware-acceptance--2026-10-17).

## Configure an existing source

Execute in TD against an upgraded controller:

```python
controller.ConfigureMixAnalysis(controller.parent(), 'audioAnalysis')
controller.GetMixProfile()
controller.GetMixState()
```

The first argument is an existing COMP scope, and the source reference resolves
inside it. The scope is saved relative to the controller. No audio network is
built, no target values are restored and hardware stays disconnected. A live scope
rename is refreshed on Project Pre Save. Explicitly reconfigure a replaced or
invalid target; it must not silently attach to a new operator at the old path.

`SetMixProfile(scope, descriptor)` accepts the versioned
[descriptor](../plans/mix-style-contract.md). `GetMixProfile()` returns a detached
saved record; `GetMixState()` exposes mode/view readiness, selected item, changed
write count and unavailable controls. `ClearMixProfile()` removes MIX assignments
without removing PLUGIN mappings. Configuration requires released knobs and exit
from LEARN. Only the analysis style is enabled in this slice.

## Hardware views

| View | Current analysis projection |
| --- | --- |
| MIX overview, native Level | One band's Threshold per knob |
| Native Pan | Each band's Gain |
| Native Send A / B | Each band's Add / Smooth |
| Touch item, then FUNC | Selected band's Threshold, Gain, Add, Smooth on knobs 1–4 |

Readable combined name/value feedback uses SHOW CONTROL VALUE. Native Volume/Pan
headings are firmware UI, not renamed TD pages. Each band retains its own meter
source when SEL changes the control function. Focus uses the selected band's
meter on screen 1; other meters are cleared. Unsupported channel families, Focus
offsets beyond CI=0 and unassigned functions have no business input route.

The supplied meters read `audioAnalysis/out1['low']` and `['mid']` over 0..1.
These are processed outputs, not threshold-comparison inputs. Detection state is
unchanged, so an inactive Mid can correctly have zero level. Meter scaling is
independent of knob ranges; yellow/red points are global across MIX. Feedback is
coalesced at 10 Hz, with no replay of old meter samples after backpressure.

[SysEx API v1.6](../../../../docs/ROTO-CONTROL_SYSEX_API_v1.6.pdf), section 2.23,
defines a timeout for SHOW CONTROL VALUE. Assigned text is therefore renewed on
the same bounded feedback tick even when its value stays unchanged. Unsent
renewals coalesce per screen; unchanged motor values are not resent. After MIX
feedback stops, the device returns to native names such as Volume/Pan/Send.
Check combined TD name/value text while the connection is active.

Touch only selects an item. After any mode/view/selection transition, release the
knob and start a fresh touch before writing. Pair halves older than 250 ms, stale
ingress and untouching motor echoes cannot write. Software edits move motors
after release. Loading, selecting and viewing make zero parameter writes.

FUNC can remain on across MIX → PLUGIN → MIX within one connection. The adapter
accepts a direct Focus readback on return, without requiring an overview event
or toggling FUNC. Physical observation confirms `MIX-FOCUS / Low` and FUNC on;
the controller's native Volume/Pan/Send headings remain. A separate fresh
connection reported overview and FUNC off, so connection startup and mode
round trips are distinct acceptance cases.

## Separation from PLUGIN

MIX assignments remain independent of PLUGIN Layout/Track/Device and Follow.
Shared Track traffic and queued feedback belong to the active hardware mode.
MIX consumes its own CCs, including currently unsupported buttons, before the
PLUGIN routing/LEARN/ACK path. A PLUGIN owner failure does not block valid MIX
targets. Returning to PLUGIN restores its metadata and normal matching-ACK recall.
No second MIDI owner or new wire protocol is introduced.

## Current limits and installation

Overview Pan/Send input has source coverage; it has not had physical acceptance
in this slice. Active is retained as typed Toggle metadata but has no business button route.
Menus, trigger indicators, High/Kick adapters, second-page Focus and the slot
editor are later slices. No detent or freely replaceable native-heading promise
is made. Layers remain planned; audio Gain/Mute processing is deferred to
[issue #26](https://github.com/joshuahhn/roto_control/issues/26).

For a current disconnected controller, make a recovery `.tox` through TD, then
execute `scripts/upgrade_mix.py` and call `install(controller, source_dir)`. It
embeds three helpers and refreshes the extension/lifecycle source, preserving
existing mappings and target values. Generic export clears the MIX profile and
starts disconnected with no user paths. The older full Inspector builder has a separate
ASCII-locale source-loading limitation in this TD process; this upgrader does
not rebuild Inspector.
