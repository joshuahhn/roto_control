# ROTO-CONTROL binding API

Choose single-target Knob 1 mode or a collection of up to eight knobs and eight PLUGIN buttons. Bind a COMP custom parameter or a Python callback; consumers do not handle MIDI. The built-in Value target remains available via Unbind.

Transport uses a managed external Python process. Protocol/session behavior, target-unit conversion and TD integration are separate source modules. Parameter Execute DATs watch registered targets. Value changes are event-driven; Tick checks target validity/path and performs a one-time value resync after a path change.

Diagnostics are inside base_state and available via controller.State, without outer CHOP outputs in the portable tool. Value is normalized 0–1; Targetvalue uses target units. Transport resets on extension reinit. Parameter mapping restores the saved Layout/Track/Plugin; Python registration mode runs the saved registration hook to recreate runtime callables. Direct API registrations remain temporary. Connect is explicit.

Direct hardware LEARN watches new COMP custom parameter edits, offers the edited target and commits the slot reported in the matching acknowledgement. Its observer is disabled outside LEARN. Interactive explicit assignment also uses the Inspector COMP/Parameter pickers and AssignParameter to persist one slot without replacing other mappings. Assigned records live in controller storage and overlay the saved registration on reload. Hardware LEARN selection is still performed on the controller.

Collection configuration lives in base_targets/targets; per-target diagnostics in base_targets/state. Target parameters and callbacks expose values/events; the internal controls_values CHOP remains available for diagnostics. Buttons support Toggle/Pulse; Pulse actions use parameter or callback events. Callback collection registration is recreated by the same saved registration hook.

See functions/controls.md for collection registration, functions/binding.md for registration and functions/lifecycle.md for connection, learning, failures and demos. New binding hardware acceptance is recorded separately from simulated MIDI checks in HANDOFF.md.

The public interface adds GetValue(id) and GetControlState(id). Saved registration.onRegister supports mixed parameter/callback controls. See functions/portability.md for exporting an embedded-code component independent of demo layout.
