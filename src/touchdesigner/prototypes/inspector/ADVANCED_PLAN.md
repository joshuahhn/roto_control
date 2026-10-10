# Advanced parameter workspace: first slice

2026-10-08. Status: first slice installed; see [ADVANCED_REPORT.md](ADVANCED_REPORT.md). The user accepts deferring further performance work and agrees to native metadata inspection plus TD editor access first. Native Label/default drafts are now installed as the first6b slice (DEFINITION_EDIT_REPORT.md); native slider/clamp bounds are also installed (DEFINITION_BOUNDS_REPORT.md); Static Menu labels are installed with active/inactive binding reconciliation (DEFINITION_MENU_REPORT.md); lossless scalar Float/Int Style preview/Apply is installed (STYLE_MIGRATION_REPORT.md); other Style conversions remain future work. The plan below preserves the pre-build scout and allocation; measured cleanup places native actions at1000/1200 with an annotation starting975 for an exact20px gap. Native same-owner dialog reuse and Follow behavior pass the isolated test.

## User flow and compact layout

Open a control, then its existing information button. Add a **Native parameter** group above the existing Mapping / Hardware routing / Technical groups. Reuse `container_details`, its scroll viewport and current 224px section delta. The collapsed editor remains178px; this section remains402px including the base. Opening Mapping instead remains312px. Content length changes the internal scroll extent, never the section/window height. Fold uses its existing list scroll; Popup uses the existing intended-geometry/settlement path and retains manual width/base height/top-left. No additional inspector Window COMP or automatic native dialog on open/selection/startup.

Readout:

- Native name, Label, Page and Style; clearly distinguish Style from mapping Mode and numeric input preference.
- Default constant plus default evaluation mode/expression/bind expression when relevant; do not describe a constant default as the entire default behavior.
- Numeric **Slider range** (`normMin/normMax`) separately from **Clamp limits** (`min/max` with `clampMin/clampMax`). Mapping Range stays in Mapping.
- Evaluation mode, read-only/enable state; BIND master and inherited range, or EXPRESSION/EXPORT source where present. Show the assigned parameter and resolved master separately; opening an editor targets the assigned owner.
- Menu names/labels: bounded eight-item preview with total count; the TD Definition editor gives full access. Callback/unassigned/deleted targets show a specific reason and no native-editor action. Do not retain Par/OP handles in display snapshots or TD storage.

The existing Details footer becomes five24px MDI actions at the bottom-right, with12px right inset/6px gap: Refresh, Reveal, Repair, **Values**, **Definition**. Use TD's bundled icon metadata to select consistent icons and provide hover hints. Reveal preserves controller Follow/routing by clearing destination child selection before showing the COMP node in its parent network while Follow is enabled; preserve Repair's explicit Assign flow. The current section width fits these actions without widening the editor. Long target/source text is selectable and wrapped.

**Values** calls documented `owner.openParameters()`; **Definition** calls documented `ui.openCOMPEditor(owner)`, available only for a custom parameter on a valid COMP. These open TD-owned dialogs only on explicit user clicks. Probe repeat-click reuse and Follow-on routing behavior on an isolated fixture before installation; do not assume either dialog's reuse or selection behavior. If opening can change routing under Follow, expose a clear guard, leaving Follow unchanged. Do not select Network Editor nodes or change the native parameter page merely to focus a parameter in this slice.

## Verified live scout

Active `inspector_editor_actions.34.toe`, TD2025.33230, MCP13316, nominal60Hz. project_info supplies no Perform root: use the verified paths below, not an assumed /project1.

| Scope | Existing state / bounds |
| --- | --- |
| Controller | `/roto_control_python/roto_python`: connected PLUGIN, idle LEARN/touch, six matching ACKs; Follow on |
| Model | `/inspector_model`, shortcut InspectorModel;15 direct children, rightmost functional node ends x1265, annotation ends1290; y−345..150 |
| Views | `/inspector_below`, `/inspector_popup`, shortcut InspectorDemo;43 direct children each; last functional node ends2400, annotation2425; y−825..190 |
| Four editor hosts |52 direct children each; last functional node ends2630, annotation2655; y−1145..190. No new root/editor host required |
| Details section | Existing218px container,178px viewport plus footer; current annotation (−25,−185),980×375; rightmost functional node ends930 |
| Windows | Existing main240×390, B1 TOGGLE/value1 Mapping Popup328×312; only Below main/editor open |
| Signal graph | Model and both view roots: zero signal connections, no wire cycles. Python command dependencies require separate review |
| Errors | Inspector/controller child roots clear. Global scout reports a historical parent storage-save warning from the now-destroyed export fixture; process-object storage corrected to PID on disk. No claim that the parent's retained warning is cleared |

