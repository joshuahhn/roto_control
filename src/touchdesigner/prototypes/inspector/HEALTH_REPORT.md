# Inspector Milestone 1 verification

2026-10-08 · TD 2025.33230 · checkpoint `inspector_editor_actions.3.toe`.

Fold and Popup now share health/capability/command rules through one embedded command module. Row markers and editor headings distinguish Mapped, Pending, Saved, Invalid, Re-learn and Unassigned. Hardware ACK is never inferred from a saved destination. The compact dimensions and 24px actions are retained; the checkpoint leaves one main Inspector in Popup presentation with no open editor.

## Verification

- 230 runtime + 42 Inspector tests pass. Stale metadata/session/definition commands are rejected; runtime Value/ACK/touch updates retain Value draft tokens.
- `verify_health.py` tests an isolated disconnected controller with captured output: ACK vs pending, stale disconnected ACK, re-LEARN, readonly/EXPRESSION targets, invalid-target cleanup availability and inactive browse. Six contexts keep source/info/revision/native-definition caches at four or fewer. Production catalog/registry/session stay unchanged; fixture Value and MIDI output remain untouched.
- `verify_health_events.py` runs four phases in separate TD turns. Native touch publication disables Apply/Clear without manual refresh. Changing evaluation mode to EXPRESSION with the same Value invalidates cached definitions and the draft automatically. The fixture is removed and production state restored.
- `verify_editor_actions.py` retains the existing Ping/Clear protocol, confirmation and layout checks. Generic UI export/reload checks embedded promoted commands, empty definition cache, no configured controller or user destinations, and exactly two restored subscriptions.
- Both view roots contain 29 functional nodes with no overlap. Existing callback nodes move into an Events group; annotations satisfy measured containment and gaps. Repeated command/cleanup builders retain stable annotation counts and two subscriptions. No operator/subscriber errors or frame polling DAT is added.

## Performance

The native-definition cache avoids re-reading every Par definition on every sync. It refreshes on editor open, native mode events, changed source metadata and before commands; other definition changes are revalidated on open/action. The four-context cache retains scalar snapshots and clears on controller/session changes and generic export.

Matched read-only probes alternate the previous committed model (`1d8111f`) and the new model over the same two real contexts, after 20 warm-up iterations. For 100 measured calls, p95 is **0.223ms before / 0.177ms after**; mean is **0.196ms / 0.156ms**. Both use the existing foundation classes and no view subscribers in this comparison. The separate installed-model fixture reports approximately **0.161ms p95**, zero additional idle text writes, and one pending run for 1,000 RequestSync calls.

These are projection/dispatch microprobes, excluding native rendering, physical MIDI and full TD frame cost. They do not establish whole-process memory stability, a long-duration soak or guaranteed frame rate. Evidence: `health_performance.json`, `health_verification.json`, `health_events.json`, `health_network.json`, `live_export_reload.json`.

## Remaining scope

Milestone 2 adds mapping Range/Mode/input configuration. Assignment/retargeting, typed Value widgets, filters, scoped Clear All, diagnostics and native custom-parameter definitions remain in later milestones. The old Inspector remains necessary. Physical forgotten-map Ping/re-LEARN acceptance is still pending; existing K2/LEARN acceptance is retained, not reused as proof of the new hardware recovery path.
