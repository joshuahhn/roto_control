# Layouts and Tracks

A saved Layout contains multiple selectable Tracks. Each Track currently has one Plugin mapping set of up to 8 knobs and 8 buttons. The schema retains a Plugins list for future expansion; multiple Plugins per Track are rejected in this version.

Select Layout on the Layouts page. Select Active Track on the Tracks page, or use the hardware Track selector while connected in PLUGIN mode. New Track name plus New empty Track creates and selects a Track. Display / Trackname renames the current Track; Pluginname renames its Plugin. Delete Track uses Yes/No confirmation and cannot remove the last Track. Layout deletion remains separately confirmed. Configuration edits are retained automatically; save the containing TD project to persist to disk.

Different Tracks and Layouts may reuse EFFECT / CUSTOM display names without sharing their mappings. IDs are stable and independent of display names and hardware list indices. Track and Plugin names accept at most 12 printable ASCII bytes. Layout labels are independent of wire display limits. The old eight-Layout cap is removed; hardware Track lists are paged in groups of eight. The two-byte count bounds the registry to 16383 Tracks per Layout; this is a protocol encoding ceiling, not a tested hardware capacity.

Inspector shows Layout / routing Track / Plugin. Clear and Clear All affect only that Plugin's mappings; their confirmations expire on context changes. Missing targets remain visible and can be cleared. Switching reads current target values, does not restore numeric presets and never fires Pulse actions. Renaming does not require re-LEARN. Changed Menu choices do.

## Selection and readiness

Track browsing pages do not select Tracks. Hardware selection is handled via general ROTO SELECT TRACK (0A 09); this Ableton-compatible host does not depend on Logic-only SET TRACK SELECT MODE (0B 15). Only the routing Track's Plugin is advertised, at Plugin index 0. Layouts are TD configuration, not hardware Plugin entries.

TD-origin switching is blocked during LEARN, touch or LOCK. Under LOCK, hardware Track selection is tracked separately while the locked Plugin keeps routing; unlock attempts to follow the selected Track. Inspector flags a difference between selected and routing Track. This behavior follows the Ableton integration model but still requires physical acceptance on this firmware. No force-selection flag is used.

Control routing resumes individually on matching mapping reports. An empty Plugin can be selected with zero ready controls; there is no invented global completion acknowledgement or timeout-based confirmation. MIDI CC does not carry Track/Plugin identity, so delayed old CC after new mapping acknowledgement cannot always be distinguished. Reused legacy parameter hashes can also be ambiguous; migration does not silently change them.

PUSH/TOGGLE is configured in Roto-Setup. The TD adapter must match hardware TYPE; switching Tracks does not reconfigure it.

## Python API

- `GetLayouts()` returns detached IDs, labels, active state, active display names and Track count.
- `CreateLayout(name)`, `SelectLayout(id)`, `RenameLayout(id, name)`, `RemoveLayout(id)` manage outer configurations. Creating does not select; the UI combines both actions.
- `GetTracks(layout_id=None)` returns detached Track IDs/names, Plugin IDs/names and saved active state. Omitted Layout means current Layout.
- `CreateTrack(layout_id, name)` creates an empty Track and returns its ID without selecting it.
- `SelectTrack(layout_id, track_id)` activates the specified Layout and Track.
- `RenameTrack(layout_id, track_id, name)` changes its hardware display name.
- `RemoveTrack(layout_id, track_id)` removes it; active removal selects a surviving Track. It does not erase unrelated hardware mappings.
- `GetLayoutContext()` reports Layout, routing Track, Plugin, hardware-selected Track, lock and a context key. Selection is not proof that all controls have recalled.
- `SetLayoutNames(track_name, plugin_name)` remains a compatibility API for the current Track and Plugin's display names.

Direct API deletion has no UI confirmation. Callers must use IDs, not labels or wire indices.

## Persistence and compatibility

Registry v2 migrates each v1 Layout into one Track plus one Plugin inside that same Layout. Layout IDs, group/device identities, target identities/indices, overrides and removal records are retained. New Tracks receive independent Plugin identities. Session connection and mapped flags are never restored as routing authority.

Callbacks cannot yet be serialized into these Plugins. Existing registration-hook mode remains available and preserves the suspended registry. SelectLayout or Collection plus Applybinding returns to saved parameter mappings.

Generic tox exports start disconnected with one empty Custom Layout / EFFECT Track / CUSTOM Plugin, no user assignments or deletion records. MIDI helper and TD sources are embedded; Python with mido/python-rtmidi remains external.

## Acceptance status

Automated and disconnected native verification cover migration, Track isolation, paging packets, source-aware selection, lock state handling, stale mapping rejection, native UI callbacks and save/reload. Physical multi-Track A/B/A, motor/LCD, reconnect and LOCK acceptance remain pending. Earlier isolated Plugin-switching evidence does not establish Track-switching acceptance.
