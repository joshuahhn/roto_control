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

The latest [MIX working snapshot](current/ROTO-CONTROL.mix-analysis.20.toe) has its
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
