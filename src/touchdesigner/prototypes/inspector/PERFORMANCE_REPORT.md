# Inspector publication performance

2026-10-08, TD2025.33230. The repeated backend Inspector projection is a demonstrated bottleneck. The shared compact UI cache is not the main cause of the 14-value burst spikes. Production bindings/Values survive the live source upgrade and MIDI reconnect; all six original mappings re-acknowledge.

The optional legacy Inspector projection now caches one transient signature and queues at most one owned end-frame callback when inputs change. Pending bursts skip even signature/deep-copy work; the callback reads the latest catalog/UI scope. Value/MIDI/Pulse dispatch, binding snapshots, ACK processing and native control outputs remain synchronous. Direct UI refresh runs normally; forced refresh cancels the pending callback. Disconnect flushes the final empty/disconnected projection and cancels the callback; replaced/deleted extensions cannot render late. Cached catalog reads also avoid the eagerly evaluated fallback live scan.

| Workload | Frame p95 before / after (ms) | Wall-gap p95 before / after (ms) | Sampled dropped frames before / after |
| --- | --- | --- | --- |
| closed_idle | 7.35 / 8.19 | 18.10 / 18.55 | 0 / 0 |
| closed_1 | 7.47 / 8.06 | 20.24 / 18.50 | 0 / 1 |
| popup_1 | 7.51 / 7.97 | 19.92 / 19.15 | 0 / 0 |
| closed_14 | 8.09 / 9.15 | 30.05 / 23.75 | 3 / 0 |
| fold_14 | 17.56 / 7.99 | 30.14 / 23.21 | 1 / 0 |
| popup_14 | 15.86 / 9.57 | 28.78 / 23.41 | 2 / 0 |
| details_14 | 17.27 / 8.38 | 29.91 / 23.23 | 2 / 0 |
| popup_frozen_14 | 11.91 / 10.69 | 30.20 / 22.43 | 2 / 0 |

Each entry is the median of forward/reverse 6-second case p95s, excluding the first second; it is not a pooled p95. Whole-project timings include the disconnected sixteen-slot fixture, profiler and production project. Perform CHOP reports the prior drawn frame and can miss script/cadence costs; wall gaps are reported separately. Idle frame p95 also drifted from7.35 to8.19ms across runs, so small differences cannot establish isolated drawing cost. Frozen/closed UI workloads retain burst spikes, whereas backend publication ablations reduce them. No isolated GPU render-time claim is made.

Cache-only did not remove bursts because each callback presents a different catalog state. Coalescing only the optional UI projection reduces actual render calls from roughly930 full publication calls to46–47 renders per measured five-second burst interval. Final 14-value workloads report zero sampled dropped frames in these short cases, but wall-gap p95 remains22–24ms: the fixed60Hz cadence/performance headroom gate is still open. A whole-publication coalescing experiment was fixture-only and is not installed.

236 runtime and116 Inspector tests pass, covering retries, page/confirmation/context/Follow invalidation, forced refresh, latest-state batching, bounded ownership, cancellation and stale-extension rejection. Native before/cache-only/intermediate/final artifacts are callback_cost*_timings.json and their corresponding acceptance files; all completed runs preserve production and remove temporary operators/wrappers. The final 30-minute workload has not been rerun after this observer change.

Generic controller export is disconnected, embeds both revised DAT sources and retains no registered destinations. Source scripts remain authoritative. Full project restart and remaining physical button/resize gates are separate from this short performance evidence.
