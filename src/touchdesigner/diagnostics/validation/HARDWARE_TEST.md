# Issue #15 physical controller test — 2026-10-11

Project: `cleaned_owned_inspector_review.1.toe`, TD 2025.33230, controller
`/roto_clean_demo/roto_python`, actual ROTO-CONTROL via external MIDI process.
User performed each physical gesture and confirmed motor/LCD observations.

Before installation, saved `hardware_results/20261011_114002/main_before_hardware.tox`
and registry/source configuration in `before.json`. Installed candidate with the
external disconnected `scripts/upgrade_layouts.py` builder, then reconnected. It adds the
merged Snapshot runtime to this older owned-Inspector save and embeds the #15
commands/UI. Exact four changed/added DAT source hashes match external source.
All three Layout IDs remain intact; original canonical artifacts were not replaced.

- Knob1 LEARN acknowledged actual hardware index/hash; mapped `demo_A.Amount`.
  Physical turns changed Amount from 0.4 to 0.01361 (later 0.00415).
- Actual Inspector model Snapshot Save preserved the current value, with intent
  Sync1 and confirmed Save Sync2. Single intent sample 0.939ms; not a latency benchmark.
- Software value 0.75 followed by explicit Snapshot Recall returned to 0.00415,
  with verified native parameter readback. User confirmed both motor and LCD at
  high and recalled low values. Recall command sample 2.534ms is TD execution only.
- Empty Button8 temporarily assigned this Snapshot; actual mapping ACK received.
  Physical press received `191 27 127` and recalled Amount from 0.65 to 0.00415;
  user confirmed motor/LCD. No synthetic MIDI injection used.
- Actual Inspector view two-click Clear removed Button8 only. Confirmed click
  Sync2, sample 5.555ms. Knob1 preserved and re-ACKed on reconnect. After Clear
  and reconnect, user pressed Button8 and confirmed no recall; native readback
  remained 0.6. Unassigned hardware sent no new Button8 CC in the trace.
- Rejected0, Lasterror empty and recursive TD errors empty throughout final checks.

Evidence: [raw run](hardware_results/20261011_114002/). Active saved project is
`hardware_results/20261011_114002/hardware_verified.1.toe` (TD incremental save),
with configured `hardware_verified_controller.tox`. Original recovery and final
configured candidate artifacts retained. This is targeted Knob1/Button8 acceptance,
not all-slot or hardware touch/LEARN-between-confirmation acceptance. Those guard
regressions retain source/native evidence; no full-frame or end-to-end latency claim.
Main remains connected with Knob1 mapped to Amount0.6, test Snapshot retained,
Button8 cleared. No commit, push, canonical replacement or upstream modifications.

Harness correction: `Offerparameter` was initially passed a slot tuple; this API
requires target ID. It rejected before mutation; retry with the existing target ID
succeeded. Two earlier read-only diagnostic queries used incorrect host/state paths;
corrected to `_host`/`base_state`. No product checks were weakened.
