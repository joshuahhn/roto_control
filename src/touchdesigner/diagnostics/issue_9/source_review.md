# Issue #9 independent source review

Fixed point: `1cb09d983f970fe4cc01b85639c7baccecd8b092`, unstaged tracked and new files included. No feature commits. Standards and Spec reviews ran independently against the same pinned patch using the `code-review` skill; both independently ran the prior 252-test suite.

## Standards axis

No hard documented-standard violation reported. Two correctness/performance findings were actionable:

- P1: `OP.fetch` defaults to inherited parent storage. Every external COMP owner-token read now goes through local `fetch(..., search=False)`. A fixture models native inheritance and proves an ordinary child is neither a clone nor the same owner. Official reference: [OP Class / fetch](https://docs.derivative.ca/OP_Class).
- P2: repeated full-scope inventory from every control getter/MIDI message. Synchronous observation contexts now cover GetControlStates, publish and Tick batches; nested context/Follow reads share that inventory, and the default tag sampler avoids a second traversal. Mutations, hardware/software writes, Activate and detached revision checks still force fresh validation. Tests exercise 16 slots, 256 nonwriting messages and a clone introduced before a write inside a read batch. No native timing/headroom claim is made.

## Spec axis

One P2 finding: unavailable CUSTOM/LEGACY parameter reads fell back to cached values and could report valid. Parameter availability/read/finite validation now independently gates values and mapped/valid diagnostics. Deleted, unreadable and nonfinite targets return `value=None`, `value_source=unavailable`, `valid=False`, `mapped=False`. Callback caches retain their explicit cached semantics.

An additional source edge check preserves current minimum/maximum/index/wire identity when a target disappears before its latest definitions are captured; only its last saved destination locator is reused.

Second independent review confirmed the local-token, batching/freshness and active-getter fixes. It found one further P2: inactive library reads accepted NaN as live/valid. `GetPluginTargets` now rejects NaN/Infinity/unreadable/non-numeric values as unavailable; regression covers those cases. Final targeted Standards and Spec re-reviews verified this delta; neither reported a further concrete regression. The Spec reviewer also ran the 33 owner tests and shared-value/Pulse cases.

Post-fix suite: 263 tests pass. Native source/storage/save-reload/export, Inspector integration (including same-context quarantine Activate), and physical FUNC/SEL/ACK/LCD remain pending. Issue #9 remains OPEN; this review does not satisfy #11's blocker or authorize other threads' runtime integration, commit/push/merge or shared TD changes.
