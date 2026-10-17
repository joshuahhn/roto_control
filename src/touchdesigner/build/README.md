# Component builders

Execute `build_network.py` inside live TD and call `build(parent_comp, source_dir)`
with `source_dir` set to `src/touchdesigner`. It resolves current runtime,
upgraders and shared helpers from that root. It creates a disconnected controller;
it does not configure or connect physical MIDI.

`build_inspector.py` builds the controller-owned Inspector. `build_free_learn.py`
installs the parameter listener used by the collection upgrader. Existing
Inspector-specific builders remain with their `prototypes/inspector` fixtures.
