# Controller-owned Inspector packaging

This delta composes the closed Actions (#12), automatic Follow (#10 v5) and COMP
migration (#11 corrected native import) sources. Snapshot #13 is excluded.
The existing new compact Inspector replaces the Palette Lister presentation.

## Interface and ownership

`Openinspector` / **Open Inspector** is a Pulse on Connection after Disconnect.
The normal parameter callback calls `RotoPythonExt.Openinspector()`; it validates
the controller-owned model and both current views, then shows the Fold window.
It does not connect MIDI, activate a Device, change Follow COMP, assign a mapping,
write a target value or recall an Action. A foreign/stale model is an error.

Each controller contains:

```text
roto_python
  inspector
    targets / database / context_state / inspector_data  (headless publisher)
    owned_runtime
    inspector_model
      base_commands / base_targets / event-driven observers
    inspector_below  (primary Fold view + independent popup editor)
    inspector_popup  (alternate new presentation + its popup editor)
```

Controller and Model OP parameters use clone-local parent expressions, not root
shortcuts. Local parent shortcuts inside each model/view resolve their own
callbacks. Two controllers can be renamed or moved independently. No root sibling
model/view or old Lister is required by factory or portable tox.

## Local extension generations

The native model COMP is the ownership boundary; a retained Python extension
is not necessarily its current generation. Quiesce preflights all current
named/attached model and view references, valid native owner equality, and local
Controller/Model OP parameters before unsubscribing or stopping any generation.
A previous generation is eligible only with that same valid native model owner;
foreign, invalid or unreadable references fail before effects. Open remains
strictly attached to the current generation and never falls back to the old one.

The documented native `onInitTD` hooks on model and views attach subscriptions
to the current local model after extension initialization. They do not initialize
extensions recursively, poll, open windows, connect MIDI, select routing, change
Follow, write target values or recall Actions. Already-current subscriptions are
a no-op. Reattachment preserves BROWSE context/filter/preferences and retains the
existing draft/dialog/token invalidation of public UI Connect/Disconnect. Old
local queued observations/subscribers are shut down, including during quiesce;
repeated native destruction does not reset the current generation's picker.
This is interface robustness, not a diagnosis of any earlier native re-init.
See [Derivative extension lifecycle documentation](https://derivative.ca/UserGuide/Extensions).

## Build, upgrade and export

`build_network.build(parent, source)` finishes Layout setup before building the
owned Inspector. `upgrade_layouts.upgrade(controller, source,
legacy_inspector_archive=NEW_PATH)` is the disconnected full source upgrade.
The new `build_inspector.build(controller, source, legacy_archive=NEW_PATH)` is
the UI packaging entry point after runtime source upgrade. If old Lister exists,
a **new native-saved tox archive is mandatory before presentation removal**.
A fresh project recovery must also be saved before live upgrade. Necessary
`targets`, `database` and `context_state` publication DATs remain at stable paths.
All source/callback DATs are embedded with FILE/sync/load disabled.

Repeated identical packaging verifies the embedded source manifest and current
local model/view identities, then returns without rebuilding subscriptions.
Changed packaging disconnects only its old views/model before rebuilding. It
never changes the controller's saved mappings/IDs/libraries or external targets.
Standalone prototype scripts remain development tools; production packaging
supplies explicit parent/model/views/source inputs to the shared geometry builders.

`export_component.export` sanitizes only its detached clone. It clears nested UI
storage, drafts, hidden target readouts, menu context and runtime subscriptions,
then initializes the empty clone-local model. Absolute Parameter Execute watcher
paths are not serialized; current local watchers are rebuilt on load. Generic
exports retain source/helper/docs, and have no user mappings, Actions/hooks,
receipts/backups, Focus refs, owner tokens or MIDI session. They do not open UI.
Python with MIDI dependencies remains external.

## Network recipe and live boundary

`cleanup_network.plan/apply/verify` groups the controller and Inspector wrapper
using measured node sizes, checks annotation containment/non-overlap and forwards
wired outputs left-to-right. It changes network presentation only, not panel
geometry, parameters, callbacks or targets. Unknown functional nodes stop cleanup.
Unrelated annotations are preserved; removing old managed annotations requires
explicit recorded paths in `obsolete_annotations`. Do not delete sibling views automatically: archive old UI/project first, install
and prove owned UI, then remove only explicitly verified obsolete presentation
siblings. User tools, archived original controller and unrelated OPs stay intact.

Source tests cover local Open, two instances, relocation, publisher scheduling,
idempotent packaging and nested generic sanitation. Native install/Open/reload/
standalone generic/two-instance/cleanup proof remains a separate Root-authorized
window. No previous physical acceptance is replayed by this packaging change.
