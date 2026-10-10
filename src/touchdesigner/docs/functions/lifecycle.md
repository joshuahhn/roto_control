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

State['Value'] is the normalized monitor; the old outer Control / Value and Offer Value parameters are removed. Use target parameters or SetValue for value changes, and hardware LEARN/Inspector or Offerparameter(id) for learning. Diagnostics live inside base_state and controller.State. Targetvalue uses the selected target's units. Targetid names that target. Connected/Plugin/Learning/Mapped/Touched describe session state. Bindingvalid and Lasterror expose target/callback failures. Rx counts all MIDI messages, including F8 timing clock; Tx counts outgoing messages. Rejected counts malformed/unsupported mapping packets; Echoblocked counts suppressed physical-input feedback.

A deleted target, readonly/mode change or callback exception suspends that binding and clears mapping. Further target dispatch is stopped. Fix the cause and bind again; Disconnect stays available. Error strings are diagnostics, not stable error codes. A failed SetValue raises as well as reporting its error.

Saved Binding page configuration is restored after initialization (first Tick, or Apply/Connect). Python registration mode recreates its runtime registration using registration.onRegister(controller). MIDI remains disconnected until Connect. Temporary direct API/demo-button registrations do not change saved setup. Development source DATs stay synced to disk. Use export_component.py for an embedded-code tox with no demo bindings; The MIDI helper is embedded; only Python with the MIDI packages remains external. See portability.md.

## Source upgrades

Disconnect, load changed dependency DAT source, then reinitialize the Extension. Existing host instances can retain old class implementations even when a synced DAT displays new source. Verify the restored setup/runtime before Connect. upgrade_controls.py applies this ordering; it preserves the user-owned targets table and registration hook.

## Sequence verification

`verify_api_sequences.py` builds an isolated six-target fixture without opening MIDI ports. Run build_fixture, wait one TD frame, then exercise. Check the deferred native Pulse callback on the next frame. The saved registration hook also supports extension reinit and tox reload checks. This complements test_api.py with real TD parameters/watchers; synthetic MIDI does not establish physical PUSH acceptance.

Collection restore refreshes watcher OP expressions even when their source text is unchanged, to clear initialization-time unresolved caches. Verify actual watcher OP handles and a direct parameter edit after disk reopen.

## COMP Follow lifecycle

The existing Tick samples the current Network Editor at 10 Hz, fences uncertain routing, drains bounded MIDI batches and makes one guarded activation decision. Pending intents carry a connection generation; Connect/Disconnect/open failure/child failure clear both TD and hardware requests while retaining saved links and Follow preference. A fresh offline selection can change local context; reconnect recalls that committed context.

The lifecycle Execute DAT has Project Pre Save enabled. `onProjectPreSave` synchronously refreshes Focus links independently of the timeline; a callback name alone is insufficient on TD 2025.33230. Managed component saves and export prepare links explicitly. Startup never opens MIDI or activates from the initial selected COMP. See layouts.md for guards, missing-link and reload policies.

## Owned Inspector lifecycle

The event-driven nested model observes the controller's stable catalog/context
DATs. A view subscribes only to its current local model. Disconnected packaging
releases old subscriptions/runs before initialization, and repeated identical
packaging returns without a reinit. Openinspector validates local ownership and
shows the Fold window without Connect, Activate or target/Action calls. Before
replacing old Lister, save a fresh project recovery and pass a new tox archive
path to the owned build/upgrade entry point. UI source/dock callbacks are embedded.
