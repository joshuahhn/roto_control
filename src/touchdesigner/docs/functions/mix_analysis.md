# Analysis integration API

Use `SetMixProfile(scope, descriptor)` to control an existing analyzer with
different parameter/channel names. The `analysis` descriptor below is a TD-side
data contract, version 1. The controller translates it to the existing official
[MIX SysEx/CC protocol](../../../../docs/ROTO-CONTROL_SYSEX_API_v1.6.pdf), chapter 4
and Appendix B. An analyzer does not need to implement MIDI or SysEx itself.

`ConfigureMixAnalysis(scope, source='audioAnalysis', bands=('Low', 'Mid'))` is a
convenience adapter for our known audioAnalysis COMP. It expects `Lowthresh`,
`Lowgain`, `Lowadd`, `Lowsmooth`, `Lowactive`, their Mid/High equivalents, and
`out1['low']` / `out1['mid']` / `out1['high']` for the selected bands. Pass an
ordered subset such as `bands=('High', 'Low')`; the default remains Low/Mid.
The MIX page's Analysis bands field uses the same adapter and accepts names
separated by spaces or commas. Kick is not accepted by this adapter yet.
The MIX page's Analysis source picker uses this
adapter. Other analyzers use the descriptor API; the picker does not infer their
parameter names, ranges or signal stage.

## Control contract

An analysis item represents one band/detector. Choose a stable item `id` and
readable `label`; supply only the controls it actually has. Parameter names can
be anything. The control keys below determine the hardware position.

| Key | Required target type | MIX overview | First FUNC Focus |
| --- | --- | --- | --- |
| `threshold` | Writable Float | Native Level, if chosen as `primary` | Knob 1 |
| `gain` | Writable Float | Native Pan | Knob 2 |
| `add` | Writable Float | Native Send A | Knob 3 |
| `smooth` | Writable Float | Native Send B | Knob 4 |
| `active` | Writable Toggle | Item's button in native On/Off bank | Buttons still select items |

Set `primary` to an available Float key to choose the overview Level target,
or `None` for no overview control. Missing controls leave their positions empty;
they do not shift later controls or use a PLUGIN assignment. Analysis Menu,
Pulse, callback/expression strings and arbitrary extra control keys are not
supported. The native Volume/Pan/Send headings remain firmware UI; combined TD
name/value captions show the actual target. In the analysis overview, the selected
item instead keeps its band name/value with a `>` marker until selection changes.
FUNC details retain their control captions.

Float controls default to the target's `normMin`/`normMax`. An optional `range`
overrides these in target units, with finite increasing limits compatible with
the target's clamps. Toggle range is 0..1. Targets must satisfy the existing
[Binding rules](binding.md), including writable CONSTANT or supported BIND
chains. This integration does not replace expressions, exports or bind masters.

## Minimal example for another analyzer

Assume your existing `my_analyzer` COMP already has writable Float
`Triggerlimit` and Toggle `Enabled`, plus a public CHOP `levels` with channel
`band_energy`. Their names deliberately differ from audioAnalysis. This example
does not construct those operators or change their settings.

```python
controller = op('roto_python')
scope = op('my_analyzer')

descriptor = {
    'version': 1,
    'style': 'analysis',
    'id': 'my-analysis.main',
    'source': '.',
    'items': [{
        'id': 'band-a',
        'label': 'Band A',
        'primary': 'threshold',
        'controls': {
            'threshold': {
                'label': 'Limit',
                'kind': 'float',
                'target': {'op': '.', 'parameter': 'Triggerlimit'},
                'range': [0, 0.6],
            },
            'active': {
                'label': 'Enabled',
                'kind': 'toggle',
                'target': {'op': '.', 'parameter': 'Enabled'},
            },
        },
        'meter': {
            'source': {
                'kind': 'chop', 'op': 'levels',
                'channels': ['band_energy'],
            },
            'measure': 'scalar',
            'range': [0, 1],
            'stage': 'analyzer band energy before threshold',
        },
    }],
}

# Release knobs and exit LEARN before replacing MIX configuration.
controller.SetMixProfile(scope, descriptor)
print(controller.GetMixState())
```

Choose the example range and `stage` only after checking your analyzer. An output
named `level` is not necessarily before threshold. Here the first knob controls
Triggerlimit, the overview button controls Enabled and the meter reads
band_energy independently. There is no required Low/Mid naming and no automatic
detection/audio enabling.

All `op` references, including `source`, resolve within the explicit existing
COMP `scope`. `.` references the scope itself; descendants use paths such as
`filters/band1`. Absolute paths, `..` and Python expressions are not accepted in
the descriptor. Place the scope at their common ancestor if controls and meters
live in separate descendants. The saved scope is controller-relative; callers
pass a real COMP handle. Keep profile/item IDs stable and independent of paths.

## Meter contract

A meter is read-only feedback and does not require a writable control:

- CHOP source: `{'kind': 'chop', 'op': 'levels', 'channels': ['left', 'right']}`.
  Use one or two actual channel names. One channel fills both native bars.
- Parameter source: `{'kind': 'parameter', 'op': '.', 'parameter': 'Outputlevel'}`.
  A numeric read-only/expression-driven parameter can be feedback; it is never
  written by the meter. Use `measure='scalar'`.
- `scalar` reads each CHOP channel's sample 0 or the parameter's evaluated value.
  Use it for an already calculated envelope/RMS/energy output.
- `rms_dbfs` calculates RMS over each CHOP channel's available sample buffer,
  then `20 * log10(RMS)`. Use it for audio samples, with a dB range such as
  `[-60, 0]`. Do not apply it again to an already calculated level.
- `range` maps source units to bar height and clips outside values. It is
  independent of every control range. `stage` must describe the actual signal
  location. Yellow/red meter thresholds remain global MIX settings.

Feedback is coalesced at 10 Hz. Missing/replaced sources, removed channels and
nonfinite samples clear bars. Trigger indicators are not enabled in the current
runtime: a descriptor containing `trigger` is rejected even though the planning
contract describes it. A level bar is not a trigger/threshold-crossing guarantee.

## Lifecycle and diagnostics

`SetMixProfile` saves plain descriptor data and the relative scope, replacing
one active MIX profile only. It does not connect, learn controls, recall target
values or modify PLUGIN Layout/Track/Device assignments. Configuration requires
released knobs, exit from LEARN and no parameter dispatch. Loaded configuration
rebuilds target references without applying saved values. It is independent of
the MIX page's uncommitted draft.

`GetMixProfile()` returns a detached saved record. `GetMixState()` reports
`active`, `ready`, `view`, `selected`, `epoch`, changed `writes`, profile `error`
and per-control `controls` errors. A valid descriptor can retain unavailable
individual targets; inspect those errors after registration. Structural/source
configuration errors raise `ValueError` before replacing the previous profile.
`ready=False` while disconnected is expected, not proof that registration failed.

Parameter replacement, type/range/menu/mode changes and stale input suspend the
affected routes; release and explicitly reconfigure after changing the target
contract. One profile has at most eight ordered items, with first FUNC Focus
only. General Float step sizes, mixed styles, audio Gain/Mute and trigger
indicators remain outside this API slice. See the full
[descriptor contract](../plans/mix-style-contract.md) and
[MIX behavior](mix.md) for the remaining guards and accepted hardware scope.
