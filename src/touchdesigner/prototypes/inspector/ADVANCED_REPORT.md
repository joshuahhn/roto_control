# Native parameter readout and editor access

2026-10-08, TD2025.33230. Milestone6a is installed in the existing Fold/Popup editors. The information section now starts with native parameter definitions and exposes TD-owned Values/Definition dialogs. Controller runtime, mappings, Values, routing and the real MIDI process are retained.

## Behavior

Native readout separates Label/name/Page/Style, default constant and default evaluation mode/expression/bind expression, slider range, clamp limits/toggles, evaluation ownership/read-only state and Bind master/inherited range. Menu options use an eight-item preview/count; long fields wrap and remain selectable. Native Style, mapping Mode, Mapping Range and numeric input Float/Int preference remain distinct.

Reuse the existing224px Details section delta: base178px, Details402px, Mapping312px. Metadata size changes the internal scroll extent, never Window height. Five24px MDI footer actions align bottom-right (12px right inset/6px gaps) and are Refresh / Reveal / Repair / Values / Definition, with hover labels/reasons. Native metadata is read on open/Refresh/actions, not every Value update. Native edits made in TD appear after Refresh/reopen. Callback/empty/deleted targets give explicit reasons. LEARN/touch guard native editor actions; fresh mapping/session/owner identity is revalidated before dispatch. Reveal now works with Follow on: it shows the target COMP node in its parent network, clears destination child selection while Follow is enabled, and centers the node at a readable 1:1 zoom. It leaves Follow and controller routing unchanged.

Values calls `owner.openParameters()`; Definition calls `ui.openCOMPEditor(owner)` for custom parameters. These open only on an explicit click and target the assigned owner even for a bound alias. No automatic Network Editor navigation or native page change is added. The native dialogs allow normal TD editing; direct Inspector metadata setters and automated Style migration remain future slices.

## Verification

- 239 runtime tests and127 Inspector tests pass. Eight new metadata/command tests cover detached scalar snapshots, distinct ranges/default behavior, bounded Menu preview, Bind chains, expression/export/default source readout, callback/missing/built-in reasons, exact dialog dispatch, LEARN/touch, resolver race and mapping/session/owner-token invalidation. One additional Popup regression covers stale panel-root height.
- `advanced_verification.json`: isolated native Float/Int/Menu/Toggle/Pulse/Bind/Expression fixture, both presentations, default edit then Refresh, Value traffic without metadata reads, wheel scrolling, guards and callback/empty states. Fixed402px section/178px viewport/24px icons. Fixture metadata actions fire no Pulse/callback/MIDI; controlled fixture Value edits are isolated from hardware motor recipients. Production catalog/registry/routing/process/session exact, two subscribers, no errors; fixture removed.
- Native Values and Definition each dispatched twice to the same fixture owner. CUA shows the correct TD dialog; one close returns directly to Edit mapping. Both tests keep Follow on and preserve routing/pane owner. No native dialogs remain open after verification. This is observed same-owner reuse, not a claim of multiple-owner native dialog behavior.
- `advanced_builder_verification.json`: fresh external UI builder displays native metadata, retains fixed section, opens no test Windows and restores two subscribers after cleanup.
- `advanced_network.json`: measured containment/no overlaps in four reused editor hosts, bounded eight native readout fields, five footer actions and one shared native module. There are no new signal wires or per-frame observers.

Source: parameter_definition.py, commands.py, live_model.py, ui.py, build_commands.py and build_parity.py. `install_advanced.py` changes only Inspector modules/UI, without controller reinit/rebind/reconnect. Pure snapshot state lives locally on each view; it is not persisted. Generic reload must embed the module, clear native labels/values/action state and verify empty geometry/targets, as asserted in verify_live_exports.py.

Generic UI export/reload now passes those assertions with production process/catalog retained. Its first attempt caught existing Menu/Mapping opener callbacks reset to press handlers by the fields builder; the old release-inside checks are unchanged. build_live now runs build_context_menu after all field/section builders. The corrected full upgrade and subsequent generic reload both pass the accepted inline header/editor callback gates. No new menu Window or timing workaround.

## Programmatic expansion mismatch

Native screenshot exposed Window height402px while its Size From Window panel root stayed178px; upper controls stretched and Details was clipped below the viewport. Section-height transitions now write the matching panel-root height alongside Opening Height. This affects only explicit programmatic section deltas, using the existing intended-geometry/cancellable settlement path. No new resize loop/Open pulse; manual width/base height remains user-owned. Native fixture confirms root/window402px and content y0; CUA confirms the section appears with fixed typography. Manual drag deformation remains deferred in issue#6.

One initial verification harness access used COMP.adapter rather than its extension adapter; fixed and failed fixture cleaned before the passing run. A readout inspection accidentally included docked callback DATs; corrected to textCOMP-only. No production writes occurred in either probe. The optional CUA window-inventory method is unavailable here, so native reuse evidence uses two API opens followed by one AX close returning to Inspector.

Performance work, full-rate cadence and deferred resize issue#6 remain outside this slice. No new30-minute soak or full process restart is claimed. No commit/push.

### Reveal correction (2026-10-08)

Live reproduction on checkpoint36: Reveal disabled under Follow; direct dispatch returns the Follow guard and pane stays at /inspector_model. Removed that UI/adapter guard, clear destination child selection before navigation when Follow is enabled, reuse an open Network Editor (fallback if current pane is not one), and home without zoom. Four regression tests fail before the fix and pass afterward; totals239 runtime/131 Inspector tests. Native Popup crosshair click enters /roto_control_python/pixelSortV3 with Follow on and unchanged catalog/registry/MIDI process/session, two subscribers (reveal_verification.json). Updating embedded sources reloads Inspector extensions; K2 Details is explicitly reopened after settlement. Production controller is not reinitialized.
