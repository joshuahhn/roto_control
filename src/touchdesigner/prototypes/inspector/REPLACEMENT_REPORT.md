# Replacement acceptance checkpoint

2026-10-08, TD 2025.33230. **Replacement is not accepted yet.** The old Inspector remains available. After fixing the Popup lifecycle height bug, a new full 1800-second soak completed with no errors, bounded state and unchanged production mappings/session. Height and long-run state stability pass; frame-time headroom and physical replacement gates remain open.

## Parity against the old Inspector

The authoritative old UI columns/actions are in `code/py/roto_python/inspector/inspector_data.py` and `list_events.py`.

| Old behavior | Compact equivalent | Evidence |
| --- | --- | --- |
| Sixteen knob/button slots and mapping state | Sixteen compact rows; health markers and editor heading | Native health/target fixtures |
| COMP/parameter assignment, empty slots, replacement | Inline searchable Target picker with explicit Assign | targets_verification.json |
| Mode, Min/Max, hardware input declaration | Mapping draft, compatible Mode/Range/HW Type, Apply | mapping_verification.json |
| Numeric live Value | Continuous typed Value, numeric Float/Int cycle, Menu/Toggle | live_value_verification.json, targets_verification.json |
| Learn/Re-learn offer | Ping; controller LEARN remains required | editor_actions_verification.json, targets_hardware_acceptance.json |
| Clear registration and Clear All | Confirmed Clear and scoped Clear Device | parity_verification.json |
| COMP/callback pages | Compact footer filters | parity_verification.json |
| ID/error/current context/Follow/LOCK readout | Details with separate controller/view state | parity_verification.json |
| Native parameter Style conversion | Neither old nor compact Inspector implements conversion | Additional Advanced workspace scope |

Physical K2 Range re-LEARN now has user-confirmed 0.25/0.75 endpoints and a matching native ACK. This exposed a stale Mapping message and erroneous Value-token invalidation after ACK. Both are fixed with pure/native regression evidence; the user also confirmed restored 0/1 endpoints and the hardware acknowledged message. The original live Value is restored, completing this physical gate. Declared PUSH/TOGGLE adapter physical acceptance remains unverified. Header first-click selection, real K2/LEARN alert, target assignment and Ping have prior user acceptance. Source/evidence: replacement_physical_gates.json and physical_range_relearn.json. Native drag deformation remains separately deferred in issue #6.

## Automated workloads

`acceptance_probe.py` is finite and cancellable: real-data read-only matched frame cases, then a disconnected sixteen-slot mixed Float/Int/Menu/Toggle/Pulse fixture. It uses a temporary Perform CHOP/null and frame sampler, bounded recent windows, one active Inspector, alternating Fold/Popup, section/picker/menu operations, fixture LEARN/touch state, retargeting and 10 Hz parameter updates. Pulse parameters are never fired. Production mappings and MIDI are not changed. `sample_process_memory.py` samples whole-process RSS externally, rather than launching subprocesses in TD's frame loop. All temporary operators are destroyed on Stop; pre-test Popup rectangles are restored. Fixture-phase geometry is normalized separately. Short smoke captures use a separate artifact prefix and cannot overwrite the incomplete 30-minute capture.

The new twenty matched real-data cases (forward/reverse order) recorded p95 whole-project Perform CHOP frame cost between 6.67 and 8.82 ms; closed-window baseline repeats were 7.97 and 8.14 ms. These measurements include observer/project work and have order drift; they are not isolated GPU drawing timings or an old-versus-new application benchmark. Fold rows exceeded its forward baseline by about 10.6%, but the reverse repeat was below baseline; this does not establish a consistent regression or a performance pass.

The interrupted soak recorded bounded state and whole-process RSS of 3413.0–3425.7 MiB. It remains an incomplete capture, archived as replacement_acceptance_interrupted.json / replacement_rss_interrupted.jsonl with `complete=false` and `reason=height_bug_investigation`. A repeated-row toggle initially skipped Details/Picker; it was corrected at 160 seconds. The new run uses the corrected harness from the start.

## Completed 30-minute soak

The new run completed 1800.01 seconds and 16,437 batches of fourteen non-Pulse parameter updates, alternating Fold/Popup every minute and changing editor sections every five seconds. Opening/settled-height guards reported no drift. View operator counts remained unchanged. Production catalog, registry, routing and adapter session were preserved; the fixture/probe were destroyed and the external sampler exited. The original real K1 Popup rectangle was restored to 328x178 at (272,312), with two subscriptions and no pending model work or geometry callbacks.

| Measurement | Result | Interpretation |
| --- | --- | --- |
| Model/definition contexts | At most 2 each; capacity 4 | Bounded |
| Pending model work | At most 1 context / 14 slots | Bounded |
| Picker snapshots | At most 2 pages / 34 entries; no sampled pending jobs | Bounded |
| Fixture MIDI queue | 0 bytes; no MIDI process opened | Isolated |
| Whole-process RSS after first 2 soak minutes | 3452.94–3454.28 MiB; first/last 3453.31/3453.41 MiB | No sustained growth observed in this run |
| Last 10 minutes RSS | 3453.16–3453.41 MiB | Plateau within the observed interval |
| Minute-bucket Sync + Flush p95 | 0.665–0.782 ms | Only explicit model sync/flush is timed |
| Minute-bucket whole-project frame p95 | 15.25–19.46 ms | Some buckets exceed the 16.67 ms budget at 60 Hz |
| Minute-bucket wall frame-gap p95 | 28.70–31.57 ms | Cadence spikes remain; headroom gate is open |

