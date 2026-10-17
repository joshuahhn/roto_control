# ROTO-CONTROL Python context

## Purpose

Python host for ROTO-CONTROL in TouchDesigner, with Layout/Track/Device mapping, parameter and callback targets, an owned compact Inspector, Action presets and slot-value Snapshots. Official Ableton/Logic integration behavior remains a reference.

This current overview was reconciled against source `2de08c9` (2026-10-12). Source checkout, embedded DATs and saved artifacts can differ: identify the relevant baseline before changing behavior. Use [projects/README.md](projects/README.md) for the canonical project entry and its receipt, and [HANDOFF.md](HANDOFF.md) for dated acceptance scope.

## Main-screen page feedback

Parameter mapping briefly shows the common TD custom page of acknowledged controls on the main screen, then restores the Track name after two seconds on a safe Tick. Ambiguous or unavailable pages use the Track name. See [Layouts](docs/functions/layouts.md#main-screen-context) and the dated acceptance in [HANDOFF.md](HANDOFF.md#automatic-parameter-page-hint--2026-10-17). The [generic export and receipt](exports/README.md) distribute both caption and LEARN metadata changes. The checked-in demo `.toe` retains its separate older project receipt; the locally saved working project includes both changes.

## LEARN metadata

Immutable `protocol.LearnParameter` describes an offer independently of session state. Registered controls, Free LEARN and the legacy Host use the pure `learn_parameter_message(parameter, value)` encoder; `Controls.specs` passes Menu labels explicitly. Free LEARN retains metadata for pending offers without constructing a temporary session-enabled Control or inspecting `formatter.__self__`. Existing index/hash/Menu signatures, session guards, matching ACK commits, routing and target writes keep their established paths. Native encoding/reload evidence and the limit on physical LEARN acceptance are recorded in [HANDOFF.md](HANDOFF.md#learn-metadata-integration--2026-10-17).

## Track group colors

This source branch adds a fixed 83-entry ROTO palette color per Track group, with a Layout-page `Track color` menu, read-only `Track BG preview` RGB parameter and `SetTrackColor` API. It reuses Track details/selection packets; omitted colors retain the original palette 0. The worktree's generic export/receipt and the local working project were refreshed through TD after physical red/purple Track acceptance. This feature builds on merged PR #23; this branch's checked-in demo toe retains its older receipt. See [Track group colors](docs/functions/layouts.md#track-group-colors) for scope and guards, and the [save/export handoff](HANDOFF.md#track-color-bg-preview--2026-10-17) for artifact identity.

## Architecture

The independent [MIX controls](docs/functions/mix.md) add versioned descriptions,
Low/Mid analysis and wired Layer Mix float routing with 10 Hz native meters.
One MIX source/style profile is active at a time. Layer input-order/Setup changes
require explicit reconfiguration; Layer Operation/Swap and audio remain planned. `mix_runtime`
also maps overview On/Off buttons to each band's Active Toggle; FUNC buttons
retain native item selection. It
owns MIX mode/view/touch state; the extension keeps the existing external MIDI
owner and mutually exclusive MIX/PLUGIN business dispatch. PLUGIN Layouts,
Follow and LEARN remain separate. See the latest HANDOFF for native versus
physical evidence. The generic export adopts this slice with empty MIX data;
the checked-in demo project retains its separate older receipt.

`protocol.Host` owns protocol and session state behind complete-message send/receive and normalized parameter callbacks and configurable target identity/label/display. binding.Binding converts target units and handles target writes/callback dispatch. `RotoPythonExt` adapts that interface to TD parameters and a managed external MIDI process. The child owns mido/rtmidi ports; nonblocking pipes keep MIDI I/O out of TD's native MIDI library. Internal base_state owns readonly diagnostics. The generic controller has no CHOP input/output connectors; public State and APIs expose runtime data. Saved Binding page configuration is reapplied after extension initialization; callback mode runs the user-editable registration DAT.

Binding UI now exposes only Parameter mapping (`collection`: Free LEARN, Inspector, Layouts/Tracks) and Python registration (`callback`: saved reconstruction hook). Legacy single-target APIs remain callable; their outer configuration fields are removed after disconnected migration. `setup.configure_ui` is the shared builder/export upgrade. Native input-only receive retesting and its reproducible runner are documented in `diagnostics/native_midi/README.md`; production continues to use the external backend.

The outer Control page is also removed. `_value_parameter` uses legacy outer Value during migration and internal `base_state.Manualvalue` afterward. `setup.remove_control_ui` migrates saved self-Value destinations with identities intact. Manualvalue is compatibility backing state, excluded from public State; it has no second manual-input callback path. Existing target watchers and SetValue/Offerparameter APIs remain.

Outer pages are Connection, Binding, Layout and Device. `setup.combine_context_pages` keeps the saved mapping set and Track group on Layout (14 fields, including Track color and its RGB preview), with Device/Focus/name management on a separate Device page (6 fields), preserving parameter names, values, enable states and callbacks. Builders/upgrades/exports share this presentation helper. Active Device (SEL) selects an independent Plugin; Device Focus COMP links its tool and defaults its Device display name to the COMP name. Active Track group (FUNC) and Layout names remain independent. The `roto_device` OP tag registers a COMP as its own Device in Active Layout/Track while idle, reusing existing Focus links. Removing a tag retains saved mappings. Existing Track Focus links migrate to their Device. Delete pulses use an asynchronous native popup rather than permanent Yes/No parameters.

## Source Files

- `scripts/build_network.py`: explicit-parent builder; embedded source snapshots and README; binding restore
  completes before return, so immediate caller assignments survive the first Tick.
- `code/py/roto_python/protocol.py`: protocol and one-parameter host.
- `code/py/roto_python/RotoPythonExt.py`: TD adapter and process lifecycle.
- `code/py/roto_python/*_callbacks.py`: parameter/frame/exit callbacks.
- `scripts/midi_process.py`: external MIDI owner; exact port resolution.
- `scripts/upgrade_network.py`: in-place disconnected upgrade and demo construction.
- `code/py/roto_python/binding.py`: target metadata/conversion and adapters.
- `tests/runtime/test_binding.py`: binding behavior, failures and target identity checks.
- `tests/runtime/test_protocol.py`: behavior tests through MIDI and parameter interfaces.

## Constraints

No legacy host imports, no automatic hardware connection, no arbitrary parameter writes. Only acknowledged matching target/kind/slot mappings are accepted; identities include target id and value semantics. Invalid or foreign SysEx is ignored/counted. Runtime state is extension-owned and never persisted as a connected session. Target configuration/custom parameters and registration hook source persist; runtime callback objects do not. This prototype is macOS-oriented; nonblocking pipe behavior on other platforms is unverified. Hardware LEARN may store an assignment on the controller and is explicitly triggered by the user. No serial/firmware/configuration writes.

## Verification

Follow [AGENTS.md](../../AGENTS.md#change-scoped-validation) for the authoritative change-scoped policy and [tests/README.md](tests/README.md) for test entry points. Native checks cover only affected TD behavior; physical checks cover only affected MIDI/ACK/feedback behavior, including indirect changes. Record the baseline, changed paths and evidence scope; reuse unaffected acceptance. Documentation changes need diff/link/consistency review, not live TD or hardware acceptance.

## Collection architecture

collection_protocol.CollectionHost shares the established session handshake and holds independent Control state. controls.Controls validates adapters and table specifications. base_targets contains persistent targets, 16 event-driven watchers, per-target runtime state, bounded real button/mapping RX diagnostics. Target values are available through the runtime APIs; historical CHOP presentation is not the current generic interface. Existing single-target API and saved configuration remain available. Buttons have Toggle/Pulse modes; Pulse uses native hardware TOGGLE with immediate latched CC and Trigger/Ready display feedback, no TD timeout; both latched values trigger actions. No MIX transport buttons or firmware configuration is in scope.

API sequence is documented in docs/functions/lifecycle.md. Button input declares hardware button_type separately from TD action mode; targets table column defaults existing buttons to toggle. Shared button confirmation follows successful consumer dispatch, while knobs retain motor echo suppression.

Internal Inspector reads persisted target data through GetControlCatalog; Disconnect retains destinations/ranges/values. All 16 physical slots remain visible, with per-COMP pages and Unassigned placeholders. The owned compact Inspector packages its model, Fold view and Popup inside each controller. Connection Open Inspector opens it. Build entrypoint is scripts/build_inspector.py; current view/model sources live in prototypes/inspector. The former Lister presentation is historical.

Inspector Clear uses RemoveControl / RemoveAllControls: delete registration, disable watcher, suppress saved-hook restore and replay outgoing PLUGIN 0E on reconnect. ClearLearn / ClearAllLearn retain registration as separate hardware-only APIs. Hardware persistence is verified by reconnect, not an unmap acknowledgement.

Mapped parameter COMP visual claims are handled by base_targets/mapping_marks (source code/py/roto_python/base_targets/mapping_marks.py), independently of Inspector UI. Runtime OP IDs/path pairs distinguish controller claims; roto_mapped/cyan ownership restores original styling after the last active mapping.


Inspector confirmation is UI-only; direct removal and hardware-only clear APIs execute without UI confirmation. ConfigureControl validates/replaces one collection adapter, unmaps only a changed mapped slot and persists overrides by ID. requires_relearn survives restore until matching acknowledgement. Inspector highlights pending configuration and edits through this common API. Value writes do not require re-LEARN.

Inspector COMP/Parameter pickers discover compatible custom parameters on demand. AssignParameter changes one slot and stores generated stable identities/relative destinations in parameter_assignments; restore overlays these records over the saved table/hook. Collection runtime objects for other slots are retained. Assignments can occur during hardware LEARN and the Inspector automatically offers the selected target; no Applybinding is required. Clear removes the assignment overlay and tombstones its superseded source ID.

FreeLearner retains pending parameter offers independently by index/hash during hardware LEARN. The learn_parameters Parameter Execute DAT watches compatible custom parameter edits only during connected PLUGIN LEARN, scoped to the linked Device's COMP and descendants (nested linked Devices own their subtrees). Unlinked explicit Devices retain manual registration compatibility. Matching CONTROL MAPPED index/hash commits the reported kind/slot via AssignParameter, then the common parser acknowledges it; foreign COMP edits and stale Focus ownership cannot populate the current library. Persisted assignments carry explicit parameter indices (reserved dynamic indices start at 128); slots no longer imply the wire index. Direct parameter edits require no Inspector action.


## Active repository

Continue development in joshuahhn/roto_control, src/touchdesigner. The nin-lab location is a migration backup. Documentation embedding uses scripts/td_project_docs.py. Canonical entries are projects/current/ROTO-CONTROL.toe and exports/roto_python.tox; use the project receipt and dated save/export evidence to identify their source baseline. Markdown-only changes are embedded during the next authorized save/export.

## Historical architecture and milestone notes

The dated sections below preserve implementation history. Their source-only, pending, local-preparation and numbered-artifact statements describe that checkpoint, not current requirements. Later owned Inspector, Snapshot, #15 and #3–#5 results in HANDOFF.md supersede earlier status for the same case. Reuse only the scope actually accepted; outstanding limitations are listed at the top of HANDOFF.md.


## Multi-Track registry v2 (2026-10-06)

Historical v2 baseline: Layouts own ordered Tracks; each Track originally owned one Plugin with independent parameter mappings. See the v3 section below for current multi-Device behavior. layouts.py owns versioned migration and Track metadata/selection; protocol.Host delegates Track announcements through tracks_callback. Hardware Track pages are distinct from selection. Only the current routing Track's Plugin is advertised. Under LOCK, selected Track and routing Track may differ; physical behavior remains pending acceptance. Inspector context and clear confirmations are Plugin-scoped. See docs/functions/layouts.md and multitrack_native_verification.json. The .32 baseline is historical; consult the project receipt and dated HANDOFF save/export entries for artifact identity.

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
#11 migration, excluding #13. `scripts/build_inspector.py` now owns model/views under the
controller's `inspector` wrapper and exposes Connection `Openinspector`. Stable
headless catalog/context publication stays; old Palette presentation is archived
before disconnected upgrade. See `docs/plans/owned-inspector-packaging.md`. Source
checks do not constitute native packaging acceptance or canonical promotion.

## Slot-value Snapshot presets — #13 source (2026-10-09)

Snapshots save normalized current-page control positions and recall through the saved Device's **current** mappings. This follows the user's explicit Brightness→Blur remap clarification, superseding original target-identity preparation. No target registry/Relink or Snapshot-specific registration hook; JSON slot values rebuild providers in both existing setup modes before mapping restore. Existing Action dispatch/guards/results/feedback, owner scopes and Inspector freshness remain authoritative. See [Snapshot contract](docs/functions/snapshots.md). Native/save-load/export/physical acceptance is separately pending; no shared live promotion.

### Snapshot + Follow COMP source composition

Root accepted Snapshot response51a83 by separate parent adjudication (r1 Spec findings retained), then authorized composition with source-reviewed Follow COMP v4 TREE7e12cb6. Shared command/model/UI now preserve both Snapshot capture-token guards and native Follow preference/button; LIVE/BROWSE remains independent. Five bounded interop regressions use the actual command/observer/UI seams on fake TD boundaries. Snapshot delta now compares accepted Follow7e12; backend Follow bytes stay exact. Root coordinated native/physical acceptance remains separately pending; no #11 migration is added.

### Accepted Follow v5 policy with Snapshot guards preserved

Root source-approved Follow v5 TREE81ea0aca changes only automatic TD-origin routing: it skips TOUCH wait, retaining LOCK/LEARN/ownership/session/fresh ACK and manual/hardware/default guards. Composed as exact policy hunks over accepted r3 TREE5da574. Only RotoPythonExt.BindControls overlaps Snapshot's runtime file; its method is exactv5 and all Snapshot methods/core/shared UI remain exactr3. Snapshot capture/edit/recall preflight still requires touch release. One bounded interop regression covers this distinction; no new setting, target registry, dispatcher or #11 implementation. Native acceptance is separately queued by Root.

### Snapshot composed onto merged owned Inspector

#13 now composes accepted Snapshot r4 TREE27ebd30 onto merged fork main d7888fe (owned Inspector + closed #11). Owned Openinspector/headless publication/local lifecycle, current controls/layouts/Follow/migration are preserved; no old Lister revival. Strict packaging verifies snapshots DAT source/required flags and classifies embedded Snapshot docs. Public Knobs remain Float/Int/Menu; BUTTON PUSH/TOGGLE/Pulse/Action capture excluded, no public Toggle-Knob policy expansion. Source-only candidate and three small fake-TD seam checks precede Root-coordinated direct native acceptance. Earlier composition/history/pins remain unchanged.
