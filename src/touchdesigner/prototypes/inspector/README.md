# Compact real-data Inspector prototype

The latest live project is `inspector_editor_actions.4.toe`, saved through TD 2025.33230. The earlier `inspector_real_data.toe` checkpoint passed reload verification. Both retain the existing Roto controller and mappings. MIDI starts disconnected after reload; use the existing controller's Connect pulse. The compact UI is separate from the production table Inspector.

## Use

Only one compact Inspector is shown at a time, with its editor collapsed. Click **FOLD ↔ / POPUP ↔** to switch presentation in that same window; Popup opens only when a control is clicked. Opening the alternative Inspector closes the other compact view and its editor. The current checkpoint retains the user's Popup preference.

- **Device** occupies the first selector row; **Layout | Track** share the second. All three open native dropdown menus with the selected item checked. Selecting a menu item browses the real registry without changing hardware routing. Opening a menu does not cycle; stale selections after a context/session change are ignored.
- The **LIVE** indicator follows the controller's active context. After browsing it reads **BROWSE**; click it to return to the active context.
- Click a K/B row to inspect its real Label, Target, Range and Value. Label and Target remain read-only. Click **MAPPING ▸** to expand Range, compatible Mode and Input settings.
- Row markers show mapping health: **● Mapped**, **○ Pending**, **◇ Saved**, **! Invalid / Re-learn**, **· Unassigned**. The editor heading names the selected state. Inactive or disconnected saved mappings never claim a current hardware ACK; an invalid inactive target does not interrupt other rows.
- The Mapping section has its own 24px **× / ✓ Cancel / Apply** actions. It calls one existing `ConfigureControl` API after validating a fresh draft. Range/Mode semantics require hardware re-LEARN; an Input-only PUSH/TOGGLE adapter change retains the ACK. Native Menu/Toggle/Pulse use fixed compatible Mode/Range; Float/Int knobs permit validated Range edits. Python registration callbacks support compatible Toggle/Pulse modes. Cancel discards only the Mapping draft. Configuration uses its own commit and never writes Value.
- Value is a continuous live edit for a valid non-Pulse target on the active Device. User text edits call the existing `SetValue` API immediately, with no Value Apply/Cancel. Incomplete/invalid/out-of-range text never writes. Model/controller updates refresh the field when it is not being edited and do not echo a write. Inactive Devices are browse-only but their parameter values update live.
- **HW Learn** directs the user to the controller's LEARN button. Hardware LEARN changes the surface and displays `LEARN MODE ON`; this UI does not invent a hardware learning state.
- **↻ Ping** (top right) reoffers the selected control's existing mapping metadata through `Offerparameter`, including a registration whose hardware mapping was forgotten. Connect to PLUGIN, open hardware LEARN, select the matching knob/button and click Ping. `Awaiting hardware ACK` means sent, not learned. It does not change Value or fire Pulse actions.
- **⌫ Clear** (top right) removes only the selected registration through `RemoveControl`, preserving its target parameter and Value. Click once to show an inline question, then click **?** within eight seconds to confirm. Cancel, selecting another control, context/session/metadata changes or another action invalidate confirmation. Exit LEARN and release the control first. Offline removal uses the existing controller's pending unmap behavior on reconnect; hardware unmap has no ACK.
- **× Cancel / ✓ Apply** exist only inside the Mapping section. Ping/Clear remain top right; all actions are 24 × 24 using TD’s bundled Material Design Icons font (refresh, backspace-outline, close and check). Clear confirmation uses help-circle-outline from the same font. The Value status row uses the full width. Clear confirmation keeps its question visible during hover.

The Inspector is **240 × 390** at its default content size. Native resizing retains actual window dimensions without scaling field text. The Popup initially aligns beside the Inspector; its width and height resize independently, with **Size from Window** enabled and fixed aspect off. Default size is **240 × 178**; later selection does not resize/reposition an open Popup to match the main window. Editors use 12px side insets and 6px gaps between rows and adjacent controls; Mapping Cancel/Apply align with their own description. Mapping is collapsed by default, retaining the 178px editor. Expanded editor content is 312px: Fold expands inside the main list; Popup adds 134px to its current native height downward, preserving width, top-left and the upper fields. Collapsing removes only that section height; manual resizing becomes the new base size. The main Inspector stays unchanged. Its native window can still be resized manually, and a smaller viewport retains scrolling. `fit_editor_height.py` trims an existing Popup to its current content height once, without locking later manual resize. The main header stays pinned; both scroll areas use mouse-wheel scrolling or the native scrollbar. Changing a live Value or Mapping retains an already opened Popup for reuse; the native X or `DismissPopup()` closes it. No editor is opened automatically during startup or verification cleanup.

## Shared model

