# Layouts, Tracks and Devices

A saved Layout contains multiple selectable Track groups. Each Track contains 1..127 Devices (the protocol calls them Plugins). Each Device owns independent target identities and a learned control-page library, with up to eight pages of 8 knobs and 8 buttons per page. Layout is a TD saved configuration; Device is the controlled tool COMP. Tracks are explicitly managed groups, not automatically inferred from COMP parents.

The Layout custom page manages the saved mapping set and Track groups. The separate Device page manages the active COMP/Device, its Focus link and display name. Active Layout selects the saved configuration; New / rename Layout is its name draft. Active Track group (FUNC) selects a group, and Active Device (SEL) selects one tool inside it. New Track / Device actions create and select empty records; Focus linking does not automatically map parameters. Delete actions open a native popup with Cancel; no permanent confirmation buttons. Last Layout/Track/Device deletion is rejected. Popup choices expire on any of the three context IDs or extension reload. Save the containing TD project to persist changes.

## Tagged COMP workflow

Add the `roto_device` OP tag to an external COMP under the controller's parent scope. Within about one second while idle, it gets an independent Device in Active Layout / Active Track, with a Focus link and COMP-derived name. Existing links anywhere in Active Layout are reused; repeated scans, rename and reload do not duplicate Devices. Layout names stay independent: selecting pixelSortV3 changes Device, not the Layout named T. Removing a tag stops automatic discovery and preserves the saved Device/mappings; use Delete Device for explicit removal.

With Follow selected COMP on, selecting the tagged COMP activates its Device. Adding a tag to an already selected COMP also re-evaluates Follow. Startup/reload still establishes a selection baseline. Registration waits during LOCK, LEARN, touch, pending routing, backlog or transport opening; Python registration does not auto-create Devices. Tags removed before idle are not registered. Controller implementation COMPs and utility/system nodes are excluded. Track capacity remains 127 Devices; `GetCompContext()['tag_error']` reports discovery failures.

Select the Device first, then enter hardware LEARN and edit its compatible custom parameter. A linked Device's Free LEARN observer accepts only that COMP and its descendants; an explicitly linked nested Device owns its subtree. Public BIND parameters belong to their public COMP. Foreign COMP edits cannot populate the active Device's library, and delayed ACKs are rejected if the Focus ownership changed. Float/Int/Menu knobs, Toggle/Pulse/Menu buttons retain their existing adapters.

In PLUGIN mode, FUNC selects a Track group, Hold SEL selects a Device within that Track, and normal-view arrows change the active Device's control page. Layout is selected in TD. These are separate contexts; selector-view arrows browse the respective lists.

Set **Device Focus COMP** to link the active Device. Its name defaults to the linked COMP name, including live rename; hardware displays at most 12 printable ASCII characters, replacing non-ASCII characters with ?. The Device selector retains the full COMP name. Unlinked Device names are editable; `RenamePlugin` explicitly opts into a manual display name, and relinking opts back into COMP naming. Track group names/manual Device names accept at most 12 printable ASCII bytes. Layout labels are independent of wire limits. Layout rename never renames Devices. Names never change stable IDs or mapping hashes.

Track and Device lists each use eight-item banks. Device count is bounded to 127 by the one-byte protocol encoding; Track count to 16383 by its two-byte encoding. These are encoding ceilings, not physically tested capacities.

Inspector shows Layout / routing Track / Plugin. Clear and Clear All affect the currently displayed control targets; off-page definitions remain saved. Confirmations expire on Track, Device or control-page changes. Missing targets remain visible and can be cleared. Switching reads current target values, does not restore numeric presets and never fires Pulse actions. Renaming does not require re-LEARN. Changed Menu choices do.

## Selection and readiness

Track browsing pages do not select Tracks. Hardware selection is handled via general ROTO SELECT TRACK (0A 09); this Ableton-compatible host does not depend on Logic-only SET TRACK SELECT MODE (0B 15). The routing Track's Device bank advertises the real count, each Device identity/name and absolute selected index. Hold SEL selects a Device inside that Track (PLUGIN 07, page-relative index); PLUGIN 04 browses its eight-item list bank without selection. Invalid indices are ignored. Layouts are TD configuration, not hardware Plugin entries.

