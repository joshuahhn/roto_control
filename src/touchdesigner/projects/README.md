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

The later [MIX working snapshot](current/ROTO-CONTROL.mix-analysis.18.toe) has its
own [receipt](current/ROTO-CONTROL.mix-analysis.18.json). It identifies saved
runtime `7a99f31`; the generic export separately pins `dbd341c`. These saved
versions differ from both the checkout and the unsaved live TD state. Integration
does not reload, save or modify that live project.
