# Snapshot presets

A Snapshot stores current control positions, independently of mapping definitions. It follows the **current mapping of each saved slot**, including the current control page in the saved Device. It does not pin the original parameter.

For example, save Knob 1 at `0.4`, then replace Brightness with Blur. Recall outputs `0.4` through Blur's current mapping: range `0–10` writes `4`. Brightness receives no write. Float/Int conversion, rounding and Menu position use the existing mapping adapter. A newly assigned Menu uses its current options; the Snapshot stores position, not the former option name. An existing Menu mapping whose options drift still requires normal mapping repair/re-LEARN.

This slot behavior is the user's explicit clarification for #13 on 2026-10-09 and supersedes the original selected-parameter identity/menu semantics. There is no Snapshot target registry, reconstruction hook, Relink or historical target/type/range fingerprint.

## Save and manage

```python
preset = controller.SaveSnapshot('Clean')  # Currently mapped Knobs 1–8.
preset = controller.SaveSnapshot('Selected', [('knob', 1), ('knob', 2)])
controller.GetSnapshot(preset['id'])
controller.GetSnapshots()                  # Detached records; no writes.
controller.GetSnapshots(scope=(layout_id, track_id, device_id))
controller.ValidateSnapshot(preset['id'])  # Current slot readiness only; no writes.
controller.OverwriteSnapshot(preset['id'], expected_revision=preset['revision'])
controller.DeleteSnapshot(preset['id'], expected_revision=preset['revision'])
```

Explicit `slots` selects real current Float/Int/Menu Knob mappings. BUTTON slots (PUSH or TOGGLE), native Pulse, Action and arbitrary callback slots are excluded. The internal Snapshot binding adapter also understands writable Toggle parameters, but current public assignment supports Toggle on Buttons only: no public Toggle-to-Knob assignment is available. This feature does not expand that policy. Buttons only invoke Recall through the shared Action API. Save captures Knobs only; default Save captures all mapped Knobs; no mapped Knobs is an error. Default Overwrite captures the preset's existing selected slots; an explicit slot list replaces that selection. Duplicate/empty/invalid selections fail without changing stored data.

Save/Overwrite capture **live** normalized positions (`0–1`), not cached host values or former target units. They never write targets. A new preset gets a durable `snapshot.<uuid>` ID. Overwrite retains that ID and increments its revision; a stale confirmation fails. Same-name Save is an error requiring explicit Overwrite. Delete removes values and unregisters the provider; saved Button references remain visibly unavailable. Creating the same label again gives a new ID and never redirects old references.

Each preset has explicit Layout/Track/Device IDs and COMP/CUSTOM category/owner metadata. It belongs to the saved Device, and applies its saved slot positions to that Device's **currently loaded page**. UI names/dialogs show Knobs, normalized positions and this Device/current control page. No absolute page identity is invented from the hardware arrows. Browse can inspect/delete/manage references; capture/overwrite/recall require that Device to be activated. A preset is not transferable to another Device merely by assigning its Action there. Legacy Python registration has its own registration scope.

## Recall

```python
controller.AssignAction(1, preset['id'], button_type='push')
result = controller.RecallAction(preset['id'])  # Explicit software recall.
```

Both use the existing [Action entry point](actions.md): Button PUSH/TOGGLE edge handling, LEARN, ACK, owner/quarantine, restoration, routing transition and recursive-dispatch guards are shared; Snapshot preflight also requires touched controls to be released. Snapshot adds no dispatcher or hardware mode. Assigning a Button does not recall. Layout/page selection, LEARN, ACK, query, reload and export never recall.

Recall resolves current slot mappings, checks their existing write readiness before the first write, converts saved positions through their current ranges and uses `Binding.write`. Unassigned, suspended, Pulse/Action/callback or incompatible slots return `validation_failed` with zero writes. This readiness check reuses the mapping's current validation; it does not compare targets with historical Snapshot identities or semantics. Changed mapping definitions are intentional and accepted.

Writes are real TD parameter writes. Results preserve `preset_id`, `revision`, per-slot `mapping_id`, saved position, output value, attempted/verified flags, true target-unit `actual_value` and error. A setter/readback failure stops the batch and returns honest `partial`/`execution_failed`; final readback catches later callback changes to earlier values. There is **no atomic rollback guarantee** for consumer side effects. Motor/LCD feedback uses the existing Host path with true readback, including partial failures.

Hardware non-success follows Action failure isolation: that Button needs explicit repair/reassignment and fresh matching ACK. An independently invalid target mapping can also be suspended by the normal target watcher; repair it through existing assignment APIs. Software failure does not suspend every Button referencing the preset. Provider diagnostics remain distinct from mapping readiness errors; details-only result changes do not invalidate Inspector assignment tokens.

## Inspector and persistence

Use Connection **Open Inspector** to open the controller's owned compact Inspector, then choose **Snapshot presets…** in the existing filter menu. Save current Knobs directly, or add/remove selected Knobs and Save the selection. Choose a preset to inspect saved/current positions, validate, explicitly Overwrite/Delete, assign to the selected Button, or Recall. Name/Overwrite/Delete dialogs are asynchronous; cancellation performs no action and stale session/context/definition/revision confirmations are rejected, including every implicitly captured slot in default Save/Overwrite. Activate a browsed Device before capture/recall. The local model/views and headless publication remain owned by this controller; opening or rebuilding their subscriptions never recalls a preset. No additional Inspector window or geometry is created.

JSON storage `snapshot_presets` version `2` contains IDs, labels, revisions, scope and `{kind, slot, value}` entries. No target paths/handles, callbacks, old ranges or session/ACK state persist. During both Applybinding setup modes, saved providers rebuild after `onRegisterActions` and before mapping restore/`onRegister`; no Snapshot-specific user hook is needed. Existing saved mappings then resolve their current parameters. Save the project/component normally to persist the data. Extension reload itself executes no preset. The abandoned, unshipped version-1 parameter-target experiment is rejected and retained for recovery rather than guessed/migrated into slot data.

Generic export clears all presets/tombstones, user mapping references, runtime providers and registration hooks/session state. Source Markdown is embedded through `scripts/td_project_docs.py` when the component is built/exported. Actual TD save/load/export, native dialog behavior and physical feedback remain separately coordinated acceptance gates.
