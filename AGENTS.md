# ROTO-CONTROL development

- Reply in Cantonese with English technical terms.
- Protocol design and capability reviews: read [official integration guidance](docs/integration-guidance.md).
- TouchDesigner work lives in src/touchdesigner. Read its CONTEXT.md and HANDOFF.md; preserve upstream Ableton/Bitwig code unless requested.
- Use external Python builders and source files. Never edit toe/tox binaries directly; save/export through live TD.
- Load td-general and relevant TD skills before live TD changes. Verify the active project first.
- Source Markdown is authoritative; scripts/td_project_docs.py embeds snapshots.
- Generic tox exports are disconnected and have no user mappings. MIDI helper and DAT source are embedded; Python with mido/python-rtmidi remains external.
- Follow the change-scoped validation policy below; read HANDOFF.md as dated evidence, not a queue of required tasks.
- Do not commit or push without user instructions.

## Python script organization

- In `src/touchdesigner`, put `test_*.py` in `tests/`, `verify_*.py` in `verify/`, `upgrade_*.py` in `upgrade/`, and `build_*.py` in `build/`. Keep feature-specific diagnostic scripts with their existing diagnostic fixtures.
- Pass `src/touchdesigner` as `source_dir` to builders/upgraders after moving scripts; resolve source and sibling script paths from that root. Update callers and current documentation when relocating a script.
- Keep `python3 -m unittest discover -q` working from `src/touchdesigner`; run individual tests with `python3 -m unittest discover -s tests -p 'test_<name>.py'`.

## Change-scoped validation

- Identify the changed behavior and checkout/source baseline first. During development run the relevant existing tests; extend them for a missing regression before adding another verifier. Preserve wrong-target, stale ACK, persistence and exactly-once coverage.
- Before delivery, run `python3 -m unittest discover -q` from `src/touchdesigner` for runtime source changes, plus checks for any affected builder/UI not covered by discovery. Run `git diff --check`. A passing run on the final relevant source is sufficient; repeat only after a relevant change, failure or new evidence. Documentation-only changes need a scoped diff, link/consistency review and diff check, not runtime or live acceptance.
- Reuse acceptance for unaffected behavior. State the baseline, changed paths and evidence scope; source tests, native TD checks and physical acceptance prove different things. Historical `pending`/`gate` wording does not create a task or delivery blocker; consult later results for the same case and keep unresolved limitations separate.
- Use targeted native TD checks only for affected TD-native behavior (callbacks, panel/window geometry, lifecycle, save/load or embedding). Use targeted hardware checks only for affected MIDI/ACK/feedback behavior, including indirect changes. Confirm the active project before live work. An unavailable TD/controller is a stated limit on the claim, not a reason to expand the investigation or repeat unrelated acceptance.
- If a check cannot answer the question, distinguish a product defect from a test-method or environment problem. Choose one experiment with an observable result that separates the plausible causes; repeat a check only with a changed condition or hypothesis. Stop when the scoped claim is supported or its limitation is clear.
- Put one-off probes and outputs in a system temporary directory by default. Retain a new harness/result in the repo only for an explicit reusable regression or acceptance need, with its scope, prerequisites and output location documented. Preserve existing tests and evidence; propose consolidation/deletion separately for user decision.
- Markdown is authoritative. A documentation-only edit does not require re-embedding or saving artifacts; refresh embedded snapshots during the next authorized live save/export affecting those artifacts.

## Fork safety

- This fork is `joshuahhn/roto_control`; upstream is `Melbourne-Instruments/roto_control`. Target GitHub mutations at the fork using an explicit `--repo` or API repository path. Treat upstream as a read-only reference unless the user explicitly requests an upstream action.
- Keep inherited Ableton/Bitwig code, `COPYING.MIT`, copyright notices and `docs/ROTO-CONTROL_*.pdf` references intact outside explicitly requested changes. Preserve fork-specific TouchDesigner work when incorporating upstream changes.
- Before edits or Git operations, inspect working-tree status. Preserve existing staged, unstaged and untracked work; use scoped patches rather than replacing whole directories or checking out files over local edits.
- Repository deletion (local checkout or GitHub), removal of `.git`, archival, transfer, visibility changes, remote removal/repointing and fork detachment require an explicit user instruction for that action. A cleanup, setup or upstream-sync request does not authorize them.
- Destructive Git operations require an explicit user instruction: force-push (including `--force-with-lease`), `reset --hard`, `clean -f` variants, history rewrites, or deleting branches/tags. Prefer a new branch/worktree and reversible edits.
- For upstream sync, fetch and review the diff first, then integrate on an isolated branch/worktree. Preserve fork commits and local work; replacing the fork with upstream is not a sync strategy.
- Preserve saved `.toe`/`.tox` snapshots, exports, verification evidence and user mappings during cleanup. Within an authorized TD save/export workflow, retain a recovery copy before replacing a canonical artifact and save/export through live TD.
- Honor authorization already given in the current task or session; it applies only to the requested action and scope. Verify the final diff stays within that scope and report any intentional changes to inherited files or preserved artifacts.

## Agent skills

### Issue tracker

For specs, tickets and issue operations, use GitHub Issues in `joshuahhn/roto_control`; read `docs/agents/issue-tracker.md`.

### Triage labels

For issue triage, use the five role labels defined in `docs/agents/triage-labels.md`.

### Domain docs

Before code exploration, follow the single-context glossary and ADR rules in `docs/agents/domain.md`.
