# Open this project

**[ROTO-CONTROL.toe](current/ROTO-CONTROL.toe)** is the current project to open.
It has the compact owned Inspector and the candidate tested with the physical
ROTO-CONTROL on 2026-10-11: Knob1→demo_A.Amount, Snapshot motor/LCD feedback,
Button8 Snapshot Recall, and Clear/reconnect. Button8 is now cleared; Amount0.6.

This is a saved working candidate; source changes have not been committed/merged.
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
