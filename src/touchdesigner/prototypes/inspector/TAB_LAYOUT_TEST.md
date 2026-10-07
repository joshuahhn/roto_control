# Physical tab and selector test

The physical FUNC/SEL recognition capture now matches the existing Track and Device registry. The remaining click question concerns selecting an item inside an already open menu, not opening the header dropdown. No special Custom Device or registry migration follows from these observations.

In the manufacturer's PLUGIN-mode manual, FUNC selects a Track, while held SEL selects a Device within that Track. The TD saved Layout is an outer mapping set selected in TD. Current registry hierarchy is Layout → Track → Device; placing Device first in the compact header does not reverse that hierarchy. MIX and MIDI give FUNC different functions. Source: [manufacturer manual, PLUGIN controls](https://static1.squarespace.com/static/61516d07b4fcfe7439d39b38/t/68006d12f646de52f6f1588b/1744858401479/ROTO-UserManual-V1-1-4-April2025.pdf#page=7), [TD registry semantics](../../docs/functions/layouts.md).

## Recorder

[tab_layout_probe.py](tab_layout_probe.py) is a temporary diagnostic file, not production runtime. It wraps the existing receiver and host sender, forwarding their original arguments, return values and exceptions. It opens no new MIDI port, sends no synthetic message and writes no registration, target Value or routing preference. It records:

- General Track, Plugin Device, MIX and normal-page messages, preserving unknown raw packets.
- Routing/selected IDs and readable Track/Device lists, plus current slot target identities.
- Inspector header callback calls and native menu opening, focus loss and close.
- Native list press/release coordinates, click classification, double-click dispatch and item callback acceptance. These hooks preserve native return values and are removed on Stop.
- Human screen observations through explicit markers. A packet alone never proves which screen was visible.

Queued TX is host queue acceptance, not proof of bytes delivered or hardware success. Continuous CC/value-display messages are excluded. Memory is bounded to 512 events; list snapshots are capped at 64 entries with full counts. There is no timer/per-frame scan or per-packet disk write. Save/Mark/Stop writes the JSON report. Stop restores original handlers without overwriting a later replacement hook. Starting a second recorder is rejected.

Run this in a separate TD Python namespace:

```python
from pathlib import Path
probe = dict(globals())
exec(Path(project.folder + '/prototypes/inspector/tab_layout_probe.py').read_text(), probe)
controller = op('/roto_control_python/roto_python')
views = tuple(op('/' + name).ext.InspectorView for name in ('inspector_below', 'inspector_popup'))
probe['Start'](controller, project.folder + '/prototypes/inspector/tab_layout_capture.json',
               views=views, menu=op.TDResources.op('popMenu').ext.PopMenuExt)
```

Use the already connected controller. In PLUGIN mode, press FUNC and note the names shown; then hold SEL and note the Device names. Select the already active Device and compare FUNC again. Avoid LEARN/Clear during this recognition test. Try each Inspector header once; if it needs another click, record which button, whether a menu was already open, and which window previously had focus. These observations can be supplied in chat; the agent can add markers and stop/save the recorder.

```python
probe['Mark'](controller, 'FUNC screen: T, TRACK')  # Replace with actual observation.
probe['Save'](controller)
probe['Stop'](controller)
```

No capture survives a TD restart or extension reload unless explicitly saved first. The recorder is never embedded in generic exports. Stop it before rebuilding/reinitializing extensions.

## Physical recognition findings

User observed FUNC: **T, TRACK**; held SEL: **pixelSortV3, fractal_pop**; release: **pixelSortV3, T**. These match the captured Track and Device names. The LCD's T is the Track name; the outer TD Layout happens to also be named T. Inspector selectors browse saved contexts without selecting hardware routing. During this capture, Inspector browsing changed to Custom while hardware routing stayed T / T / pixelSortV3. The visual Device-first header does not change Layout → Track → Device ownership.

[tab_layout_capture.json](tab_layout_capture.json) contains 59 events, zero drops/logging errors, and unchanged routing. Twelve received CONTROL_MAPPED messages and twelve queued LEARN_PARAM replies come from the original runtime. No Track/Device selection packet was received in this capture; human observations establish the displayed screen names. Five delivered header callbacks opened menus. An immediate Close within winOpen is the native menu's normal internal cleanup, not evidence of a canceled first click. Recorder stopped and every hook restored. See [derived findings](tab_layout_findings.json).

## Software checks and open item-selection question

The user clarified that all three menus sometimes need two clicks on an **item inside an already open menu**. Earlier 30/30 header-opening results test a different step and do not resolve this symptom. The mouse-release header trial was withdrawn after this clarification; header callbacks retain their original press behavior.

[verify_selector_items.py](verify_selector_items.py) uses native list mouse-down, waits three frames, then releases on an existing alternative. All 30/30 selections passed, across Device/Layout/Track, with routing/session preserved. A single-call virtual leftClick failed to deliver the equivalent list callback and was replaced by staged gestures; this fixture limitation is not a reproduction of the physical two-click bug. [selector_item_verification.json](selector_item_verification.json) records the staged results. The temporary recorder now distinguishes native list gesture delivery, double-click dispatch and callback acceptance. Physical item-selection cause/fix remains unresolved; no speculative item/focus workaround is installed.

