# Targeted native validation — pending TD connection

The 2026-10-10 attempt found no twozero_td instance; TouchDesigner MCP
`project_info` failed to connect to `http://127.0.0.1:13316/mcp`.
No live project was inspected or changed. Source tests are not native acceptance.

When the selected project is open and MCP responds:

1. Confirm project path/build and local controller/model/view identities. Read any
   in-component instructions; retain a live-TD recovery export before changing code.
2. Use a disconnected, controller-local fixture with real Float/Int/Menu Knobs.
   Embed candidate commands/ui in that fixture only; do not redirect production
   views or open another MIDI owner. Verify installed DAT bytes against the worktree.
3. Measure SnapshotIntent and confirmed Save with 1 and 8 native Knobs against
   retained baseline source, using alternating bounded trials. Record Sync counts,
   elapsed median/p95 and native-definition refresh cost; capture changes no values.
4. Save through the actual model/view command path. Change a native definition,
   assignment or routing context before confirmation and check stale rejection;
   value-only edits must remain eligible. Confirm exactly one Save dispatch.
5. Exercise Clear's two-click path on fixture registrations. Second click must
   refresh once before dispatch. Touch/LEARN/replacement between clicks reject;
   values remain unchanged and only the selected registration is removed.
6. Export the disposable fixture through TD, reload it disconnected, and check
   candidate DAT bytes/local references and errors. Retain the export and evidence.
7. Stop fixture observers/queued callbacks before scoped cleanup; verify original
   source, mappings, values, MIDI ownership and visible project state preserved.

Do not mark this checklist complete until actual native results exist. No full
hardware campaign is required for unchanged protocol/dispatch code; physical
behavior remains separately unverified.

## Completed targeted native run (2026-10-10)

Correct project: `cleaned_owned_inspector_review.1.toe`, SHA256
`4f9bbe4b23a56fc4538c706a94697d8ae45cb221c699bb418658e2af0726d512`,
TD2025.33230. It was recovered from the retained owned-Inspector acceptance
artifacts, not main's older canonical `.75` Lister project. Original main source
was preserved; candidate was built only under an isolated disconnected fixture.

- Real native Float/Int/Menu and BIND Knobs; installed command/view DAT bytes exact.
- Twelve alternating baseline/candidate samples per workload; default8 median
  2.626→0.424ms, explicit8 3.297→0.321ms, explicit1 0.558→0.246ms.
  These measure synchronous command duration, not whole-frame or hardware latency.
- Actual Save leaves values unchanged; native definition drift expires confirmation;
  value-only drift remains eligible without rewinding current values.
- Actual view Action/Clear: second-click Sync3→2; registration removed once;
  duplicate click rejected; controlled runtime touch between clicks rejected.
  This uses native view/host state, not physical gestures or real MIDI touch.
- Actual fixture `.tox` save/load: two Snapshots restored, local model/controller
  references and changed source bytes correct, disconnected and zero native errors.
  This is a configured fixture export, not a sanitized generic export.
- Both fixture roots removed after quiescing observers. Original main executable
  sources, registry, catalog and no-process state match the captured baseline.
  Original compact Inspector reopened; canonical binaries remain unchanged.

Raw results and retained configured `.tox`: [native_results](native_results/).
One harness DAT-path error is retained as `configure_failure.json`; the corrected
fixture completed without changing product code. `.toe` candidate reopen, generic
sanitization, physical gestures/MIDI/motor feedback and long-duration FPS are not
claimed. No candidate installation into the original main controller.
