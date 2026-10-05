# Binding registration

```python
controller = op('roto_python')
controller.BindParameter(target.par.Speed, id='visual.speed', minimum=0, maximum=10)
controller.SetValue(7)  # target units; clamps to configured range


def changed(event):
    print(event['id'], event['value'], event['origin'])

controller.BindCallback(id='app.speed', label='Speed', minimum=0, maximum=10,
                        value=5, on_change=changed)
controller.SetValue(7)  # motor/state only; does not call changed
controller.Unbind()    # restore built-in normalized Value target
```

Methods are promoted on the controller COMP. One registration replaces the active binding. Bind methods return its id; SetValue returns the clamped value. Validate registrations before mutating the previous binding.

BindParameter accepts a writable CONSTANT/BIND custom Float or Int Par handle. Label defaults to the Par label; omitted limits use normMin/normMax. Limits must be finite, increasing and within enabled target and bind-master clamp bounds. Integer limits must be integers; integer writes round to steps. Current wire feedback remains continuous 14-bit, with integer conversion in software.

Use a stable nonempty id independent of operator paths/display labels. Wire identities include id/range/integer semantics; a different target cannot use an old acknowledged mapping. A reused id with changed value semantics is rejected within the current extension session. Assign distinct ids to distinct targets. The built-in target preserves the original Value/device hashes for compatibility.

The callback receives {'id': id, 'value': target_value, 'origin': 'hardware'} only when a hardware value changes. Callback runs on TD's main thread; keep it short. Do not recursively SetValue, Bind or Unbind inside it. Callback objects are not serialized. Put registration in the internal registration DAT onRegister(controller) and select Registration hook mode to recreate them after reload.

The external parameter watcher skips hardware/software write echoes. Target rename resyncs after the OP reference changes. A TD Collapse Selected/restructure can reinitialize the controller extension; saved setup is reapplied after initialization; direct API registrations need registering again. EXPRESSION/EXPORT modes, readonly and nonnumeric parameters are rejected. BIND references are supported only when their same-style Par chain resolves to a writable CONSTANT master. Missing/cyclic/non-Par masters or driven masters are rejected; no bind expression or master mode is replaced.

Binding replacement/Unbind is rejected while touched or learning. Bind while idle and follow LEARN again unless the controller acknowledges the new identity. Disconnect keeps the active binding within the extension session; extension reload restores the saved Binding page configuration, rather than any temporary direct API registration.

## Saved parameter setup

Set Setupmode to parameter, Targetcomp to the target COMP, Targetpar to its custom parameter name, and Bindingid to a stable ID. Useparrange selects normMin/normMax; otherwise Minimum/Maximum are used. Targetlabel is optional. Applybinding validates and applies this configuration. These custom parameters persist in the project/tox. In Registration hook mode the saved internal registration DAT must call BindParameter, BindCallback or BindControls; mixed parameter/callback collections are supported. Invalid setup exposes an internal Lasterror and prevents Connect until corrected/applied.

State is a snapshot dictionary (controller.State); diagnostics are not outer custom parameters. For example controller.State['Mapped'] and controller.State['Targetvalue'].

## Query interface

`GetValue(id=None)` returns the last tracked value in target units. `GetControlState(id=None)` returns a detached dictionary with id, kind, slot, mode, label, value, normalized, minimum, maximum, mapped, touched, valid, connected, plugin, error, button_type, binding_type, comp, parameter and requires_relearn. Querying does not write parameters or dispatch callbacks. An omitted ID selects Knob 1; if there is no Knob 1, specify an ID. Unknown IDs raise ValueError, including in single-target SetValue/Offerparameter. Built-in Value uses ID `Value`.

`State` remains aggregate transport diagnostics; use GetControlState for individual mapping/validity. Pulse GetValue/CHOP output stays zero; consume Pulse events. Query values are the last tracked state, not a synchronous forced parameter poll.

Saved Registration hook mode keeps the legacy menu value `callback` for compatibility. The hook may register a parameter, callback or mixed collection. It must make a new registration on each restore. Direct registration calls remain temporary; saved hooks run after extension initialization.

A failed saved registration suspends the whole host: all target queries report invalid/unmapped and the registration error. Correct the setup and Applybinding before reconnecting. A consumer/write failure suspends only that target in a collection.

GetControlStates() lists all registered target snapshots; see inspector.md for destination fields and their meaning.

`ClearLearn(id=None)` requests hardware unmap for one registered control (omitted ID selects Knob 1). It keeps TD registration/value and returns True once the command is queued. It requires connected PLUGIN, rejects hardware callback recursion, LEARN mode and touch on that control, and clears pending pairs/feedback for that control. Unknown IDs raise; failed send does not report local success. The command is current-page scoped and has no hardware acknowledgement. See inspector.md for persistence verification.


`ConfigureControl(id, *, minimum=None, maximum=None, mode=None, button_type=None)` edits one collection target through validated adapters and persists overrides by ID. No-op edits preserve its mapping. Changed range/TD mode requires re-LEARN and clears only that control if mapped. An input-adapter-only edit preserves its mapping/feedback state and needs no re-LEARN. Native styles/clamps must match; bounds must include its current value. Guarded during LEARN/touch/hardware callbacks. `GetControlState()['requires_relearn']` remains true through save/reinit until a matching mapping acknowledgement.

`ClearAllLearn()` preflights connected PLUGIN, no LEARN and no touched controls, then requests ClearLearn for every registered control. Returns a tuple of IDs; target registrations and values remain. Transport failure mid-batch can be partial. Direct APIs execute without UI confirmation; Inspector asks Yes/No.
