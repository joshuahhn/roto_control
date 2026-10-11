# Shared inspector model verification

2026-10-07 · live TD 2025.33230 · roto_control_python.75.toe · nominal 60 Hz.

The Below and Popup views now use one actual model extension, with separate drafts/selection/scroll. Frame-end notifications merge updates, the four-context LRU is bounded, display-text writes are deduplicated and Popup Apply/Cancel sessions reuse the native window. This report measures the implemented model and native views, rather than the alternative feed functions in the earlier benchmark.

## Results

Seven phases recorded 2520 frames; the first 60 frames of each phase were excluded from timing summaries. Each Inspector remained visible. All sixteen controls were temporarily mapped in all eight contexts, exercising the worst fixture size. The model ingest ran on every test frame; frame-end dispatch used the shipped `endFrame=True` scheduler. Test fixtures and local drafts were restored afterward, and the temporary Execute DAT / Perform CHOP harness was removed.

| Scenario, both views visible | Producer p95 ms | Dispatch p95 ms | Frame interval p95 ms | Native popup opens during phase |
| --- | ---: | ---: | ---: | --- |
| Idle | 0.001 | 0.000 | 17.26 | [0, 0] |
| 16 values / frame | 0.057 | 0.179 | 20.51 | [0, 0] |
| 32 batches / frame | 0.460 | 0.159 | 20.11 | [0, 0] |
| Identical values | 0.057 | 0.000 | 17.09 | [0, 0] |
| 8 contexts / frame | 0.170 | 0.166 | 20.39 | [0, 0] |
| Edit / Apply / Cancel | 1.749 | 0.123 | 18.88 | [0, 0] |
| Idle after stress | 0.002 | 0.000 | 17.20 | [0, 0] |

Producer timings include validation/cache writes and synthetic interactions where applicable. Dispatch timings include both subscribed views and their native text-parameter updates. These are separate percentile distributions, so their p95 values must not be added and called a measured total p95. Frame interval also includes the rest of the active TD project and native rendering. Boundary flushes can land just outside a phase's counters; the continuous phases record 359 flushes for 360 input frames.

Identical traffic caused only the initial transition flush and sixteen text writes per view; after warm-up there were no dispatches. Idle generated no model notifications or text writes. The 32-batch phase submitted 184,320 values but produced 359 measured phase flushes, without accumulating a queue of historical updates. The eight-context feed kept pending slots at or below 128 and the derived cache at or below four contexts.

Both views stayed at 280 operators throughout every phase; the model adds three operators. Each phase reported zero additional native Popup opens, exactly two subscribers and no subscriber exceptions. Process CPU memory reported by Perform CHOP stayed within approximately 2808.4–2808.7 MiB during measured frames. These are whole-process measurements in an already-warmed TD session, not standalone inspector memory allocations.

## Correctness and lifecycle

20 live checks passed, including 128 cross-view context/slot commits, 128 cancels, 96 reused Popup edit sessions, independent unfinished drafts, shared Learn alerts, stale draft rejection, stale producer-generation rejection, atomic invalid batches, native wheel callbacks, cache eviction, reconnect bounds, hidden-window write deferral and catch-up on native reopen. The hidden/reopen probe was staged across separate native event-loop turns.

All three live-exported `.tox` files were reloaded. The two view extensions resolved the same model; two subscribers survived extension replacement; their embedded sources matched the authoritative Python files. Reload exposed a destruction-order race, now covered by a unit test: an old view may only unregister its own callback, never the replacement view's callback with the same operator identity.

- Runtime suite: 230 tests passed.
- Shared-model unit suite: 12 tests passed.
- Errors under `/inspector_model`, `/inspector_below` and `/inspector_popup`: none.
- `git diff --check`: passed.
- Temporary harness: removed. No permanent frame-polling DAT was exported.

## Limits

This remains mock data. No MIDI, controller adapter, real parameter mapping or disk persistence is connected. The cache bounds derived catalog rows; the demo's authoritative eight-context source remains resident. A production adapter needs its own bounded source lifecycle and must pass the model generation when delivering delayed results.

Worst continuous redraw traffic still raises frame interval above the 16.67 ms target; the shared data layer does not eliminate native text/render cost. These short tests establish bounded queues/subscriptions/operator counts and observed process-memory stability, not an hours-long leak guarantee or a promise of stable 60 fps in every project.

Normal Apply/Cancel usage avoids the previously expensive native close/open lifecycle. Explicit native X / reopen still uses that TD lifecycle; this change does not prove that the earlier process-level retention on repeated OS window destruction has been fixed.

Evidence: `shared_stress_results.json`, `shared_correctness.json`, `shared_reload.json`. Reproduce traffic with `python3 prototypes/inspector/run_shared_stress.py --port 13316` from `src/touchdesigner`. The main `.toe` was not saved; exports contain only the demo modules.
