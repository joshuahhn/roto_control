# Independent MIX controls

This slice implements saved Low/Mid/High/Kick/Snare/Rhythm analysis, two custom
analysis assignments and wired Layer Mix descriptions on
an independent eight-slot MIX page, float input, analysis Active buttons and native
meter feedback. Source tests, native TD checks
and scoped hardware acceptance cover touch selection, FUNC details, sustained
captions, Mid Gain input/motor return, overview Active toggles, Layer Mix overview
Opacity input/motor return, Input 2 Focus captions, curated Operation selection,
Swap input/motor return and normal PLUGIN restoration. The generic
tox includes this slice with no MIX assignments; the checked-in demo project
retains its separate older receipt. See [dated evidence](../../HANDOFF.md#mix-lowmid-hardware-acceptance--2026-10-17).
High also has physical overview/Focus caption, persistent-selection, Gain
input/motor-return and Active/changing-meter acceptance. The six-item overview,
Kick Active/actual trigger, Threshold input and final motor/PLUGIN restoration
have scoped hardware acceptance. Snare/Rhythm Active/trigger/Threshold/motor
return also pass. Slot 7 Gain / Slot 8 read-only aliases and the tested
unassigned input positions pass. See the
[physical batch](../plans/mix-analysis-acceptance.md) for exact scope.

## Configure an existing source

Use the controller's **MIX** custom parameter page:

1. Choose Draft style: Analysis bands or Layer Mix inputs.
2. Drag the existing audioAnalysis COMP or Layer Mix TOP onto Draft source.
   For Analysis, set Analysis bands to an ordered list such as `Low Mid High`.
   Spaces or commas separate names, and case does not matter. New/generic drafts
   default to `Low Mid High Kick Snare Rhythm`; saved drafts stay unchanged.
   One band is also valid. Empty, duplicate or unknown names are
   rejected. Kick/Snare/Rhythm each have only Threshold/Active and independent
   pre-threshold level/actual trigger feedback. See the complete
   [analyzer inventory and assignment contract](mix_analysis.md).
3. For Layer Mix, use the six Custom blend slots. Fill any two to six different
   modes and leave unused slots None. Each slot offers the source's complete TD
   blend list. All None omits the Operation control.
4. Release knobs, exit LEARN, then press Apply MIX draft. Applied MIX shows the
   accepted profile. Invalid configuration leaves the previous profile active.

Analysis has optional `MIX Slot 7` / `MIX Slot 8` assignment pages. Set a user
name, the other analyzer COMP's actual parameter names and independent CHOP
feedback, then use the same Apply. Blank item name leaves a slot unassigned.
See [custom assignments](mix_analysis.md#custom-slots-7-and-8); these stay within
analysis style and do not create a general mixed-style editor.
Each custom slot also has an optional Threshold comparison toggle, off by
default. Use it only for a mono scalar level sharing the assigned Threshold's
units; it applies to overview and first Focus through the same Apply and does
not alter the analyzer.

Draft edits do not change routing or target values. Draft and applied settings
persist separately; loading never applies an unfinished draft. Clear MIX
assignments removes only the active MIX profile and keeps the draft for reuse.
It also requires released knobs, exit from LEARN and no parameter dispatch.
Neither pulse connects hardware. The editor never enables Layer Mix Setup or
Per Layer Operation; configure those intentionally on the source first.
An unavailable saved custom choice remains labelled Unavailable until replaced;
Apply rejects it instead of silently choosing a different mode.

Operation preset contains user-named choice lists, without fixed built-in
categories. Enter Preset name and press Add Operation preset to save the draft;
Save preset edits / name updates the selected record. Selecting a preset only
loads the six draft slots. Saving, renaming or deleting a preset does not change
an already applied profile. Press Apply MIX draft to use the current slots.
Two filled slots are sufficient; six is the editor's capacity, not a minimum.
Normal configured saves preserve these presets; generic exports clear them.

The same configuration remains available from Python:

For another analyzer with different parameter/channel names, use the
[Analysis integration API](mix_analysis.md). It documents the TD descriptor v1,
control types/positions, meter units/stage, lifecycle and a complete example.

Execute in TD against an upgraded controller:

```python
controller.ConfigureMixAnalysis(controller.parent(), 'audioAnalysis', ('Low', 'Mid', 'High', 'Kick', 'Snare', 'Rhythm'))
controller.GetMixProfile()
controller.GetMixState()
```

Omitting `bands` retains the original Low/Mid pair. The first argument is an
existing COMP scope, and the source reference resolves
inside it. The scope is saved relative to the controller. No audio network is
built, no target values are restored and hardware stays disconnected. A live scope
rename is refreshed on Project Pre Save. Explicitly reconfigure a replaced or
invalid target; it must not silently attach to a new operator at the old path.

`SetMixProfile(scope, descriptor)` accepts the versioned
[descriptor](../plans/mix-style-contract.md). `GetMixProfile()` returns a detached
saved record; `GetMixState()` exposes mode/view readiness, selected item, changed
write count and unavailable controls. `ClearMixProfile()` removes MIX assignments
without removing PLUGIN mappings. Configuration requires released knobs and exit
from LEARN. Analysis and layers are enabled; one profile/style is active at a
time. Configuring another source replaces MIX assignments, without changing
PLUGIN assignments. Mixed-style slots and a profile-switching UI remain planned.

## Analysis selection

In the analysis overview, the selected band's screen keeps a `>` marker, its
band name and current value, such as `>High 0.200`. Touch another band to move
the marker; releasing touch does not expire it. First touch still selects without
writing. FUNC details use their normal control names. Long band labels shorten
to leave room for the value; this is display feedback, not a new control target.
Overview selection keeps unchanged motor positions; it still sends real TD value
changes and recalls the relevant positions when switching to FUNC details.

## Layer Mix floats

```python
controller.ConfigureMixLayers(existing_scope, 'layermix_layers', operation_choices=[])
```

Use an existing Layer Mix TOP with 1..8 wired inputs only. The adapter records
their order and identities, and describes fields already enabled by Setup.
It never enables Opacity/Brightness/Levels or changes wiring, operation, values
or extensions on the TOP. Reference-only or mixed wired/reference layers are
not supported by this slice.

| View | Layer projection |
| --- | --- |
| MIX overview, native Level | Each input's Opacity |
| Native Pan | Each input's Brightness |
| Native Send A / B | Each input's Black Level / Gamma |
| Touch item, then FUNC | Selected input's Opacity, Brightness, Black Level, Gamma on knobs 1–4 |

Combined captions use `Opac`, `Bright`, `Black` and `Gamma` to fit the hardware
text field. Normalized ranges come from the actual TD parameter metadata.
Disabled fields stay unavailable. Overview buttons have no Layer Mix business
action; Focus buttons keep native input selection.

The meter is scalar readback of that layer's Opacity over 0..1, duplicated into
both native bars. It does not measure image intensity or an audio signal.
Changing the input identities/order, sequence count or Setup flags invalidates
the profile before further writes. Restoring old wiring does not resume it:
release the knobs and explicitly configure again. Target identity and parameter
guards also apply to every write. Operation/Swap source status follows below.

## Operation presets and Swap

First-Focus Operation is on knob 5 and Swap on knob 6. Hardware acceptance covers
Common plus custom Xor/Z Film, reaching Z Film, Add/Over motor feedback, Swap
unavailable under Add, Swap On input and Off motor return. Focus buttons continue selecting inputs.
Operation/Swap are described only when the existing TOP already uses Per Layer.
The caller must let the TOP cook after enabling that setting; the adapter never
enables it itself.

```python
controller.ConfigureMixLayers(
    existing_scope, 'layermix_layers',
    operation_choices=['over', 'add', 'xor', 'zfilm'])
```

Explicit `operation_choices` has no implicit library entries. Names are TD menu
names, not display labels/indices. Duplicates keep their first occurrence; use
at least two distinct choices, or an empty list to omit Operation. The descriptor
API retains its 24-choice capacity. The preset editor stores two to six choices.

```python
preset_id = controller.SaveMixOperationPreset('My two modes', ['over', 'add'])
records = controller.GetMixOperationPresets()  # detached id/name/operations records
controller.SaveMixOperationPreset('Renamed', ['screen', 'multiply'], preset_id)
controller.RemoveMixOperationPreset(preset_id)  # applied profile remains intact
```

Preset names are nonempty and unique without case differences. Stable preset
IDs survive name edits. Presets contain choice lists only, not target values,
source paths, touches or a connected session. Loading/applying a list does not
coerce the TD Operation value into that list.

Legacy `operation_library` / `custom_operations` Python calls retain their old
behavior, including the original default, for existing integrations. These
arguments cannot be combined with explicit `operation_choices`. Existing applied
descriptors are not truncated. Upgrade converts an old library-plus-custom UI
draft into explicit slots; if it has more than six choices, upgrade stops before
source/UI writes and asks that draft be reduced first. New UI has no fixed
Common/Contrast/Math menu. A larger API-applied list stays active, but is not
automatically copied into the six-slot editor.

The real TD menu retains all options and labels for identity validation. The
controller only steps through its chosen list. `Op 2 Add` means the second choice
in that list. If TD selects a value outside the list, `Op *` marks that value;
no motor position is fabricated and no target value is coerced. A fresh gesture
can select a listed value. Changing the underlying TD menu or labels invalidates
the old route until reconfiguration. PLUGIN keeps its existing 24-option limit.

Swap displays On/Off and uses two knob positions. TD disables it for commutative
operations such as Add/Screen; the controller then shows Unavailable and blocks
input. When an operation such as Over enables it again, a held touch/partial CC
pair cannot write until release and fresh touch. Discrete value selection is
implemented; physical MIX detents are unverified. SysEx API 3.10's step-count
field belongs to PLUGIN LEARN; chapter 4 does not document a corresponding MIX
haptic/step-count setting.
The [haptics review](../plans/mix-haptics-findings.md) also checks Serial v1.3,
official integrations and firmware notes. MIX has documented fixed 0 dB indents,
but no published setter for arbitrary MIX detent counts, positions or strength.
Those native mixer reference points do not establish TD parameter haptic semantics.
Native Send C/D project Operation/Swap; the send count/names retain missing fields
as unassigned. Second-page Focus is still disabled.

## Hardware views

| View | Current analysis projection |
| --- | --- |
| MIX overview, native Level | One band's Threshold per knob |
| Native Pan | Each band's Gain |
| Native Send A / B | Each band's Add / Smooth |
| Touch item, then FUNC | Selected band's Threshold, Gain, Add, Smooth on knobs 1–4 |
| Overview button On/Off bank | Button 1 → Low Active; button 2 → Mid Active |

In overview, the button beneath an item toggles that band's Active parameter.
Only native On/Off switch mode 0 is assigned. Solo/Arm banks and unassigned slots
never toggle Active or fall back to PLUGIN. A press toggles once; release and
held duplicates do not. View/session fences reject stale presses and require a
release before a held button can act in the new view. Active is not a knob target.

LED feedback follows the actual Toggle, including software edits. Native Mute
polarity is inverted: Active=True sends CC value 0, Active=False sends 127. The
state is confirmed again after momentary release. Meter sources remain independent
of this feedback; an inactive detector may itself produce zero output.

FUNC Focus buttons select items. The read-only hardware check found Button 2
selects Mid through Track selection, without a CC21 press/release. These buttons
keep that firmware function; Active is operated from overview.

Readable combined name/value feedback uses SHOW CONTROL VALUE. Float captions
reserve space for the three-decimal value before shortening the label to the
12-character field, such as `Thres 49.459`; target values are unchanged. Native Volume/Pan
headings are firmware UI, not renamed TD pages. Each band retains its own meter
source when SEL changes the control function. Focus uses the selected band's
meter on screen 1; other meters are cleared. Unsupported channel families, Focus
offsets beyond CI=0 and unassigned functions have no business input route.

The supplied meters read the selected `audioAnalysis/out1` band channels
`low`, `mid` and/or `high` over 0..1.
These are processed outputs, not threshold-comparison inputs. Detection state is
unchanged, so an inactive Mid or High can correctly have zero level. Meter scaling is
independent of knob ranges; yellow/red points are global across MIX. Feedback is
coalesced at 10 Hz, with no replay of old meter samples after backpressure.

Kick instead reads the verified `audioAnalysis/math2['low']` before its threshold
and the actual `out1['kick']` detection independently. Snare uses `math16['high']`
and `out1['snare']`. Rhythm uses `math10['chan0']` before the threshold clamp,
scaled over 0..100, and `out1['rythm']`; its Threshold target retains 10..90.
These detectors have no Gain/Add/Smooth targets. First FUNC Focus uses Knob 1
for Threshold and screen 5 for read-only
`Trig Off` / `Trig 0` / `Trig 1` / `Trig ?`; Knob 5 does not write. An observed
trigger is held for 200 ms for readability, without changing detection. See the
[trigger API](mix_analysis.md#trigger-contract) and pending
[batched hardware check](../plans/mix-analysis-acceptance.md).

The known Kick/Snare/Rhythm adapter declares threshold references for overview
and first Focus.
On the tested firmware screen 1, the upper horizontal bar shows actual Threshold,
the lower shows pre-threshold Level, both extending left to right on the meter's
single scale. Kick/Snare use 0..1 and Rhythm 0..100. The API's Left/Right names
describe channels, not physical direction. Profiles without the corresponding
optional view field keep their original meters. See the
[reference contract](mix_analysis.md#threshold-comparison). The earlier
[Kick prototype](../../HANDOFF.md#highkick-hardware-and-threshold-comparison-prototype--2026-10-17)
was accepted at 0.490; installed production overview, first-Focus transition
and normal PLUGIN return have now passed without parameter writes.

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

View and item-selection messages follow their received order within a connection,
including several messages in one Tick. Routing waits for the buffer to drain;
buffered CC gestures remain fenced and need a fresh touch. Missing feedback
clears both bars and recovers when its samples return, without disabling a
separately valid control. Empty scalar samples are handled by the same clear path.

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
in this slice. Second-page Focus and a mixed-style slot editor are later slices.
MIX hardware LOCK behavior has not been verified; overview touch selection was
accepted with LOCK off.
Analysis-only custom slots 7/8 are configured as above. No detent or freely replaceable native-heading promise
is made. Contrast/Math and other custom combinations have source/native coverage;
they were not individually checked on hardware. The editor configures one
source/style profile, without per-item libraries or mixed-style slots;
audio Gain/Mute processing is deferred to
[issue #26](https://github.com/joshuahhn/roto_control/issues/26).

For a current disconnected controller, make a recovery `.tox` through TD, then
execute `scripts/upgrade_mix.py` and call `install(controller, source_dir)`. It
embeds three helpers and refreshes Binding, setup and the extension/lifecycle source, preserving
existing mappings and target values. Generic export clears the MIX profile, user
Operation presets and draft, and
starts disconnected with no user paths. The older full Inspector builder has a separate
ASCII-locale source-loading limitation in this TD process; this upgrader does
not rebuild Inspector.
