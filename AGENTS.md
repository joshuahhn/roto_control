# ROTO-CONTROL development

- Reply in Cantonese with English technical terms.
- TouchDesigner work lives in src/touchdesigner. Read its CONTEXT.md and HANDOFF.md; preserve upstream Ableton/Bitwig code unless requested.
- Use external Python builders and source files. Never edit toe/tox binaries directly; save/export through live TD.
- Load td-general and relevant TD skills before live TD changes. Verify the active project first.
- Source Markdown is authoritative; scripts/td_project_docs.py embeds snapshots.
- Generic tox exports are disconnected and have no user mappings. MIDI helper and DAT source are embedded; Python with mido/python-rtmidi remains external.
- Run python3 -m unittest discover -q from src/touchdesigner for runtime source changes. Run git diff --check; never weaken checks.
- Do not commit or push without user instructions.
