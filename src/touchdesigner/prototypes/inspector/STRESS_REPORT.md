# Inspector stress-test report

TD 2025.33230, project `roto_control_python.75.toe`, nominal 60 Hz. Scoped to the two mock demo COMPs. No controller API, MIDI connection, production mappings, or main project save is involved.

## Outcome

- **PASS — sustained display traffic**: both variants stayed near 60 fps under 16 changing values per view per frame. Latest Python update p95: full refresh **1.67 ms**, shared cached display **0.20 ms** (~8.4× faster). These are Python update timings, not total rendering cost.
- **PASS — Below interactions**: updated build frame-interval p95 **17.22 ms**.
- **PASS — Popup row switching with an existing window**: p95 improved from **148.22 ms** to **16.91 ms** after removing repeated native open pulses.
- **WARN — native Popup lifecycle**: opening/closing every frame still stalls (updated p95 **153.58 ms**). A nominal 10 Hz interaction schedule is much better (p95 **18.04 ms**), but this does not prove long-running lifecycle safety.
- **WARN — process memory retention**: the primary run went from ~2248 MiB to ~2530 MiB after high native-window churn. Additional lifecycle runs increased it further. The final 30 s idle sample stayed near 2978–2978 MiB. OP-tracked CPU memory stayed ~0.95 MiB per prototype and OP count stayed 395 each. This points to process-level/native-window retention; allocation ownership and an indefinite leak are **not proven**.
- **WARN — live-feed integration**: mutating a mock record alone does not refresh a row. The cached/dirty paths are measured alternatives in the harness, not an installed production live-data adapter.

## Coverage and fixes

28 recorded phases / 10,080 frames. The primary phase run contains 5,760 frames. Both variants passed 128 context/slot Apply+Cancel cases each (2 Layouts × 2 Tracks × 2 Devices × 16 slots), reversed/equal range rejection, draft preservation during synthetic value updates, and bounded wheel scrolling. TD sanitizes non-finite numeric parameter input before the UI validation seam; the test does not claim raw transport-payload validation.

Fixed after red probes:

1. Reject invalid/malformed slot indices before mutating selected state.
2. Stamp drafts with their context; reject Apply if the context has changed.
3. Ignore a deferred context callback once the view already represents the new context.
4. Reuse an already-open Popup when size/position is unchanged, and use one opening pulse instead of two.

The test repeatedly changes mappings, selects rows, applies/cancels, switches Device, toggles Learn and scrolls to both limits. The 32-batch/frame test coalesces to the latest values before painting. Identical display text skips writes. No new operator accumulation was observed. No TD operator errors or graph cycles were found. Runtime unit suite: 230 tests pass.

## Shared-module recommendation

Use the existing controller as the authoritative data owner. Add one shared read cache of catalog/value data keyed by stable Layout/Track/Device IDs and revision; views subscribe to changes. Cache row OP references per view and compare the formatted display text before writing. Coalesce bursts into one bounded paint; retain the latest values for hidden views and refresh when revealed.

Keep each view's selection, scroll and draft separate. Context/version checks must guard Apply. Bound metadata caches and invalidate on mapping changes, Device removal/relink, source rebuild and connection generation changes. Do not cache a whole native window per Device: that multiplies UI objects and does not solve native window lifecycle retention. Reuse one editor/window, or test a panel-based popup/overlay if disappearing on Apply is required.

This is a short synthetic stress test on this TD project, not a hardware/MIDI test, heavy-scene benchmark or overnight soak. Average frame interval at 60 fps is ~16.67 ms; p95/p99 and native-window churn reveal problems an idle happy path misses. The added Execute DAT / Perform CHOP instrumentation was removed afterward. Main project and production networks were not saved or upgraded. Process-level memory retained by native lifecycle testing remains in the current TD session.

## Reproduce

With both demo COMPs loaded in this checkout's live TD project:

```sh
python3 prototypes/inspector/run_stress.py --port 13316 --suite main
python3 prototypes/inspector/run_stress.py --port 13316 --suite lifecycle --output lifecycle_retest.json
python3 prototypes/inspector/run_stress.py --port 13316 --suite cooldown --output cooldown_retest.json
```

`stress.py` is a temporary frame-paced harness. `run_stress.py` isolates its runner state from DAT dependency reinitialization, creates instrumentation under `/inspector_stress`, restores demo state and deletes that temporary COMP when complete. It refuses a different project folder or an existing stress COMP. Tests can create many native windows; the lifecycle limitation above remains relevant to reruns.

Raw evidence: `stress_baseline.json`, `stress_results.json`, `stress_followup_before.json`, `stress_followup_after.json`, `stress_final.json`, `stress_edges_before.json`, `stress_edges_after.json`, `stress_review.json`. `stress_preliminary.json` retains an earlier instrumentation pass and is not used for headline metrics. Perform CHOP `cook` is a cook flag; frame time is sampled from `msec`. GPU cook/OP memory snapshots do not include every native window/drawing allocation.
