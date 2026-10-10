# Real-data Inspector verification

2026-10-07 · TD 2025.33230 · `inspector_real_data.1.toe`.

The user requested real controller data and fewer editor windows, then authorized restarting TD. The application was closed after a live-TD checkpoint and reopened in a new process. The final real-data project was saved and reload-verified separately. Canonical production project/export files and upstream Ableton/Bitwig source were not replaced.

## Accepted behavior

- User confirmed both physical K2 value updates and hardware LEARN on/off alerts work in the new Inspector.
- Value Apply reaches the existing controller API and refreshes the row through native data events. The small software probe was restored before physical acceptance; later user values were retained.
- Browsing inactive `fractal_pop` displays its real Power without changing controller routing from `pixelSortV3`. A staged native parameter change verifies inactive live refresh after the watcher's baseline settles.
- One Inspector supports Fold/Popup presentation switching. Popup opens only on control selection. Verification leaves Fold open, with both editor windows closed.
- Two view subscriptions survive reinitialization/reload; derived context caches stay bounded at four. No subscriber errors or operator errors were reported.
- Generic model/view tox reload has no configured controller or saved destinations. Reattaching the read adapter preserves the production catalog and connected MIDI session.
- Saved project reload starts MIDI disconnected. Context/target IDs match the saved snapshot. Float values match within 5e-7; the observed maximum serialization difference was about 1.72e-7.

## Performance scope

An in-process read-only probe measured 100 syncs over the real active/inactive contexts: p95 **0.395 ms**, maximum **0.667 ms**. Repeated unchanged snapshots caused **zero additional UI text writes**. A burst of **1,000 RequestSync calls retained one queued run**. The model contains **no Execute DAT polling every frame**; the existing production controller's frame-based MIDI handling remains unchanged.

This measures projection/sync cost, not total rendering time or guaranteed 60 fps. Physical acceptance verifies the reported control and alert interactions, not all slots, mapping edits or hours-long memory behavior. The previous native-window churn retention is addressed operationally by reusing a requested Popup; explicit repeated X/reopen still uses the TD native lifecycle.

## Limits

Mapping Label/Target/Range are read-only. Value edits require the active Device, a valid non-Pulse target, LEARN off and the control released. Inactive browsing does not activate hardware routing. LEARN is controlled by hardware. Ping and Clear now use existing controller APIs as described below; no controller-extension source changes.

Evidence: `live_verification.json`, `live_performance.json`, `live_saved_state.json`, `live_export_reload.json`, `restart_before.json`. Tests: 230 runtime + 21 model tests. `git diff --check` passes. No commit or push.

## Compact editor actions (2026-10-07)

Both editors now have 24 × 24 icon buttons: Ping/Clear at the top right, Cancel/Apply on the right of the status/`Value edits live target` row. The user's spacing refinement gives 12px side insets, 6px row/control gaps and a 178px editor height, removing the spare footer space. Hovering names the action in its status line. Clear arms an inline eight-second confirmation rather than opening another window. Session/context/metadata tokens and LEARN/touch guards prevent stale removal. Ping only reoffers existing metadata in hardware LEARN and explicitly waits for a hardware ACK; it never claims an offer has been learned.

`verify_editor_actions.py` passes against a disconnected native controller clone with captured output: a forgotten mapping emits a parameter-details packet, Ping without LEARN is rejected, Pulse Ping does not trigger its target, Clear requires two native callback invocations and removes only one registration, and parameter Value is preserved. The production catalog, registry and connected session remain unchanged. All four editors fit the icon controls with consistent row gaps, without network-node overlap or operator errors. The physical forgotten-map/re-LEARN cycle remains unverified. Evidence: `editor_actions_verification.json`. Current tests: 230 runtime + 33 Inspector model/editor tests. Latest checkpoint: `inspector_editor_actions.2.toe`.


## Health and shared commands (2026-10-08)

Milestone 1 is installed in Fold/Popup with compact row health markers, editor state and shared guarded Value/Ping/Clear commands. Native touch/mode callbacks, invalid inactive target isolation, six-context cache bounds, zero idle text writes and generic command reload pass. 230 runtime + 42 Inspector tests pass. Latest checkpoint: inspector_editor_actions.3.toe. See [HEALTH_REPORT.md](HEALTH_REPORT.md) for matched performance evidence and remaining replacement/hardware gates.


## Mapping, dropdown header and live Value (2026-10-08)

Milestone 2 adds collapsible Mapping configuration with separate Apply/Cancel, Device-first native dropdowns and direct continuous Value editing with no Value Apply/Cancel. Popup Size from Window fixes linked width/height resizing; real mouse drags verify each axis independently. Mapping expansion retains the window size and scrolls; selecting another control does not resize an open Popup to match the Inspector. Native configuration/live-value/resize fixtures preserve production state. 230 runtime + 61 Inspector tests pass. Latest checkpoint: inspector_editor_actions.4.toe. See [MAPPING_REPORT.md](MAPPING_REPORT.md) for evidence and remaining hardware/parity gates.


## Popup accordion and native icons (2026-10-08)

The user’s screenshots clarify that Mapping should grow the Popup downward. It now adds/removes 134px relative to the current manual size, preserving width/top-left and keeping the upper fields stationary. Main Inspector resizing remains independent; Value remains live. Four editor actions and Clear confirmation use TD’s bundled Material Design Icons font. Native size fixture and 230 runtime + 68 Inspector tests pass. Latest checkpoint: inspector_editor_actions.6.toe.

A persistent bottom white strip was reproduced during native mouse resize; visibility/forced-cook probes did not fix it, while TD’s direct panel capture renders correctly. Native UI automation subsequently timed out. The resize rendering issue remains unresolved and is not covered by the passing geometry tests. See MAPPING_REPORT.md.
