# Independent Device context

Approved direction: user said “go” after the Ableton/Bitwig/Logic parity research, 2026-10-07. Implement independent Plugin selection before name synchronization; reverse hardware-to-TD UI selection remains phase two.

## Domain and migration

Layout is a saved configuration, Track an explicitly managed tools group, Device/Plugin a controlled tool COMP. Do not infer Tracks from parent COMPs or merge existing mapping variants. Keep existing Layout/Track/Plugin/group/device/parameter IDs and wire hashes, current targets, off-page libraries, pending clear/relearn records, and registration behavior.

Registry v3 supports 1..127 Plugins per Track, an active Plugin per Track, and Plugin-scoped optional Focus COMP links. Migrate v1 through v2; v2 Track Focus moves to its sole Plugin. Existing names stay manual unless a bound Focus link enables COMP naming. No auto-discovery/creation or auto-mapping. Unique bound COMP links across the Active Layout; duplicate variants require explicit Layout/profile decisions. Across reload links remain path-based, with the previous documented limitation. Rename/reparent/missing-handle and synchronous pre-save policies remain intact.

Names: linked Devices default to current COMP name (hardware truncation remains 12 printable ASCII bytes; non-ASCII COMP-name characters display as ?). Stable UUID identity is unaffected. Full COMP name can remain in metadata/UI. Unlinked Devices use an editable display name; RenamePlugin explicitly opts into manual naming. Layout rename never changes Device identity/name. Manual linking sets COMP naming again.

## API and UI

Promote GetPlugins, CreatePlugin, SelectPlugin, RenamePlugin, RemovePlugin, SetPluginComp. IDs are explicit (layout, track, plugin). Keep SetTrackComp as a compatibility wrapper operating on that Track's active Plugin. SelectComp resolves all three IDs. GetLayoutContext/GetCompContext expose selected and routing Plugin IDs, pending Plugin and Plugin-scoped Focus.

Use existing Layout custom page: Active Layout; Track selector/name/create/delete; Device selector, Device name, Device Focus COMP, new Device name/create/delete. Do not add Binding modes or confirmation buttons. Device deletion uses the existing asynchronous native popup, expires on all three context IDs and preserves last-item guards. All selection/data parameters disabled in Python registration as appropriate.

## Protocol and transaction

Announce a real Device count, eight-item Device metadata bank, absolute selected Device index. PLUGIN 04 only browses list banks; PLUGIN 07 chooses a page-relative index in the advertised bank. Reject invalid indices/banks without mutation. Per-control mapping recall remains index/hash based, with no guessed absolute normal control page.

One arbiter carries (layout, track, plugin) for TD Follow, hardware Track and hardware Plugin requests. Latest intent wins. Track requests remember destination active Plugin when queued. Manual API/UI selection stays synchronous and guarded, clears obsolete pending requests. Hardware request commit occurs after a complete batch/backlog drain. Every different routing context immediately fences old input, mapping/FreeLearner recall and feedback, including same-Track Plugin changes. Carry session generation and epoch through partial lines; no old writes/Pulse calls or replay. Fresh matching recall alone enables controls after switching.

LOCK blocks TD Follow/API and hardware Track routing changes; Track browsing can still differ from routing. Explicit hardware Plugin selection may replace the locked Plugin **within the routing Track**, as Ableton/Bitwig do. This intent still waits for LEARN/touch/backlog, and fences immediately. Preserve selected Track divergence under this exception. Unlock follows latest pending selection; no obsolete intent replay. Maintain lock state across CollectionHost replacement, rollback and session resets. Browsing Device list itself does not activate or fence.

All target preflight, activation, rollback, failed rollback pause/repair, no domain Disconnect, transport-only Disconnect, offline Follow, baseline-only startup and cancellation-on-pane-exit rules continue from live-select-comp.md.

## Build and verification

No additional operators or signal wires: edit existing layouts, text_comp_follow, extension, setup and Inspector source as necessary. External upgrade installs all dependencies disconnected before reinit; builders/export use shared UI helpers. No toe/tox binary edits. Preserve existing measured topology/positions.

1. Unit regression plus new same-Track A/B/A, 9th Device bank/list/select, invalid banks, cross-Track destinations, empty Device, independent Clear/library isolation, CRUD/last-item guards and context-specific deletion expiry.
2. v1/v2/v3 idempotent migration: deep compare stable identity/target/library payloads; move only Focus metadata and add name policy. Test duplicate rejection and COMP rename without re-LEARN.
3. Arbiter/fence tests: same-batch select B -> knob/Pulse, LEARN/touch/backlog, fresh recall, partial-line epochs, LOCK explicit Device select vs Track browse, latest mixed-origin intent, rollback/session cancellation and disconnected Follow. Existing tests must remain meaningful; schema expectations adapt to Plugin-owned Focus.
4. Native isolated two-COMP/same-Track fixture verifies real custom parameter and Pulse writes, Follow selection, SEL protocol, metadata banks, rename/save/reload and no value writes on selection. Never manufacture physical acceptance.
5. Main upgrade comparison preserves baseline identities/targets/libraries and parameter values; reconnect verifies active target recall. Temporary test Devices/COMPs never remain in the user's registry.
6. Generic tox reload is empty/disconnected, Follow off, no Focus links, source/file dependencies or MIDI process; registration template remains user-editable. Save verified project/tox through TD, embed authoritative source docs, copy canonical artifact bytes only after checks.
7. Run python3 -m unittest discover -q in src/touchdesigner and git diff --check. Check native errors and geometry; write evidence and HANDOFF. Physical multi-Device SEL/LOCK/motor/LCD acceptance stays pending until the user actually tests it.

Research evidence: ../research/live-select-parity.md. No automatic macros, Plugin enable/bypass inference, hardware-to-TD pane reveal, firmware updates, commit or push in this phase.
