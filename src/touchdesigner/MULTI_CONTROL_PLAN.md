# One-page controls milestone

Scope: eight assignable knobs and eight assignable buttons in PLUGIN mode. Keep the tested single-target mode and API working. Navigation/transport/MIX and multiple pages remain separate scope.

Official Ableton reference commit 2d43a72c6699983080f8765292498502ff08be57: CONTROL_MAPPED carries parameter index/hash, control kind at byte 8 (knob 0, button 1), slot at byte 9 (0..7), and macro flag at byte 10. Knob CCs are 12..19/44..51, buttons 20..27, touches 52..59. PARAM_VALUES starts with kind/slot. Acknowledgement must match both target identity and configured control; do not infer mappings from touches.

Add Collection mode with stable group ID. A saved internal targets table contains kind, slot, id, target COMP, parameter, mode, min/max and label. Numeric parameters support knobs; Toggle and Pulse support buttons. Python callers can register the same controls using BindControls(specs, group_id=...). SetValue(value, id=...) and Offerparameter(id=...) address registered targets. Old no-id methods retain Knob 1 behavior.

Use one watcher per control under base_targets, not per-frame parameter value polling. Target paths are resolved relative to the controller, or as absolute TD paths. Runtime diagnostics go in a separate state table; public control output has knob1..knob8 and button1..button8 channels in target units. Keep outer custom parameters free of diagnostics.

Button Toggle follows latched input state. Pulse acts on each latched button message, with 40 ms duplicate-message debounce and a 0.2-second LED flash; physical press/release behavior must be verified against the user's firmware before declaring acceptance. Callback pulse events identify target ID, pulse kind and hardware origin.

Phases: pure collection protocol/adapter tests; builder upgrade and saved table restoration; live isolation/echo/error tests; hardware learn of two knobs plus Toggle/Pulse buttons and repeated presses; remaining slots and reconnect/reopen; docs/layout/save.

New source DATs: collection_protocol and controls under the controller. New base_targets owns targets/state tables, sixteen Parameter Execute watchers, controls_values Script CHOP -> null_controls -> out_controls. Root select_controls -> null_controls -> out_controls provides a second output. Positions are allocated outside existing groups and verified using actual bounds.
