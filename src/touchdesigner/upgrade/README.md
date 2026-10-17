# Disconnected component upgrades

Execute the required upgrader inside live TD with an explicit controller and
`src/touchdesigner` source root. Read its function signature first: network and
collection upgrades take the containing parent; Layout and MIX upgrades take the
controller. Make a recovery copy through TD before modifying a user component.

`upgrade_serial.py` takes the controller and exposes `install(controller,
source_dir)`. It embeds the optional read-only Serial worker and observation
owner without adding UI or changing mappings. Finish or disconnect a Serial
read before running any runtime upgrade, even when MIDI is disconnected.

`upgrade_inspector_hardware.py` adds the Hardware snapshot Details section to an
existing owned Inspector. Its `install(controller, source_dir, *,
expected_project, recovery_path)` requires the exact active project path and a
new recovery `.tox` path. It checks local model/view/editor ownership, preserves
existing nodes and outer layout, and requires inactive MIDI/Serial. It refreshes
affected extensions without restarting TD or running the full Inspector builder.

Sibling builders live in `build/`; export, MIDI and documentation helpers remain
in `scripts/`. The `.patch` files here are historical source-reproduction
records for their named commits, with their original paths retained.
