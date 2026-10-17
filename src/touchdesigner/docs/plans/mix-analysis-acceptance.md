# Analysis hardware batch

Current results: six-item overview, High Active/changing meter and Kick
Active/actual trigger/Threshold input plus motor/PLUGIN restoration pass. A
temporary upper-Threshold/lower-Level Kick comparison was accepted for now. Its
installed production Focus display has passed. The user then requested the same
comparison in overview. Installed production overview, first-Focus transition
and normal PLUGIN return then passed with zero parameter writes. Snare/Rhythm
Active/trigger/Threshold/motor return now pass too. Custom Slot 7 Gain / Slot 8
read-only aliases and unassigned Focus Knob 1 / overview Knob 8 input also pass.
Reuse completed cases rather than running the whole batch again. See [dated evidence](../../HANDOFF.md#highkick-hardware-and-threshold-comparison-prototype--2026-10-17).

## Installed reference feedback

Completed for Kick on 2026-10-17: overview upper Threshold near 26% / lower
dynamic Level, first Focus with the same pairing, normal demo_A PLUGIN return.
Zero parameter writes; original profile, values and local control IDs restored.
The earlier Focus-only round had three accidental Kickthresh writes to 0.274675;
the user identified the accidental turn and 0.261747 was restored before this
zero-write follow-up. Other detectors/custom slots are not accepted by this case.

Reproduction procedure:

Use the final source without any output/receive probe override. Agent configures
a bounded, disconnected-first Kick profile after a fresh snapshot, then user
remains in MIX-TRACKS / FUNC off. With hands off, confirm upper Threshold near
26% and lower pre-threshold Level varying over the common 0..1 scale. Enter first
FUNC Focus and confirm the same pairing; the previous Focus display pass is
reused, with only the transition checked here. Existing detection
state remains unchanged. Make one small Threshold gesture, confirming only the
upper reference tracks its actual value while the lower remains the signal.
Restore 0.261747 or the freshly captured value, confirm motor/reference return,
then normal PLUGIN display and disconnection. This replaces the temporary send
override acceptance; it does not repeat unrelated LEARN/Layer Mix tests. Keep
the generic export and original saved profile free of test assignments.

Run when the user is back at the controller. Source tests and native fixtures
cover configuration/routing/persistence; they do not prove the new hardware
display or the actual detector's timing. No MIDI connection is needed to prepare
this checklist. Full item inventory and assignment requirements are in the
[Analysis API](../functions/mix_analysis.md#existing-audioanalysis-inventory).

## Preparation by the agent

1. Verify the active TD project and `/roto_clean_demo/roto_python`, source hashes,
   disconnected child/pending state, released knobs and exit from LEARN. Keep
   the old controller disconnected and untouched.
2. Take a fresh recovery `.tox` and snapshot the applied profile, editor draft,
   registry/control IDs, Snapshots and all analyzer/demo/layer values. Preserve
   intervening user edits; do not reuse an old value snapshot.
3. Configure the known adapter with `Low Mid High Kick Snare Rhythm` in that order.
   Use empty custom slots initially. Do not
   enable audio monitoring, change playback/gain, build audio routing or overwrite
   the original draft. Connect with a bounded test window and automatic input
   shutdown. The agent performs configuration and restoration; the user need not
   work through extra Apply steps.

## High Active and meter

1. User selects MIX, MIX-TRACKS, FUNC off, without touching knobs. Expect Threshold
   captions for Low/Mid/High/Kick/Snare/Rhythm in slots 1–6 and unchanged values.
2. Establish the actual initial Highactive value. If off, Button 3 should be off.
   User presses/releases Button 3 once; verify exactly one Highactive change,
   matching LED, no Float writes, and a changing public high meter when the
   actual source has high-band energy. Lack of source energy is inconclusive,
   not a failed transport check.
3. User presses/releases Button 3 again. Verify initial Active state restored
   and no change to Low/Mid/Kick. Reuse accepted High Focus/Gain/motor-return
   behavior; do not repeat unrelated tests.

## Kick Threshold, Active and actual trigger

1. In overview, touch/release Knob 4, then FUNC. Expect MIX-FOCUS / Kick,
   Threshold on screen/Knob 1, blank controls 2–4, and read-only screen 5. Meter
   on screen 1 reads the verified pre-threshold level independently of detection.
2. With Kickactive false, expect `Trig Off`. Verify Knob 5 has no route with a
   fresh touch and small turn; zero parameter writes. Stop if the view differs.
3. Return to overview. Button 4 toggles Kickactive exactly once per press/release.
   Return to Kick Focus. Compare `Trig 0` / `Trig 1` against timestamped actual
   `out1['kick']` observations. A detected pulse is held for 200 ms for readability;
   level above the displayed threshold alone is not evidence of a trigger.
4. With Kick selected, make one small Knob 1 gesture. Confirm only Kickthresh
   changes within its real range and the meter continues. The agent restores the
   captured value; user confirms caption and motor return. Do not assume a high
   threshold guarantees no detection; check the actual source.
5. Return to overview and restore Kickactive. Focus should show `Trig Off` again.
   Change mode with knobs released, then return to MIX. Follow actual persisted
   FUNC/readback state; stale `Trig 1` must not survive a boundary.

## Snare and Rhythm

Completed on 2026-10-17 using production source `f7c53ab`: both overview captions
and upper reference scales, initial/off and on LEDs, actual Trig 0/1, first Focus,
Threshold gestures and motor return, then normal PLUGIN return. Snare reached
0.4107672587438198 through 46 changed writes; Rhythm reached 61.70725752304218
through 72. Four Active presses added four writes. The clean round therefore
made exactly 122 changed writes and restored 0.311515 / 49.4591 and both Active
False. All unrelated values/profile/draft remained unchanged.

Rhythm's `Thresh 49.459` exceeded the 12-character field and showed `Thresh 49.45`.
A separate Float caption fix shortens the label before encoding, keeping the
numeric digits; its scoped native/source checks and physical follow-up are
recorded in the latest handoff.

Reproduction procedure:

Repeat the affected Kick checks for items 5 and 6, one at a time: overview
Button 5/6 Active, touch that item then FUNC, Threshold on Focus Knob 1,
read-only trigger on screen 5, and screen 1's independent meter. Snare's meter
uses `math16['high']` over 0..1. Rhythm uses `math10['chan0']` over 0..100 while
its Threshold target remains 10..90. Compare detections with actual
`out1['snare']` / `out1['rythm']`; report lack of source pulses as inconclusive.
Restore each captured Threshold/Active before proceeding. No Gain/Add/Smooth
routes should appear for these detectors.

## Two custom slots

Completed on 2026-10-17 using runtime source `7a99f31`, real draft/Apply and the
existing audioAnalysis COMP. Slot 7 `Gain TEST` uses Lowgain / Gain primary;
Slot 8 `Level TEST` is meter-only. Both read processed `out1['low']` over 0..1.
Overview names, Gain 2.000 / 29% motor, paired meters, selection, Slot 7 first
Focus with Gain on Knob 2, and Slot 8 first Focus/meter pass. Lowgain reaches
2.6131966062381737 through 32 changed writes, then restores to 2.000 / 29%.

Fresh touch/turn/release on unassigned Focus Knob 1 receives 20 CC12/44 pairs
and touch ON/OFF; overview Slot 8 receives 22 CC19/51 pairs and touch ON/OFF.
Both produce zero parameter writes, with every analysis value unchanged.
A diagnostic observer records raw input without overriding receive/send.
Normal PLUGIN return passes; all values, original profile/draft and four local
control IDs are restored, with no MIDI process, pending bytes or observer.
Custom trigger/comparison feedback and foreign analyzer sources retain their
existing native/source coverage; they are not additional physical claims here.

Reproduction procedure:

Use the user's chosen existing analyzer if available. Otherwise use a temporary
assignment to existing Lowgain/public low output, clearly labelled as a test
alias, without constructing another audio graph. Assign slot 7 a user name,
Gain target, explicit Gain overview control and meter source/stage; assign slot
8 read-only meter feedback with no controls. Use the same original Apply once.
Check names/selection, slot 7's one intended target gesture and software/motor
restore, and zero writes from slot 8. Native validation already covers cross-COMP
scope, so hardware need not repeat a separate graph-building exercise. Restore
both custom drafts and the original applied profile at finish.

## Restore and finish

Restore captured values/profile/draft and verify only expected test writes
occurred. Do not erase confirmed user edits. User selects PLUGIN and confirms
demo_A's original parameter/value display, then the agent disconnects/reaps the
child and checks zero pending bytes/no overrides. Verify the original control
IDs/registry and Snapshots, reporting any learned/local reconciliation separately.
Keep TD open and all existing audio nodes. Record physical results by affected
case; do not claim the whole analyzer or all nine items are supported.
