# Named Action presets

`RegisterAction(id, label, recall, *, replace=False)` registers a runtime consumer entry point. `id` is an explicit stable identity, independent of display name, COMP path, mapping ID and Layout ownership. `recall(event)` may call the consumer's existing COMP preset API or Python function; there is no assumed universal TD preset API. Duplicate IDs require explicit `replace=True`. The consumer must keep the meaning of an ID stable; reusing an ID for a different target cannot be detected by the controller.

`AssignAction(slot, action_id, *, button_type='push', id=None)` assigns one Button in the **current routing Device**, including an existing CUSTOM or COMP-owned configuration. It does not browse/activate another context or allocate COMP-owned Layouts. The returned detached control state contains the generated mapping `id`, `action_id`, `action_available` and `action_result`. Supplying a mapping ID is optional; default IDs are independent UUIDs. Reassigning the same valid action to the same slot retains the mapping; use `ConfigureControl(mapping_id, button_type=...)` to change its input adapter.

Supported registration workflow (no new assignment picker):

```python
# Saved controller registration DAT; runs in both setup modes.
def onRegisterActions(controller):
    consumer = controller.parent().op('my_tool')
    def recall(event):
        if consumer is None or not consumer.valid:
            return dict(status='unavailable', error='Tool missing')
        return consumer.op('presets').module.recall_clean(event)
    controller.RegisterAction('my-tool.preset.clean.v1', 'Clean', recall)
```

After `Applybinding()`, explicitly call `AssignAction(1, 'my-tool.preset.clean.v1')`. Open hardware LEARN, select Button 1, then use Inspector Learn or `Offerparameter(mapping_id)`. Wait for the matching ACK, exit LEARN and press the Button. Assignment/offer/ACK never recalls. Both the internal Inspector and current Inspector prototype show the action label/ID, availability, last result and error, including inactive saved configurations. Result/readback detail changes notify views without changing assignment tokens; changing action identity invalidates stale tokens. Its “Action presets” filter is a presentation category, not ownership metadata. Automatic structured result/readback changes use the existing `context_state` DAT notification and scheduled `RequestSync` chain: a detached runtime `actions` payload also covers registered actions outside current slots. It does not save results into the Layout registry or require a visible status/table change. Parameter-value-only traffic does not change this payload.

In Python registration mode, `onRegister(controller)` must still replace bindings. To register a saved collection directly, pass specs like `dict(kind='button', slot=1, id='my.mapping', action_id='my-tool.preset.clean.v1', label='Clean', mode='pulse', button_type='push')` to `BindControls`. The controller supplies the registry dispatch adapter; consumers do not supply a second `on_change` dispatcher. Anonymous callback Layouts remain unsupported.

## Dispatch and results

Only matching acknowledged, enabled, connected PLUGIN controls accept hardware input. Existing fences/session epochs reject stale input; LEARN suppresses business input. PUSH recalls on a rising edge: held duplicates and release do not recall. TOGGLE retains the existing latched-press adapter, including zero-valued presses and its 40 ms debounce/immediate idle feedback. Every accepted press calls `recall` once even if parameter values already match.

Hardware event fields are `action_id`, mapping `id`, `origin='hardware'`, `kind='pulse'`, `value=1`. `RecallAction(action_id)` is an explicit software entry point using the same consumer callback/results with `origin='software'`, `kind='pulse'`, `action_id` (no mapping ID). It rejects LEARN, restoration, recursive dispatch and pending/gated/paused/backlog context transitions and unavailable/quarantined owners. An owner returning requires explicit Activate before recall, as in the accepted #9 authority contract. It does not require a mapped Button. Selection, feedback, queries, source reload and export never call this entry point.

A callback returns `None` for success or a JSON-safe result object:

```python
return dict(status='validation_failed', error='Menu descriptor changed',
            preset_id='snapshot.immutable-id', revision=4,
            entries=[dict(target_key='choice', attempted=False, actual_value='beta')])
```

Accepted statuses are `succeeded` (`success` is normalized to `succeeded`), `unavailable`, `failed`, `validation_failed`, `execution_failed`, `partial`. Non-success remains non-success even when Python returns normally. Exceptions and invalid/non-JSON/NaN results become `failed`. Result `action_id` is always the registered ID; other JSON-safe fields, including provider entry/readback details, are preserved. Missing failure error gets a diagnostic fallback. `GetActionState(id)['result']`, `GetControlState(mapping_id)['action_result']` and the Inspector database expose detached results; the row shows status/error. `GetActions()` lists registered runtime entries.