TD-origin switching is blocked during LEARN, touch or LOCK. Under LOCK, hardware Track selection is tracked separately while the locked Plugin keeps routing; unlock queues the latest selection for one guarded activation after the MIDI batch drains. Inspector flags a difference between selected and routing Track. This behavior has passed physical Track-selection/LOCK acceptance on the tested firmware. No force-selection flag is used. Explicit hardware Device selection may replace the locked Device within the routing Track, while preserving the lock and selected/routing Track difference. It still waits for LEARN, touch and backlog drain. Physical Device LOCK acceptance passed: locked Track B selection keeps routing on Track A, SEL switches A's Device without clearing LOCK or the selected Track B, and unlock activates Track B (device_lock_hardware_verification.json). A subsequent physical mapped-control test also passes: pixelSortV3 Knob 2 Lowthresh and Button 1 Mask Image remain controllable while another Track is selected under LOCK; LED/LCD feedback follows the Menu; TD Lowthresh=0.75 moves Knob 2 to approximately 75%. Locked SEL to fractal_pop recalls Knob 1 Power, and turning its unassigned Knob 2 leaves pixelSortV3 Lowthresh unchanged. TD Power=12 moves Knob 1 to approximately 71% with matching LCD feedback (device_lock_controls_hardware_verification.json).

Control routing resumes individually on matching mapping reports. An empty Plugin can be selected with zero ready controls; there is no invented global completion acknowledgement or timeout-based confirmation. MIDI CC does not carry Track/Plugin identity, so delayed old CC after new mapping acknowledgement cannot always be distinguished. Reused legacy parameter hashes can also be ambiguous; migration does not silently change them.

PUSH/TOGGLE is configured in Roto-Setup. The TD adapter must match hardware TYPE; switching Tracks or Devices does not reconfigure it.

## Follow selected COMP

On each saved Device, set **Device Focus COMP** on Layout, then enable **Follow selected COMP** on Binding. Selecting that COMP in the current Network Editor activates its `(Layout, Track, Device)` within Active Layout. One COMP can have only one bound Follow link per Layout; other Devices may still map parameters from that COMP without a Follow link. Python registration retains the preference but cannot Follow serialized Device contexts.

Follow uses the sole selected operator, provided it is an external COMP. Zero selection, mixed families, multiple selection, unlinked/missing COMPs or other panes do not select a Device. A manual Track/Device choice remains until a new COMP selection. Reopen, reinit and entering another pane establish a baseline; they do not activate the already selected COMP. Turning Follow off then on evaluates the current selection immediately. Keep TD playing for selection polling and MIDI.

Automatic selection waits for LOCK, LEARN and touch to clear; the latest observed TD/hardware Track/Device request wins. Explicit hardware Device selection is the LOCK exception described above. While locked, the routing Device remains controllable until an explicit Device switch or unlock fence. A different routing context (including a same-Track Device change), or unlock with pending selection, immediately fences control input, mapping recall and old feedback until activation/recovery. Knob/button events during this interval are discarded. Controls require fresh matching recall afterward. Disconnect, reconnect/open failure and child failure cancel pending requests; a new offline selection can still change local context without opening MIDI.

Focus links follow valid live COMP handles through rename/reparent. Saved destinations inside that linked COMP are rebased across active and inactive mapping variants, without changing IDs/hashes. Deletion latches a missing link; recreating the same path requires explicit relinking. Across file reload the saved relative path acquires a fresh handle, so a replacement made while the controller was not observing cannot be distinguished. Project pre-save refreshes links even with the timeline stopped. For custom component saves call `controller.ext.RotoPythonExt._follow.refresh_links()` immediately before `.save()`; the generic exporter performs its own preparation.

- `SetPluginComp(layout_id, track_id, plugin_id, comp)` persists a Device link; `None` unlinks. It does not change mappings. Linking enables COMP naming.
- `SetTrackComp(layout_id, track_id, comp)` remains a compatibility wrapper for that Track’s active Device.
- `SelectComp(comp)` immediately selects its linked Track and Device in Active Layout; guards raise rather than queue.
- `GetCompContext()` returns a detached snapshot of preference, observed/routing/requested COMP, pending source/sequence/reason, session generation, routing epoch/gate and errors.

Inspector includes Follow status. Domain failures retain the MIDI session, clear the failed request and do not retry every poll. A rollback/observer failure pauses Follow and gates input; repair the cause and use Apply setup to resume. Hardware-to-TD UI selection/reveal remains later work. Layout names stay independent of Device names.

## Plugin control pages

Control pages within a Plugin are separate from Track-list pages. The host retains a Plugin-scoped parameter library (`page_targets`) independently of the current 16 physical slots. Learning Page 2 Knob 1 retains Page 1's parameter definition. Hardware CONTROL MAPPED reports identify the current slot's target by parameter index/hash; the host restores the matching definition and its watcher. Parameter indices are allocated across the entire Plugin library, including inactive pages.

