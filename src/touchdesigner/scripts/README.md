# External TouchDesigner scripts

Run builders inside live TD with an explicit source root (`src/touchdesigner`),
not the scripts folder. The builder finishes binding restoration before returning;
source text is copied into DATs without bidirectional source-file writes. `../build/build_network.py` constructs a component;
`../upgrade/upgrade_layouts.py` upgrades a disconnected controller; `export_component.py`
exports a disconnected generic component. `midi_process.py` owns external MIDI.
`td_project_docs.py` embeds authoritative Markdown snapshots.

`serial_read_process.py` owns the optional read-only Serial job. It is embedded
beside the controller and launched only by `ReadHardwareConfig(port=...)`.
`../upgrade/upgrade_serial.py` provides `install(controller, source_dir)` for an
otherwise current disconnected controller. Retain a recovery tox first. The
upgrader preserves mappings and settings and never connects hardware. See
[Serial read-back](../docs/functions/serial.md) for the supported platform,
page, status, and timeout recovery contract.

`../upgrade/upgrade_mix.py` installs the independent MIX source on an
otherwise current disconnected controller. Make a recovery through live TD,
then call `install(controller, source)`; it preserves PLUGIN assignments and
does not rebuild Inspector or connect MIDI. See [MIX](../docs/functions/mix.md).

Example inside live TD:

```python
from pathlib import Path
source = Path('/absolute/path/to/src/touchdesigner')
script = source / 'build/build_network.py'
namespace = dict(globals())
exec(compile(script.read_text(), str(script), 'exec'), namespace)
namespace['build'](parent_comp, source)
```
