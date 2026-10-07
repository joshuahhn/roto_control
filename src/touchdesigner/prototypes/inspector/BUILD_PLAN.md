# Compact Inspector build plan

2026-10-08. The initial scout below was read-only. Milestones 1–4 are implemented; milestones 5–6 remain planned.

Milestone 1 adds mapping health, shared commands/capabilities, bounded native definition caching and root callback cleanup in both views. Pure tests and isolated native fixtures pass, including automatic touch/mode updates and invalid inactive targets. See [HEALTH_REPORT.md](HEALTH_REPORT.md) for evidence and performance scope. Milestone 2 adds a separate collapsible Mapping draft and validated Range/Mode/Input configuration. The header now uses Device-first dropdowns with Layout | Track below. See [MAPPING_REPORT.md](MAPPING_REPORT.md). Milestone 3 adds shared bounded target discovery, explicit assignment/retargeting and typed Value controls; see [TARGET_REPORT.md](TARGET_REPORT.md). Milestone 4 adds filters, Details, scoped Clear Device and Reveal/Repair; see [PARITY_REPORT.md](PARITY_REPORT.md). The old Inspector remains available; replacement acceptance and native parameter definition editing remain later work.

Native window resize deformation in both the main Inspector and Popup is unresolved and deferred by the user in [issue #6](https://github.com/joshuahhn/roto_control/issues/6). It does not block other milestones; native visual acceptance remains required before replacement.

## Outcome and scope

Retain the compact vertical list and Fold/Popup presentation while restoring the existing Inspector's assignment, configuration and diagnostic capabilities. Use one editor with Value, Mapping and Advanced sections. Fold content scrolls inside the existing window. Popup sections add/remove only their height delta downward; manual width/height remain independent. Keep 24px actions, 12px side insets and 6px gaps as the starting design, not a restriction on future fields.

Replacement requires target assignment/replacement, compatible mapping Mode, PUSH/TOGGLE adapter, mapping Range, mapping health, COMP/callback filters, scoped Clear All and diagnostics. Native custom-parameter definition/Style editing is additional scope: the old Inspector does not perform native Style conversion.

Source builders/modules remain authoritative. Existing controller APIs own writes. Retain the old Inspector until the replacement gates below pass. Preserve upstream integrations and production runtime during the parity milestones. No commit/push or PR mutation is part of this planning pass.

## Verified scout

| Area | Current live state |
| --- | --- |
| Project | `inspector_editor_actions.2.toe`, TD 2025.33230, nominal 60 Hz |
| Controller | `/roto_control_python/roto_python`; Connected/Plugin/Mapped true; LEARN/touch false; no Lasterror |
| Roots | `/inspector_model` (100,-300), `/inspector_below` (400,0), `/inspector_popup` (750,0); each 160 x 130 in the network |
| Shortcuts | Shared model: `InspectorModel`; each view: `InspectorDemo` |
| Model | 11 direct children, including four annotations; six Python/observer DATs and one documentation DAT |
| Views | 29 direct children each; Below depth-two inventory contains 88 operators. Each editor has 32 direct children, including auto-generated text callback DATs |
| Signal graph | Model and both view roots have zero signal connections and no wire cycles. This does not prove that Python callback dependencies are cycle-free |
| Errors | No operator errors under the three prototype roots |
| Windows | Both main and both editor windows currently closed; preserve this during planning |
| Perform root | No `/perform` operator. Use the verified explicit component paths rather than assuming `/project1` |

Model network bounds: annotations span x=0..830 and y=-345..150. Functional DAT bounds end at x=805. The rightmost view nodes end at x=960; root rows extend to y=-800. The existing editor's own child network ends at y=-960.

Two overlapping pairs exist in the inspected Below root: `ui` / `window_opened` at (0,0), and `click_follow` / `click_presentation` at (800,-800). The Popup root's overlap list must also be captured before cleanup; only its graph/errors/root geometry were checked in this pass. These are network-layout issues, separate from visible panel spacing.

## Modules and ownership

```text
Existing Roto controller: catalog, validation, MIDI/session, authoritative mappings
  inspector_model
    InspectorModel / live_model: bounded projection + subscriptions
    base_commands: capabilities, token checks, write commands, result messages
    base_targets: on-demand compatible-target discovery + bounded picker cache
    existing observers: coalesced frame-end refresh
  inspector_below / inspector_popup
    ui: presentation and window lifecycle
    editor_state: independent Value/Mapping drafts and confirmation state
    base_draft: existing field backing, extended rather than duplicated
    editor_below / editor_popup
      existing Value/action controls
      container_mapping: range, mode and input type
      container_picker: search + bounded result rows
      container_advanced: parameter definition and diagnostics
```

The controller is the only authoritative mapping store. Picker tables and caches are projections, not a second registry. Fold and Popup share commands/capability rules and use the same field schema; their draft/scroll/selection remain local. Do not create a controller clone for each module or selection.

`commands.py`, `target_catalog.py` and `editor_state.py` are external Python sources embedded as DAT modules by the builders. Start with two shared baseCOMPs and one extra module DAT per view. Add further modules only where a separate responsibility emerges.

## Data flow and public interface

| User operation | Shared command / existing API | Required behavior |
| --- | --- | --- |
| Browse | Existing Choices/GetCatalog | Never changes routing; inactive state reads as saved/browsed, not a fabricated hardware ACK |
| Live Value edit | Existing `Commit` -> `SetValue` | Validate native type/range, active context, LEARN/touch and draft token; unchanged draft does not rewind live Value |
| Configure mapping | Proposed `Configure(context, slot, patch, token)` -> `ConfigureControl` | Submit compatible range/mode/input changes together; validation and re-LEARN remain controller-owned |
| Assign/retarget | Proposed `Assign(context, slot, target_handle, token)` -> `AssignParameter` | Support empty slots; revalidate OP/Par and duplicate ownership at execution; preserve other registrations |
| Ping / Clear | Existing methods, delegated to shared commands | Preserve current guards/confirmation; offer is not an ACK; Clear keeps target Value |
| Clear All | Proposed `ClearDevice(context, confirmation)` -> `RemoveAllControls` | Confirm explicit Layout/Track/Device and full registration fingerprint; report remaining/removed targets on partial failure |
| Explicit activation | Later command -> existing SelectLayout/SelectTrack/SelectPlugin | Separate action from browsing; honor controller routing/session guards |
| Diagnostics | Public snapshots/context plus existing state DATs | Read only; distinguish controller Follow/LOCK/selected-routing state from view-following |

Use the view's Model OP parameter and parent shortcuts across components. There are no new signal wires, TOP/CHOP conversion chains, in/out operators or null endpoints required for this command-based design. Callback execution routes UI -> shared commands -> controller API -> existing publication -> shared model -> view. Commands must not call back into a second write through the refresh path.

Retargeting and subsequent configuration are separate commits initially. Two different controller API calls must not be presented as one atomic transaction. Configuration-only patches use the single validated `ConfigureControl` call.

Capabilities name four distinct concepts: native `Style`, mapping `Mode`, declared hardware input TYPE and TD parameter evaluation mode. Native Toggle/Pulse/Menu enforce compatible mapping choices. Menu has fixed index bounds and labels; buttons keep 0/1 bounds. A Hardware adapter change does not rewrite controller TYPE and normally retains mapping; changed range/mode semantics require re-LEARN.

Projection changes must include `button_type`, binding type and capability-related metadata, currently absent from the model's metadata signature. Add native evaluation/read-only/clamp information when deriving editable-field capabilities. Re-read definitions on section open/explicit Refresh and before applying; a value-change watcher alone does not cover definition or evaluation-mode changes. Compatible BIND aliases whose resolved master is writable remain supported; duplicate bind-master ownership and unsupported expression/export modes are distinct rejection reasons. Runtime health/touch updates need notification without invalidating a Value draft merely because the value changed. Extend exact observers as needed for Touched/Bindingvalid/Lasterror and controller Follow/LOCK; recheck native owner/parameter names before installation. Do not watch every Rx/Tx increment. Individual target state is read freshly at command execution even if aggregate touch status has not changed.

## Operator and position allocation

Coordinates below are network positions, not panel pixels. New operators have explicitly planned sizes; use measured sizes again after creation. Existing root/model annotations remain, with new functional groups beside them.

| Parent / operator | Type / family | Position / size | Role and connection |
| --- | --- | --- | --- |
| `inspector_model/base_commands` | baseCOMP / COMP | (875,-40), 160 x 130 | `InspectorCommands` shortcut; Model OP references `parent.InspectorModel`; invoked through model wrapper |
| `base_commands/InspectorCommands` | textDAT / DAT | (0,0), 130 x 90 | Embedded `commands.py`; promoted extension, no execute-every-frame DAT |
| `inspector_model/base_targets` | baseCOMP / COMP | (1105,-40), 160 x 130 | `InspectorTargets` shortcut; Model OP references `parent.InspectorModel`; on-demand discovery |
| `base_targets/TargetCatalog` | textDAT / DAT | (0,0), 130 x 90 | Embedded `target_catalog.py`; query/cache methods |
| `base_targets/table_candidates` | tableDAT / DAT | (175,0), 130 x 90 | Bounded visible result projection; no signal input |
| each view / `editor_state` | textDAT / DAT | (1135,0), 130 x 90 | Independent draft/capability state; imported by existing `ui` |
| each view / `click_follow` | existing panelexecuteDAT | (1135,-210), 130 x 90 | Move existing overlapping callback, preserve panel target |
| each view / `click_presentation` | existing panelexecuteDAT | (1310,-210), 130 x 90 | Same; keep one main window |
| each view / `window_opened` | existing parameterexecuteDAT | (1485,-210), 130 x 90 | Move off `ui`, retain existing monitored window |
| each editor / `container_mapping` | containerCOMP / COMP | (1135,-40), 160 x 130 | Mapping fields, created once on first use |
| each editor / `container_picker` | containerCOMP / COMP | (1365,-40), 160 x 130 | Search/result panel, created once on first use |
| each editor / `container_advanced` | containerCOMP / COMP | (1595,-40), 160 x 130 | Definition/diagnostics panel, created once on first use |

Shared model annotation reservations: Commands at (850,-65), 210 x 215; Targets at (1080,-65), 210 x 215. Their tops align at y=150 with existing groups and have 20px gaps. Internal Commands annotation: (-25,-25), 180 x 175. Internal Targets annotation: (-25,-25), 355 x 175. All preserve 25px bottom/side and 60px top clearance.

View state annotation reservation: (1110,-25), 180 x 175. Events: (1110,-235), 530 x 175, giving 35px between the two new groups. Event operators are top-aligned at y=-120. Existing view groups need bounds computed during cleanup instead of adding boxes over the current grid blindly. Editor section annotations reserve (1110,-65), (1340,-65), (1570,-65), each 210 x 215; their horizontal gaps are 20px.

Inside each new section, start a fresh local position map at x=0 and place independent handlers at 175px spacing; parallel source/field groups start 210px lower. Names must be verified after creation to catch numbered duplicates. Parent panel layout uses relative dimensions, `fit=off`, exact scroll clipping and the existing native window size; it does not derive UI scaling from these network coordinates.

Live `get_help` verified available parameter groups for base/container/text COMP, table DAT and panel/parameter execute DAT. Relevant controls include `fit`, `crop`, `mousewheel`, `pvscrollbar`, `text`, `type`, `precision`, `editmode`, `callbacks`, `panels`, `panelvalue`, `offtoon`/`ontooff`, `op` and `pars`. Query exact menus again before building. Select-only metadata, disabled choices and contextual hints should explain unsupported operations.

## Build milestones and gates

| Milestone | Deliverable | Gate before moving on |
| --- | --- | --- |
| 1. Health + command seam | State badges; connected/invalid/saved/Needs re-LEARN distinctions; shared capabilities/commands; fix root node overlaps | Fresh real snapshots drive badges, inactive targets never claim ACK, stale commands are rejected, idle causes no extra text writes |
| 2. Mapping configuration | Collapsible Mapping section with range, compatible Mode and PUSH/TOGGLE declaration | Invalid drafts preserve existing config; adapter-only change retains ACK; changed semantics require re-LEARN; callback/native/Menu cases tested separately |
| 3. Assign + typed Value | Searchable compatible-target picker; empty-slot assignment/retarget; Menu dropdown, Toggle switch, integer-aware fields | Replaced target fences old events; duplicate bind-master ownership, unsupported modes and readonly/missing targets explained; compatible BIND aliases supported; unaffected controls preserved; no Pulse action from rendering or Ping |
| 4. Diagnostics + parity tools | COMP/callback filters, stable ID/error detail, Follow/LOCK/routing state, scoped Clear All and target reveal/repair | Scope/confirmation expiry and partial-failure reporting pass; browsing stays read-only; no extra editor windows or per-frame tree scans |
| 5. Replacement acceptance | Fresh builders, generic exports, project reload, all slots and adversarial updates, physical Ping and configuration re-LEARN | Old Inspector parity checklist complete, physical gates recorded, bounded subscriptions/queues/cache and render cost measured |
| 6. Advanced workspace | Parameter metadata inspection/editor link, definition-change preview, explicit context activation; later templates/batch repair/Style migration | Definition vs mapping semantics clear; reference impact assessed; no automatic native Style recreation without a tested migration contract |

Native Style migration is a separate prototype, first on an isolated target. `Par.style` is read-only; copying Value into a recreated parameter is insufficient. A migration design must account for parameter groups, name/label/page/order, defaults/clamps/menu choices, expression/export/bind references, mapping identity and re-LEARN. Initial Advanced UI displays Style and links to TD's editor rather than inventing a setter. Metadata writes also need their own change contract; they are not implied by mapping Range edits.

For each milestone, use the skill's build sequence: infrastructure -> source modules/data -> processing/capabilities -> references/callbacks -> exposed parameters -> extension initialization. Create containers before children, initialize extensions after all dependencies exist, and verify promoted calls from outside the component. Build independent operators in a phase with `build_network` where supported; use the external idempotent builder for callback contents/custom parameters/lifecycle. Never rebind or reinitialize the production extension just to refresh the new UI.

## Cache, lifecycle and verification

- Keep the existing four-context model LRU and one frame-end scheduled refresh. Allocate each section once per editor host and reuse it. Four existing hosts are the maximum, not one editor per slot.
- Picker uses at most 24 visible result rows per host, backed by the shared on-demand catalog. Bound its cache by both 32 scope/kind snapshots and 4,096 entries; release OP/Par references on eviction/disconnect and refresh/revalidate before committing. Large uncached discovery uses a cancellable, finite job with one pending continuation and a cooperative 2ms work budget per event-loop slice. It is initiated by opening/refreshing the picker, not by permanent frame polling. Context/session/query generation changes cancel old results. These limits are defaults to test, not measured optimum values. Typing filters the current snapshot without rescanning every frame.
- Subscribe only to relevant owners/parameters. Closed/hidden sections defer text writes. Diagnostics RX/TX counters are read on open/refresh, not added to hot observers.
- New caches, candidate tables, confirmation tokens, target handles and draft destinations must clear during generic export. Reload must restore exactly two view subscriptions and no embedded controller or user destinations.
- Pure tests exercise commands/drafts with fake adapters; native fixtures use isolated disconnected controllers and captured protocol output. Do not delete or reconfigure the user's current real mappings merely to test removal or configuration.
- Test stale drafts/session/context/target deletion, changing Menu options, mixed Int/Float/Menu/Toggle/Pulse/callback targets, touched controls, LEARN on/off, disconnect/reconnect and partial Clear All failure. Confirm that UI refresh cannot execute business Pulse or echo a second write.
- Re-run the 230-runtime/79-current-Inspector baseline plus meaningful new tests; run `git diff --check`. Review operator errors, callback/reference graphs, actual sizes, annotation containment/gaps, names and file dependencies after each milestone.
- Before declaring replacement, run matched idle/redraw/editor/context/picker workloads and a 30-minute fixture soak. Log operator/subscriber/cache/queue counts and whole-process memory, plus sync/dispatch/native-render timing separately. Compare against a fresh baseline in the same project; investigate a >10% p95 regression rather than assuming that the historical 0.395ms sync result guarantees rendering performance. Native OS X/reopen churn is a separate scenario.
- User hardware acceptance covers forgotten-map Ping/ACK, knob Range re-LEARN, button input adapters and Menu behavior, then all sixteen slots/cross-Device isolation. Sent metadata and unmap requests alone do not establish persistent hardware success.

The next implementation slice is Milestone 5: replacement acceptance. Milestones 1–4 are implemented; the deferred resize bug remains tracked separately, and parameter definition changes remain later work.

## Source references

- [Current compact UI](ui.py), [shared live adapter](live_model.py), [builders](build_live.py), [export lifecycle](export_live.py).
- [Existing Inspector operations](../../code/py/roto_python/inspector/inspector_data.py), [native menu callbacks](../../code/py/roto_python/inspector/lister_callbacks.py), [controller APIs](../../code/py/roto_python/RotoPythonExt.py).
- [Inspector semantics](../../docs/functions/inspector.md), [current verification](LIVE_REPORT.md), [historical mock stress](SHARED_MODEL_REPORT.md).

## Additional integration investigations

User requested [Serial API feasibility/read-back (#7)](https://github.com/joshuahhn/roto_control/issues/7) and [CHOP/binding takeover with selectable synchronization (#8)](https://github.com/joshuahhn/roto_control/issues/8). Both require scoped design/prototype evidence before extending the production host. The latter separates source ownership from target sync strategy and coordinates with runtime BIND ownership issue #5. They do not establish that EXPRESSION/EXPORT/non-Par masters are writable today, and do not supersede the deferred resize issue. The Mapping label is now HW Type for the declared local button RX adapter.

## In-window header dropdown refinement

After two physical traces show missing first-item releases and a timing-only trial fails, replace the three floating header menus with one bounded panel per Inspector root. Keep existing selector IDs/guards and read-only browsing. External builder: build_context_menu.py; pure row pool/capacity: context_menu.py; UI dispatch in ui.py. Reuse eight rows and native MDI icons, add bounded paging/wheel callbacks and scoped ESC dismissal, then verify same window, no dimension/routing/session changes, generic scrubbing and native geometry. Physical input acceptance remains pending; resize issue #6 stays deferred.

## Milestone 5 acceptance progress

Finite matched-frame/RSS/16-slot runners and native parity rechecks are implemented. The first soak stopped after 352 seconds when Popup height reached 2074px for 178px content. The collapse/reopen viewport-cache race is fixed and reproduced before/after; the full 30-minute gate remains pending. Source/evidence and physical gates are in REPLACEMENT_REPORT.md and replacement_physical_gates.json. Real production data is restored.