The 186 RSS samples cover the whole TD process, including the fixture and observer. These numbers do not isolate Inspector memory. Perform CHOP reported zero dropped frames at bucket boundaries, which is insufficient to rule out intervening cadence spikes. Soak `case` labels record state at the interval boundary, after the next style transition; they cannot attribute each minute's timing to Fold or Popup. Use the matched cases for style comparison.

Evidence: replacement_acceptance.json, replacement_rss.jsonl, replacement_summary.json and replacement_restoration_before.json. Fresh external builder verification passes with current embedded source, three fixed dropdown pools, no opened test windows, empty geometry state and production preserved (replacement_builder_verification.json). Generic reload is verified separately in live_export_reload.json.

Before a performance acceptance claim, profile parameter dispatch/callback work and native panel drawing separately under the same update workload, then repeat a matched baseline. The shared caches are bounded, but further caching alone is not demonstrated to solve the frame spikes.

## Popup height regression found and fixed

The stopped probe had a 2074px Popup for 178px collapsed content. A smaller staged replay reproduced the same fault: after a settled Mapping expansion, collapsing and closing/reopening in one tick adopted the old viewport cache. Each reopen added 134px: 178 -> 312 -> 446 -> 580 -> 714 -> 848.

The view now retains its latest requested geometry through native/viewport settlement. Further section changes and immediate reopen use that intended height. A cancellable three-frame settlement callback clears the request; closed hosts synchronize their opening height, and Disconnect cancels the callback. No permanent frame poll or extra Window is added. Manual resizing after settlement still supplies the new base, preserving width/top-left. Both native Window geometry and Size From Window viewport caches must settle; synchronously updated Window members alone are insufficient.

Evidence: popup_reopen_height_before.json fails; popup_reopen_height_after.json passes twenty cycles at 178px. popup_height_race_after.json passes thirty same-tick section/dropdown cycles; popup_manual_base_verification.json preserves a manual 376x220 base through 376x354 expansion/collapse and restores the original rectangle. Deferred-geometry unit tests reproduce the stale arithmetic and close/reopen cache path. Editor dropdown native gestures still pass; production catalog/session stays unchanged.

## Remaining gates

- Establish fixed-cadence headroom after the publication optimization; short callback/visibility ablations isolate repeated backend projection as a main bottleneck, but wall-gap spikes remain.
- Complete full project restart acceptance for final replacement; fresh builder and generic reload checks pass independently.
- Physical declared input adapter acceptance; physical wheel/OS Escape and deferred resize visual acceptance.
- Native custom-parameter metadata/editor link and Style migration remain later Advanced workspace scope.

No commit or push. The stress probe and external sampler are stopped; the model is restored to the real production controller.

Fixed UI checkpoint: inspector_editor_actions.27.toe; the acceptance snapshot uses the active project save filename. Generic reload verifies no owned geometry/settlement state and collapsed 178px hosts. The earlier popup_height_fix_smoke_acceptance.json remains a separate 10-second smoke; the new full run supplies the 30-minute stability evidence.

## Physical Range test: ACK message refinement

The 0.25–0.75 physical test received a matching K2 ACK: runtime mapped=True, requires_relearn=False, and the user confirmed both endpoints. The open editor nevertheless retained its Apply-time message, while treating the health flag's change as a configuration revision. Live reproduction caught both misleading text and disabled Value editing. requires_relearn now participates in display notifications rather than configuration tokens; target/Range/Mode/definition/session changes still fence drafts. Mapping status resolves the saved pending message against current health, and the completed Range/Mode Ping notice clears on ACK. A stale or replaced target cannot gain an acknowledged message.

116 Inspector tests and 230 runtime tests pass. mapping_verification.json verifies native ACK publication updates both editor roots, retains the token and Value editability, and performs no Value dispatch. This refinement follows the completed height soak; that soak was not rerun for the message change. Production controller sources and MIDI session remain unchanged. The user confirmed the restored 0/1 endpoints and hardware acknowledged message. The original live Value is restored, completing physical Range acceptance. Generic export/reload also passes with the revised Inspector sources.

## Publication optimization follow-up

[PERFORMANCE_REPORT.md](PERFORMANCE_REPORT.md) records matched closed/Fold/Popup/frozen workloads and a scoped optional UI publication change. Forward/reverse median frame p95: Fold17.55→7.99ms, Popup15.86→9.57ms, Details17.27→8.38ms. Wall gaps improve to about23–24ms but remain above a uniform60Hz cadence. A transient projection signature and one owned end-frame render coalesce legacy JSON/table rebuilding while keeping authoritative state, Value/Pulse/MIDI dispatch and ACK processing synchronous.236 runtime /116 Inspector tests pass. Live upgrade reconnects MIDI and preserves all original bindings/Values, with six mappings re-ACKed. Generic controller export41 reloads disconnected with no registered destinations and revised embedded sources. The30-minute soak was not rerun after this observer change; fixed-cadence and full project restart gates remain open.
