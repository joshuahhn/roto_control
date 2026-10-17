# ROTO-CONTROL Python context

## Purpose

Python host using official Ableton/Logic integration behavior as reference. Read this document as context for the local source, not proof that source, saved artifacts and remote main are identical. Current artifact entry is [OPEN_PROJECT.md](OPEN_PROJECT.md); dated acceptance and unresolved limits are in [HANDOFF.md](HANDOFF.md).

## Checkout and artifact scope

Checked 2026-10-12: this local main is at `1cb09d9` with uncommitted changes; GitHub/origin main is `40ac7a4` and includes issue #15 via merged PR #17 plus later fixes. Local main is 22 commits behind. Synchronizing it is separate work that must preserve local edits and artifacts.

The local source still builds the Lister Inspector. The current saved project contains the owned Inspector candidate installed separately, as recorded on 2026-10-11. Do not infer saved runtime parity from this checkout or apply a builder to the current project without resolving which source/artifact is intended. The architecture below describes local source; historical milestones are not current validation gates.

On 2026-10-17 the saved runtime received the automatic parameter-page caption change, then the LEARN metadata refactor. [PR #23](https://github.com/joshuahhn/roto_control/pull/23) now publishes both changes as source/tests/docs plus the synchronized generic export/receipt at `acc7a5c`; its checked-in demo toe retains its older independent project receipt. The local working-project receipt identifies caption source `e6a5c2f` plus [the scoped LEARN patch](upgrade/learn_metadata_e6a5c2f.patch), runtime hashes and recovery. Its eight principal runtime hashes match the combined PR source. Both changes are now in the local saved artifacts. The older [caption patch](upgrade/page_caption_2de08c9.patch) retains its original `2de08c9` reproduction scope. Do not replace the saved runtime with this older dirty checkout wholesale; see the latest [handoff](HANDOFF.md#generic-export-pr-update--2026-10-17).

Before the Track color work below, the local [generic export and receipt](exports/README.md) were synchronized to source `0ed7d97`: 19 runtime/helper DATs and ten embedded Markdown snapshots matched, with an empty/disconnected native reload. Those earlier generic files and scoped documentation are published in PR #23 at `acc7a5c`; the current local artifacts include the later Track color and read-only preview feature.

## Saved Track palette feature

The 2026-10-17 Track palette and read-only RGB preview source lives in the separate worktree
`/Users/huihongnin/.t3/worktrees/roto_control/td-track-colors`, based on `acc7a5c`.
Its three changed DATs, including the preview in setup, are saved in `/roto_clean_demo/roto_python` in the local
canonical toe. The local generic tox/receipt and feature-worktree generic export
also include the feature, identified by committed source `0254000`,
19 runtime/helper hashes and ten Markdown hashes. Physical red/purple Track
feedback passed; temporary groups/colors were removed and the controller remains
disconnected. See the [save/export handoff](HANDOFF.md#track-color-bg-preview--2026-10-17).
[PR #25](https://github.com/joshuahhn/roto_control/pull/25) publishes Track colors and the preview; its source commit is `0254000` and export HEAD `0ac1ada`. The older controller remains unchanged. PR #23 is merged; checked-in demo artifacts
retain their separate version; this dirty checkout's older source must not replace the saved runtime.

## Architecture

`protocol.Host` owns protocol and session state behind complete-message send/receive and normalized parameter callbacks and configurable target identity/label/display. binding.Binding converts target units and handles target writes/callback dispatch. `RotoPythonExt` adapts that interface to TD parameters and a managed external MIDI process. The child owns mido/rtmidi ports; nonblocking pipes keep MIDI I/O out of TD's native MIDI library. Internal base_state owns readonly diagnostics; Parameter CHOP, selective Null and outCHOP expose its channels. Saved Binding page configuration is reapplied after extension initialization; callback mode runs the user-editable registration DAT.

Binding UI now exposes only Parameter mapping (`collection`: Free LEARN, Inspector, Layouts/Tracks) and Python registration (`callback`: saved reconstruction hook). Legacy single-target APIs remain callable; their outer configuration fields are removed after disconnected migration. `setup.configure_ui` is the shared builder/export upgrade. Native input-only receive retesting and its reproducible runner are documented in `diagnostics/native_midi/README.md`; production continues to use the external backend.

The outer Control page is also removed. `_value_parameter` uses legacy outer Value during migration and internal `base_state.Manualvalue` afterward. `setup.remove_control_ui` migrates saved self-Value destinations with identities intact. Manualvalue is compatibility backing state, excluded from public State; it has no second manual-input callback path. Existing target watchers and SetValue/Offerparameter APIs remain.

Outer pages are Connection, Binding, Layout and Device. `setup.combine_context_pages` keeps the saved mapping set and Track group on Layout (10 fields), with Device/Focus/name management on a separate Device page (6 fields), preserving parameter names, values, enable states and callbacks. Builders/upgrades/exports share this presentation helper. Active Device (SEL) selects an independent Plugin; Device Focus COMP links its tool and defaults its Device display name to the COMP name. Active Track group (FUNC) and Layout names remain independent. The `roto_device` OP tag registers a COMP as its own Device in Active Layout/Track while idle, reusing existing Focus links. Removing a tag retains saved mappings. Existing Track Focus links migrate to their Device. Delete pulses use an asynchronous native popup rather than permanent Yes/No parameters.

## Source Files

- `build/build_network.py`: explicit-parent builder; source-synced code DATs and embedded README.
- `code/py/roto_python/protocol.py`: protocol and one-parameter host.
- `code/py/roto_python/RotoPythonExt.py`: TD adapter and process lifecycle.
- `code/py/roto_python/*_callbacks.py`: parameter/frame/exit callbacks.
- `midi_process.py`: external MIDI owner; exact port resolution.
- `upgrade/upgrade_network.py`: in-place disconnected upgrade and demo construction.
- `code/py/roto_python/binding.py`: target metadata/conversion and adapters.
- `tests/test_binding.py`: binding behavior, failures and target identity checks.
- `tests/test_protocol.py`: behavior tests through MIDI and parameter interfaces.

## Constraints

No legacy host imports, no automatic hardware connection, no arbitrary parameter writes. Only acknowledged matching target/kind/slot mappings are accepted; identities include target id and value semantics. Invalid or foreign SysEx is ignored/counted. Runtime state is extension-owned and never persisted as a connected session. Target configuration/custom parameters and registration hook source persist; runtime callback objects do not. This prototype is macOS-oriented; nonblocking pipe behavior on other platforms is unverified. Hardware LEARN may store an assignment on the controller and is explicitly triggered by the user. No serial/firmware/configuration writes.

## Verification

Follow [change-scoped validation](../../AGENTS.md#change-scoped-validation). Protocol tests cover handshake, metadata, input pairing, mapping validation, touch and echo suppression. Only affected TD-native behavior needs a corresponding native check; only affected MIDI/ACK/feedback behavior needs corresponding hardware acceptance. Reuse unaffected results with their baseline and scope. Record unavailable checks as limitations, not an expanding task list. Documentation-only edits do not require live TD, hardware or artifact re-embedding.

## Collection architecture

collection_protocol.CollectionHost shares the established session handshake and holds independent Control state. controls.Controls validates adapters and table specifications. base_targets contains persistent targets, 16 event-driven watchers, per-target runtime state, bounded real button/mapping RX diagnostics and target-unit CHOP output. Existing single-target API and saved configuration remain available. Buttons have Toggle/Pulse modes; Pulse uses native hardware TOGGLE with immediate latched CC and Trigger/Ready display feedback, no TD timeout; both latched values trigger actions. No MIX transport buttons or firmware configuration is in scope.

API sequence is documented in docs/functions/lifecycle.md. Button input declares hardware button_type separately from TD action mode; targets table column defaults existing buttons to toggle. Shared button confirmation follows successful consumer dispatch, while knobs retain motor echo suppression.

Internal Inspector reads persisted target data through GetControlCatalog; Disconnect retains destinations/ranges/values. All 16 physical slots remain visible, with per-COMP pages and Unassigned placeholders. External Lister config lives inside the inspector wrapper. Build entrypoint includes build/build_inspector.py; Inspector source is code/py/roto_python/inspector/inspector_data.py.

Inspector Clear uses RemoveControl / RemoveAllControls: delete registration, disable watcher, suppress saved-hook restore and replay outgoing PLUGIN 0E on reconnect. ClearLearn / ClearAllLearn retain registration as separate hardware-only APIs. Hardware persistence is verified by reconnect, not an unmap acknowledgement.

Mapped parameter COMP visual claims are handled by base_targets/mapping_marks (source code/py/roto_python/base_targets/mapping_marks.py), independently of Inspector UI. Runtime OP IDs/path pairs distinguish controller claims; roto_mapped/cyan ownership restores original styling after the last active mapping.


Inspector confirmation is UI-only; direct removal and hardware-only clear APIs execute without UI confirmation. ConfigureControl validates/replaces one collection adapter, unmaps only a changed mapped slot and persists overrides by ID. requires_relearn survives restore until matching acknowledgement. Inspector highlights pending configuration and edits through this common API. Value writes do not require re-LEARN.

Inspector COMP/Parameter pickers discover compatible custom parameters on demand. AssignParameter changes one slot and stores generated stable identities/relative destinations in parameter_assignments; restore overlays these records over the saved table/hook. Collection runtime objects for other slots are retained. Assignments can occur during hardware LEARN and the Inspector automatically offers the selected target; no Applybinding is required. Clear removes the assignment overlay and tombstones its superseded source ID.

FreeLearner retains pending parameter offers independently by index/hash during hardware LEARN. The learn_parameters Parameter Execute DAT watches compatible custom parameter edits only during connected PLUGIN LEARN, scoped to the linked Device's COMP and descendants (nested linked Devices own their subtrees). Unlinked explicit Devices retain manual registration compatibility. Matching CONTROL MAPPED index/hash commits the reported kind/slot via AssignParameter, then the common parser acknowledges it; foreign COMP edits and stale Focus ownership cannot populate the current library. Persisted assignments carry explicit parameter indices (reserved dynamic indices start at 128); slots no longer imply the wire index. Direct parameter edits require no Inspector action.


## Active repository

Continue development in joshuahhn/roto_control, src/touchdesigner. The nin-lab location is a migration backup. Documentation embedding uses scripts/td_project_docs.py. Open projects/current/ROTO-CONTROL.toe; generic export is exports/roto_python.tox. Numbered snapshots are historical; see projects/README.md and the checkout/artifact distinction above.


## Multi-Track registry v2 (2026-10-06)

Historical v2 baseline: Layouts own ordered Tracks; each Track originally owned one Plugin with independent parameter mappings. See the v3 section below for local multi-Device behavior. layouts.py owns versioned migration and Track metadata/selection; protocol.Host delegates Track announcements through tracks_callback. Hardware Track pages are distinct from selection. Under LOCK, selected Track and routing Track may differ. Subsequent physical LOCK acceptance is recorded in HANDOFF.md; the original pending state is historical. Inspector context and clear confirmations are Plugin-scoped. See docs/functions/layouts.md and diagnostics/runtime/results/multitrack_native_verification.json.

## Live Select COMP (2026-10-07)

text_comp_follow.CompFollower owns optional Device Focus links, current-pane selection sampling and a single latest-intent arbiter shared with hardware Track/Device selection. Binding Followcomp defaults off only on creation/export; Layout Focuscomp edits the active Device link. SetPluginComp, SelectComp and GetCompContext expose the link/context; SetTrackComp remains a compatibility wrapper for the Track’s active Device. No additional Binding mode or signal wires.

Selection/unlock fences immediately suppress business input, mapping/page recall, FreeLearner commits and old feedback; keep session/LOCK/LEARN/touch-release traffic. Drain buffered complete lines before activation; partial inbound lines retain their ingress epoch. Disconnect/open failure/child failure clear pending intents and selected/routing divergence through connection generations. Domain failures do not Disconnect; failed rollback/observer pauses until Apply setup repair. Saved Follow=True restores baseline only. Project Pre Save is explicitly enabled on the lifecycle DAT; its synchronous callback refreshes live links even while paused. Generic exports clear links/preference. Native evidence is in diagnostics/runtime/results/comp_follow_native_verification.json. Later tagged-COMP physical Follow/recall passed; guarded/locked Follow remains a separate limitation in HANDOFF.md.

## Meter capability probe (2026-10-17)

On firmware 3.3.0 / SysEx API 1.6, native stereo VU bars displayed in MIX after
official MIX initialization. The same channel-16 CC65/66 signal did not display
bars in PLUGIN after that successful MIX control. Real stereo file audio and
duplicated mono device input both passed user-observed MIX tests. These are
bounded capability probes, not a production meter API or MIX control backend.
Runtime source and saved toe/tox artifacts were not changed.

The three requested uses are audio CHOP level, Layer Mix layer opacity and
audioAnalysis level beside an adjustable threshold. Opacity can supply a
normalized scalar but still needs an explicit layer adapter. The current host's
PLUGIN mappings cannot be assumed to control MIX knobs. For audioAnalysis, read
the signal before its threshold comparison; raw audio RMS and the post-trigger
output are different measurements. PLUGIN numeric feedback is a possible next
prototype, not verified native VU support. See HANDOFF.md for initialization,
evidence scope and cleanup.

The next bounded MIX prototype passed one-knob threshold control, motor recall
and simultaneous native meter display. It mapped touched Knob 1 to
`audioAnalysis.Kickthresh` over 0..0.6, read pre-comparison `math2/low` for its
meter, and kept the existing PLUGIN parser/guards. A temporary MIX receiver
owned its one-track view instead of treating MIX selection as PLUGIN Track
selection. This proves the small adapter approach; it is not installed in the
saved runtime. `Kickactive` stayed off, so actual kick-trigger acceptance is
separate. The user's resulting threshold 0.26174693279619116 was preserved.

Actual Kick output was subsequently verified with `Kickactive` temporarily on:
hardware K0/K1 follows `out1['kick']`, retaining observed pulses for 0.2 seconds.
At threshold 0.600, K1 correctly remained possible because measured pre-threshold
peaks reached about 0.70. A meter range must therefore be independent of the
knob's 0..0.6 range. All parameters and bindings were restored afterward.
The user selected an independent MIX page with eight slots, each with its own
control target and meter source, rather than sharing the current Device's
PLUGIN assignments. Production implementation is the next active task.

The user clarified the intended workflow as tool/source → selected item → detail
controls, using touch to select and FUNC to open details, rather than requiring
physical SEL for item selection. The [MIX view proposal](docs/plans/mix-view-mappings.md)
and [three-style contract](docs/plans/mix-style-contract.md) describe `layers`,
`analysis` and `audio`, with typed Float/Menu/Toggle targets and separate read-only
feedback. Native Level/Pan/Send names are adapter addresses. This supersedes both
the Level-only assumption and using native function names as the TD domain model.
Low Focus now has bounded physical proof for four readable name/value texts,
first-meter placement and Gain touch input/motor return. Multi-item selection,
other input types, Focus buttons and second-page offsets remain unverified.
Audio refinement is deferred to [issue #26](https://github.com/joshuahhn/roto_control/issues/26),
so analysis remains the first active style. The initial read-only Low Focus
probe was user-observed as `MIX-FOCUS / Low` with Thresh/Gain/Add/Smooth values
and a continuing meter. Gain was temporarily changed to 2.84093267411341 and
restored to 2.000, with motor return and zero further input writes after input was
disabled. The probe's timeout metadata cleanup was corrected to restore PLUGIN
metadata only on actual return. User confirmed normal PLUGIN; disconnected audit
preserves all parameters, Snapshots, four original control IDs and 19 DAT hashes.
Production descriptor/analysis integration for Low/Mid is next, using a separate
worktree rather than this older dirty runtime checkout.

## Independent Device context v3 (2026-10-07)

Each Track explicitly groups 1..127 Plugins with separate active Plugin, identities, targets and off-page library. Focus links are Plugin-scoped; sole selected COMP resolves to (Layout, Track, Plugin). Hardware SEL uses eight-item Device banks independently of Track browsing. PLUGIN 04 browses; PLUGIN 07 queues a page-relative Device selection. The existing arbiter/fences/session generations cover same-Track Device transitions. LOCK stops automatic Follow and hardware Track routing, but explicit hardware Device selection can replace the locked Device inside the routing Track after LEARN/touch/backlog guards. Selected Track divergence persists; unlock follows current selection. Reverse hardware-to-TD UI selection remains deferred.

GetPlugins/CreatePlugin/SelectPlugin/RenamePlugin/RemovePlugin/SetPluginComp are promoted. v2 links move from Track to its sole Plugin without merging existing mapping variants or changing any stable ID/hash. Linked names follow COMP rename; manual names remain supported, Layout rename is independent. Upgrade captures current registry before replacing source. Software/native evidence and artifacts are recorded in the final HANDOFF entry.