A failed hardware dispatch suspends only that Button and clears its local mapping readiness. Other controls and the MIDI session remain usable; no success confirmation is emitted for the failed Button. Repair the provider, explicitly `AssignAction(..., id=old_mapping_id)` again, then obtain a fresh matching ACK. Explicit software recall returns the same result and diagnostics without suspending every mapping referencing the action. There is no rollback of arbitrary consumer side effects.

Snapshot providers can prevalidate their entire write plan and return `validation_failed` before any write; after native writes/readback they may return `success`, `execution_failed` or `partial` with entry details. That policy belongs to the provider (#13). This action layer neither captures Snapshot values nor implements another batch writer. It reads actual mapped parameter values after recall, including partial failure; deferred native watchers do not redispatch actions. Inactive contexts read true values on activation. COMP ownership/quarantine, publication and matching-ACK readiness retain the common-base semantics. Assignment/range/IDs/control-page libraries stay independent.

## Reconstruction, unavailable and export

`Applybinding()`/deferred initialization replaces the runtime action registry, runs `registration.onRegisterActions(controller)` once, then restores mappings. A missing hook leaves entries unavailable. A failed hook clears any partially registered entries, exposes its error and still restores unrelated parameter mappings. The hook must register entry points only; public software recall is refused while restoring. MIDI remains disconnected after extension initialization; Connect stays explicit.

Layout/Device/control-page records persist only `action_id` plus mapping metadata (ID, label, Pulse mode, adapter, slot/index/hash). They never pickle/store callables or capture preset values. Runtime results are not reconstructed; JSON diagnostic summaries may remain in the saved catalog until refresh. Labels never resolve missing actions to another entry.

`UnregisterAction(id)` removes the runtime entry point while retaining dangling mappings and their unavailable diagnostics; it does not unmap/delete user definitions. Re-register the same stable ID to restore availability; overwriting a provider's data can retain the ID. Missing entries also survive normal save/reload/page recall, so a late explicit registration can recover them. `RemoveControl(mapping_id)` remains the explicit mapping deletion workflow.

`export_component.export` clears clone storage/mappings, resets the runtime action registry and replaces both consumer registration hooks. Generic tox contains empty provider-capable source, no user actions, target references or connected session. Source remains untouched. Do not save/export binaries by editing them; run through TD in the coordinated native window.

## Evidence and pending gates

`test_action_presets.py` covers the contract with synthetic MIDI/fake TD handles. Run the complete suite from `src/touchdesigner`: `python3 -m unittest discover -q`. The composed common base is `61d0e03fc454dba496618fdf33ab4a5169437b19`. Full source suites currently pass 300 runtime and 215 Inspector tests. Native stages in `verify_action_presets.py` are prepared for a disconnected disposable fixture, using this worktree's source. Native execution, actual tox reload/export and physical Button/LED/LCD/motor acceptance are pending; source tests do not satisfy those gates.


## Action error provenance and assignment freshness

`GetControlState`/current catalog and Action library previews now expose `mapping_error` separately from the complete visible `error`. `mapping_error` reports binding/controller/owner or missing-action failures; provider execution status/error remains in `action_result` and the existing visible `error`. The Inspector uses authoritative `mapping_error` for Action metadata freshness, while keeping provider errors as display/health observations. Software partial/error then success/error-clear with stable identity, availability and ACK fields updates diagnostics without expiring assignment tokens. Unknown/older Action projections without string provenance conservatively retain generic error fences. Parameter/callback generic errors and true descriptor/definition/owner/session/availability/identity changes retain stale-command rejection. Hardware partial still suspends only its Button, clears readiness and requires explicit repair/fresh ACK; its real binding failure is metadata, not hidden history.

The r6 actual same-status scheduled.71→.72 gate passed in attempt4, including both resolved WeakMethod views; the companion actual partial/error token gate failed. These are bounded native observations, not full native/reload/export/physical acceptance. See docs/plans/issue-12-action-error-token-diagnosis.md for the stronger source regression and outstanding executor gate.
