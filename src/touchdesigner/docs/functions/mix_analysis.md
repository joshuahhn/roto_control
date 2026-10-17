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
ordered subset such as `bands=('Low', 'Mid', 'High', 'Kick', 'Snare', 'Rhythm')`;
the Python call's default remains Low/Mid for existing callers.
The MIX page's Analysis bands field uses the same adapter and accepts names
separated by spaces or commas. Kick exposes only `Kickthresh` and `Kickactive`.
Its meter reads the verified pre-threshold `math2['low']`, and its actual trigger
reads `out1['kick']`. Snare uses `Snarethresh` / `Snareactive`, pre-threshold
`math16['high']` over 0..1 and actual `out1['snare']`. Rhythm uses the source's
`Rythmthresh` / `Rythmactive`, `math10['chan0']` before the threshold clamp over
0..100, and actual `out1['rythm']`. Rhythm's knob range is the real parameter's
10..90, independent of that meter range. These paths/scales were inspected in the
existing COMP; the adapter requires them and does not construct them.

New/generic GUI drafts default to all six in that order. Existing saved drafts
and applied profiles are preserved on upgrade. Other analyzers use the explicit
custom slot fields or descriptor API; the picker does not infer their parameter
names, ranges or signal stage.

## Existing audioAnalysis inventory

The inspected local COMP has 24 analysis controls across nine items, plus nine
read-only Analysis Data outputs. This is an inventory, not a claim that all nine
items are implemented by the convenience adapter.

| Item | Writable parameters | Public `out1` feedback | Convenience adapter |
| --- | --- | --- | --- |
| Low | `Lowthresh`, `Lowgain`, `Lowadd`, `Lowsmooth`, `Lowactive` | `low` | Yes |
| Mid | `Midthresh`, `Midgain`, `Midadd`, `Midsmooth`, `Midactive` | `mid` | Yes |
| High | `Highthresh`, `Highgain`, `Highadd`, `Highsmooth`, `Highactive` | `high` | Yes |
| Kick | `Kickthresh`, `Kickactive` | `kick`, actual detection | Yes; separate pre-threshold meter |
| Snare | `Snarethresh`, `Snareactive` | `snare`, actual detection | Yes; separate pre-threshold meter |
| Rhythm | `Rythmthresh`, `Rythmactive` | `rythm`, actual detection | Yes; separate pre-threshold score |
| Slow spectral density | `Ssdactive` | `smsd` | Not yet |
| Fast spectral density | `Fsdactive` | `fmsd` | Not yet |
| Spectral centroid | `Scactive` | `spectralCentroid` | Not yet |

Keep the source's actual `Rythm` spelling in parameter references. Spectral
feedback scales still need source-specific verification before assigning them.
Nine items exceed this slice's single
eight-item profile; no second item bank is implemented.

Other existing parameters are `Audioout` and `Listenvolume` for audio monitoring,
`Galmap` for Enable Mapper, and five Neutone controls: `Neutoneactive`,
`Neutonebass`, `Neutonedrums`, `Neutonevocals`, `Neutoneother`. They are outside the
current analysis mapping. Their existence does not verify a Neutone plugin or
authorize enabling audio/processing. About/Help metadata needs no MIX target.

For this known adapter, assign the source COMP and ordered item names; it fills
the known control and feedback references. For another analyzer, explicitly
assign its control targets, meter sources/units/stages, and optional actual
trigger sources. Read-only feedback is not a writable parameter mapping.

## Custom slots 7 and 8

The controller's `MIX Slot 7` and `MIX Slot 8` custom parameter pages are staged
assignments for another analyzer, using the same analysis controls. They share
the existing MIX page's Apply; there is no extra Apply button. Names do not
define new controls or a new protocol.

