# Compact real-data Inspector prototype

The latest live project is `inspector_editor_actions.2.toe`, saved through TD 2025.33230. The earlier `inspector_real_data.toe` checkpoint passed reload verification. Both retain the existing Roto controller and mappings. MIDI starts disconnected after reload; use the existing controller's Connect pulse. The compact UI is separate from the production table Inspector.

## Use

Only one compact Inspector is shown at a time, with its editor collapsed. Click **FOLD ↔ / POPUP ↔** to switch presentation in that same window; Popup opens only when a control is clicked. Opening the alternative Inspector closes the other compact view and its editor. The current checkpoint retains the user's Popup preference.

- Layout / Track / Device chips browse the real registry without changing hardware routing.
- The **LIVE** indicator follows the controller's active context. After browsing it reads **BROWSE**; click it to return to the active context.
- Click a K/B row to inspect its real Label, Target, Range and Value. Mapping metadata is read-only in this prototype.
- Value is editable for a valid non-Pulse target on the active Device. Apply calls the existing controller `SetValue` API; Cancel discards the local draft. Inactive Devices are browse-only but their parameter values update live.
- **HW Learn** directs the user to the controller's LEARN button. Hardware LEARN changes the surface and displays `LEARN MODE ON`; this UI does not invent a hardware learning state.
- **↻ Ping** (top right) reoffers the selected control's existing mapping metadata through `Offerparameter`, including a registration whose hardware mapping was forgotten. Connect to PLUGIN, open hardware LEARN, select the matching knob/button and click Ping. `Awaiting hardware ACK` means sent, not learned. It does not change Value or fire Pulse actions.
- **⌫ Clear** (top right) removes only the selected registration through `RemoveControl`, preserving its target parameter and Value. Click once to show an inline question, then click **?** within eight seconds to confirm. Cancel, selecting another control, context/session/metadata changes or another action invalidate confirmation. Exit LEARN and release the control first. Offline removal uses the existing controller's pending unmap behavior on reconnect; hardware unmap has no ACK.
- **× Cancel / ✓ Apply** share the status/`Value edits live target` row at its right edge. All four buttons are 24 × 24; hovering shows their names/actions in the status line. Clear confirmation keeps its question visible during hover. Both Fold and Popup use the same controls, without extra dialogs or a larger editor.

The Inspector is **240 × 390** at its default content size. Native resizing retains actual window dimensions without scaling field text. The Popup matches the Inspector width and aligns beside it; default size is **240 × 178**. Editors use 12px side insets and 6px gaps between rows and adjacent controls; Cancel/Apply align with the description and the extra footer row is removed. The header stays pinned; the content uses mouse-wheel scrolling or the native scrollbar. Apply/Cancel retains an already opened Popup for reuse; the native X or `DismissPopup()` closes it. No editor is opened automatically during startup or verification cleanup.

## Shared model

`live_model.py` projects the existing controller catalog and Layout registry. The controller remains authoritative. One shared model supplies both views, with a four-context LRU and bounded derived source/info/revision entries. Active data comes from `GetControlCatalog`; inactive data resolves saved targets and reads their current parameters. Neither browsing nor cache eviction changes mappings, values or the routing context.

Existing catalog DAT changes and exact parameter watchers schedule a coalesced frame-end sync. Watched owners/parameters follow subscribed contexts, including inactive Devices. There is no added permanent per-frame polling DAT. Equal data does not notify views; equal display text is not written. Closed Inspectors defer value text writes and catch up on reopen. A burst of 1,000 sync requests retains one pending run.

`ui.py` keeps selection, scroll, draft and last displayed text local to each view. Generation/context/slot/revision tokens reject stale Apply requests after session or metadata changes. Hardware value traffic leaves metadata draft tokens valid. Applying an unchanged snapshot Value preserves the latest live value. Weak subscriptions and callback-specific unsubscribe prevent an old extension's destruction from unregistering its replacement.

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

230 runtime tests and 33 Inspector model/editor tests pass. Native checks and the user's physical acceptance cover real K2 updates and hardware Learn alerts. Additional checks cover Value Apply, inactive Power updates through a native watcher, independent browsing, a single main window, saved project reload and generic exports. A disconnected native fixture verifies Ping protocol output without Value/Pulse dispatch, Clear's second-click confirmation and removal isolation; physical Ping/re-LEARN acceptance remains pending. See `LIVE_REPORT.md`, `live_verification.json`, `live_performance.json`, `live_export_reload.json` and `editor_actions_verification.json`.

`shared_verify.py` and `run_shared_stress.py` require the mock model and reject live mode before synthetic mutation. The earlier mock evidence remains in `SHARED_MODEL_REPORT.md` and `shared_*` files; `STRESS_REPORT.md` / `stress_*` describe the preceding architecture. `run_stress.py` is a legacy harness and rejects shared-model views.
