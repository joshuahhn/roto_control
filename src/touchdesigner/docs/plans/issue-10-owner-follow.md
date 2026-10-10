# Issue #10 cross-Layout COMP Follow source contract

Source implementation on `t3/issue-10-comp-layout-follow`, composed onto accepted
#12 Git TREE `55ef1a5febecb6c4f2428e49e899e15d5c030fd8` from common commit
`61d0e03fc454dba496618fdf33ab4a5169437b19`. #9 and #12 are CLOSED/accepted.
The dependency TREE is not a commit; delivery diff compares directly against it.
This candidate
has no feature commit/push, native installation, live promotion or physical PASS.
The earlier implementation brief is a historical preparation snapshot.

## Destination / #11 integration

`LookupCompLayout(comp)` remains the #9 owner authority. Follow uses it without
allocation, migration or identity creation. A registered COMP's unique bound
Layout wins over any mapping/Focus reference in a CUSTOM or LEGACY Layout.

`SelectComp(comp)` and automatic Follow share this destination policy:

1. Read the bound owner Layout's saved `active_track` and that Track's
   `active_plugin`. These are existing registry Device IDs, not wire `device_id`.
2. Require the saved Device's `focus_comp` to be bound, qualified by the exact
   `owner_id`, have the owner's locator and resolve to the same live COMP handle.
3. Select that complete `(layout_id, track_id, plugin_id)` once through existing
   `Layouts.select_plugin`. An unlinked/foreign saved Device is unavailable for
   Follow; there is no first-match/name/order or entry fallback.

New registration's saved active Device is its entry, so a new owner has an initial
destination. Multiple qualified variants, including manual labels and multiple
Tracks, retain independent IDs/assignments/ranges/libraries. Explicit activation
updates the saved choice; A/B/A Follow returns to that owner's last chosen variant.
`entry_plugin_id` protects the enrollment/recovery entry and is **not** a separate
Follow default. #11 can preserve atomic qualified variants; if it intends a
particular variant to be followed, its accepted transaction must set the existing
saved active Track/Device to that valid variant. #10 does not migrate user records.

CUSTOM Focus/parameter references remain manually usable. LEGACY compatibility
retains the original unique Focus resolution only in the active LEGACY Layout for
a COMP without a local owner token and without a registered owner at its locator.
The locator check only prevents fallback to an unavailable/replaced owner; it
never grants ownership. Missing/conflicted/unregistered owner identity cannot be
overridden by a legacy reference. A bound return to the quarantined active owner
still needs explicit Activate and new matching control ACKs.

## Pending intent / fences / context

TD and hardware retain one latest-intent arbiter. Requests carry the connection
generation, full destination, original committed routing key and destination
owner ID. Flush re-resolves a TD COMP using fresh owner inventory and the saved
variant, and rejects changed routing origins, owner IDs or destinations. It does
not reject harmless live value/captured-catalog revision changes. Native #9 owner
guards force another inventory before activation. No generic revision-based
migration or replacement API is introduced.

Hardware FUNC/SEL requests stay within their original routing lists. LOCK delays
automatic Follow/Track routing; explicit hardware SEL retains its existing
same-routing-Track exception. Automatic TD Follow ignores touch release; manual
activation, hardware FUNC/SEL and editing retain touch guards. LEARN/backlog/opening-session/dispatch guards,
connection generations, old ingress epochs and transport/domain error policy
are preserved. Fenced CC/ACK/page recall/FreeLearner/Pulse/feedback is discarded,
not replayed. Controls resume individually only on matching recall.

Changing Layout is not a new pane selection: observation scope now tracks
Parameter/Python mode, while the pane baseline survives Follow and manual
activation. Startup/reinit/reload/pane return still establish baselines, Follow
off/on can explicitly evaluate, and manual choice lasts until a new selection.
A fresh request made during install survives to the next flush, with input/ACK
still gated between those commits. Stale pre-commit hardware origins are rejected.

`GetCompContext()` adds detached `pending_layout_id`, `pending_owner_id` and
`follow_destination_policy='saved_active_owner_qualified_device'`. Existing
`LookupCompLayout`, `SelectComp`, `SelectPlugin` and `GetLayoutContext` signatures
are unchanged; no persisted schema or hardware protocol field is added.

One existing activation publishes routing, selector values and scoped hardware
announcements. Inspector reads the committed triple/owner; LIVE follows it and
BROWSE remains a separate view. Old Activate tokens expire after Follow's routing
epoch/context change. Accepted backend publication/ACK/Action sources retain their exact bytes; the
explicit post-v3 Inspector UI requirement changes only its existing command,
adapter, shared builder and view seam. No selection
writes numeric/Menu/Toggle values or dispatches Pulse/callback/Presets.

## Verification / delivery

