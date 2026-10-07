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
