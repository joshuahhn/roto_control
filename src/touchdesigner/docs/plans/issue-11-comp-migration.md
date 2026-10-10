# Issue #11 explicit COMP mapping migration

Original source candidate based on `61d0e03fc454dba496618fdf33ab4a5169437b19`;
current scoped delta is composed onto accepted #12 local TREE
`55ef1a5febecb6c4f2428e49e899e15d5c030fd8` (not a commit).
[#9](https://github.com/joshuahhn/roto_control/issues/9) is CLOSED and its native
dependency is satisfied. [#11](https://github.com/joshuahhn/roto_control/issues/11)
remains OPEN. This candidate has not been installed in native TD; no user mapping,
live project, canonical binary, upstream integration or other worktree is changed.

## Workflow and authority

The migration module is embedded as `layout_migration` by `upgrade_layouts.py`;
the existing external builder calls that upgrade. Updating source does not run
migration. There is no startup/discovery migration or guessed classification.

The helper resolves shared `FIELDS`, `DEFAULTS` and `ActivationRollbackError`
from the installed same-controller `layouts` DAT module. Standalone Python
`import layouts` is not a native DAT dependency resolver. The DAT must be valid,
local and readable, with the identical Layouts manager class and usable shared
constants/exception; missing/foreign/unreadable dependencies fail closed. No
sys.path/import alias, copied schema, duplicate exception or global cache is used.

1. Coordinate a completely disconnected controller: no process/opening session,
   callback registration, LEARN, touch, LOCK, pending/gated/paused/backlog routing,
   quarantine or incomplete binding restore. Preserve a native recovery project
   or managed tox through TD before any real save/export. Generic tox is sanitized
   and cannot serve as a user configuration recovery copy.
2. Capture `GetLayoutRegistry()` and full user configuration. Allocate/reuse owners
   explicitly with #9 `RegisterComp` separately. Review source stable triples and
   owner tokens, not names/order/destination paths. The historical 5-record JSON
   inventory is not live evidence and is not loaded by migration.
3. Call `PlanCompLayoutMigration(migration_id, classifications, entries=None,
   active_variants=None)`.
   It returns a detached complete candidate, source revision/fingerprint, a row
   for every source Device and Track/container lineage. Planning only flushes
   current definitions/ownership metadata; it never writes target values or
   installs bindings. Unspecified records remain in place with a reason.
4. Review the entire manifest, new empty scaffolds and entry selection. Call
   `ApplyCompLayoutMigration(plan, recovery_path=...)` with an unused external path.
   It captures all local controller storage, full registry/materialized data,
   routing context, custom parameter settings, registration hook and targets DAT
   into a lossless typed JSON envelope at a new `.json` path, opened exclusively and fsynced before
   commit. Opaque/nonfinite recovery data is rejected; no lossy copy is accepted.
5. Validate the isolated source/native fixture, actual project and managed tox
   save/load, rerun/upgrade and empty generic export/load, then coordinate the
   minimum physical recall gate before canonical replacement/delivery by root.

Explicit classification example (IDs must come from the reviewed live inventory):

```python
rows = [{
    'source': [layout_id, track_id, plugin_id],
    'decision': 'move',
    'owner_layout_id': registered_layout_id,
    'owner_id': registered_owner_token,
    'evidence': {'kind': 'user-confirmed-ownership',
                 'reference': 'specific reviewed classification/capture record'},
}]
plan = controller.PlanCompLayoutMigration('user-reviewed-migration-v1', rows)
# Review plan first; only then, under the coordinated offline workflow:
result = controller.ApplyCompLayoutMigration(plan, recovery_path=recovery_file)
```

`registration-provenance` is the other accepted evidence kind. Both require a
documentary reference; the caller asserts ownership explicitly. A linked COMP
alone is insufficient. A retain decision requires a reason. Each move requires
a LEGACY source, bound source Focus matching the unique registered live owner
handle/local token/locator, and an existing bound COMP destination. CUSTOM and
already-owned sources cannot be moved. Unlinked/missing/ambiguous records remain
unclassified and in place; explicit invalid move requests fail the whole plan.

## Preservation and container policy

Devices remain atomic variants. All `id`, `group_id`, wire `device_id`, target
IDs/indices/identities/ranges/semantics, ordering, nine state fields, off-page
library, manual naming and unknown Device fields survive unchanged. Only moved
Focus metadata is qualified with the confirmed owner ID/canonical locator.
Device hashes remain `digest(device_id,8)`; target hashes `digest(identity,6)`.
Library index/hash collisions fail preflight, without automatic re-LEARN.

Track groups are partitioned by explicit destination. If any children remain,
the source retains the original Track ID; otherwise the first moved Device in
saved order determines which destination reuses it. Additional groups receive
deterministic new Track IDs, preserving Track metadata and child order. Lineage
records every split/reuse. A completely emptied source Layout retains its ID,
label/category/other metadata and gets an explicitly listed empty Track/Device
scaffold with new independent IDs. No old Device is deleted or duplicated.

Owner empty entries remain unless `entries={owner_layout_id: plugin_record_id}`
explicitly chooses a qualified existing/moved variant. The entry is not a wire
Device ID and does not define #10 Follow policy. Multiple same-owner qualified
Focus variants are preserved; no unlink/merge/drop. Manual `SelectPlugin` remains
available; #9's automatic Follow ambiguity policy remains unchanged.

The #10 notification describes Follow using the owner Layout's saved
`active_track/active_plugin`, never its entry ID/name/order/first Focus. This
candidate remains based on common `61d0e03`; no unaccepted #10 patch is imported.
By default migration preserves each destination's saved active choice, except
administrative relocation of the current routing Device described below.
`active_variants={owner_layout_id: plugin_record_id}` explicitly sets an inactive
owned Layout's saved Track/Device choice, requiring bound owner-qualified Focus.
This is independent of `entries`. A choice that would replace the current routing
Device is rejected; Activate separately. Plan/receipt `selection_changes` and the
full recovery/candidate show all outer saved-choice changes and their policy.
Administrative relocation preserves the existing Follow selection observation
baseline, updates only the common base's established `(old_layout,legacy)` scope
and invalidates old routing epoch; a mode-only scope is preserved for future #10 composition.
it does not turn the already-selected COMP into a new selection intent.

If the routing Device itself moves, its routing triple follows that same atomic
Device; the existing host, collection, watchers and materialized fields remain
installed. This administrative relocation changes containers, not target values
or bindings. It sends no MIDI/LEARN/UNMAP, does not Connect and does not Activate
a different Device. Manual selection afterward still reads live values and needs
fresh matching per-control hardware recall. Browse/Activate/FUNC/SEL scopes stay
as in the common base; no cross-Layout selector union or guessed control page.

## Transaction, rerun and recovery

Apply regenerates the candidate from the current flushed snapshot and compares
the entire supplied plan. Under `manager.mutating`, it force-checks ownership,
revision and both manager/persisted full fingerprints again, writes the recovery
copy, then commits registry/receipt and presentation context in one synchronous
TD-thread transaction. Reentrant mutations are blocked; no asynchronous gap
separates CAS from commit. `CheckLayoutRevision` alone is not used as a commit API.
The regular subsequent Tick publishes observer metadata after the transaction;
no observer or hardware readiness is treated as an atomic commit acknowledgement.
Rollback never lowers the routing epoch. A fresh intent/session observed during
an observer failure retains its pending payload/observation and ingress fence for
the existing next-flush fresh validation; it is not erased by restoring the old
configuration. No #10 origin/generation/owner payload is guessed or rewritten.

Receipt metadata is additive registry `comp_migrations[migration_id]`, version 1.
Identity is the explicit migration ID/version/request plus source Device stable
triples, not a target hash/name. Reusing an ID with a different request fails.
Repeated apply, planning, structural upgrade and reload return the original
receipt without recreating records or overwriting subsequent user edits. Missing
completed variants are reported rather than resurrected. No-op plans create no
receipt or recovery file. Recovery paths are never overwritten, including reruns.

Save/menu/publication failure restores full controller storage, registry,
materialized fields, routing/selected/bank context, owner/Focus handles and
presentation drafts, retaining a newer revision to invalidate stale plans.
Existing bindings/targets are never replaced. Target/native parameter settings
are captured for recovery but are not written during compensation. If recovery
itself fails, report `ActivationRollbackError`, pause/gate routing and retain the
immutable external recovery file; require explicit repair, not automatic retry.
The `layout_migration.decode` helper reads recovery envelopes for inspection;
it does not automatically install data or execute a hook/action.

Presentation compensation restores native evaluation modes after value/expression
setters; those setters change mode according to [Par Class](https://docs.derivative.ca/Par_Class).
OP-valued settings are captured as portable locators. Unrelated inactive
missing/conflict/unregistered owners keep their unavailable records; migration
does not require a live handle for their retained qualified Focus links.

## Accepted Action interoperability

Saved named Action references move only inside an explicitly classified atomic
Device. Preserve `action_id`, mapping ID, slot/index/identity/wire hash, adapter,
label, assignments and off-page library unchanged, including dangling providers.
An Action ID is never ownership evidence. CUSTOM Action mappings remain in place.
Malformed Action descriptors fail preflight rather than being converted/repaired.
Anonymous callback targets still require a reconstruction factory and are rejected.

Planning/apply/compensation never register, reconstruct or Recall an Action and
never install new bindings. The same runtime Action registry, providers, results,
collection and host controls survive relocation and successful rollback. Persisted
catalog diagnostics remain part of the full recovery copy. Real reload follows
accepted #12 semantics: saved registration reconstructs providers; runtime results
are not reconstructed or copied into the registry. Generic export retains #12's
empty mappings/provider hooks and disconnected state. Shared Action/publication/
ACK/owner/Inspector implementations remain unchanged relative to accepted #12.
No #10 implementation is imported; the explicit saved-active policy above applies.

## Acceptance matrix and evidence boundaries

| Case | Required evidence |
| --- | --- |
| F01 v1/v2/v3, inactive/empty records | Existing structural upgrade suite + complete migration manifest/invariant tests |
| F02 same-owner cross-Layout variants/same names | Atomic preservation, qualified duplicate Focus, explicit entry, native locators |
| F03 CUSTOM shared target | Independent full configurations/ranges; real value reads, no relocation |
| F04 missing/clone/unlinked/ambiguity | Fail-closed explicit move; retain/report unclassified; no implicit relink |
| F05 mixed Track | Original ID reused once; deterministic split lineage; routing same Device |
| F06 full library | 128 definitions/slot reuse/index/hash preservation; native page recall |
| F07 nine saved fields | Assignment/overrides/catalog/removal/pending/relearn/library deep comparison |
| F08 rerun/reload/upgrade | Receipt persisted; edits retained; stale plans rejected; recovery immutable |
| F09 collisions/schema/callback/capacity | Full preflight; no renumber/re-LEARN/callable conversion |
| F10 failure/recovery | Save/menu/publication injection; full restore; failed restore paused/gated |
| F11 no writes/Browse/Activate | Float/Pulse values unchanged; zero Pulse/Preset calls; common-base UI guards |
| F12 native persistence | Actual stopped-timeline project/managed tox save-load; full manifest/owner tokens |
| F13 generic export/load | Empty disconnected CUSTOM, no user receipt/storage backups/links/tokens/process; embedded helper/source |
| F14 physical recall | Existing learned source → migrated owner A/B/A/CUSTOM, reconnect/page recall without re-LEARN |

Prepared fixture: `diagnostics/issue_11/native_migration_fixture.py`. Seed requires
an empty controller/root and verifies installed source equality. It creates two
owners, mixed legacy Track, same-owner variant, manual CUSTOM, unlinked record
and Pulse target plus one saved demo Action registration/mapping. It never
Connects, switches projects or saves binaries. Native
source execution, failure injection, Pulse observer, actual save/load/export and
physical acceptance remain pending and must be recorded separately by root's
Inspector sole executor. Preserve every failed attempt/recovery capture.

## Short direct native window (Inspector sole executor)

Use one clean demo with the prepared two owners, variants, CUSTOM, unlinked,
Amount/Reset and named Action; do not use removed tools or historical inventories.
Retain the existing recovery checkpoint and every failed attempt.

1. Disconnected: seed, review explicit rows, run plan/apply/rerun. Compare the full
   registry/materialized/context recovery, atomic IDs/libraries/lineage/saved-active
   choice; observe unchanged Amount, zero Reset pulses and zero Action recalls.
2. Inject one commit/publication failure before a successful migration: compare
   complete compensation; exercise failed restoration once for paused/gated output.
   Check stale CAS before commit. Retain each recovery file; do not unlink it.
3. Save/load the demo project and managed tox through TD; verify owner tokens,
   original mappings/libraries/Action IDs, explicit provider reconstruction and
   idempotent rerun. Select variants/pages: no automatic Pulse/Action recall.
4. Export/load generic tox through TD: empty disconnected mappings/receipt,
   no user provider hooks/references; demo/source recovery remains intact.
5. Only root's coordinated physical batch: learn clean-demo source mappings first,
   migrate disconnected, then recall the same IDs after explicit Activate and
   matching real ACKs without re-LEARN. Test one deliberate Action Button and
   parameter input, then restore the checkpoint. Synthetic tests are not physical
   acceptance; do not repeat accepted #9/#12 physical gates.

The 14-case matrix remains the acceptance inventory; source coverage does not
replace its applicable native/physical evidence. No external validation framework,
extra rehearsal project or automatic source promotion is required.

Native import correction gate: repeat the accepted public `RemoveControl('Value')`
empty preparation and unchanged fixture.seed, then actual public Plan and Apply
with the installed local layouts DAT. Verify shared dependency/transaction/identity
preservation before continuing the five direct steps above. The prior actual Plan
failed with ModuleNotFoundError before any Apply; source regression green does not
satisfy this native gate. See diagnostics/issue_11/native_request.md.
