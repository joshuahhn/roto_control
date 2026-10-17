# Open this project

**[ROTO-CONTROL.toe](current/ROTO-CONTROL.toe)** is the current project to open.
It has the compact owned Inspector and the candidate tested with the physical
ROTO-CONTROL on 2026-10-11: Knob1→demo_A.Amount, Snapshot motor/LCD feedback,
Button8 Snapshot Recall, and Clear/reconnect. Button8 is now cleared; Amount0.6.

This description records the 2026-10-11 saved candidate. Check `current/project.json`
and dated HANDOFF save/export entries for artifact identity; source merges alone
do not update embedded DATs or prove a saved artifact matches the checkout.
Connect uses the existing external Python environment, with an embedded MIDI helper.

- `current/`: current working project and identity receipt.
- `archive/legacy/`: all former root .toe snapshots, including the old Lister
  roto_control_python.toe; these are historical, not the current Inspector.
- `archive/backups/`: previous TouchDesigner Backup snapshots, when present.
- `archive/organization-recovery/`: recovery copies made during organization.
- `components/inspector/`: historical Inspector .tox exports, when present.
- `../exports/`: existing generic controller exports.

Archive files retain their bytes. Source/venv links support old relative paths;
old snapshots may still contain historical absolute paths. JSON/JSONL captures live
in diagnostics, with a byte/hash relocation index at
[artifact_moves.json](../diagnostics/organization/artifact_moves.json).

If TouchDesigner creates numbered saves in current, the unnumbered ROTO-CONTROL.toe
is the named entry point; retain numbered copies as recovery history.

## Local organization history

Integration of local commit `1f735bd` preserves its additional project snapshots,
recovery copies and receipts. Its different unnumbered project/export are retained
byte-for-byte in [local-organization-1f735bd](archive/local-organization-1f735bd/).
They do not replace the canonical project or the current generic MIX export.

The saved #28 [MIX working snapshot](current/ROTO-CONTROL.mix-analysis.20.toe) has its
own [receipt](current/ROTO-CONTROL.mix-analysis.20.json). It contains #28 preset
direct activation, the restored original Low/Mid profile and four local control
definitions. TD's numbered save also updates `ROTO-CONTROL.mix-analysis.toe` to
the same bytes. This working snapshot and the generic export pin the uncommitted
source with 22 runtime/helper and 12 documentation hashes against baseline
`4ec8016`. The generic export is independently sanitized and reload-verified;
a full project restart is not newly accepted.

The earlier [.18 snapshot](current/ROTO-CONTROL.mix-analysis.18.toe) and its
[receipt](current/ROTO-CONTROL.mix-analysis.18.json), identifying saved runtime
`7a99f31`, remain unchanged. The unnumbered canonical `ROTO-CONTROL.toe` and
`project.json` also retain their separate older identity.

## Serial read-back working snapshot

The first Serial working copy is [ROTO-CONTROL.serial-readback.1.toe](current/ROTO-CONTROL.serial-readback.1.toe),
with its [receipt](current/ROTO-CONTROL.serial-readback.1.json). TD also saves the
same bytes to `ROTO-CONTROL.serial-readback.toe`. It retains the original four
definitions and Analysis Low/Mid profile, adds the optional read-only Serial API,
and embeds 24 runtime/helper and 13 documentation hashes. It starts disconnected
with no stored Serial observation. Configured tox reload and generic export
reload pass; a full project restart is not newly accepted.

The #28 `.20` project, its alias and receipt remain unchanged. The generic export
now distributes this Serial slice independently of the older canonical project.
Source is uncommitted against `4ec8016`; exact file hashes in the receipts identify
the saved code. See HANDOFF for source, native and physical evidence scopes.

The latest working copy is [ROTO-CONTROL.serial-replug.1.toe](current/ROTO-CONTROL.serial-replug.1.toe),
with its [receipt](current/ROTO-CONTROL.serial-replug.1.json) and identical
`ROTO-CONTROL.serial-replug.toe` alias. It adds the empty-USB-inventory diagnostic
fix and disconnected physical unplug/replug acceptance. The same unit returns
under a new USB incarnation, and all four stored control records remain equal.
The source suite passes 659 tests. Configured and generic tox reloads match
24 runtime/helper and 13 docs hashes. The earlier Serial `.1`, its alias and
receipt remain unchanged. Full project restart and in-flight unplug are separate
unaccepted cases.

The latest working copy is [ROTO-CONTROL.recall-fixed.1.toe](current/ROTO-CONTROL.recall-fixed.1.toe),
with its [receipt](current/ROTO-CONTROL.recall-fixed.1.json) and identical
`ROTO-CONTROL.recall-fixed.toe` alias. It fixes ordinary MIDI reconnect dropping
the Enabled Toggle mapping. All four demo controls map without re-LEARN or value
changes. The source suite passes 662 tests; configured and generic tox reloads
match 24 runtime/helper and 13 document hashes. Earlier Serial snapshots remain
unchanged. `ROTO-CONTROL.button-recall.1.toe` is the retained preliminary candidate,
superseded by the normalized-choice fix after independent review.

## Serial Inspector working snapshot

The [Serial Inspector snapshot](current/ROTO-CONTROL.serial-inspector.1.toe),
its identical unnumbered alias and [receipt](current/ROTO-CONTROL.serial-inspector.1.json)
add explicit read-only Serial Details. The original four controls, Analysis
Low/Mid profile, values, user storage and 4,629 existing node IDs are preserved.
Configured/generic component reloads verify 30 runtime source hashes, including
the affected owned Inspector DATs, and 13 document hashes. Source discovery passes
681 tests. Real GET reads preserve all four stored records; TD stays open and
disconnected. Full project restart is explicitly skipped this round. Previous
projects and receipts retain their bytes; the generic export is refreshed.