`live_model.py` projects the existing controller catalog and Layout registry. The controller remains authoritative. One shared model supplies both views, with a four-context LRU and bounded derived source/info/revision entries. Active data comes from `GetControlCatalog`; inactive data resolves saved targets and reads their current parameters. Neither browsing nor cache eviction changes mappings, values or the routing context.

Existing catalog DAT changes and exact parameter watchers schedule a coalesced frame-end sync. Watched owners/parameters follow subscribed contexts, including inactive Devices. There is no added permanent per-frame polling DAT. Equal data does not notify views; equal display text is not written. Closed Inspectors defer value text writes and catch up on reopen. A burst of 1,000 sync requests retains one pending run.

`ui.py` keeps selection, scroll, Mapping draft and last displayed text local to each view. Generation/context/slot/revision tokens reject stale Mapping commits and Value editing scopes after session or metadata changes. Hardware value traffic leaves metadata tokens valid. Only user text callbacks dispatch Value; programmatic Text COMP changes never do. Equal Value writes are no-ops. Weak subscriptions and callback-specific unsubscribe prevent an old extension's destruction from unregistering its replacement.

`commands.py`, embedded in `base_commands/InspectorCommands`, owns shared health/capability rules and guarded Value/Ping/Clear execution. The promoted command extension resolves the current model on each call, including after reload. Touch/LEARN health changes update action availability without expiring a Value draft; mapping, input adapter and native definition changes expire it. Readonly, unsupported evaluation modes and invalid clamp ranges block Value/Ping while permitting guarded registration cleanup.

Native definition snapshots have a separate four-context LRU containing scalar metadata, not retained Par handles. They refresh on editor open, mode events, changed catalog metadata and before commands; session/controller detachment clears the cache. Definition changes without native events are rechecked on open/action. BIND master owners join exact watchers. Equal editor capability snapshots avoid repeated control writes; no RX/TX counter watcher or permanent frame polling is added.

`model.py` remains the foundation and original mock catalog for isolated synthetic tests. Its eight-context fixtures are separate from real controller data; live mode rejects fixture updates, snapshots, resets and restores. Historical synthetic stress reports do not establish performance for every real controller workload.

## Exports and builders

Load `inspector_model.tox` first, then either view export. Set the model's **Data → Controller** OP parameter to an existing Roto controller. The generic exports have no controller reference, saved target IDs/destinations or user mappings. Python is embedded; no external source file is read at runtime. Reconnecting the hardware remains the production controller's responsibility.

`build_model.py` and `build.py` create the original demo layers. `build_live.py` attaches them to an existing controller and installs the live adapter without rebinding or restarting the production extension. Execute builders in a separate namespace when using `exec`:

```python
from pathlib import Path
namespace = dict(globals())
exec(Path(project.folder + '/prototypes/inspector/build_live.py').read_text(), namespace)
```

`export_live.py` temporarily detaches only the UI read adapter, clears exported draft/selector data, saves all three components through live TD and restores the adapter. It never disconnects production MIDI or writes target parameters. `verify_live_exports.py` reloads those generic UI exports and restores the link, verifying that the production session/catalog remains unchanged. Never edit `.toe` or `.tox` binaries directly. `inspector_demo.tox` is the older combined design.

## Verification

```sh
python3 -m unittest discover -q
python3 -m unittest discover -s prototypes/inspector -p 'test_*.py' -q
```

230 runtime tests and 68 Inspector model/editor/dropdown tests pass. Native checks and the user's physical acceptance cover real K2 updates and hardware Learn alerts. Additional checks cover Value Apply, inactive Power updates through a native watcher, independent browsing, a single main window, saved project reload and generic exports. A disconnected native fixture verifies Ping protocol output without Value/Pulse dispatch, Clear's second-click confirmation and removal isolation; physical Ping/re-LEARN acceptance remains pending. Milestone 1 fixtures additionally verify native touch/mode callbacks, invalid inactive targets, six-context cache bounds, zero idle text writes and generic command reload. Popup Mapping expands downward with width/top-left preserved; native resize rendering is still under investigation (see MAPPING_REPORT.md). Milestone 2 additionally verifies configuration failures, ACK/re-LEARN distinctions, independent Mapping drafts, callback factory targets, direct native dropdown selection, independent width/height mouse resizing, Popup wheel scrolling and continuous Value callbacks without deferred write echoes. See `LIVE_REPORT.md`, `MAPPING_REPORT.md`, `HEALTH_REPORT.md`, `live_verification.json`, `live_export_reload.json` and `editor_actions_verification.json`.

`shared_verify.py` and `run_shared_stress.py` require the mock model and reject live mode before synthetic mutation. The earlier mock evidence remains in `SHARED_MODEL_REPORT.md` and `shared_*` files; `STRESS_REPORT.md` / `stress_*` describe the preceding architecture. `run_stress.py` is a legacy harness and rejects shared-model views.
