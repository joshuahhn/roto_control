# ROTO-CONTROL Python context

## Purpose

Build a new Python host from scratch, using official Ableton/Logic integration behavior as reference. First milestone accepted: handshake and Value controlled by Knob 1. Current milestone: up to 8 knobs and 8 buttons with parameter/callback targets; software verification passed; physical Knob 2/8 and Button 1/2/8 acceptance passed. Other slots have software coverage.

## Architecture

`protocol.Host` owns protocol and session state behind complete-message send/receive and normalized parameter callbacks and configurable target identity/label/display. binding.Binding converts target units and handles target writes/callback dispatch. `RotoPythonExt` adapts that interface to TD parameters and a managed external MIDI process. The child owns mido/rtmidi ports; nonblocking pipes keep MIDI I/O out of TD's native MIDI library. Internal base_state owns readonly diagnostics; Parameter CHOP, selective Null and outCHOP expose its channels. Saved Binding page configuration is reapplied after extension initialization; callback mode runs the user-editable registration DAT.

Binding UI now exposes only Parameter mapping (`collection`: Free LEARN, Inspector, Layouts/Tracks) and Python registration (`callback`: saved reconstruction hook). Legacy single-target APIs remain callable; their outer configuration fields are removed after disconnected migration. `setup.configure_ui` is the shared builder/export upgrade. Native input-only receive retesting and its reproducible runner are documented in `diagnostics/native_midi/README.md`; production continues to use the external backend.

The outer Control page is also removed. `_value_parameter` uses legacy outer Value during migration and internal `base_state.Manualvalue` afterward. `setup.remove_control_ui` migrates saved self-Value destinations with identities intact. Manualvalue is compatibility backing state, excluded from public State; it has no second manual-input callback path. Existing target watchers and SetValue/Offerparameter APIs remain.

Outer pages are Connection, Binding, Layout and Device. `setup.combine_context_pages` keeps the saved mapping set and Track group on Layout (10 fields), with Device/Focus/name management on a separate Device page (6 fields), preserving parameter names, values, enable states and callbacks. Builders/upgrades/exports share this presentation helper. Active Device (SEL) selects an independent Plugin; Device Focus COMP links its tool and defaults its Device display name to the COMP name. Active Track group (FUNC) and Layout names remain independent. The `roto_device` OP tag registers a COMP as its own Device in Active Layout/Track while idle, reusing existing Focus links. Removing a tag retains saved mappings. Existing Track Focus links migrate to their Device. Delete pulses use an asynchronous native popup rather than permanent Yes/No parameters.

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

FreeLearner retains pending parameter offers independently by index/hash during hardware LEARN. The learn_parameters Parameter Execute DAT watches compatible custom parameter edits only during connected PLUGIN LEARN, scoped to the linked Device's COMP and descendants (nested linked Devices own their subtrees). Unlinked explicit Devices retain manual registration compatibility. Matching CONTROL MAPPED index/hash commits the reported kind/slot via AssignParameter, then the common parser acknowledges it; foreign COMP edits and stale Focus ownership cannot populate the current library. Persisted assignments carry explicit parameter indices (reserved dynamic indices start at 128); slots no longer imply the wire index. Direct parameter edits require no Inspector action.


## Active repository

Continue development in joshuahhn/roto_control, src/touchdesigner. The nin-lab location is a migration backup. Documentation embedding uses the local scripts/td_project_docs.py; current project is .32.toe and portable export is .20.tox.


## Multi-Track registry v2 (2026-10-06)

Historical v2 baseline: Layouts own ordered Tracks; each Track originally owned one Plugin with independent parameter mappings. See the v3 section below for current multi-Device behavior. layouts.py owns versioned migration and Track metadata/selection; protocol.Host delegates Track announcements through tracks_callback. Hardware Track pages are distinct from selection. Only the current routing Track's Plugin is advertised. Under LOCK, selected Track and routing Track may differ; physical behavior remains pending acceptance. Inspector context and clear confirmations are Plugin-scoped. See docs/functions/layouts.md and multitrack_native_verification.json. The .32 baseline above is historical; consult the final HANDOFF entry for current artifacts.

## Live Select COMP (2026-10-07)

text_comp_follow.CompFollower owns optional Device Focus links, current-pane selection sampling and a single latest-intent arbiter shared with hardware Track/Device selection. Binding Followcomp defaults off only on creation/export; Layout Focuscomp edits the active Device link. SetPluginComp, SelectComp and GetCompContext expose the link/context; SetTrackComp remains a compatibility wrapper for the Track’s active Device. No additional Binding mode or signal wires.

Selection/unlock fences immediately suppress business input, mapping/page recall, FreeLearner commits and old feedback; keep session/LOCK/LEARN/touch-release traffic. Drain buffered complete lines before activation; partial inbound lines retain their ingress epoch. Disconnect/open failure/child failure clear pending intents and selected/routing divergence through connection generations. Domain failures do not Disconnect; failed rollback/observer pauses until Apply setup repair. Saved Follow=True restores baseline only. Project Pre Save is explicitly enabled on the lifecycle DAT; its synchronous callback refreshes live links even while paused. Generic exports clear links/preference. Native and synthetic evidence are in comp_follow_native_verification.json; physical Follow acceptance is pending.

## Independent Device context v3 (2026-10-07)

Each Track explicitly groups 1..127 Plugins with separate active Plugin, identities, targets and off-page library. Focus links are Plugin-scoped; sole selected COMP resolves to (Layout, Track, Plugin). Hardware SEL uses eight-item Device banks independently of Track browsing. PLUGIN 04 browses; PLUGIN 07 queues a page-relative Device selection. The existing arbiter/fences/session generations cover same-Track Device transitions. LOCK stops automatic Follow and hardware Track routing, but explicit hardware Device selection can replace the locked Device inside the routing Track after LEARN/touch/backlog guards. Selected Track divergence persists; unlock follows current selection. Reverse hardware-to-TD UI selection remains deferred.

GetPlugins/CreatePlugin/SelectPlugin/RenamePlugin/RemovePlugin/SetPluginComp are promoted. v2 links move from Track to its sole Plugin without merging existing mapping variants or changing any stable ID/hash. Linked names follow COMP rename; manual names remain supported, Layout rename is independent. Upgrade captures current registry before replacing source. Software/native evidence and artifacts are recorded in the final HANDOFF entry.

## Named Action presets — source-only #12 (2026-10-08)

RegisterAction/AssignAction/RecallAction share the existing Pulse Button input path and return structured success/failure results. Layout/Device/page libraries persist explicit action IDs plus mapping metadata, never runtime callables. Both setup modes rebuild entry points from registration.onRegisterActions before mappings restore. Anonymous callbacks retain their legacy behavior. See docs/functions/actions.md for the stable consumer contract; Snapshot values and COMP ownership remain #13/#9 scope. Source tests pass; coordinated native fixture/reload/export and physical acceptance remain pending. Shared live/canonical artifacts have not been updated.

## Owned Inspector composition (local preparation)

The packaging candidate composes accepted #12 Actions, #10 v5 Follow and corrected
#11 migration, excluding #13. `build_inspector.py` now owns model/views under the
controller's `inspector` wrapper and exposes Connection `Openinspector`. Stable
headless catalog/context publication stays; old Palette presentation is archived
before disconnected upgrade. See `docs/plans/owned-inspector-packaging.md`. Source
checks do not constitute native packaging acceptance or canonical promotion.
