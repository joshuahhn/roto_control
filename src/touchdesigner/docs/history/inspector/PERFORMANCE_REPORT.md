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

## Fixed deadlines, native drawing and synchronous outputs (2026-10-08)

A second finite probe uses an anchored10Hz deadline instead of shifting the next update to now+100ms. Closed/Fold/Popup/frozen, optional legacy projection disabled, main Network Editor redraw disabled and whole-publication bypass run forward/reverse8s cases with first1s excluded. A separate native Perform DAT run samples the feed frame and following callback/flush frames. Whole-publication bypass remains a disconnected-fixture diagnostic; disabling main redraw made cadence worse, so neither setting is shipped. Every completed probe preserves real catalog/registry/routing/session and removes fixtures/hooks; redraw is restored.

| Workload at10Hz /14 Values | Wall-gap p95 before / after (ms) | Native frame-work p95 before / after (ms) | Native worst sampled frame before / after (ms) |
| --- | --- | --- | --- |
| Closed |24.28 /22.24 |9.93 /8.33 |14.47 /11.31 |
| Fold rows |23.73 /22.31 |not captured |not captured |
| Popup editor |23.38 /22.39 |11.94 /8.43 |14.38 /12.74 |

These are medians of forward/reverse case p95s, not pooled p95s. Native closed/Popup each contain84 burst-aligned snapshots per source version. Native Window redraw remains about3ms: Popup3.25→3.35ms; closing/freezing the compact UI retains callback spikes, and suppressing all fixture publication approaches idle cadence. This locates remaining repeated work in backend publication rather than drawing. The first cadence_native snapshots fell mainly between bursts and are retained as exploratory; use cadence_native_bursts and cadence_candidate_native for the native comparison. Native measurements include monitor overhead and CPU/driver work, not isolated GPU execution. [Perform DAT documentation](https://docs.derivative.ca/Perform_DAT) describes the native log categories; [Performance Monitor](https://docs.derivative.ca/Performance_Monitor) documents Window redraw and GPU interpretation limits.

The shipped change builds one detached control snapshot per publication, reused by catalog/ACK cleanup and mapping-mark observation. Stable controls_values channels receive only changed samples; schema changes, operator replacement or missing changed channels rebuild the output safely. Value, catalog, CHOP outputs, hardware dispatch and ACK remain synchronous. There is no whole-publication batching, extra poll or timer. Unit regressions reproduce repeated channel destruction, verify unrelated channel identity/write isolation, schema/operator replacement and the one-snapshot boundary.239 runtime/118 Inspector tests pass. A native fixture passes18 API writes with exact binary-fraction Float/Int/Toggle Values, synchronous output shape/catalog, no Pulse or MIDI dispatch and unchanged production. Failed fixture setup attempts were cleaned up; the final verifier explicitly configures Int0..7 and uses the runtime's zero default for an unfired Pulse ACK counter.

A separate requested60Hz run includes single-control Popup and14-value Closed/Fold/Popup. Single-control delivers59.76–60.05 updates/s; Fold/Popup14-value repeats deliver59.87–60.05. One reverse Closed14 case delivers49.47 updates/s with74 missed synthetic producer deadlines; the other delivers59.89. The producer keeps the latest requested update when late, so missed deadlines reduce offered synthetic load and do not prove hardware MIDI packet loss. All60Hz cases report zero sampled dropped frames/operator errors; the10Hz candidate Closed reverse case reports one sampled dropped frame. No full-rate acceptance is inferred from zero dropped-frame channels. Idle wall-gap p95 drifts19.31→19.85ms; candidate cadence also records a FrameStart timestamp. Small timing differences alone are not isolated UI regressions.

The fixed/uniform60Hz gate remains open, despite reduced publication cost and short native burst headroom. A whole-frame atomic parameter-change boundary or per-target catalog projection could be the next deeper improvement; neither is implemented here. No new30-minute soak or full process restart follows this change. Prior stability and physical input acceptance remain separate evidence.

Evidence: cadence_summary.json; cadence_ablation/cadence_candidate timings+acceptance; cadence_native_bursts/cadence_candidate_native native logs+timings+acceptance; cadence_60hz native+timings+acceptance; control_publication_verification.json and control_publication_install.json. The live installation preserves all six bindings/Values/context and receives six matching ACKs.
