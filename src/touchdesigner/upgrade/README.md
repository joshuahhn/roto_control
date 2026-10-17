# Disconnected component upgrades

Execute the required upgrader inside live TD with an explicit controller and
`src/touchdesigner` source root. Read its function signature first: network and
collection upgrades take the containing parent; Layout and MIX upgrades take the
controller. Make a recovery copy through TD before modifying a user component.

Sibling builders live in `build/`; export, MIDI and documentation helpers remain
in `scripts/`. The `.patch` files here are historical source-reproduction
records for their named commits, with their original paths retained.