Normal Plugins do not report an absolute control-page number. Observed left/right notifications (GENERAL 14/15) suspend old slot routing immediately; subsequent mapping reports rebuild the active slots. Empty pages remain input-disabled. TD does not guess a page number by counting arrow presses. Eight pages / 128 distinct targets have automated coverage; physical control-page acceptance is separate from previously accepted Track-list paging.

Offline deletion is reconciled only against the matching removed-target identity, never by replaying a slot-only unmap after an unrelated page's acknowledgement. Explicit Clear removes the target definition; learning/replacing a slot through hardware retains earlier definitions because the page number is not transmitted. Definitions deleted by the old one-page implementation cannot be reconstructed from a hash alone; re-LEARN the affected target once.

## Python API

- `GetLayouts()` returns detached IDs, labels, active state, active display names and Track count.
- `CreateLayout(name)`, `SelectLayout(id)`, `RenameLayout(id, name)`, `RemoveLayout(id)` manage outer configurations. Creating does not select; the UI combines both actions.
- `GetTracks(layout_id=None)` returns detached Track IDs/names, active Plugin IDs/names, Plugin counts and saved active state. Omitted Layout means current Layout.
- `CreateTrack(layout_id, name)` creates an empty Track and returns its ID without selecting it.
- `SelectTrack(layout_id, track_id)` activates the specified Layout and Track.
- `RenameTrack(layout_id, track_id, name)` changes its hardware display name.
- `RemoveTrack(layout_id, track_id)` removes it; active removal selects a surviving Track. It does not erase unrelated hardware mappings.
- `GetPlugins(layout_id=None, track_id=None)` returns detached Device IDs, names, full COMP names, name policy, Focus links and active state.
- `CreatePlugin(layout_id, track_id, name)`, `SelectPlugin(layout_id, track_id, plugin_id)`, `RenamePlugin(layout_id, track_id, plugin_id, name)`, `RemovePlugin(layout_id, track_id, plugin_id)` manage independent Devices. Creation does not select; active removal selects a surviving Device.
- `GetLayoutContext()` reports Layout, routing Track/Plugin, hardware-selected Track/Plugin, Device bank/count, lock and a context key. Selection is not proof that all controls have recalled.
- `SetLayoutNames(track_name, plugin_name)` remains a compatibility API for the current Track and Plugin's display names.

Direct API deletion has no UI confirmation. Callers must use IDs, not labels or wire indices.

## Persistence and compatibility

Registry v3 migrates v1 via v2, retaining each Layout and each Track/Plugin. A v2 Track Focus link moves to its sole Plugin; no Tracks or mapping variants are merged. Existing unlinked names stay manual; linked names follow the COMP. Layout IDs, group/device identities, target identities/indices, overrides and removal records are retained. New Tracks and Devices receive independent Plugin identities. Session connection and mapped flags are never restored as routing authority.

Callbacks cannot yet be serialized into these Plugins. Existing registration-hook mode remains available and preserves the suspended registry. SelectLayout or Collection plus Applybinding returns to saved parameter mappings.

Generic tox exports have Follow off and no Focus links; they start disconnected with one empty Custom Layout / EFFECT Track / CUSTOM Plugin, no user assignments or deletion records. MIDI helper and TD sources are embedded; Python with mido/python-rtmidi remains external.

## Acceptance status

Physical multi-Track A/B/A, reconnect, Lowthresh motor/LCD, LOCK/unlock and ninth-Track list paging passed on 2026-10-07 (multitrack_hardware_verification.json). These tests did not cover Plugin control pages. The reported cross-control-page overwrite is fixed in source with automated eight-page/128-target coverage and disconnected native verification; physical re-LEARN/page recall validation is pending.

Live Select software/native verification passed on TD 2025.33230 (comp_follow_native_verification.json). Physical Follow between tagged fractal_pop and pixelSortV3 passed: fractal_pop Knob 1 Power responds, returning to pixelSortV3 recalls its original mappings, and Layout remains T (tag_device_hardware_verification.json). Guarded switching acceptance remains pending; earlier manual Track acceptance does not establish it.

Independent Device selection has automated same-Track A/B/A, bank, LOCK, identity, input-fence, session and native TD verification recorded in device_context_native_verification.json. Physical SEL, unlocked Device deletion/rename list/display, locked Device selection and unlock-to-selected-Track pass (device_metadata_hardware_verification.json; device_lock_hardware_verification.json). LOCK mapped knob/Menu button dispatch, motor/LCD feedback and cross-Device target isolation pass for pixelSortV3 and fractal_pop (device_lock_controls_hardware_verification.json). Ninth-Device banking physical acceptance remains pending.
