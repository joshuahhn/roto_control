# ROTO-CONTROL development

- Reply in Cantonese with English technical terms.
- TouchDesigner work lives in src/touchdesigner. Read its CONTEXT.md and HANDOFF.md; preserve upstream Ableton/Bitwig code unless requested.
- Use external Python builders and source files. Never edit toe/tox binaries directly; save/export through live TD.
- Load td-general and relevant TD skills before live TD changes. Verify the active project first.
- Source Markdown is authoritative; scripts/td_project_docs.py embeds snapshots.
- Generic tox exports are disconnected and have no user mappings. MIDI helper and DAT source are embedded; Python with mido/python-rtmidi remains external.
- Follow the change-scoped validation policy below; read HANDOFF.md as dated evidence, not a queue of required tasks.
- Do not commit or push without user instructions.

## Change-scoped validation

- Identify the changed behavior and checkout/source baseline first. During development run the relevant existing tests; extend them for a missing regression before adding another verifier. Preserve wrong-target, stale ACK, persistence and exactly-once coverage.
- Before delivery, run `python3 -m unittest discover -q` from `src/touchdesigner` for runtime source changes, plus checks for any affected builder/UI not covered by discovery. Run `git diff --check`. A passing run on the final relevant source is sufficient; repeat only after a relevant change, failure or new evidence. Documentation-only changes need a scoped diff, link/consistency review and diff check, not runtime or live acceptance.
- Reuse acceptance for unaffected behavior. State the baseline, changed paths and evidence scope; source tests, native TD checks and physical acceptance prove different things. Historical `pending`/`gate` wording does not create a task or delivery blocker; consult later results for the same case and keep unresolved limitations separate.
- Use targeted native TD checks only for affected TD-native behavior (callbacks, panel/window geometry, lifecycle, save/load or embedding). Use targeted hardware checks only for affected MIDI/ACK/feedback behavior, including indirect changes. Confirm the active project before live work. An unavailable TD/controller is a stated limit on the claim, not a reason to expand the investigation or repeat unrelated acceptance.
- If a check cannot answer the question, distinguish a product defect from a test-method or environment problem. Choose one experiment with an observable result that separates the plausible causes; repeat a check only with a changed condition or hypothesis. Stop when the scoped claim is supported or its limitation is clear.
- Put one-off probes and outputs in a system temporary directory by default. Retain a new harness/result in the repo only for an explicit reusable regression or acceptance need, with its scope, prerequisites and output location documented. Preserve existing tests and evidence; propose consolidation/deletion separately for user decision.
- Markdown is authoritative. A documentation-only edit does not require re-embedding or saving artifacts; refresh embedded snapshots during the next authorized live save/export affecting those artifacts.