Native Lowthresh read-only scout: custom Float, Page Mask, Label Low Threshold, default0.25, slider0–1, clamp0–1/both on, CONSTANT, readOnly false. Original live mappings/Values untouched.

Editor hosts are `container_scroll/container_content/editor_below` and `base_popup/editor_popup/container_editor_content` under each view. A missing-path probe omitted editor_popup; corrected against the live host paths. No nodes were created by scouting.

No functional overlaps appear in the scoped root/editor inventories with measured sizes. Existing annotation/docked-DAT containment is checked again during implementation cleanup, rather than inferred from signal graphs.

## Interface and data flow

Add external `parameter_definition.py`, embedded once as a module DAT in `inspector_model/base_commands`; no separate controller, registry, CHOP, poll or model cache. Reuse existing adapters and command boundary:

```text
View Details open / Refresh
  → Model.ParameterDefinition(context, slot, token)
  → shared command validates mapping identity/session/context
  → adapter resolves assigned native Par and reads a detached definition snapshot
  → view retains one scalar snapshot and renders its fixed section

Values / Definition click
  → Model.OpenNativeEditor(context, slot, token, kind)
  → fresh target resolution / identity and definition validation
  → native TD dialog API
```

Public readout returns `{target, native, actions, reason}` with immutable/detached scalar data. Read metadata on section open, explicit Refresh and before an editor action. Existing Value traffic updates the normal live field; it does not reread all native metadata or invalidate the snapshot on every CC. Native definition edits are reflected on Refresh/reopen; immediate live definition-change observation is not promised in this slice.

Readout is available for valid inactive/disconnected saved mappings. An external dialog cannot use a stale selection/session token; refresh and retry rather than silently targeting a replacement. Native editing has consequences outside Inspector's mapping guards: Definition entry requires LEARN off/control released; callback/deleted targets are disabled with reasons. Mere readout requires no MIDI connection and never offers/relearns a mapping. Do not disable the metadata readout solely because expression/export mode makes live Value unwritable.

Future metadata mutation needs a separate definition fingerprint covering owner ID, group identity, label/page/default/defaultMode, ranges/clamps, menu source/options and evaluation ownership. It must not reuse the Value-dependent fingerprint or treat a mapping Range patch as a native definition write. No metadata setter or automatic Style recreation in this slice.

## Operators and positions

All positions are network coordinates, separate from panel pixels. Reuse measured bounds and annotations; build idempotently with an external Python builder. Use build_network for independent structural operators where it preserves the existing external-builder workflow; source content/custom parameters/callback configuration remain on disk.

| Parent / operator | Type / family | Position / size | References / behavior |
| --- | --- | --- | --- |
| base_commands / parameter_definition | textDAT / DAT |(350,0),130×90 | Embedded Python module; no extension or per-frame execute |
| base_commands / annotate_commands | existing annotateCOMP |(−25,−25),530×175 | Expand internal annotation to contain third DAT; model root remains unchanged |
| each Details / native_values | containerCOMP / COMP |(1130,0),160×130 |24px panel button, assigned owner's Value dialog |
| each Details / native_definition | containerCOMP / COMP |(1330,0),160×130 |24px button, custom definition dialog |
| each Details / click_native_values | panelexecuteDAT / DAT |(1130,−210),130×90 | lselect; release-inside callback, no delay timer |
| each Details / click_native_definition | panelexecuteDAT / DAT |(1330,−210),130×90 | Same; parent.InspectorDemo Action |
| each Details / annotate_native | annotateCOMP / COMP |(1105,−235),410×425 |20px gap after existing annotation;25px sides/bottom,60px top |
| each container_info / container_native | containerCOMP / COMP |(rightmost existing nodeX+175,0),160×130 | Readout group within existing viewport; verify child bounds before placement |
| container_native / text_heading | textCOMP / COMP |(0,0),160×130 | Bold heading, fixed panel font size |
| container_native / label0..7, value0..7 | textCOMP / COMP | five-column grid,200px X /210px Y spacing,160×130 | Fixed row pool, wrapped/selectable long values; hidden rows cleared |

