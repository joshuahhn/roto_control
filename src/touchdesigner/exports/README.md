# Generic controller export

Use [roto_python.tox](roto_python.tox) for the reusable controller. Its adjacent
[receipt](roto_python.json) records the artifact SHA-256, source commit,
embedded runtime/documentation hashes and scoped native validation.

The current export includes main-screen parameter-page hints, explicit LEARN
metadata, an 83-entry Track color menu and a read-only Track BG preview.
Track colors default to palette 0. Palette 47 preview is unavailable pending
[issue #24](https://github.com/joshuahhn/roto_control/issues/24).
It starts disconnected, with Follow off and no user mappings, Focus or
ownership links, or Snapshot records. Python defaults to `python3`; a Python
interpreter with `mido` and `python-rtmidi` remains required. Runtime DATs, the
MIDI helper, owned Inspector and documentation are embedded.

The demo `.toe` has its own [project receipt](../projects/current/project.json).
Check that receipt separately for its saved runtime version. Numbered exports
remain historical recovery copies; use the unnumbered tox and adjacent receipt.
