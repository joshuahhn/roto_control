# Issue 12 scheduled Action result-details ingress diagnosis

## Actual native failure (not accepted)

Read-only original evidence: `/var/folders/5q/krg7wb4d4lsgpmlmgqvywj_w0000gn/T/roto-issue12-native-20261008T193240Z-4mqgqcpa/native_scheduled_details.json`. No manual Sync, no physical MIDI. Succeeded .71 reached model Sync28; succeeded .72 updated runtime/database but not targets, model Sync or Info across hundreds of frames. Assignment token remained identical. Retain the FAIL/history and all holder/tox/recovery evidence. The source reproduction below matches this notification pattern; a native re-run remains mandatory.

## Tight red feedback loop

From `src/touchdesigner/prototypes/inspector`:

```sh
python3 -m unittest -q test_scheduled_action_details.ScheduledActionDetailsTests.test_same_status_nested_details_reach_info_via_scheduled_ingress
```

Executed twice before fix: `AssertionError: 1 not greater than 1 : Scheduled model Sync never ran`. The final expanded regression also goes red against immutable r5 inspector_data loaded from tree9e251bb549d3b62d39882ea9d00f48738e379a06 in memory. No immutable bundle was edited.

The minimal replay uses actual `_publish_inspector`/`_flush_inspector`, `inspector_data.refresh`, the existing build_live observer install block and its callback text, `InspectorModel.RequestSync`/`SyncController`, model projection and scheduled subscriber dispatch. Only TD operator/parameter/DAT-change events and the end-frame runner are fake. It never calls manual model Sync to deliver the tested update. Current table must remain unchanged while same-status nested details go.71→.72. Removing that details update or changing visible status removes the missing-signal condition. Tests do not claim actual TD cook/DAT-event timing, live promotion, real parameter handles, tox reload/export or physical acceptance.

## Ranked hypotheses before fix and boundary probes

1. Missing structured detail in observed notification signal: predict publisher runs, database updates, targets/context_state unchanged and zero observer events. Confirmed in source replay: notifications=[], only args[0]._flush_inspector() scheduled, Sync1→1, Info.71.
2. Stale RequestSync coalescing latch: predict observer event/RequestSync but no model callback. Excluded at the earlier boundary: no notification happened; a context metadata event schedules and completes Sync2.
3. Projection/display equality misses nested details: predict Sync increments but Info/view stale. Excluded: same scheduled chain triggered by diagnostic context metadata signal updates Info.72 and detail-only slot notification.
4. Source snapshot stale: predict database.71. Excluded: database.72.

The context-change diagnostic probe is a discriminator only, not a workaround, native acceptance or a new runtime action.

## Correction and invariants

`inspector_data.action_diagnostics` reads detached JSON-safe registered action states. `projection_signature` includes it even when current slots/catalog are unchanged. `refresh` includes it as `actions` in the existing transient `context_state` DAT payload. Existing build_live `ControllerMetadata()` observer schedules RequestSync, whose owned run coalesces updates and executes the normal bounded model sync/one scoped owner observation. Builder watcher paths/source do not require changes. No observer is added to the full value database, no periodic scan/force Sync is introduced, and no routing/dispatch/MIDI/preset writes occur from metadata.

Status, nested error, revision, entries and readback travel as detached provider data. Details-only updates use DISPLAY_FIELDS, retain assignment tokens and emit display slot masks with metadata mask0. Action identity changes keep existing stale-token invalidation. Layout registry/owner/routing payloads do not change for result/value observations. Parameter-only value updates leave context_state unchanged. All registered actions provide the notification signal, so an inactive/off-page-only result can refresh its existing cached/subscribed context without adding a target to current slots or unioning library assignments. Existing owner notification fields/guards remain intact.

Source suite: runtime309, Inspector219 PASS, with four automatic ingress cases. Actual native chain is still pending. Root must verify the new full tree/patch/manifest, complete original baseline restoration/checkpoint, and explicitly authorize sole Inspector executor start. Re-run .71→.72 using a fresh frame/actual installed DAT parity, unchanged targets and assignment token, increasing scheduled model Sync and fresh Info/notifications; no manual Sync. Retain old failure and new attempt/restoration artifacts and their paths/hashes. Only after acceptance may root continue dependent actual reload/generic export; physical remains separately pending. #12 stays OPEN, #13 blocked. No #10/#11/#13 runtime changes.
