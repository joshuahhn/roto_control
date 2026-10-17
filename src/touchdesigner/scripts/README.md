# External TouchDesigner scripts

Run builders inside live TD with an explicit source root (`src/touchdesigner`),
not the scripts folder. The builder finishes binding restoration before returning;
source text is copied into DATs without bidirectional source-file writes. `build_network.py` constructs a component;
`upgrade_layouts.py` upgrades a disconnected controller; `export_component.py`
exports a disconnected generic component. `midi_process.py` owns external MIDI.
`td_project_docs.py` embeds authoritative Markdown snapshots.

`upgrade_mix.py` installs only the independent Low/Mid MIX source slice on an
otherwise current disconnected controller. Make a recovery through live TD,
then call `install(controller, source)`; it preserves PLUGIN assignments and
does not rebuild Inspector or connect MIDI. See [MIX](../docs/functions/mix.md).

Example inside live TD:

```python
from pathlib import Path
source = Path('/absolute/path/to/src/touchdesigner')
script = source / 'scripts/build_network.py'
namespace = dict(globals())
exec(compile(script.read_text(), str(script), 'exec'), namespace)
namespace['build'](parent_comp, source)
```
