# Native inspector design studies

Two independent TD 2025.33230 prototypes:

- `inspector_below.tox`: an editor folds beneath the selected control.
- `inspector_popup.tox`: an editor opens beside the Inspector at matching width.

Both open at **240 × 390** content size (40% smaller in each dimension than the earlier 400 × 650). Layout uses actual window size, so resizing is retained without scaling field text. The header stays fixed; an event-driven Panel Execute handler translates captured mouse-wheel steps into the native scrollbar position, clamped at either end. The design uses neutral gray surfaces; Learn uses a subtle warm gray surface and explicit text. The Popup editor is 240 × 194 at the default Inspector width.

Pulse each component's `window_main` → Open as Separate Window. Context chips cycle through the demo Layout / Track / Device choices. Click a K/B row; edit Label, Target, Range or Value directly. Apply commits to that demo context and Cancel discards the draft. The two components keep independent state. Learn changes the surface to amber with a visible mode alert; no hardware command is sent.

State is ephemeral. These fixtures do not call the production controller extension, map real parameters, send MIDI or save the main project. Closing Popup with the OS close button keeps its selected draft; select another row or click the current row twice to reopen.

`build.py` is an external live-TD builder. Execute it with `prototype_name='inspector_below'` and `prototype_style='below'`, or `prototype_name='inspector_popup'` and `prototype_style='popup'`. Rebuilding replaces only that demo component's internals. `ui.py` is authoritative source; each export embeds it with its chosen initial presentation. Exports are saved through live TD and have no external source dependency. `inspector_demo.tox` is the earlier combined design.