`test_owner_follow.py` allocates actual source owner Layouts and covers cross-owner
A/B/A, saved variants, CUSTOM/LEGACY separation, owner unavailable/replacement,
guards/mixed-source arbitration, batch/partial-line fencing, fresh recall,
disconnect/open/child failure, rollback/repair, new commit-time requests,
rename/reload baselines, and real Inspector model/adapter routing projection.
Native inspection of TD definitions is explicitly excluded from that unit test.

`test_owner_follow_actions.py` checks the composition against accepted #12:
Action references remain independent per owner/CUSTOM, selection/ACK never recalls,
current Actions obey LOCK and transition/LEARN/fresh-ACK fences; touched automatic
Follow routing no longer waits for release, callback-time
selection uses the existing arbiter, newer commit/rollback intents remain fenced,
partial-result metadata stays separate from mapping errors, and reload returns to
the saved qualified variant without callback execution. Runtime provider APIs,
Action dispatch, assignment identities and details-only publication are unchanged.

The old prepared native fixture remains unexecuted historical v2 source. The
current [short direct checklist](../../diagnostics/issue_10/README.md) uses the
existing demo_A/demo_B/CUSTOM contexts under root's Inspector sole executor;
accepted #9/#12 gates are not repeated. Retained failed source attempts remain
with the old immutable candidates.
Runtime/Inspector checks and immutable candidate hashes are recorded at delivery;
root owns source/native/physical acceptance and commit/push/issue closure.

## Inspector automatic Follow preference (explicit post-v3 requirement)

`Follow COMP: ON/OFF` is controller preference, independent of LIVE/BROWSE view
following. `FollowCompToken/FollowCompCapability/SetFollowComp` live in the existing
command service and model facade. The token includes generation, bound controller
session/identity, active routing/owner stamp and observed preference. The adapter
rechecks those observations and writable `Followcomp`, controller/local extension,
mode/restore/dispatch/mutation/paused/owner availability before a single native
parameter write. No MIDI connection prerequisite, direct follower calls, second
arbiter, implicit Activate or quarantine repair. Native callback is authoritative.

Actual current `NETWORKEDITOR` owner `selectedChildren` is the sampler source,
not a Parameter pane. Explicit ON can produce a valid intent for that selection;
LOCK/LEARN/session/owner/variant guards remain unchanged; automatic Follow touch
deferral is superseded by the explicit policy below. OFF cancels through
the same callback. Existing observers notify both views even with empty targets;
BROWSE key/filter/draft is retained and LIVE does not write this preference.
At the v4 UI freeze, runtime/Action dispatch and v3 backend bytes were unchanged.
The v5 policy changes only the scoped routing/install guards described below. Current
native UI/physical gates remain coordinated by root; prior native bounded PASS
is reusable only for unchanged bytes. No physical PASS is claimed by this source.

## V5 explicit user policy: no touch wait for automatic Follow

User: 「我觉得呢个 touch gate 应该系唔需要。 使用者喺用量嘅时候已经知道佢做紧啲乜嘢。」
This supersedes **only automatic TD COMP Follow routing** touch deferral. It is
not a global touch-safety removal or a new setting. The current selected owner's
saved qualified Device can commit with manager/host touch flags set. LOCK/LEARN,
backlog/transport, owner/quarantine, original routing/session/intent freshness,
mutation/dispatch/paused handling, rollback and fresh per-control ACK remain.
Selection still reads live values and never recalls Presets/Action/Pulse.

Actual routing sites: CompFollower.flush stops treating touch as a TD-intent
wait, context pending_reason excludes touch for that source, Layouts selection
preflight receives a transient automatic_follow marker, and its install/rollback
passes the same marker to BindControls. The latter permits only touched
replacement while both the Layout manager is mutating and the existing follower
is committing. It does not permit LEARN/dispatch, nor general touched binding
outside that transaction. No persisted option or second arbiter is introduced.

Explicit SelectComp/SelectPlugin/SelectLayout/manual Activate and default shared
guard callers still require release; hardware FUNC/SEL, tag enrollment, Value
editing, assignment, rename, native definitions and Action provider/dispatch
safety are unchanged. Public selection signatures stay unchanged; internal
routing markers default false. UI commands/adapter/view/builder remain exact v4.
No Snapshot source or records are integrated or migrated.

`test_follow_touch_policy.py` was RED against exact v4 before runtime edits:
remaining-touch variant commits and honest pending_reason failed, while manual
activation still rejected touch. Source evidence preserves the red log/sources,
initial overlong test-label failure, later install guard discovery, and fixture
expectation corrections. These source mocks prove policy logic, not physical TD.
Prior touch-deferral tests/native SYNTH results remain in immutable v4 and earlier
pins as evidence for the superseded policy. The held-A human observation remains
history with unknown cause; no source diagnosis or physical reproduction is claimed.

Root reuses already accepted UI/physical A/B/A/LOCK/LEARN/fresh-ACK/zero-selection
scopes only for unchanged behavior. Next gate is a minimal direct native changed-
policy check and final usable input, then fresh mandatory restoration. No further
human touch gate, accepted A/B/A replay or external harness campaign is requested.
