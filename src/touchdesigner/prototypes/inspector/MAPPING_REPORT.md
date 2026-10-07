# Inspector Milestone 2 verification

2026-10-08 · TD 2025.33230 · checkpoint `inspector_editor_actions.7.toe`.

Device is the first selector row; Layout | Track share the second. All three use native dropdowns with checked selections, rather than cycling taps. Native mouse selection of fractal_pop enters browse mode while hardware routing remains on pixelSortV3. Duplicate display names resolve to stable IDs; stale menu choices after session/context changes or registry removal are ignored.

## Mapping and live Value

Both editors have one reusable collapsible Mapping section, with its own draft/token and 24px Cancel/Apply. Range, compatible Mode and PUSH/TOGGLE input declaration submit through one existing ConfigureControl call. Native Menu/Toggle/Pulse keep compatible fixed Mode/Range; Float/Int knobs support Range edits. Python registration callbacks support compatible Toggle/Pulse modes. A single changed configuration refreshes the Value field without writing it. The controller owns validation, ACK and re-LEARN semantics.

Value has no visible Cancel/Apply controls. User text callbacks write continuously through SetValue; controller/model-driven field changes never dispatch writes. Incomplete/nonfinite/out-of-range text, stale selection/definition/session, LEARN and touched targets cannot write. Outside active typing the field follows the current target Value. The legacy Apply/Cancel handlers and hidden nodes remain for compatibility; they are not user-facing actions.

## Native window behavior

Popup width and height can be resized separately. The viewport uses Size from Window with fixed aspect off; the former fixed-size viewport constrained native resizing to its aspect. Real mouse drags verify 334x250 -> 374x250 horizontally, then 374x250 -> 374x280 vertically. The temporary size change is restored. Selecting another control does not resize/reposition an open Popup to follow the main Inspector.

Mapping is collapsed at 178px content height, expanded at 312px. Fold expands within the scrolling main list. Following the user’s collapsed/expanded screenshots, Popup now adds 134px downward when Mapping opens and removes that delta when it closes. Width, native top-left, upper fields and the main Inspector stay fixed. Manual expanded resizing becomes the new base; repeated layout updates do not reopen/grow the window. Closing through the OS while expanded retains a pending collapsed size for the next open. Reopening uses the viewport’s retained content dimensions; TD’s closed native cache can include a 32px title bar after reload, which previously accumulated in opening height. Native reopen checks now retain 334x318. Native tests verify 286x214 -> 286x348 with the same top-left while the main Inspector is independently resized. Size from Window and scrolling remain available for manual resizing. Ping/Clear and Mapping Cancel/Apply use the same bundled Material Design Icons font, including Clear’s confirmation icon.

## Evidence

- **230 runtime + 68 Inspector tests** pass, including configuration schemas/guards, independent drafts, dropdown selection fences, independent window sizing and live Value scopes.
- `verify_mapping.py` uses isolated disconnected native controllers: invalid Range preserves configuration; changed Range sends one unmap without Value/Pulse writes; input-only change retains ACK; Int/Menu/Toggle/Pulse rules and callback reconstruction factory behavior pass; stale/LEARN/touch guards pass. Fixture configuration changes never reach production.
- `verify_live_value.py` runs in separate TD turns: a user callback writes immediately once, equal values deduplicate, invalid values do not write, software Value updates follow the field, and deferred Text COMP/model updates do not echo. Original production catalog/registry/session are preserved.
- Existing Ping/Clear verification retains protocol/confirmation/isolation checks with the hidden Value actions and wider Value status row. Generic exports reload embedded Mapping state and Value callbacks with no controller, target destinations or Mapping draft data, and exactly two subscriptions.
- Measured cleanup covers 30 functional nodes per view root, 35 per editor content and 20 per Mapping section. Native callback migration avoids duplicate docked DATs. Groups have containment/gaps and functional nodes do not overlap. Accordion reuse retains operator counts and two subscriptions; no frame polling is added.

Artifacts: `mapping_verification.json`, `live_value_verification.json`, `dropdown_verification.json`, `window_sizes_verification.json`, `mapping_network.json`, `mapping_performance.json`, `live_export_reload.json`.

The installed-model read-only probe has approximately 0.190ms p95 over 100 sync/dispatch calls, with zero additional idle text writes. Twenty-five accordion cycles retain operator counts. This excludes native rendering, physical MIDI and whole-process memory/long-duration soak acceptance; it is not a guaranteed frame-rate result.

## Remaining scope

Target assignment/retargeting, typed Menu/Toggle widgets, filters, scoped Clear All, diagnostics and native parameter definition editing remain later milestones. The old Inspector remains necessary. Physical Range re-LEARN, PUSH/TOGGLE adapter acceptance and forgotten-map Ping recovery remain pending. Current native fixtures prove software/API behavior, not physical hardware persistence.

## Resize rendering investigation

A real horizontal native drag reproduced a persistent white strip at the bottom of the Popup in the macOS window capture. Toggling root display and forcing viewport/window cooks did not remove it; those probes are reverted. The direct TD panel capture renders the full dark background correctly. Native UI automation then timed out, preventing a verified post-resize visual fix. Root cause and transient resize flicker remain unresolved; no per-frame forced render, resize polling or window-reopen workaround was installed. Size assertions and unit tests do not establish that this native rendering issue is fixed.

## Remove spare window height

The user reported leftover empty space. The current manually enlarged 334x318 Popup held only 178px of content. `fit_editor_height.py` trims its height once to 178px, preserving width/top-left and the main Inspector. Mapping expands to exactly 312px and collapses back to 178px, with viewport height matching content in both states. Generic exports retain the compact height. Free manual resize remains available; no runtime polling or controller change is added. Native geometry/catalog checks pass. This does not resolve the separately recorded native repaint issue.
