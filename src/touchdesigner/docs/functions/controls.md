# Multiple controls

For direct mapping, open hardware LEARN, select a control and change any compatible COMP custom parameter. TD offers it automatically and commits the hardware-reported slot after a matching acknowledgement. The Inspector COMP / Parameter picker is an optional explicit assignment path. The persistent one-slot API is `controller.AssignParameter("knob", 2, target.par.Speed)` or `controller.AssignParameter("button", 5, target.par.Reset, button_type="push")`. Metadata is inferred and other collection mappings are preserved. See inspector.md for automatic offers during hardware LEARN. `BindControls` below remains the complete-registration API.

Hardware can report several mappings together on LEARN exit. Free LEARN retains each offer for 30 seconds, reserves its parameter index, and matches acknowledgements independently by index/hash, including out-of-order reports. Repeated offers for the same pending parameter retain its ID/index. At most 128 offers can await acknowledgement. Layout, Device, control-page, input-fence and transport-session resets cancel pending offers. A Menu's acknowledgement determines knob selection versus button Cycle even when hardware did not send a selection CC before the edit; the offered hash is saved with the actual mode and unchanged Menu options.

```python
controller.BindControls([
    dict(kind='knob', slot=1, id='scene.speed', parameter=scene.par.Speed),
    dict(kind='button', slot=1, id='scene.enabled', mode='toggle', parameter=scene.par.Enabled),
    dict(kind='button', slot=2, id='scene.reset', mode='pulse', parameter=scene.par.Reset),
], group_id='scene.controls.v1')
controller.SetValue(7, id='scene.speed')
controller.SetValue(1, id='scene.enabled')
controller.Offerparameter(id='scene.reset')  # LEARN only, no business action
```

Knobs accept writable CONSTANT/BIND custom Float/Int parameters; buttons accept Toggle/Pulse parameters matching mode. Registration validates the entire collection before replacing the current one. Slots are fixed: each target must be learned onto its configured hardware slot. Duplicate slots, IDs, parameter handles or shared bind-master chains fail. Bound Toggle/Pulse references are supported under the same writable Par-chain rules as numeric targets. Hardware acknowledgements must match logical index, target hash, kind and slot.

For Python callbacks, replace parameter with on_change and initial value; numeric targets also supply minimum/maximum. Each changed knob/Toggle callback receives id, value in target units, origin='hardware'. Pulse callbacks receive the same keys plus kind='pulse', value=1 on every accepted press according to button_type. Software SetValue never calls on_change. Pulse targets reject SetValue; use Offerparameter for LEARN and invoke your business action directly when needed. Do not recursively bind/unbind/SetValue from hardware callbacks.

```python
def onRegister(controller):
    controller.BindControls([
        dict(kind='knob', slot=1, id='app.speed', label='Speed', minimum=0,
             maximum=10, value=5, on_change=changed),
        dict(kind='button', slot=2, id='app.reset', label='Reset', mode='pulse',
             on_change=changed),
    ], group_id='app.controls.v1')
```

Put callback registration in the internal registration DAT and select Python registration mode to recreate it after reload. Parameter mapping restores the saved active Layout/Track/Plugin; the targets table remains the initial source for a new registry. Temporary direct BindControls calls are replaced by saved configuration after extension initialization. BindParameter/BindCallback/Unbind switch back to single-target mode. Binding changes are rejected during LEARN, touch or hardware callback dispatch.

Per-control watchers react to software edits and skip expected hardware writes. Knob input pairs never combine across slots. Touch defers only that knob's motor feedback; releasing applies its pending value. Invalid targets suspend independently; other controls continue. Root Bindingvalid is false if any target is invalid; inspect state rows for the reason.

Hardware button type and TD action mode are separate. Declare `button_type='toggle'` (default) or `'push'` for each button, matching its TYPE in Roto-Setup. This declaration selects the input adapter; it does not change hardware settings. `mode` selects the TD action.