Native action text children and docked callbacks use the existing external builder's sizing/layout, with explicit post-build bounds. Panel settings verified through get_help: fit off, horizontal anchors, crop on, mousewheel, automatic vertical scrollbar, text selectonly, scaletofit never, panelunits fonts. Actions use the existing InspectorDemo shortcut; Model reference remains the view's Model OP parameter. Module access stays inside base_commands; no new cross-COMP absolute parameter expressions or signal wires/in-out operators.

## Build phases and verification

1. External module and pure command tests: definition formatting/type cases, bounded Menu preview, callback/missing target, stale selection/session/owner replacement, BIND range/master, EXPRESSION/EXPORT readout and independent native/mapping ranges. Mock dialog dispatch to verify exactly one correct API call per accepted click; no Value/Pulse/MIDI mutation.
2. Structural section additions in an isolated disconnected fixture. Load td-comp-architecture, td-dat-family and td-python-extension before creation. Reuse the four hosts, existing Details toggle/viewport and local section state; create parents before children.
3. Install embedded modules/references/callbacks with dependencies in place. Reinitialize only affected Inspector extensions, preserve actual controller MIDI process, mappings and Values. Do not rebuild/reinit the production controller.
4. Native verification: all supported numeric/Menu/Toggle/Pulse definitions, callback/empty/invalid states, stale actions, native edit then Refresh, Follow behavior and repeat-click dialog reuse. Use one explicit native dialog test at a time; do not open four test editors. Verify section402/base178/Mapping312, independent width/top-left and rapid close/reopen height stability in Fold/Popup. Compare catalog/registry/process/RX-TX effects with baseline, two subscriptions and zero business dispatch from readout/actions.
5. td-review-network + td-network-cleanup: scoped errors, callback dependencies, promoted methods, names/no numbered duplicates, measured positions/annotation containment. Run239-runtime baseline via `python3 -m unittest discover -q` in src/touchdesigner and118-Inspector baseline plus meaningful new tests; `git diff --check`.
6. Generic controller remains unchanged; generic UI exports embed the new module and clear all native snapshots/references/action state. Reload verifies empty state and two subscribers. Embed source Markdown and save/export through live TD after checks. No commit/push without user instruction.

Performance/full-rate cadence and resize issue#6 remain deferred. This slice does not declare full old-Inspector replacement acceptance.

## Later slices

**6b: direct metadata editing.** Label/default/native slider/clamp bounds first, followed by static Menu labels. Separate draft/preview/Apply; edits do not write live Value implicitly. Resolve group/shared/BIND/clone/menuSource ownership and reconcile controller definitions/re-LEARN consequences before committing. Preserve references and other mappings; no claim of atomicity across native setters and controller API calls.

**6c: Style migration prototype.** First lossless scalar Float/Int slice installed; STYLE_MIGRATION_REPORT.md records the isolated native test, identity/reference checks and compensation. Remaining physical acceptance is grouped in ACCEPTANCE_BATCH.md. Other styles/groups/shared ownership require further prototypes. Isolated test COMP first. Par.style is read-only. Account for group/page/order/name/defaults/menu/expression/export/bind references and controller IDs; preview affected references and provide a tested rollback contract before production support.

Local TD2025.33230 primary API docs consulted: Par Class Members, OP Class Methods (`openParameters`), UI Class Methods (`openCOMPEditor`). Exact panel parameters queried live with get_help. First-slice native dialog reuse/Follow behavior remains empirical work, not an inferred API guarantee.

Explicit context activation installed as slice6d: compact inactive-bank footer, one full-context SelectPlugin call, stale intent and controller guards; ACTIVATION_REPORT.md records isolated verification. Physical acceptance remains in the single pending batch.
