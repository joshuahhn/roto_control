# Issue #4 verification

`verify_native.py` builds and removes an isolated controller without physical MIDI.
It checks both partial-CC directions, same/split batch Unlock routing and locked
Device selection. `native.json` records results.

`physical_unlock.json` records the user's locked selection/Unlock acceptance.
Physical batch timing and CC-half injection were not measured. Original mappings
and values were restored after removing the temporary Layout. Recovery exports
and original mapping snapshots are retained locally, not published.
