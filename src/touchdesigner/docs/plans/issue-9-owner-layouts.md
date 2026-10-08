# Issue #9 owner Layout implementation contract

Status: source implementation on `t3/issue-9-comp-custom-layouts`; no feature commit, push, merge, native deployment or physical acceptance. [Issue #9](https://github.com/joshuahhn/roto_control/issues/9) stays OPEN. [PR #14](https://github.com/joshuahhn/roto_control/pull/14) supplies product direction only; its docs are not a deployed runtime.

This contract implements the ownership allocation boundary. Cross-owner Follow (#10), migration of existing configurations (#11), and presets (#12/#13) remain separate. The earlier Inspector context contract in the root checkout is a read-only design reference; no root or Inspector worktree changes were imported.

## Vocabulary and routing

- **Ownership category** belongs to a Layout: `COMP`, `CUSTOM`, or `LEGACY` (unclassified). It describes where definitions are saved, not what parameters they target.
- **Layout** contains Tracks; each Track contains **Device configurations** (the protocol/API calls these Plugins); each Device has its own learned **control-page library**. Several variants may belong to the same owner.
- **Owner identity** is a durable token; a relative path locates the live COMP. Names, display order, Focus links, target references and hardware list bank offsets do not identify an owner.
- **Focus** identifies a Device's LEARN/Follow scope. It does not assign Layout ownership. Explicit API registration may target an external parameter; the existing Focus-scoped Free LEARN policy remains.
- **Inspector Browse** chooses a view. **Activate** uses one existing `SelectPlugin(layout,track,plugin)` command after the Inspector's own freshness/session/guard checks. Browsing metadata/targets does not select or connect. LIVE follows the routing projection; it does not change Follow preference.
- **FUNC** lists Tracks in the routing Layout; **SEL** lists Devices in the routing Track. Arrows address the routing Device's learned control pages. No union across owner Layouts, no category button, no absolute control-page index is introduced.

Under LOCK, hardware selected Track can differ from routing Track. Hardware explicit SEL retains its existing same-routing-Track exception; TD Activate still rejects LOCK. A successful Device selection resets visible Track/Device list banks; that does not change ownership. The reported SEL -> FUNC alternate “layout/layer” physical root cause remains unproven.

## Persistent representation

Registry `version=3` is retained with additive `ownership_version=1` and nonnegative integer `revision`. This avoids moving legacy mappings as part of #9. Versions 1/2 still use the existing structural upgrade. Any existing record lacking category becomes `LEGACY`, even if named Custom/CUSTOM or linked to a COMP. Only a fresh empty registry and explicit `CreateLayout` create `CUSTOM` records.

New owned Layout:

```python
{
    'id': '<layout-id>', 'name': '<editable display label>', 'category': 'COMP',
    'owner': {
        'id': 'owner.<uuid>', 'path': '../relative/COMP',
        'state': 'bound',
        'entry_plugin_id': 'plugin.<uuid>'
    },
    'active_track': '<track-id>', 'tracks': [...]
}
```

The COMP stores the same token under `roto_control_owner_id` in TD OP storage. Token reads always use `fetch(..., search=False)` so a nested COMP cannot inherit its parent's identity; [OP.fetch defaults to parent storage search](https://docs.derivative.ca/OP_Class). TD OP storage persistence/copy behavior must still pass native save/reload/clone acceptance. `entry_plugin_id` is a registry Device ID, **not** the Device's wire `device_id`. It identifies the recoverable owner entry, not a promise about #10's eventual unique Follow destination. New registration creates one empty EFFECT Track and a COMP-named Device with its own group/device IDs. Track/Device variants remain supported.

`owner.id` is unique per controller registry. A token is reusable by independent controllers, whose mapping databases remain independent. Identity inventory includes external COMPs under the controller's parent scope (including untagged copies), registered live handles, saved locators, and explicit enrollment candidates. Clones outside that inventory are not observable until included; this is a discovery scope limit, not a globally unique TD service.

### Same-owner duplicate Focus variants (#11 integration)

An owned Device Focus can explicitly reference the Layout owner:

```python
'focus_comp': {'path': '../relative/COMP', 'state': 'bound', 'owner_id': 'owner.<uuid>'}
```

Multiple Devices/Tracks in the same owned Layout may carry this same qualified link. Each Device remains an atomic configuration with independent `id`, `group_id`, wire `device_id`, target IDs/indices/identities and all nine saved state fields. Manual `name_mode` is valid on a qualified variant; ownership does not overwrite its label policy.

Unqualified duplicate bound Focus paths still fail validation. An owner-qualified link must match the Layout owner ID and locator; it cannot be added to CUSTOM/LEGACY to infer ownership. #11 must explicitly qualify confirmed same-owner variants in its detached plan. It must preserve unlinked/ambiguous configurations and manual Custom references in place. It may explicitly choose an existing variant as `entry_plugin_id`, preserving that variant's wire identity, or keep the newly allocated empty entry. No source variant needs to be unlinked, merged, replaced or discarded to avoid a collision.

Existing Follow resolution still requires a unique Focus destination **within the active Layout**. Multiple matching qualified variants therefore remain ambiguous for automatic Follow in #9; explicit `SelectPlugin` works. #10 must define the unique Follow destination using metadata without conflating its choice with ownership. #11 is blocked by OPEN #9, not by #10; this representation lets its preservation work proceed once the #9 prerequisite is accepted.

## Lifecycle policy

| Operation / condition | Source behavior |
| --- | --- |
| `RegisterComp(comp)` | Ensure/reuse the COMP's owned Layout, without selecting or importing existing mappings. Requires idle Parameter mapping. Same name on different COMPs never merges records. |
| Tag discovery (`roto_device`) | Calls the same allocation path while idle; does not append to active Custom Track or change routing. Removing tag retains the Layout. Existing legacy Focus mappings stay in place. |
| Live rename/reparent | Retain token and all IDs. Rebase references to the same live target across saved variants/libraries and active overlays; update COMP-derived Device labels. Layout display label remains editable and stable. |
| Reload | Discover the unique token using scope inventory/locator. A moved, untagged owner is recoverable within inventory. Never attach a saved owner just because its path/name matches. |
| Missing owner / same-path replacement with no matching token | Keep configurations; mark `missing`. Reject Activate, assignment, writes, hardware dispatch and recall. No token is assigned to the replacement automatically. |
| Active owner becomes unavailable | Clear mapping readiness and outstanding control context. Retain routing key but quarantine controls. Reload installs empty bindings with unavailable catalog entries while preserving saved targets/library. |
| Original unique token returns | Metadata can recover to `bound`; active quarantine remains until explicit Activate reconstructs bindings. Matching control ACK is still required. |
| Duplicated token / clone | Mark existing owner `conflict`, latch it and fail closed for every copy. Removing one copy alone does not acknowledge the conflict. |
| `RegisterComp(clone,new_identity=True)` | Explicitly give the chosen conflicted/unowned copy a new token and empty owned Layout. Never copy the original mapping database. Existing non-conflicted owners cannot be re-keyed. |
| `RelinkLayoutOwner(layout,comp)` | Explicit recovery/resume while another Layout is active. Reject if token still exists on another live COMP or candidate already has another token. Preserve mapping/wire IDs; rebase only that owned Layout's targets/libraries and qualified Focus variants. Independent CUSTOM references remain unchanged. |
| `UnregisterLayoutOwner(layout)` | Require another Layout active; retain tombstone `unregistered`, token, mappings, IDs and actual COMP. Tag discovery skips it; ordinary register rejects it. Explicit Relink resumes it. |
| Remove owner Layout / entry Device / entry Track | Reject direct deletion. Recovery entry/tombstone remains; future deletion policy requires a separate explicit design. No target COMP is destroyed. |
| Transaction failure | Restore affected registry/handles/token/materialized storage. If rollback itself fails, report `ActivationRollbackError` and set paused/gated with repair error. Never report success. |

Saved unavailable owner records do not quarantine the separate legacy callback registration route. Switching back to parameter Layouts restores ownership guards.

Ownership mutations also reject pending/gated/backlog/paused or opening MIDI sessions, LEARN, touch, LOCK, callback dispatch and legacy registration. They do not Connect, LEARN, UNMAP, write numeric target values or Pulse. Manual owner Layout selection uses the existing guarded activation and recall protocol.

## Integration API

Public methods are on `RotoPythonExt`; values returned by metadata/read APIs are detached copies.

| API | Contract |
| --- | --- |
| `RegisterComp(comp, *, new_identity=False)` | Idempotent ensure, returns Layout ID. No selection. |
| `LookupCompLayout(comp)` | Returns bound unambiguous Layout ID or `None`; conflict/missing/unregistered never resolves as an active owner. |
| `GetLayouts()` | Existing fields plus `category`, detached `owner`; `active` marks the registry's last selected Layout. It matches routing in Parameter mode; legacy callback mode has a separate route (`GetLayoutContext().legacy=True`, `key=None`), so this flag alone is not a routing assertion. Display order is not ownership. |
| `GetLayoutContext()` | Existing routing/selected IDs and key plus category, owner, revision, quarantine. Label contains category / Layout / Track / Device. |
| `GetTracks(L)` / `GetPlugins(L,T)` | Existing parent-scoped lists; Plugin metadata exposes qualified `focus_comp`. Their `active` fields are stored choices within their parent, not global hardware routing assertions. |
| `GetPluginTargets(L,T,D)` | Full saved library plus current definitions; read real target values at call time without activation/writes. `value_source=live/pulse/unavailable`; Pulse/unavailable values are `None`. Does not claim inactive entries are mapped/ACK-ready. |
| `GetControlState(s)` / `GetControlCatalog()` | Registered parameter values read live; unavailable owner/catalog slots have no claimed live value. Callback caches are explicitly `value_source=cached`. |
| `GetLayoutRegistry()` | Flush active definitions and owner status, then return detached complete registry and `revision`. Saved catalog observations remain advisory, not presets. |
| `CheckLayoutRevision(revision)` | Flush/check current revision; reject stale detached plan. This is a preflight seam, **not** a migration commit or rollback implementation. |
| `ValidateLayoutRegistry(snapshot)` | Validate schema/ownership/Focus/identity constraints without installing the snapshot. |
| `RelinkLayoutOwner` / `UnregisterLayoutOwner` | Explicit lifecycle operations described above. |

Synchronous read/Tick batches share one identity inventory, including nested metadata/Follow/catalog reads. This is not a timed cache: the next observation scans again, handle deletion/token/path changes trigger a fresh scan, and mutation/dispatch/Activate/revision checks force revalidation. Native performance/headroom remains an empirical gate.

Revision increases on persisted registry content changes, including structural edits, captured state, routing selection and observed owner status. No-op save/ensure does not increase it. Rollback may increase revision while restoring content, intentionally invalidating stale plans. #11 must run its revision check and serialized transaction together, retaining full registry, all materialized fields, context and rollback/paused policy. #9 supplies no arbitrary replacement/commit API and does not implement migration planning.

The nine state fields remain `parameter_assignments`, `assignment_device_id`, `control_overrides`, `removed_controls`, `pending_unmaps`, `needs_relearn`, `control_catalog`, `pending_unmap_identities`, `page_targets`. Preserve target IDs, index, identity, Menu/button semantics, off-page libraries and wire Device digest. Shared COMP/CUSTOM parameter values come from the real Par/BIND chain; definitions/ranges/libraries remain independent. Selecting a Layout reads live values and never restores saved numeric observations or fires Pulse.

Generic export calls the tested `reset_mapping_storage` on its detached clone, clears registry/token/materialized mappings, and rebuilds a fresh empty CUSTOM registry disconnected. It does not clear tokens on any external owner COMP. Existing embedded MIDI helper/external Python architecture and upstream Ableton/Bitwig/licenses/PDF references are preserved.

## Verification and remaining gates

Independent source review/fix/re-review is recorded in [source_review.md](../../diagnostics/issue_9/source_review.md).

Source baseline: 230 passing unit tests. Current source: 263 passing tests (`python3 -m unittest discover -q` from `src/touchdesigner`). Coverage includes allocation/reuse/same names, rename/reparent/reload, missing/replacement/clone, explicit recovery/unregister/rollback failure, owner-qualified variants, stale revision, shared live values and independent ranges/assignments/libraries, Pulse safety, stale ACK, existing guards and clone storage sanitization, native inherited-fetch semantics, unavailable/nonfinite parameter reads, one-inventory 16-slot/256-message read batches and fresh checks before dispatch/CAS. This evidence is unit/mock protocol behavior only.

Prepared [native source fixture](../../diagnostics/issue_9/native_owner_fixture.py) and [coordinated acceptance checklist](../../diagnostics/issue_9/README.md) have **not run in native TD**. Native source installation, TD OP storage persistence/copy, toe/tox save/reload, empty disconnected generic export, and real inactive Inspector integration are pending. No shared live project, Inspector `.45` worktree, canonical `.75` toe/`.40` tox or user mapping was changed.

One coordinated final session should combine native acceptance with Inspector, then capture physical FUNC/SEL/ACK/LCD traces. Existing accepted LOCK/paging/motor tests should not be requested again without a new regression reason. The user's exact SEL B -> FUNC symptom must be captured once alongside full candidate lists, visible offsets and routing key; synthetic MIDI cannot close that gate. No issue closure or blocker completion is implied by passing source tests or by opening implementation threads.