| Draft field | Assignment |
| --- | --- |
| Item name | User label; blank disables the slot while retaining its draft |
| Analyzer COMP | Existing component owning the assigned control parameters |
| Overview control | Explicit Threshold/Gain/Add/Smooth target, or Read-only |
| Threshold/Gain/Add/Smooth parameter | Exact existing Float name; blank omits it |
| Active parameter | Exact existing writable Toggle name; blank omits it |
| Meter CHOP / channel names | Existing CHOP and one or two named channels |
| Meter measurement / minimum / maximum / stage | Scalar or audio RMS dBFS, actual source units and signal location |
| Threshold comparison | Optional, off by default; mono scalar Level and the assigned Float Threshold must share units |
| Actual trigger CHOP / channel name | Optional real pulse output; display hold is 200 ms |

Assign only fields that exist. Controls use validated native parameter ranges;
feedback units/ranges are independent. If Active is assigned, it also supplies
the trigger's enabled state. Otherwise the trigger is observed without an enabled
flag. The descriptor API additionally supports a separate read-only enabled flag
or parameter-valued meter/trigger. Blank feedback CHOPs leave feedback unassigned.
The comparison toggle is draft-only and uses the existing Apply. Stereo/RMS or
missing Threshold assignments are rejected when it is on.

Apply resolves controls and feedback against their common existing COMP ancestor,
including sources in different networks. Stored descriptor references remain
relative and cannot escape that explicit scope. Invalid types, missing parameters,
channels, ranges or signal stages keep the previous profile. Assignment, save and
reload make no target writes and do not enable detection or connect hardware.

Custom item IDs are stable `custom.7` / `custom.8`, independent of their labels.
Slots remain physically 7 and 8 even if fewer known bands are selected or Slot 7
is blank; intervening positions stay unassigned. Configured saves retain draft
and applied data separately; generic export clears every custom name/reference
and restores empty custom slots. Mixed Layer/audio controls are not accepted.

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
name/value captions show the actual target. Float captions shorten the label
first to preserve a three-decimal value within 12 characters, such as
`Thres 49.459`. This affects display only. In the analysis overview, the selected
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
  Use one or two actual channel names. One channel fills both native bars unless
  the explicit threshold comparison below is enabled for that view.
- Parameter source: `{'kind': 'parameter', 'op': '.', 'parameter': 'Outputlevel'}`.
  A numeric read-only/expression-driven parameter can be feedback; it is never
  written by the meter. Use `measure='scalar'`.
- `scalar` reads each CHOP channel's sample 0 or the parameter's evaluated value.
  Use it for an already calculated envelope/RMS/energy output.
- `rms_dbfs` calculates RMS over each CHOP channel's available sample buffer,
  then `20 * log10(RMS)`. Use it for audio samples, with a dB range such as
  `[-60, 0]`. Do not apply it again to an already calculated level.
- `range` maps source units to the bars and clips outside values. It is
  independent of every control range. `stage` must describe the actual signal
  location. Yellow/red meter thresholds remain global MIX settings.

Feedback is coalesced at 10 Hz. Missing/replaced sources, removed channels and
nonfinite samples clear bars. A level bar is not a trigger/threshold-crossing
guarantee.

## Trigger contract

An analysis item may supply `trigger` independently of its meter and controls.
For the example above, add an existing `levels['pulse']` output from the actual
detector, then register the descriptor again:

```python
descriptor['items'][0]['trigger'] = {
    'source': {'kind': 'chop', 'op': 'levels', 'channels': ['pulse']},
    'enabled': {'op': '.', 'parameter': 'Enabled'},
    'hold_ms': 200,
}
controller.SetMixProfile(scope, descriptor)
```

`source` accepts the same scalar parameter/named CHOP references as meters. Any
positive evaluated sample means detected. Supply a real detector output, not a
comparison invented from the displayed level and knob threshold. `enabled` is
optional and references an existing Toggle; read-only/expression-driven Toggles
are accepted for feedback. This field never writes or enables detection.

`hold_ms` is an integer from 0 to 1000. An observed positive sample stays visible
for that duration after its latest observation. The runtime observes on normal
TD Ticks and publishes at 10 Hz; it cannot guarantee pulses shorter than the
sampling interval. Backlogged observations are skipped, not replayed. Mode,
view, selection and profile changes clear the display hold.

