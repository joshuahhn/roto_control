# ROTO-CONTROL

A reusable TouchDesigner tool for freely mapping ROTO-CONTROL knobs and buttons to custom parameters or Python callbacks.

## Quick Start

1. Drag `exports/roto_python.tox` into the COMP containing your tools.
2. Verify Python has `mido` and `python-rtmidi`, check Device, and press Connect.
3. Put hardware in PLUGIN mode, open LEARN, select a knob/button, then change a compatible custom parameter in any sibling or nested tool.
4. After LEARNED, exit LEARN. Hardware changes update the target; target changes update hardware feedback.

Float/Int parameters use knobs. Toggle/Pulse parameters use buttons; hardware PUSH/TOGGLE is a separate setting and must match the Inspector Hardware column. Use PUSH for press/release Pulse feedback.

Inspector displays all 16 slots, mapped COMP/parameter, values, ranges and button modes. It supports optional explicit assignment, Re-learn, edits and confirmed Clear/Clear All. Disconnect retains records. Save the containing TD project to retain mappings after reopen. Mapped target COMPs receive a tag and color.

## Controls

Connect / Disconnect own the MIDI session. Device selects the exact port; Python selects the MIDI runtime. Inspector handles assignments, Re-learn and clearing. Advanced Binding controls and public methods support parameter/callback integrations.

## Inputs and Outputs

No external wires are required. Hardware input writes mapped custom parameters or invokes callbacks. Target edits send feedback to hardware. The portable component has no CHOP connectors; use the target parameters or controller.State.

## Portability

TD code, MIDI helper, Inspector and docs are embedded in the tox. No repository source files or demo COMPs are required. The only external runtime is a Python interpreter with the MIDI packages. On another computer select that computer's Python interpreter. The portable tool starts disconnected and has no demo mappings or outer CHOP outputs.

See [portability](docs/functions/portability.md), [Inspector](docs/functions/inspector.md), [control API](docs/functions/controls.md) and [binding API](docs/functions/binding.md). Diagnostics remain inside base_state and controller.State.

## Development

Python source and external builders in this folder are the source of truth. Create the environment with `python3 -m venv .venv` and `.venv/bin/python -m pip install -r requirements.txt`. build_network.py constructs the development component; export_component.py produces a clean embedded tox after Disconnect. Generic exports strip user assignments while project saves retain them.

Validation: `python3 -m unittest discover -q`. Hardware acceptance and live checks are recorded in HANDOFF.md and verification JSON files.


## Menu parameters

Custom Menu parameters support knobs (quantized option selection) and buttons (Cycle: advance and wrap on each press). Use hardware LEARN, select the destination, then change the menu. Inspector pickers support both kinds. PUSH ignores release/held duplicates; TOGGLE accepts each latched press. Menu ranges are fixed at indices 0..N-1, and SetValue uses those indices. State includes menu_names, menu_labels and value_label. LCD feedback uses the option label. Menu options must have 2..24 unique names and matching labels, following the official Ableton quantized-step limit. Changing names, labels or order suspends the binding; assign and re-learn it.

Hardware display names are configured on the Display page: Trackname (default EFFECT) and Pluginname (default CUSTOM). Each accepts at most 12 printable ASCII bytes. `SetLayoutNames(track_name, plugin_name)` updates display metadata while retaining stable mapping identity; exit hardware LEARN before edits. Use the Layouts page dropdown to switch saved mappings. Enter Layoutname and press New empty Layout to start another configuration (up to 8). Each Layout retains its own mappings and display names; save the TD project to persist changes. See docs/functions/layouts.md for API and limitations.