The Info readout now has bold 12px group headings, muted 9px labels and 11px main values. Long paths/IDs use full-width lines in the scrollable Technical group. Existing section/window sizes stay in use. Equal detail snapshots skip all field writes; native parity fixtures still pass. Pure recorder checks cover packet families/filtering, bounded memory/logging failure, handler arguments/results/restoration and hook conflicts. Physical recognition interpretation comes from the user-observed screens and matching registry capture, not from virtual clicks.

## Physical item trace and timing trial

The user reproduced the failure: first item click did nothing and the menu stayed open. [selector_item_capture.json](selector_item_capture.json) has 50 events, zero drops/errors and restored hooks. The first Device and Layout interactions show an end event with endrow=-1 followed by a new start in the same frame; Track also starts with an end before the next start. No first-item Click/Select callback occurs. Later gestures deliver Click/Select and accepted=True. No double-click or LostFocus event was recorded. This rules out callback rejection and double-click classification in this capture; it does not prove the operating-system cause.

[replay_selector_item_capture.py](replay_selector_item_capture.py) replays the first Device's native Lister callback ordering: zero accepted callbacks after the first gesture, one after the subsequent gesture. Routing/session stay intact. It reproduces the missing selection at the native callback seam, not the macOS input dispatcher. [selector_item_replay.json](selector_item_replay.json) therefore explicitly leaves physical timing-fix verification false.

The superseded timing trial opened header dropdowns only on mouse release inside the button, and deferred opening by one TD frame so the original gesture can complete before native window focus transfers. A queued open is canceled if the view closes/is destroyed, context/model/session/menu generation changes, or another queued open already ran. No new nodes, continuous polling or native resource edits. context_callbacks.py is the authoritative generator embedded into the existing header callback DATs by build_mapping.py. Pure cancellation tests and native held/release/drag-out plus 30 item selections pass. The item fixture now stages both header and item press/release, waits for the native menu to open, and clears prior virtual interactions between samples; single-call header clicks delivered no list events in some rapid virtual samples and are not used as physical-selection evidence. Physical retesting remains necessary. A new temporary capture uses selector_item_release_capture.json; stop/save it before any rebuild/reload.

## Current in-window dropdown

The user rejected the timing trial: first item click still did nothing and the menu stayed open. selector_item_release_capture.json saved/stopped with 188 events, no drops/errors/conflicts. Device initially received a complete gesture, but later Layout/Track and reopened menus again received release-before-press; all actual selection callbacks were accepted. Timing alone did not remove the failure. The user explicitly requested dropdowns stay inside the Inspector window.

Header menus now use container_context_menu under each existing Inspector root. They open below the header, overlay content without resizing or opening another Window, and use eight reused native container rows, fixed 24px height, 11px text and native MDI check/arrow icons. Readonly labels have no unused Text callbacks. Small lists have no spare footer; longer lists have wheel/paging with a count. capacity_for fits row/footer height below the actual anchored button position. No registry, target, mapping or hardware-routing writes were added. The previous deferred-open timer is removed.

Click outside, Escape, focus loss, other actions, context changes, switching views and Disconnect dismiss the panel. Existing ID/context/model/menu-generation validation still rejects stale selections and duplicate labels remain disambiguated. Value traffic does not invalidate a menu. Generic exports clear open state, labels, check marks, count and keyboard FIFO; the keyboard listener is scoped to an open focused menu and ESC keys only.

230 runtime / 98 Inspector tests pass. Native checks cover 30 first-row-press selections, release-inside/drag-out header behavior, same panel root/no resource menu Window, outside-click/Escape callbacks, 17-item paging and the wheel Panel Execute callback, stale selection, Disconnect, unchanged main dimensions, bounded operator count and unchanged catalog/routing/session. A fresh builder probe passes and is removed, preserving the shared model object and two subscriptions. Measured cleanup has no overlaps and verifies containment. See inline_menu_verification.json, selector_item_verification.json, context_release_verification.json and context_menu_network.json.

Virtual interactMouse(wheel=...) did not deliver a wheel panel event in this TD build, so the wheel fixture sets the native panel wheel value and verifies its real Panel Execute callback. That verifies callback behavior, not physical wheel delivery. Physical first-click, wheel and OS Escape acceptance remain pending; no native input-system fix is claimed. A temporary inline_selector_capture.json recorder, if active, captures header/item press calls and callback acceptance. Stop/save it before rebuilding/reloading.

## Physical first-click acceptance

User confirms Device, Layout and Track items all select with one click in the same-window dropdown. inline_selector_capture.json saved/stopped: 24 events, five delivered item presses, five accepted selection callbacks, all three header names observed, one unchanged hardware-routing context, zero drops/logging errors/restoration conflicts. See inline_selector_acceptance.json. Temporary hooks fully removed; production MIDI remains connected and two subscriptions remain. This accepts the reported first-item-click bug and same-window layout. Physical wheel/OS Escape and deferred native resize issue #6 are separate gates. The native callback replay above was recorded before this refactor; its script targets historical floating-menu checkpoints, not the current inline UI.