In first FUNC Focus, screen 5 displays `Trig Off` for disabled detection,
`Trig 0` for idle, `Trig 1` for an observed/held detection, and `Trig ?` for
unknown or unavailable feedback. Missing/replaced sources, removed channels and
nonfinite/empty samples clear stale detections and report an error. Screen 5 is
read-only; Knob 5 has no target. Focus knobs 1–4 retain any real controls, so
Kick/Snare/Rhythm use Knob 1 only. Native headings remain firmware UI. Unassigned
Pan/Send positions can retain those native headings; no TD target is implied.
Kick/Snare/Rhythm Active, actual trigger, Threshold input and motor return have
scoped hardware acceptance. Custom slots and unassigned-knob input still need
the [batched physical check](../plans/mix-analysis-acceptance.md).

## Threshold comparison

An analysis item's meter may declare `overview_reference: 'threshold'` and/or
`focus_reference: 'threshold'`. Each optional field enables the comparison only
in its named view and references the item's existing Float `controls.threshold`.
It does not create another target. It requires `measure: 'scalar'` with one CHOP
channel or a scalar parameter source. Caller-supplied level and threshold must
have the same units and a verified signal stage. Stereo and RMS comparisons,
other control keys and missing/non-Float Threshold targets are rejected.

Each overview screen uses its normal CC pair for the measured level followed
by the actual current threshold. First Focus uses screen 1, CC65/66. Both
values are scaled/clipped by the meter's single `range`.
The reference reads target units directly after the existing identity/mode/range
check; it does not use the normalized motor position or coerce the target value.
The tested firmware 3.3.0 renders these as a lower Level and upper Threshold
horizontal bar, both extending left to right. API Left/Right names describe
channels, not physical screen orientation. Colors remain the common firmware
green/yellow/red rules, not per-data-source colors. Actual trigger feedback
still comes from the detector, independently of the comparison.

After verifying the example analyzer's `band_energy` and Triggerlimit units,
set the meter's `overview_reference` and `focus_reference` to `'threshold'`,
then register through the same `controller.SetMixProfile(scope, descriptor)`
call. Custom slots expose both through one optional Threshold comparison toggle.

The known Kick/Snare/Rhythm adapter supplies both fields automatically for its
verified pre-threshold sources. Low/Mid/High do not: their processed outputs are
not assumed to be threshold-comparison inputs. Invalid level/reference feedback
clears both bars. Existing coalescing, in-flight tails and backlog guards apply, without
extra observers or timers. Old saved profiles without either field retain their
original meter behavior. Existing Focus-only profiles keep their original
overview; explicitly reconfigure to adopt the new adapter data.
No detection, audio or target values change merely from configuration/reload.

The earlier bounded Kick prototype established the physical rendering and was
accepted at 0.490. The installed production Focus display has since passed its
scoped hardware check. Overview, first-Focus transition and normal PLUGIN
return then passed together without parameter writes.

## Lifecycle and diagnostics

`SetMixProfile` saves plain descriptor data and the relative scope, replacing
one active MIX profile only. It does not connect, learn controls, recall target
values or modify PLUGIN Layout/Track/Device assignments. Configuration requires
released knobs, exit from LEARN and no parameter dispatch. Loaded configuration
rebuilds target references without applying saved values. It is independent of
the MIX page's uncommitted draft.

`GetMixProfile()` returns a detached saved record. `GetMixState()` reports
`active`, `ready`, `view`, `selected`, `epoch`, changed `writes`, profile `error`
and per-control `controls` errors. `triggers` lists each trigger's item index,
state and error; disconnected/reloaded triggers start unknown until observed.
A valid descriptor can retain unavailable
individual targets; inspect those errors after registration. Structural/source
configuration errors raise `ValueError` before replacing the previous profile.
`ready=False` while disconnected is expected, not proof that registration failed.

Parameter replacement, type/range/menu/mode changes and stale input suspend the
affected routes; release and explicitly reconfigure after changing the target
contract. One profile has at most eight ordered items, with first FUNC Focus
only. General Float step sizes, mixed styles, audio Gain/Mute and additional
item banks remain outside this API slice. See the full
[descriptor contract](../plans/mix-style-contract.md) and
[MIX behavior](mix.md) for the remaining guards and accepted hardware scope.
