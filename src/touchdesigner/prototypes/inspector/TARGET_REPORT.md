# Target assignment and typed Value — Milestone 3

2026-10-08, TouchDesigner 2025.33230. This milestone adds compatible native-parameter assignment and typed Value controls to both compact presentations. The old Inspector remains available; native resize deformation is still deferred in [issue #6](https://github.com/joshuahhn/roto_control/issues/6).

## Interaction

Click Target, including an empty slot's **Choose target** field, to open the inline picker. Scope defaults to the active Device's Focus COMP, falling back to the controller's parent project COMP. Enter another COMP path to change the subtree. Search filters labels and parameter paths in the current snapshot. Refresh explicitly rebuilds discovery. Six reusable result rows and previous/next actions page through results; incompatible targets are dimmed and explain their rejection when selected.

Selecting/searching/canceling never changes a mapping or Value. The check icon explicitly Assigns the chosen target through the existing `AssignParameter` API. The cross closes the picker. Assignment and Mapping configuration remain separate operations. Only the active context is writable; stale context/session/registration tokens and touched controls reject assignment. Empty slots are supported. Assignment during hardware LEARN offers metadata once when PLUGIN is connected; awaiting ACK is not a successful hardware mapping claim.

Numeric Value has a compact Float ↔ / Int ↔ cycle button beside the field. Its default follows native Style, and choosing another slot resets to that default. Switching input type never writes/rounds the target, changes native Style/range or marks re-LEARN. Int input uses a native integer Text COMP with a whole-number guard; Float input on a native Int target still rejects fractions. Float retains continuous numeric editing, Menu uses TD's native dropdown with indexed labels and the current choice checked, and Toggle uses ON/OFF. Menu/Toggle edits are live, with no Value Apply/Cancel. Changed Menu definitions invalidate pending edits. Pulse remains read-only and is never triggered by rendering, assignment or Value editing.

The collapsed editor stays 178px, Mapping stays 312px, and the picker uses 428px of content. Mapping and picker are mutually exclusive. Fold expands inside the existing scrolling list; Popup uses the existing downward height-delta behavior and the same window. No additional editor window is created.

## Shared discovery and lifecycle

`base_targets/TargetCatalog` contains the shared on-demand service. The scalar cache holds at most 32 scope/kind snapshots and 4,096 total candidate records. Discovery bounds COMP traversal at 4,096 nodes, emitted candidates at 4,096 and work units at 16,384. It yields after at most 128 units or a 2ms elapsed budget per slice, with at most two jobs and one pending continuation per job. This is a cooperative budget, not a hard cap on the duration of one native validation operation.

Typing filters cached rows without rescanning the tree. Candidate handles include native owner identity and parameter/bind-chain definitions, and are revalidated before assignment. Existing controller validation owns duplicate parameter/bind-master detection, persistence and removal of the old registration. The picker does not hold a second mapping store. Completed caches contain no OP/Par handles; transient traversal generators are released on completion/cancel. Session changes, controller detachment and destruction cancel jobs and clear the cache.

Closing an editor clears hidden picker labels and typed widget labels. Generic export additionally clears scope/query, drafts, controller links and caches. Reload verifies embedded source, no saved destinations, empty discovery/picker state and exactly two view subscriptions. Production MIDI and mappings stay intact.

## Verification

230 runtime tests and 81 Inspector tests pass. Native isolated fixtures cover explicit empty-slot assignment, read-only search/select/cancel, duplicate parameter and bind-master rejection, compatible BIND Value writes, readonly/expression/unsupported targets, deleted targets, changed Menu definitions, expired handles, native integer callbacks, Menu/Toggle updates, duplicate Menu labels, Pulse isolation, old registration/observer fencing, untouched controls, both presentations and hardware LEARN offer/touch guards. The production catalog, registry and connection session are compared before and after fixtures. No production controller source or upstream integration changes are required.

Fresh native view construction passes without opening a window. Mapping regression fixtures and the staged continuous Value fixture pass, including deferred model updates without echo writes. Measured annotation containment, group spacing and functional-node overlap checks pass; prototype roots have no operator/subscriber errors. Generic exports reload through live TD with the new sources and empty user state.

Evidence: `targets_verification.json`, `targets_network.json`, `targets_performance.json`, `live_export_reload.json`, `mapping_verification.json`, `live_value_verification.json`; reproducible builders/fixtures are adjacent Python sources.

## Performance scope

Read-only actual-project discovery found 33 focused-subtree candidates and 123 project candidates in two scans. Measured discovery slice p95/max: 2.064/2.120ms; cached open p95: 0.0107ms; filtering with six-row UI update p95: 0.249ms; closed-editor model sync p95: 0.141ms. These are observations for this project, not maximum cost guarantees.

100 cached opens and 100 query changes caused no new scan. Twenty picker reopen cycles retained operator counts; idle produced no extra row-text writes. The final workload retained two cache snapshots/156 entries and zero pending jobs. Native OS rendering, MIDI timing and a long-duration memory soak were not measured. The user subsequently confirmed physical target assignment and Ping working. This accepts those user-reported interactions; Range/input-adapter acceptance and all-slot replacement coverage remain separate. See `targets_hardware_acceptance.json`.

## Remaining work

Filters, scoped Clear All, routing/Follow/LOCK diagnostics and native parameter-definition inspection remain later milestones. Full old-Inspector replacement, physical configuration/all-slot acceptance, long-duration stress and native resize visual acceptance remain separate gates.

## Section-open flash (2026-10-08)

Target/Mapping expansion used to pulse `winopen` even though changes to opening height and offsets already resize an open native window. A live 2px probe confirms height updates without an Open pulse. Removed the redundant pulse; initial editor opening remains explicit. The regression test previously counted four unnecessary Open pulses across Mapping/Target/Mapping/collapse, and now counts zero.

The staged native fixture verifies 134/250/134/0 height deltas, fixed width/top-left/main size and no Open/Close pulses across section changes, with production catalog/session preserved. Native window processing needs time between fixture phases; same-turn geometry is not an acceptance signal. Temporary pulse instrumentation is removed. Evidence: `popup_no_reopen_verification.json`; rerun `verify_popup_no_reopen.py` phases with at least two frames between calls. This verifies removal of the reopen behavior; user visual flash acceptance remains separate from the deferred manual-resize issue #6.

## Intermediate width during section expansion (2026-10-08)

The user confirms the reopen flash is gone but reports a width change during section opening. Manual native resize can leave Opening Width stale. Applying offsets before synchronizing width temporarily applies that old width. A regression models a 376px native window with a stale 286px opening width and records every intermediate width: the former ordering visits 286px; the corrected ordering stays at 376px through Mapping/Target/Mapping/collapse. Capture the original native position first, synchronize width only when stale, then apply vertical offset/height. No Update Settings pulse, forced render or Open pulse is added. A native Update Settings probe unexpectedly included the 32px title bar in height; its temporary dimensions were restored and this API is not used in production.

Staged native geometry/no-reopen checks still pass. The user confirms both section-opening flash and intermediate-width changes are resolved. This accepts the Target/Mapping section transitions; manual resize deformation remains deferred in issue #6.