| TD mode | Hardware button_type | Input and feedback |
| --- | --- | --- |
| toggle | toggle | Each latched 0/127 updates the Boolean target; confirm committed LED state and On/Off text immediately. |
| toggle | push | Press sets True, release sets False; confirm each committed state. |
| pulse | toggle | Either latched value triggers one business action (40 ms duplicate debounce); immediately confirm Ready/off after the action. |
| pulse | push | Only a rising press triggers the action; release confirms Ready/off. Repeated held/released states are ignored. |

Pulse business value/output stays zero. Hardware feedback state is separate and there is no LED/text timeout. Pulse with TOGGLE immediately sends Ready/off after each action; PUSH follows press/release. Mapping/session recall initializes Pulse feedback state to zero. Toggle feedback happens after the parameter/callback accepts the value; a failed consumer suspends the target without confirming success. Knob motor echo suppression remains separate.

Hardware-triggered parameter Pulse callbacks are acknowledged to avoid offering during LEARN or triggering the action twice. Consumer Pulse CHOP outputs remain zero; use parameter/callback events.

Groupid controls the device identity. Target hashes include target ID, numeric semantics and mode. Keep IDs stable and unique; a label/path change retains target identity. An old mapping with a changed mode/range is rejected. Disconnect/start clears every control's mapping, half-pairs and touch state; fresh mapping acknowledgements are required, with hardware recall supplying them where learned.

Pulse learn metadata uses Ready at zero and Trigger at the on state. Labels already edited in Roto-Setup are retained without re-LEARN; controls with old cached Ready/Ready or Off/On labels may require re-LEARN or a Roto-Setup edit. Software tests verify both latched values trigger actions, rapid input, control isolation and matching immediate CC/display feedback and absence of delayed reset. Physical acceptance is recorded in HANDOFF.md.

Native custom Pulse callbacks may coalesce within one TD frame. Use a Python callback target when every accepted same-frame MIDI event must execute separately. Parameter watchers acknowledge the coalesced callback once.

Numeric LCD values are rounded to at most three decimal places, with trailing zeros removed (0.12345678 → 0.123, 7.0 → 7). This formatting does not round TD target parameters or callback values.

Roto-Setup PUSH mode does not expose step labels (user-confirmed hardware setup). Ready/Trigger are host-supplied display feedback, not a PUSH configuration requirement. Physical Button 8 verification accepted six press/release pairs as six Pulse actions with held/released LED feedback; LCD text was not separately confirmed.

## Persistent catalog and removal

`GetControlCatalog()` returns detached stored registration data, including destination, bounds, last published value and current session state. Disconnect retains these records. Inspector always projects all 16 physical slots and supports per-COMP pages.

`RemoveControl(id)` deletes one registration; `RemoveAllControls()` returns the removed IDs. Both support offline operation and preserve the target parameter/value. Removed controls have no watcher, offer or input dispatch. Saved table rows/config overrides are removed; saved hooks are filtered until explicit public registration opts the ID back in. Hardware unmap is sent immediately when PLUGIN is ready and replayed on readiness after reconnect. These commands reject LEARN/touch/callback mutation and have no hardware acknowledgement. `ClearLearn` / `ClearAllLearn` still only unmap hardware and retain registration.

An adapter-only `ConfigureControl(button_type=...)` preserves the target identity, acknowledgement and LED state; it sends no metadata/unmap and needs no re-LEARN. Existing range/mode re-LEARN requirements remain. The adapter must match actual hardware TYPE; every latched TOGGLE value triggers a Pulse, whereas PUSH triggers only rising presses.


## Menu parameters

Custom Menu parameters support knobs (quantized option selection) and buttons (Cycle: advance and wrap on each press). Use hardware LEARN, select the destination, then change the menu. Inspector pickers support both kinds. PUSH ignores release/held duplicates; TOGGLE accepts each latched press. Menu ranges are fixed at indices 0..N-1, and SetValue uses those indices. State includes menu_names, menu_labels and value_label. LCD feedback uses the option label. Menu options must have 2..24 unique names and matching labels, following the official Ableton quantized-step limit. Changing names, labels or order suspends the binding; assign and re-learn it.

Cycle LED feedback follows the selected Menu value: the first option is off, all other options are on. PUSH release does not clear a selected option's LED. Software edits and mapping recall send the same state feedback; LCD text identifies the actual option. Pulse retains action/press feedback independently.
