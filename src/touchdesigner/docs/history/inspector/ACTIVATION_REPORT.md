# Explicit context activation verification

Implemented6d in shared commands/live model/view and build_activation.py. Inactive-bank Activate occupies the existing80x16 bottom-right footer, hides Clear Device and adds no Window/height/poll. Header LIVE remains return-to-routing, independent from activation. Selection menus remain browse-only.

Eight new unit tests cover browse/Value neutrality, single full-key dispatch, repeated no-op rejection, stale session/routing/deletion, freshly changed guard, install failure, all adapter fences including manager touch, offline selection, and view success/failure/draft preservation. All239 runtime and187 Inspector tests pass.

Disconnected native clone verifies different Device, Track and Layout activation without target Value changes; fresh LEARN/touch/LOCK/backlog/pause, stale connection generation, actual destination install failure and original context rollback. The controller keeps a routing fence until its next flush after successful rollback, then recovers normally. Follow stays enabled and unchanged TD selection does not reverse explicit activation. Both view footer states are checked. CUA one native footer click changes BROWSE to LIVE and restores Clear Device. No physical MIDI sent.

The first harness attempts used a Device name above the protocol12-byte limit and compared the flattened activation projection's Layout id with a Plugin id; corrected to short names and group_id. The first immediate rollback assertion was too early: existing flush owns recovery. Fixtures were removed and production catalog/registry/process/session checked after each attempt; no controller runtime edits required.

Evidence: activation_verification.json. Fixture removed, original six production ACKs/Values/registry and MIDI process preserved; subscribers2. Generic export/reload checks current commands/model/view source and hidden/unconfigured activation state. Physical LCD/recall behavior remains unverified and joins ACCEPTANCE_BATCH.md. Performance/manual resize remain deferred.

Saved through live TD as inspector_editor_actions.45.toe; actual file and settled402px K2 Details verified after save.
