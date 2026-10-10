# Inspector diagnostics and parity tools

2026-10-08, live TD 2025.33230. Milestone 4 is installed in Fold and Popup. The existing compact rows, editor hosts and native windows are reused. This completes the software parity slice; replacement acceptance remains Milestone 5.

## Behavior

The footer filters rows by COMP, Python callback or all sixteen slots. It never changes controller routing. A 24px native MDI information button opens a readonly Details section inside the existing editor, exclusive with Mapping and Target picker. Details separates view-following from controller Follow and displays stable IDs, full targets, Style/Mode, health/error, LOCK, selected/routing context and gates. RX/TX/rejected counters are snapshots on open/Refresh, with no new counter watcher.

Reveal navigates the existing Network Editor pane. It requires a fresh native target and controller Follow OFF; Follow is never switched automatically. Repair opens the existing picker and requires a separate explicit Assign. Neither adds an editor window.

Clear Device confirms the full Layout / Track / Device and the count of every active registration, independent of display filter. It uses the existing `RemoveAllControls` scope: current active registrations, preserving target Values, other Devices and inactive hardware-page libraries. It does not erase a Device's historical page library. Confirmation is single-use, expires after eight seconds, and revalidates session, context, registration identity/configuration and native definitions. Live Value traffic remains valid. LEARN, touch and inactive browsing block removal. An interrupted removal reports exact removed/remaining IDs at the command boundary and counts/error in the UI; no atomic rollback is claimed.

## Evidence

- 230 runtime tests and 98 Inspector tests pass. The six new pure tests cover filters, confirmation expiry/reuse, context isolation, live-value stability, session/config invalidation, LEARN/touch/empty guards and partial failure.
- [Native fixture](parity_verification.json) verifies COMP/callback filters, stale menu callbacks, Details reuse/exclusive sections, snapshot counters, native Follow/LOCK state, Reveal navigation/guard, Repair reuse, filtered Clear scope, cancel/repeated confirmation, changed configuration, LEARN/touch/inactive guards and an injected interruption. Callback rendering/removal dispatches no business event. Production catalog, registry, routing and MIDI session remain unchanged.
- Fresh `build.py` probe passes with the same shared model instance and two subscriptions. Identical parity source is no longer rewritten during a build; this prevents needless DAT import invalidation from closing the model held by existing views.
- Generic export/reload embeds parity source in commands and views and clears filters, confirmation requests, Details snapshots/text, drafts, picker state/cache and controller references. The production controller remains connected.
- Network cleanup measures all four existing editor hosts (46 direct functional nodes each), six reused picker rows, non-overlapping groups and no unexpected signal connections. Prototype roots report zero errors. Static panel captures confirm Details uses the existing editor; this is not an OS resize acceptance test.

## Bounded Python workload

[parity_performance.json](parity_performance.json) records 100 samples per case in the current project:

| Case | p95 | Maximum |
| --- | ---: | ---: |
| Idle sync/flush | 0.280 ms | 0.844 ms |
| Details open, equal-data sync/flush | 0.284 ms | 0.699 ms |
| Explicit Details Refresh | 0.365 ms | 0.514 ms |
| Details close/open pair in Fold | 1.045 ms | 1.197 ms |

Operator count stays constant; two subscriptions, zero discovery jobs and zero additional idle row-text writes. This is a bounded Python micro-workload, not a matched render baseline, hardware transport benchmark or long-duration memory soak. Whole-process/render stress and physical configuration re-LEARN remain Milestone 5 gates. Native resize deformation remains deferred in [issue #6](https://github.com/joshuahhn/roto_control/issues/6).

Source: [parity.py](parity.py), [commands.py](commands.py), [live_model.py](live_model.py), [ui.py](ui.py), [build_parity.py](build_parity.py), [verify_parity.py](verify_parity.py), [profile_parity.py](profile_parity.py).

## Readout and physical-tab investigation

Details typography now separates bold group headings, muted labels and larger main values. Long identity/path fields occupy full-width technical rows in the existing scrollable readout; equal snapshots skip field writes. Current bounded Python samples in parity_performance.json include the grouped readout and wheel callback; the table above reflects this final run. Thirty staged native item selections pass; physical intermittent item selection remains unresolved. The user-observed FUNC/SEL names match the Track/Device registry, as recorded in [TAB_LAYOUT_TEST.md](TAB_LAYOUT_TEST.md). No registry migration or dedicated Custom Device has been added.

Header context menus now use bounded panels inside the existing Inspector window, after the floating-menu timing trial failed physical acceptance. Eight reused native rows, outside-click/Escape callbacks, paging and wheel callback checks pass, with no main-window resize or resource menu Window. Physical input acceptance remains separate; see TAB_LAYOUT_TEST.md.

The user subsequently confirmed physical first-click selection works for all three in-window headers. inline_selector_acceptance.json records five accepted callbacks and unchanged hardware routing; recorder saved/stopped without errors or hook conflicts. Physical wheel/OS Escape and resize issue #6 remain separate.
