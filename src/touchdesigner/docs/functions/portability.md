# Portable ROTO-CONTROL tool

Load `exports/roto_python.tox` under the COMP containing the tools you want to map. Set the Python interpreter if needed, press Connect, then use hardware PLUGIN / LEARN: select a knob or button and edit a compatible custom parameter. No demo, registration table or Inspector assignment is required.

The tox embeds the controller code, Inspector, documentation and MIDI process source. DAT file sync/load paths are cleared. MIDI launches the embedded source in a separate Python process; it does not read midi_process.py from the repository. Moving or renaming the parent does not require changing those paths. Assignments use relative target paths and are retained by saving the containing TD project.

Python with mido and python-rtmidi is still required. The Python parameter preserves the configured interpreter on this machine. On another machine install those packages and select that machine's interpreter. Device is the exact MIDI input/output name. The disabled Helper parameter is retained for older component compatibility; the embedded helper takes precedence.

A generic export starts disconnected, without user targets, callbacks or mappings. It does not clear mappings on the physical hardware. Inspector shows all eight knobs and eight buttons, including empty slots. Advanced binding APIs remain available. Diagnostics are internal and accessible through controller.State. The portable version has no outer CHOP outputs; parameter targets and callbacks receive the actual values/events.

Run export_component.py in TD and call export(controller, a_new_tox_path) after Disconnect. It exports an isolated copy and never overwrites an existing destination. Development source edits require a deliberate new export.
