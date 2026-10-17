# Generic controller export

Use [roto_python.tox](roto_python.tox) for the reusable controller. Its adjacent
[receipt](roto_python.json) records the artifact SHA-256, source commit,
embedded runtime/documentation hashes and scoped native validation.

The current export includes main-screen parameter-page hints, explicit LEARN
metadata, an 83-entry Track color menu and a read-only Track BG preview.
It also includes independent Low/Mid/High/Kick/Snare/Rhythm analysis and wired Layer Mix float controls,
user-named Operation presets with two to six choices and conditional Swap,
analysis overview Active buttons, motor feedback and native meters. Two optional
custom analysis slots assign another analyzer's parameter names and CHOP feedback
through the same Apply. Detectors use independent pre-threshold meters and actual
read-only trigger feedback; their new hardware acceptance is pending. The
overview keeps the selected analysis band name/value visible after release,
without resending unchanged motor positions when selecting another band. One MIX
source/style profile is active at a time. Configure existing sources through the
[MIX draft/Apply page or Python APIs](../docs/functions/mix.md); no analysis/audio graph is constructed.
Track colors default to palette 0. Palette 47 preview is unavailable pending
[issue #24](https://github.com/joshuahhn/roto_control/issues/24).
It starts disconnected, with Follow off and no user mappings, Focus or
ownership links, Snapshot records, MIX assignments, user Operation presets or draft source paths. Python defaults to `python3`; a Python
interpreter with `mido` and `python-rtmidi` remains required. Runtime DATs, the
MIDI helper, owned Inspector and documentation are embedded.

The demo `.toe` has its own [project receipt](../projects/current/project.json).
Check that receipt separately for its saved runtime version. Numbered exports
remain historical recovery copies; use the unnumbered tox and adjacent receipt.
