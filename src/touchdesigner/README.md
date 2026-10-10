# ROTO-CONTROL

A reusable TouchDesigner tool for freely mapping ROTO-CONTROL knobs and buttons to custom parameters or Python callbacks.

## Quick Start

1. Drag `exports/roto_python.tox` into the COMP containing your tools.
2. Verify Python has `mido` and `python-rtmidi`, check Device, and press Connect.
3. Put hardware in PLUGIN mode, open LEARN, select a knob/button, then change a compatible custom parameter in any sibling or nested tool.
4. After LEARNED, exit LEARN. Hardware changes update the target; target changes update hardware feedback.

Float/Int parameters use knobs. Toggle/Pulse parameters use buttons; hardware PUSH/TOGGLE is a separate setting and must match the Inspector Mapping section HW Type. Use PUSH for press/release Pulse feedback.

Connection **Open Inspector** opens the controller-owned Fold view (with its popup editor). The alternate new presentation shares the internal model; no root sibling UI or Palette Lister is required. Inspector displays all 16 slots, mapped COMP/parameter, values, ranges and button modes. It supports optional explicit assignment, Re-learn, edits and confirmed Clear/Clear Device. Disconnect retains records. Save the containing TD project to retain mappings after reopen. Mapped target COMPs receive a tag and color.

## Controls

Connect / Disconnect own the MIDI session. Device selects the exact port; Python selects the MIDI runtime. Binding has two workflows: **Parameter mapping** uses hardware LEARN and Inspector, with saved Layouts/Tracks; **Python registration** runs `registration.onRegister(controller)` to recreate parameter/callback integrations. Apply setup restores the selected workflow; ordinary LEARN does not need Apply. Inspector handles assignments, Re-learn and clearing. For Live Select, set each Device's Device Focus COMP on Layout and enable Follow selected COMP on Binding; selecting one linked COMP in the current Network Editor selects its Track and Device within Active Layout. Old Track links migrate to their Device; no mappings or groups are merged. Reopen waits for a new selection; Follow is off in generic exports.

The outer Control page has been removed. Use mapped target parameters or SetValue for value changes, and hardware LEARN/Inspector for learning. Offerparameter remains a Python method.

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

Use the Layout page for saved mapping sets and Track groups; use the separate Device page for the active COMP, Focus link and Device name. In PLUGIN mode, FUNC selects a Track group, hold SEL selects a Device inside it, and normal-view arrows change that Device's control page. Layout is selected in TD and its name stays independent of COMP selection. Each Track group contains independent Devices, each with up to eight pages of 8 knobs and 8 buttons. New / rename Layout is the draft for the Layout create/rename actions. Device Focus COMP links a tool and defaults its Device name to the COMP name; manual hardware names use at most 12 printable ASCII bytes. Delete actions open a popup, with no permanent confirmation buttons. Inspector shows the current Layout / Track / Device; Clear All affects its current control targets, while off-page definitions stay saved. Save the TD project to retain changes. See [Layouts, Tracks and Devices](docs/functions/layouts.md) for APIs, migration and acceptance.

Add the `roto_device` OP tag to a COMP under the controller's parent. While idle it appears as its own Device in Active Layout / Active Track; existing Focus links are reused. With Follow selected COMP on, select it before hardware LEARN, then edit its compatible custom parameter. Its mappings belong to that Device. Removing the tag retains saved mappings; explicit Device deletion remains available. Discovery waits during LOCK, LEARN, touch or pending routing and is unavailable in Python registration.
