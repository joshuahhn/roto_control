# Reusable binding milestone

Planning snapshot: 2026-10-04, TD 2025.33230, live `roto_control_python.3.toe`.
This document proposes the next build. No operators or runtime behavior were changed during planning.

## Baseline

The single Value / Knob 1 prototype has accepted hardware input, LEARN auto-offer, motor feedback, LCD and mapping recall. Thirteen protocol tests pass. The inspected network has no errors and one wire: parameter_values -> null_values. That wire graph has no cycles; Python feedback still needs its own origin checks.

Keep the external mido/rtmidi child process and its owned lifecycle. Public callers must not handle MIDI bytes. Current readonly status parameters remain the UI/state interface. Runtime connections and Python callables are not persisted.

## Scope

One connected controller, one active numeric target and Knob 1. Two adapters share the same target metadata and protocol behavior:

- An external COMP custom Float or Int parameter.
- A Python value-change callback, with explicit SetValue for software-origin changes.

Keep the existing Value / manual Offerparameter prototype usable as a default target. Multiple knobs, pages, buttons, transport, CHOP input and portable tox packaging are later milestones.

## Proposed public interface

These are proposed methods, not implemented calls:

```python
controller.BindParameter(target.par.Speed, id="visual.speed", minimum=0, maximum=10)
controller.BindCallback(id="app.speed", label="Speed", minimum=0, maximum=10,
                        value=5, on_change=handle_change)
controller.SetValue(7)
controller.Unbind()
```

Connect(), Disconnect() and Offerparameter() remain. Bind methods replace the one active binding after validation; a failed bind leaves the old binding intact. Unbind returns to the built-in Value target. Connect is always explicit.

- id is a caller-supplied stable identity, independent of operator path and display label. Reusing an id for a different target is a caller error. Device identity and parameter identity must be designed together against the existing controller protocol before implementation.
- Values exposed to callers use target units. Protocol values are normalized internally. Limits must be finite and minimum < maximum. SetValue clamps to the configured range; Int targets round to integer steps.
- For parameter binding, omitted limits may use finite valid normMin/normMax; otherwise fail with a useful error. Never infer range from current value.
- Callback receives one event containing id, value and origin="hardware". Software-origin SetValue updates state/motor/LCD without invoking on_change again. Callbacks run on TD's main thread and must be short.
- Parameter binding watches only the selected parameter via Parameter Execute DAT. External edits drive feedback and LEARN auto-offer. Hardware writes must not trigger another offer or motor echo.
- Initially writable constant-mode numeric custom pars only. Reject expression, export, bind, readonly, Pulse, menu and nonnumeric pars rather than replacing their mode or expressions.
- Read initial target value before advertising metadata. Bind while disconnected or not touched/learning; reject replacement during a gesture/LEARN. Clear acknowledged mapping on identity change; never use old mapping for a different target. Require new LEARN unless the controller recalls and acknowledges the new identity.
- Invalid/deleted target: suspend target writes and report Bindingvalid=False plus LastError; do not silently switch to another parameter.
- Catch callback failures at the adapter, report LastError and suspend that binding's dispatch until rebound. Leave Disconnect available.
- Python callback registrations must be re-established after extension reload/project open. Document startup registration; do not serialize callable objects.

## Internal responsibilities

Transport owns ports and byte delivery. Protocol owns hardware session, target metadata, mapping acknowledgement, touch, normalization and feedback. Binding logic owns target read/write, validation and event origin. RotoPythonExt coordinates them and publishes TD state.

Start with small source modules inside the existing COMP. These responsibilities do not require separate sub-COMPs while they remain code-only. Tests should cross the binding interface with both adapters, without exposing MIDI details to consumers.

## Operator plan and placement

Current child bounds: annotations X=-275..330, Y=-535..150. Existing output null is at (175,0). Allocate additions to the right with a 20 px annotation gap. Read actual node dimensions before creation and finalize annotation bounds after verification.

| Parent | Type | Name | Planned position | Role / connections |
| --- | --- | --- | --- | --- |
| roto_python | textDAT | binding | (350,-210) | Source-synced binding module; language Python |
| roto_python | parameterexecuteDAT | target_callbacks | (525,-210) | Source-synced callback; watches active target only; custom/valuechange on, builtin/pulse off |
| roto_python | outCHOP | out_values | (350,0) | null_values -> input 0; formal component output |
| project root | baseCOMP | base_parameter_demo | (335,0) | Separate consumer with shortcut ParameterDemo and Speed custom Float, range 0..10 |
| project root | baseCOMP | base_callback_demo | (335,-210) | Separate consumer with shortcut CallbackDemo, registration and received-event display |

Demo callbacks and initialization DATs live inside their demo COMPs. Their internal positions are allocated after scoping the minimal example. No wired input is needed for the two binding types; consumers use parameter handles or Python registration. No inCHOP is added just for symmetry.

Retain parameter_values -> null_values -> out_values. Extend readonly custom state with Learning, Bindingvalid and LastError; retain Rx as total MIDI messages, including clock. Verify CHOP channel types/names before adding numeric state channels. Preserve existing names/shortcut and existing node positions. Add annotations for the new functional groups through the builder/tool workflow.

Use live get_help for outCHOP and parameterexecuteDAT parameters before wiring/configuration. Configure target references only after operators exist. Runtime target references use validated parameter handles; demo references use component shortcuts. No guessed relative parent-depth paths.

## Phases and gates

1. Define target identity/metadata and value conversion in pure Python. Test finite/range validation, Int steps, metadata bytes, identity changes and mapping rejection. Preserve current protocol tests.
2. Add binding adapters and proposed extension methods. Test both directions, hardware origin, duplicate echo, callback exception and target invalidation. No hardware writes during unit tests.
3. Add binding DAT, target watcher, readonly state and outCHOP through the external builder. Disconnect before synced code edits. Verify extension promotion, watcher source, outputs and errors; then reinitialize explicitly where required.
4. Create the two independent demo consumers. Bind after they exist; initialize callback registration explicitly. Demonstrate range 0..10 and software edits without per-frame Python polling of target values.
5. Hardware acceptance for each adapter: LEARN, turn knob, software update -> motor/LCD, touch deferral, no duplicate offers/echo, disconnect/reconnect identity recall. Recheck old built-in Value workflow.
6. Verify reparenting, target deletion, reload registration and process cleanup. Update README/HANDOFF, embed docs, inspect layout, and save to a checked free numbered slot.

Completion means both consumers use the same public interface without MIDI knowledge and pass live/hardware acceptance. It does not imply all control types or portable packaging are supported.

## Implementation checkpoint: 2026-10-04

Implemented both adapters, target identity/metadata, promoted registration/value methods, watcher, output and demos. Binding DAT positions were adjusted to (550,-210) and (725,-210) to leave room for the formal output and guide snapshots. Twenty-four tests pass. Both bindings passed physical LEARN/input/motor/LCD and reconnect recall; see HANDOFF.md and binding_verification.json. Rename resync passes. Collapse Selected reinitializes the tested controller setup, requiring registration again. Runtime bindings remain explicitly registered after reload.

## Saved setup checkpoint

Binding configuration now persists on the outer Binding page. Diagnostics moved to internal base_state; State provides API access and out_values retains channel names. Saved callback hook source recreates registrations after initialization. Direct API bindings stay temporary; Connect remains manual. Thirty-two tests pass; actual Callback project reopen and hardware mapping recall passed.
