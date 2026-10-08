# Issue #9 integration acceptance

The combined COMP/CUSTOM ownership and Inspector integration passed source,
native and the coordinated physical acceptance batch on 2026-10-08.
The reviewed v7 patch SHA-256 is
`c5a81e2eb7b4284fb81b2265d9f95ccc403d56085dd416932c407362456f2c1a`,
based on `55fa9b377a9d326c3786b535678400e877d20671`.
[The portable evidence digest](integration_acceptance.json) records source and
local evidence hashes. Full local captures, failed attempts, recovery artifacts
and candidate mirrors remain preserved outside this source commit.

## Acceptance

| #9 requirement | Evidence |
| --- | --- |
| Dedicated stable COMP ownership; same-name, rename, copy and lifecycle safety | `test_layout_owners.py`; native API/storage/copy/local-token fixture |
| Explicit manual activation; independent CUSTOM configuration | Native recovery/LIVE/guard checks; physical owned A/B/A activation |
| Ownership categories and Layout/Track/Device hierarchy | Metadata-driven selectors and separate Viewing/Routing status; scheduled empty-owner notification |
| Shared live parameter values with independent definitions | Ownership synchronization/isolation regressions; native library versus current-slot checks |
| Selection has no parameter or Pulse recall writes | Source regressions and disconnected native activation checks |
| Actual save/reload and generic export/load | New TD process and absent unsaved nonce; preserved tokens/identities/libraries; blank disconnected generic tox |
| Source, native and physical verification | 276 runtime + 211 Inspector tests; Standards/Spec zero unresolved findings; nine native groups and one physical batch |

v6 and v7 backend, owner observation and publication sources are byte-identical.
The v7 UI-only delta fixes waiting-ACK presentation. Its native check received two
real matching ACK packets after explicit automatic recall, with MappingDraft
closed; no synthetic ACK or additional human gestures were used.

## Limits and restoration

- Six generated UI outputs recooked after reload: WARN; no all-DAT-output equality claim.
- Four physical recorder logging errors, zero capacity drops: WARN; no complete trace or historical FUNC/SEL root-cause repair claim.
- The new session changes `rx_events` telemetry: WARN. Original executable sources,
  registry, manager snapshot, full libraries, materialized definitions, seven
  native Values, local token presence/values, Follow, views and panes were restored.
- The single physical batch covers Learn, Float/Int/Float, renamed Menu LCD and
  matching ACK, owned A/B/A, and original same-Layout/Track pixelSort/fractal A/B/A.
  The v6 waiting-text failure is retained and resolved by the v7 presentation check.
- All 102 original canonical toe/tox artifacts remain unchanged. Temporary receive
  hooks and recorder overrides were removed, and exclusive MIDI ownership returned
  to the restored controller through a fresh real session and matching ACK.

Live TD contains the original captured source baseline, not the v7 candidate.
Cross-Layout Follow (#10), migration (#11) and presets (#12/#13) are separate work.
