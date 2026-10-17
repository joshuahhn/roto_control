# Applied MIX Inspector

## Problem and usage

The Inspector used a sixteen-slot PLUGIN catalog even when hardware reported
MIX. MIX profiles contain ordered items and semantic controls, so they cannot
truthfully reuse editable PLUGIN slots.

Auto follows the connected observed mode. Explicit PLUGIN retains a pinned
Browse view, and explicit MIX permits offline inspection. The display choice is
transient and local to each view. It never changes the hardware mode.

## Shape

One detached runtime observation owns applied identity, source/target checks,
actual TD values, captions and availability. It uses the applied descriptor,
never draft parameters. Existing MIX state exposes the same inspection result.
The optional Inspector publication reads the current runtime without creating or
repairing it, and captures one observation for signature and publication.

The shared model reads `context_state.mix`, retains one transient cache and uses
its existing zero-slot, zero-metadata notifications. MIX is a separate read-only
scroll document. PLUGIN context, drafts, tokens and pending Clear remain owned
by their existing model. Hidden mutation callbacks are rejected in MIX; genuine
PLUGIN changes still invalidate stale drafts.

## Synthesis decision

Two independent same-model candidates each scored 28/30. The explicit-selector
candidate supplied the smaller existing state/notification API. The automatic
candidate supplied Auto / PLUGIN / MIX policy and one pure publication capture.
A new public getter and separate subscriber framework were rejected because the
existing model already delivers zero-slot display changes.

Model the Domain keeps semantic MIX controls separate from PLUGIN slots.
Boundary Discipline keeps native target identity rules in the runtime.
Laziness Protocol reuses publication and notification rather than adding timers.
Prove It Works requires native callback, value refresh and reload evidence in
addition to source tests.

## Tradeoffs and alternatives

A text document shows every assignment without expanding this issue into a MIX
editor. An additive builder/updater preserves existing nodes and outer geometry.
Generic export scrubs dynamic readouts and recomputes observations on reload.

Synthetic PLUGIN contexts would expose the wrong write actions and slot model.
An independent MIX window would add lifecycle and another entry point. An
always-visible MIX section would keep unrelated PLUGIN mappings prominent.
The chosen panel avoids all three costs.

## Verification boundary

Cover both styles, absent/unrestorable/zero-item profiles, source/target identity
changes, conditional Swap availability, actual out-of-range values and native
captions. Reads must not change runtime latches, targets, counters, queues,
profile/storage or parameter values. Display-only notifications must preserve
PLUGIN drafts and tokens. Test native selector callbacks, ordinary value
publication, additive-install idempotence and configured/generic reload. No
restart, audio implementation, full editor or physical feel claim is included.
