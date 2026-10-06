# ROTO-CONTROL Python context

## Purpose

Build a new Python host from scratch, using official Ableton/Logic integration behavior as reference. First milestone accepted: handshake and Value controlled by Knob 1. Current milestone: up to 8 knobs and 8 buttons with parameter/callback targets; software verification passed; physical Knob 2/8 and Button 1/2/8 acceptance passed. Other slots have software coverage.

## Architecture

`protocol.Host` owns protocol and session state behind complete-message send/receive and normalized parameter callbacks and configurable target identity/label/display. binding.Binding converts target units and handles target writes/callback dispatch. `RotoPythonExt` adapts that interface to TD parameters and a managed external MIDI process. The child owns mido/rtmidi ports; nonblocking pipes keep MIDI I/O out of TD's native MIDI library. Internal base_state owns readonly diagnostics; Parameter CHOP, selective Null and outCHOP expose its channels. Saved Binding page configuration is reapplied after extension initialization; callback mode runs the user-editable registration DAT.

## Source Files

- `build_network.py`: explicit-parent builder; source-synced code DATs and embedded README.
- `code/py/roto_python/protocol.py`: protocol and one-parameter host.
- `code/py/roto_python/RotoPythonExt.py`: TD adapter and process lifecycle.
- `code/py/roto_python/*_callbacks.py`: parameter/frame/exit callbacks.
- `midi_process.py`: external MIDI owner; exact port resolution.
- `upgrade_network.py`: in-place disconnected upgrade and demo construction.
- `code/py/roto_python/binding.py`: target metadata/conversion and adapters.
- `test_binding.py`: binding behavior, failures and target identity checks.
- `test_protocol.py`: behavior tests through MIDI and parameter interfaces.

## Constraints

No legacy host imports, no automatic hardware connection, no arbitrary parameter writes. Only acknowledged matching target/kind/slot mappings are accepted; identities include target id and value semantics. Invalid or foreign SysEx is ignored/counted. Runtime state is extension-owned and never persisted as a connected session. Target configuration/custom parameters and registration hook source persist; runtime callback objects do not. This prototype is macOS-oriented; nonblocking pipe behavior on other platforms is unverified. Hardware LEARN may store an assignment on the controller and is explicitly triggered by the user. No serial/firmware/configuration writes.

## Verification

Protocol unit tests cover handshake, metadata, input pairing, mapping validation, touch and echo suppression. Live TD checks must additionally prove extension promotion, callbacks, CHOP output, process cleanup and errors. Physical knob input, LCD, LEARN and motor follow require controller acceptance and must be recorded separately in HANDOFF.md.

## Collection architecture

collection_protocol.CollectionHost shares the established session handshake and holds independent Control state. controls.Controls validates adapters and table specifications. base_targets contains persistent targets, 16 event-driven watchers, per-target runtime state, bounded real button/mapping RX diagnostics and target-unit CHOP output. Existing single-target API and saved configuration remain available. Buttons have Toggle/Pulse modes; Pulse uses native hardware TOGGLE with immediate latched CC and Trigger/Ready display feedback, no TD timeout; both latched values trigger actions. No MIX transport buttons or firmware configuration is in scope.

API sequence is documented in docs/functions/lifecycle.md. Button input declares hardware button_type separately from TD action mode; targets table column defaults existing buttons to toggle. Shared button confirmation follows successful consumer dispatch, while knobs retain motor echo suppression.

Internal Inspector reads persisted target data through GetControlCatalog; Disconnect retains destinations/ranges/values. All 16 physical slots remain visible, with per-COMP pages and Unassigned placeholders. External Lister config lives inside the inspector wrapper. Build entrypoint includes build_inspector.py; Inspector source is code/py/roto_python/inspector/inspector_data.py.

Inspector Clear uses RemoveControl / RemoveAllControls: delete registration, disable watcher, suppress saved-hook restore and replay outgoing PLUGIN 0E on reconnect. ClearLearn / ClearAllLearn retain registration as separate hardware-only APIs. Hardware persistence is verified by reconnect, not an unmap acknowledgement.

Mapped parameter COMP visual claims are handled by base_targets/mapping_marks (source code/py/roto_python/base_targets/mapping_marks.py), independently of Inspector UI. Runtime OP IDs/path pairs distinguish controller claims; roto_mapped/cyan ownership restores original styling after the last active mapping.


Inspector confirmation is UI-only; direct removal and hardware-only clear APIs execute without UI confirmation. ConfigureControl validates/replaces one collection adapter, unmaps only a changed mapped slot and persists overrides by ID. requires_relearn survives restore until matching acknowledgement. Inspector highlights pending configuration and edits through this common API. Value writes do not require re-LEARN.

Inspector COMP/Parameter pickers discover compatible custom parameters on demand. AssignParameter changes one slot and stores generated stable identities/relative destinations in parameter_assignments; restore overlays these records over the saved table/hook. Collection runtime objects for other slots are retained. Assignments can occur during hardware LEARN and the Inspector automatically offers the selected target; no Applybinding is required. Clear removes the assignment overlay and tombstones its superseded source ID.

FreeLearner owns a pending unregistered parameter offer during hardware LEARN. A global learn_parameters Parameter Execute DAT watches custom parameter edits only during connected PLUGIN LEARN. Matching CONTROL MAPPED index/hash commits the reported kind/slot via AssignParameter, then the common parser acknowledges it. Persisted assignments carry explicit parameter indices (reserved dynamic indices start at 128); slots no longer imply the wire index for these targets. Direct parameter edits require no Inspector action.


## Active repository

Continue development in joshuahhn/roto_control, src/touchdesigner. The nin-lab location is a migration backup. Documentation embedding uses the local scripts/td_project_docs.py; current project is .32.toe and portable export is .20.tox.


## Multi-Track registry v2 (2026-10-06)

Layouts own ordered Tracks; each Track currently owns one Plugin with independent parameter mappings. layouts.py owns versioned migration and Track metadata/selection; protocol.Host delegates Track announcements through tracks_callback. Hardware Track pages are distinct from selection. Only the current routing Track's Plugin is advertised. Under LOCK, selected Track and routing Track may differ; physical behavior remains pending acceptance. Inspector context and clear confirmations are Plugin-scoped. See docs/functions/layouts.md and multitrack_native_verification.json. The .32 baseline above is historical; consult the final HANDOFF entry for current artifacts.
