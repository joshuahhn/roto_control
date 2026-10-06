# Saved mapping Layouts

Use the controller's Layouts page to select a saved configuration. Each Layout contains up to 8 knobs and 8 buttons mapped freely across COMPs. This version supports 8 Layouts (one hardware plugin page).

Enter a Layout name and press New empty Layout. Choose targets through Inspector or hardware LEARN plus a custom parameter edit as usual. Configuration edits are retained automatically in the active Layout; save the TD project to persist them on disk. Rename Layout changes the dropdown label. Delete Layout requires Yes/No confirmation and cannot remove the last Layout. Inspector Clear/Clear All affects only the active Layout.

The Display page's Trackname and Pluginname are fixed per Layout, defaulting to EFFECT and CUSTOM. These names accept at most 12 printable ASCII characters. Layout names are separate dropdown labels. Renaming does not change hardware mapping identity.

Switching reads current target values; it does not restore effect presets or trigger Pulse actions. Hardware LEARN, touch or LOCK blocks TD-origin switching. Acknowledged controls resume routing individually after recall. Empty Layouts are valid and do not have mapping acknowledgements. Missing targets remain visible as unavailable and can be cleared. Changed Menu choices require re-LEARN.

PUSH/TOGGLE hardware TYPE remains a Roto-Setup setting. The TD button adapter must match it; selecting a Layout does not change hardware TYPE. A/B/A recall has been verified with the isolated hardware probe; end-to-end acceptance of this Layout UI is a separate check.

## Python API

- GetLayouts(): detached ID/name/display-name/active list.
- CreateLayout(name): create an empty Layout and return its stable ID.
- SelectLayout(id): activate saved parameter routing.
- RenameLayout(id, name): update the dropdown label.
- RemoveLayout(id): remove a Layout directly; UI confirmation is not part of this API.
- SetLayoutNames(track_name, plugin_name): update the active Layout's hardware display names.

Callbacks cannot yet be serialized into Layouts. Existing callbacks remain available through Setupmode = Registration hook and Applybinding. This suspends Layout management while preserving its registry. SelectLayout(id), or Collection mode plus Applybinding, restores saved Layouts. Attempting to add runtime callbacks directly to an active parameter Layout is rejected before replacing its bindings.

MIDI CC messages do not carry Layout identity. The implementation gates routing on matching mapping reports, but cannot identify every delayed old CC arriving after a new control acknowledgement. Hardware-origin selection under LOCK has not been physically verified.

Generic exported tox starts disconnected with one empty Custom Layout and default display names. User assignments and other saved Layouts are removed from that template.
