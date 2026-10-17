# Portable ROTO-CONTROL tool

Load `exports/roto_python.tox` under the COMP containing the tools you want to map. Set the Python interpreter if needed, press Connect, then use hardware PLUGIN / LEARN: select a knob or button and edit a compatible custom parameter. No demo, registration table or Inspector assignment is required.

The tox embeds the controller code, Inspector, documentation and MIDI process source. DAT file sync/load paths are cleared. MIDI launches the embedded source in a separate Python process; it does not read scripts/midi_process.py from the repository. Moving or renaming the parent does not require changing those paths. Assignments use relative target paths and are retained by saving the containing TD project.

The [optional Serial reader](serial.md) and its worker source are also embedded.
Serial reads require an explicit endpoint and use the selected Python interpreter.
The macOS backend uses the Python standard library. No repository checkout or
old Serial plugin is required. Captures, endpoint selections, and child processes
are transient and are not included in a generic export.

Python with mido and python-rtmidi is still required. Generic exports default the Python parameter to `python3`, resolved through TouchDesigner's PATH. A project can instead use a relative venv path such as `.venv/bin/python` (relative to the containing .toe folder), or select an interpreter explicitly. Venv symlinks are retained. Device is the exact MIDI input/output name. The disabled Helper parameter is retained for older component compatibility; the embedded helper takes precedence.

Connect starts the MIDI process; handshake and input polling run while the TD timeline is playing. If the status stays at Opening MIDI ports with a paused timeline, press Play. Disconnect closes the process even while paused.

Before exporting an older saved COMP with the current exporter, Disconnect and upgrade its runtime through the external builder/upgrade workflow, retaining a recovery copy. The exporter requires runtime support for PATH commands and reports an upgrade requirement when that support is absent; it does not upgrade the source COMP itself. A newer exporter alone cannot make an older embedded runtime understand `python3`.

A generic export starts disconnected, with Follow off and no Focus links, user targets, callbacks or mappings. It does not clear mappings on the physical hardware. Inspector shows all eight knobs and eight buttons, including empty slots. Advanced binding APIs remain available. Diagnostics are internal and accessible through controller.State. The portable version has no outer CHOP outputs; parameter targets and callbacks receive the actual values/events.

Run scripts/export_component.py in TD and call export(controller, a_new_tox_path) after Disconnect. It exports an isolated copy and never overwrites an existing destination. Development source edits require a deliberate new export.

The model and both compact Inspector presentations are nested inside the exported
controller. Relative Controller/Model parameters resolve the loaded instance,
including renamed/moved copies; no external model or view shortcut is required.
Open Inspector is an explicit Pulse, never a startup side effect. Export strips
nested UI drafts/caches/subscribers and target readouts along with user mappings.
The old Palette Lister is not included in active owned builds/exports.
