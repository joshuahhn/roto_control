# Lifecycle, demos and state

Connect() starts the owned MIDI child; Disconnect() closes/reaps it. Offerparameter() repeats the active target offer during hardware LEARN. Keep TD playing for frame-based pipe polling.

API sequence:

1. Configure the saved targets table or `registration.onRegister(controller)` hook; call `Applybinding()` to validate/restore it. Direct Bind calls are temporary registrations.
2. Call `Connect()` and wait for the PLUGIN handshake. Previously learned matching IDs may recall automatically; check each `GetControlState(id)['mapped']`.
3. For an unmapped target: open hardware LEARN, touch the configured knob or press the configured button to select its slot, then `Offerparameter(id)`. Keep LEARN open until the matching acknowledgement arrives. Offering Pulse metadata does not execute its action.
4. Exit LEARN before normal control. Hardware input writes the parameter or invokes the callback; software parameter edits/`SetValue(value, id)` send feedback without invoking the hardware callback. Pulse rejects SetValue; invoke the application action directly for software triggers.
5. Read target-unit state with GetValue/GetControlState. Disconnect before replacing/reinitializing source. Saved configuration restores after reload; call Connect explicitly to reopen MIDI.

The first software parameter edit can also offer once during LEARN. Hardware writes do not offer. Mapping is accepted only for the registered identity, kind and slot. Selecting/replacing a binding clears its old mapping; do not bind during LEARN, touch or callback dispatch.

Use `button_type` to match hardware PUSH/TOGGLE, independently of TD `mode`; see controls.md.

At project root:

- base_parameter_demo: press Use this binding, then edit Speed (0–10). Knob changes write Speed; Speed edits drive motor/LCD when mapped.
- base_callback_demo: press Use this binding, edit Speed and press Send Speed to controller. Knob changes update Received, Events and Origin through a Python callback. Software SetValue leaves Events unchanged.

Controller Value is the normalized manual control/monitor. Diagnostics live inside base_state and controller.State. Targetvalue uses the selected target's units. Targetid names that target. Connected/Plugin/Learning/Mapped/Touched describe session state. Bindingvalid and Lasterror expose target/callback failures. Rx counts all MIDI messages, including F8 timing clock; Tx counts outgoing messages. Rejected counts malformed/unsupported mapping packets; Echoblocked counts suppressed physical-input feedback.

A deleted target, readonly/mode change or callback exception suspends that binding and clears mapping. Further target dispatch is stopped. Fix the cause and bind again; Disconnect stays available. Error strings are diagnostics, not stable error codes. A failed SetValue raises as well as reporting its error.

Saved Binding page configuration is restored after initialization (first Tick, or Apply/Connect). Registration hook mode recreates its runtime registration using registration.onRegister(controller). MIDI remains disconnected until Connect. Temporary direct API/demo-button registrations do not change saved setup. Development source DATs stay synced to disk. Use export_component.py for an embedded-code tox with no demo bindings; The MIDI helper is embedded; only Python with the MIDI packages remains external. See portability.md.

## Source upgrades

Disconnect, load changed dependency DAT source, then reinitialize the Extension. Existing host instances can retain old class implementations even when a synced DAT displays new source. Verify the restored setup/runtime before Connect. upgrade_controls.py applies this ordering; it preserves the user-owned targets table and registration hook.

## Sequence verification

`verify_api_sequences.py` builds an isolated six-target fixture without opening MIDI ports. Run build_fixture, wait one TD frame, then exercise. Check the deferred native Pulse callback on the next frame. The saved registration hook also supports extension reinit and tox reload checks. This complements test_api.py with real TD parameters/watchers; synthetic MIDI does not establish physical PUSH acceptance.

Collection restore refreshes watcher OP expressions even when their source text is unchanged, to clear initialization-time unresolved caches. Verify actual watcher OP handles and a direct parameter edit after disk reopen.
