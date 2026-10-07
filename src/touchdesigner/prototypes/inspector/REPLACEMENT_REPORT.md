# Replacement acceptance checkpoint

2026-10-08, TD 2025.33230. **Replacement is not accepted yet.** The old Inspector remains available. Runtime/native parity regression fixtures pass, but the first 30-minute soak was stopped after 352 seconds when the user reported an oversized Popup. This uncovered a reproducible UI lifecycle bug; it does not establish a completed memory/performance soak.

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

Physical Range re-LEARN is explicitly **not tested**, as reported by the user. Declared PUSH/TOGGLE adapter physical acceptance remains unverified. Header first-click selection, real K2/LEARN alert, target assignment and Ping have prior user acceptance. Source/evidence: replacement_physical_gates.json. Native drag deformation remains separately deferred in issue #6.

## Automated workloads

`acceptance_probe.py` is finite and cancellable: real-data read-only matched frame cases, then a disconnected sixteen-slot mixed Float/Int/Menu/Toggle/Pulse fixture. It uses a temporary Perform CHOP/null and frame sampler, bounded recent windows, one active Inspector, alternating Fold/Popup, section/picker/menu operations, fixture LEARN/touch state, retargeting and 10 Hz parameter updates. Pulse parameters are never fired. Production mappings and MIDI are not changed. `sample_process_memory.py` samples whole-process RSS externally, rather than launching subprocesses in TD's frame loop. All temporary operators are destroyed on Stop; pre-test Popup rectangles are restored. Fixture-phase geometry is normalized separately. Short smoke captures use a separate artifact prefix and cannot overwrite the incomplete 30-minute capture.

Twenty matched real-data cases (forward/reverse order) recorded p95 whole-project Perform CHOP frame cost between 7.15 and 9.13 ms; closed-window baseline repeats were 8.82 and 7.36 ms. These measurements include observer/project work and have order drift; they are not isolated GPU drawing timings or an old-versus-new application benchmark.

The interrupted soak recorded two subscriptions, at most two source/catalog/definition contexts, one pending context/14 slots, two picker snapshots/34 entries, zero fixture MIDI queue bytes and unchanged view operator counts. Whole-process RSS ranged 3413.0–3425.7 MiB during this partial run. This is insufficient for the planned 30-minute memory gate. A repeated-row toggle in the harness initially skipped Details/Picker; it was corrected at 160 seconds. Subsequent picker snapshots were observed. The retained capture is replacement_acceptance.json / replacement_rss.jsonl, with `complete=false` and `reason=height_bug_investigation`.

## Popup height regression found and fixed

The stopped probe had a 2074px Popup for 178px collapsed content. A smaller staged replay reproduced the same fault: after a settled Mapping expansion, collapsing and closing/reopening in one tick adopted the old viewport cache. Each reopen added 134px: 178 -> 312 -> 446 -> 580 -> 714 -> 848.

The view now retains its latest requested geometry through native/viewport settlement. Further section changes and immediate reopen use that intended height. A cancellable three-frame settlement callback clears the request; closed hosts synchronize their opening height, and Disconnect cancels the callback. No permanent frame poll or extra Window is added. Manual resizing after settlement still supplies the new base, preserving width/top-left. Both native Window geometry and Size From Window viewport caches must settle; synchronously updated Window members alone are insufficient.

Evidence: popup_reopen_height_before.json fails; popup_reopen_height_after.json passes twenty cycles at 178px. popup_height_race_after.json passes thirty same-tick section/dropdown cycles; popup_manual_base_verification.json preserves a manual 376x220 base through 376x354 expansion/collapse and restores the original rectangle. Deferred-geometry unit tests reproduce the stale arithmetic and close/reopen cache path. Editor dropdown native gestures still pass; production catalog/session stays unchanged.

## Remaining gates

- Re-run the full 30-minute soak with the new opening/actual-height guards; the interrupted run is not a pass.
- Complete fresh builder/generic reload/project restart acceptance for final replacement.
- Physical Range change -> Apply -> hardware LEARN -> new range, then restore/re-LEARN original mapping. Choose a valid temporary range containing the current Value; preserve original bounds.
- Physical declared input adapter acceptance; physical wheel/OS Escape and deferred resize visual acceptance.
- Native custom-parameter metadata/editor link and Style migration remain later Advanced workspace scope.

No commit or push. The stress probe and external sampler are stopped; the model is restored to the real production controller.

Fixed checkpoint: inspector_editor_actions.27.toe. Generic reload verifies no owned geometry/settlement state and collapsed178px hosts. Separate popup_height_fix_smoke_acceptance.json is a10-second fixture smoke after shortened matched cases, with no errors and unchanged production; it does not satisfy the30-minute gate.
