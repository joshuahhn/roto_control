# TD → ROTO MIX contract v1

Status: data contract with [analysis and Layer Mix float slices](../functions/mix.md),
2026-10-17. The user requested three initial
styles after describing tool → selected item → detail controls. This is not an
complete three-style implementation or a new MIDI wire protocol. Hardware uses the
official protocol described in [MIX view mappings](mix-view-mappings.md).

## Three styles

| Style ID | Item | Writable controls when available | Read-only feedback |
| --- | --- | --- | --- |
| `layers` | A Layer Mix input/layer | `opacity`, `brightness`, `black_level`, `gamma`, `operation`, `swap` | Layer opacity |
| `analysis` | Low, Mid, High, Kick, Snare, Rhythm, or another explicitly assigned analyzer item | Available subset of `threshold`, `gain`, `add`, `smooth`, `active` | Explicit band level; optional actual trigger |
| `audio` | An audio file/input path | `gain`, `mute` | Audio level |

Support these styles directly. No custom style plug-in system, discovery registry
or arbitrary callback expressions are needed. Small source adapters produce the
same descriptor for existing TD operators/components; built-in TOPs and CHOPs
do not need an injected extension.

The user deferred audio refinement to [issue #26](https://github.com/joshuahhn/roto_control/issues/26).
Keep `audio` in the contract, but implement/verify analysis details first. Existing
audio metering acceptance does not mean Gain/Mute processing is installed.
The [audio adapter decision](mix-audio-adapter.md) records the later isolated
Gain/Mute stage experiment and the proposed first runtime slice. That prototype
does not enable audio routing in the controller.

## Common descriptor

All OP references resolve against one explicit existing COMP scope provided by
the caller. Use relative references within that scope and the existing parameter
binding/identity rules. A reference is data, never an expression to evaluate.
The exact persistence integration is implementation work, not a new path grammar.

| Field | Meaning |
| --- | --- |
| `version` | Integer `1`; reject unknown versions |
| `style` | Exactly `layers`, `analysis` or `audio` |
| `id` | Stable profile identity, independent of its display label |
| `source` | Explicit existing source OP reference within the caller's scope |
| `items` | Ordered item descriptions; the initial MIX overview has eight configured slots |
| Item `id`, `label` | Stable item identity and readable name |
| Item `input` | Required for `layers`: existing wired input OP reference within the scope, in source input order; absent for other styles |
| Item `primary` | Key of its overview control; `null` means no writable overview control |
| Item `controls` | Optional controls under the style's defined keys; each has `label`, `kind`, `target` and optional `range` |
| Control `kind` | `float`, `menu` or `toggle`, checked against the real TD parameter |
| Control `target` | `{op, parameter}` identifying an existing writable TD parameter |
| Control `range` | Explicit numeric override when needed; otherwise validated TD normalization metadata |
| Menu control `choices` | Required ordered list of 2..24 unique existing TD option names; explicit curation, not a first-N truncation |
| Item `meter` | Optional source, measurement, range and signal-stage description |
| Item `trigger` | Optional real trigger source, detection-enabled target and display hold |

Control labels and order come from the style; native Volume/Pan/Send addresses
are assigned by the MIX adapter. They are not descriptor field names. A primary
control and a detail control reference the same target. Do not persist target
values, connected state, touches, decoded MIDI pairs or active hardware views.

`float` is continuous. `menu` retains the complete TD menu identity, while an
explicit choice list limits what the controller can select. User-named Operation
presets contain two to six custom blend choices; unused editor slots stay None.
Legacy library API calls preserve their existing expanded lists. Values outside
the list are preserved and marked, without false motor
feedback. `toggle` represents the target's boolean state. Menu reordering or
parameter replacement must invalidate stale routing before a write. This does not
promise configurable MIX detents or native button behavior.

Read-only Level/trigger signals live in feedback fields, not `controls`. Missing
controls are unavailable, with no fallback to another parameter. An item without
a gain stage can expose a meter while clearly reporting that Gain/Mute are not
configured. It must not advertise working audio control.

The [Analysis integration API](../functions/mix_analysis.md) documents how a
different analyzer maps its own parameter/channel names into this contract,
including a tested example and complete analyzer inventory. Only the convenience
adapter uses the known Low/Mid/High/Kick/Snare/Rhythm names. Two optional GUI custom
slots use the same fields with explicit parameter/channel assignments, not a new
style or generic framework.

## Feedback fields

Meter `source` is either `{kind: 'parameter', op, parameter}` for a scalar such as
Opacity, or `{kind: 'chop', op, channels}` for named CHOP channels. `measure` is
`scalar` or `rms_dbfs`; `range` is independent of every knob range. Describe `stage`
explicitly, such as parameter readback, analysis output, before threshold or after
gain/mute. Do not infer a pre-threshold measurement from an output channel's name.
Mono may duplicate into the two native bars. Missing sources clear old bars.

An analysis meter may opt into `overview_reference: 'threshold'` for overview
and `focus_reference: 'threshold'` for first Focus. Each field is independent.
It requires an existing Float Threshold control and a mono scalar signal with
the same units. Both bars share the meter range; the actual threshold is not a
normalized motor position. CC65 carries Level and CC66 Threshold; on tested
firmware these are lower/upper horizontal bars. Each overview item uses the
same ordering in its own CC pair. Known Kick/Snare/Rhythm adapters opt into both
views; custom slots have one default-off toggle for both. Legacy data without
the corresponding view field stays unchanged. Missing feedback clears
both bars. No new timers, transport or target-value state is needed.

An optional trigger supplies an actual public CHOP output, its optional
detection-enabled target, and `hold_ms`, initially 200. The hold affects display
only. Disabled detection is distinct from a measured zero trigger. Native meter
yellow/red points remain global; they are not per-item threshold markers.
Analysis first Focus puts read-only trigger text on screen 5, without a Knob 5
target. Normal Tick observations feed bounded 10 Hz output; pulses missed between
observations cannot be recovered. Mode/view/selection/profile boundaries clear
the hold. This source/native slice still needs batched detector/custom-slot hardware acceptance.

## Example: Low analysis item

The caller supplies the containing demo COMP as scope. This illustrates references
only; loading the descriptor must not write parameters or connect hardware.

```json
{
  "version": 1,
  "style": "analysis",
  "id": "analysis.main",
  "source": "audioAnalysis",
  "items": [{
    "id": "low",
    "label": "Low",
    "primary": "threshold",
    "controls": {
      "threshold": {"label": "Threshold", "kind": "float", "target": {"op": "audioAnalysis", "parameter": "Lowthresh"}},
      "gain": {"label": "Gain", "kind": "float", "target": {"op": "audioAnalysis", "parameter": "Lowgain"}},
      "add": {"label": "Add", "kind": "float", "target": {"op": "audioAnalysis", "parameter": "Lowadd"}},
      "smooth": {"label": "Smooth", "kind": "float", "target": {"op": "audioAnalysis", "parameter": "Lowsmooth"}},
      "active": {"label": "Active", "kind": "toggle", "target": {"op": "audioAnalysis", "parameter": "Lowactive"}}
    },
    "meter": {
      "source": {"kind": "chop", "op": "audioAnalysis/out1", "channels": ["low"]},
      "measure": "scalar",
      "range": [0, 1],
      "stage": "analysis output"
    }
  }]
}
```

This meter example reads the processed public Low output. It does not claim to
show Low's threshold-comparison input; that use requires a verified source and
scale. Kick's already-tested pre-threshold source is a separate configuration.

## Source-specific limits

For Layer Mix, Setup can disable per-layer fields. Operation may be global;
Operation/Swap is per-layer only when intentionally configured that way. Do not
change these settings while describing or registering a source. Resolve actual
layer parameters and detect input/layer changes before routing a fresh gesture.

For analysis, each item exposes only its real parameters. The live Low/Mid/High
controls above were read back; Kick/Snare/Rhythm have Threshold/Active rather than those same
five fields. Reading a profile must not enable detection or audio output.

For audio, require an explicit existing Gain/Mute destination. The current file
source has Volume, while the current device-input source exposes no Gain/Mute
parameter. A shared downstream gain/mute stage is a possible later slice, not
an automatic side effect of registration. Mute retains Gain and does not stop
playback/capture. Gain is writable, Level is initially interpreted as metering.

## Routing and first proof

Touch selects the item, then FUNC opens its details. Merely selecting, loading,
reloading or changing a view makes zero business writes. Reuse the current MIDI
owner, parameter validation, session/epoch protections and fresh-touch/motor-echo
rules. MIX and PLUGIN retain separate business routing.

The bounded Low prototype passed user-observed `MIX-FOCUS / Low`, combined detail
name/value text for Threshold/Gain/Add/Smooth, and the public Low-output meter.
Only Gain input was enabled: the user reached 2.84093267411341, then software
restored 2.000 and the user confirmed its motor position, all four texts and meter.
Those prototype results did not establish other float input routes, multi-item
selection, long labels, menus or button behavior. The later production Low/Mid
slice adds overview Active toggles and leaves Focus buttons firmware-owned. An
isolated later Button 2 check receives no selection/CC, superseding the earlier
item-selector interpretation; see the [current contract](../functions/mix.md).
Mute/Swap and other
style buttons remain future work. Prototype evidence is not a production API.

The probe's original timeout cleanup prematurely published PLUGIN Track metadata,
producing native VOLUME/PAN/SEND A/SEND B and EFFECT while still in MIX Focus.
Deferring that metadata restoration until actual PLUGIN return fixed the test
method; a fresh read-only check and normal PLUGIN return passed. Do not carry the
prototype's bounded-stream lifecycle into normal continuous runtime feedback.
The shared descriptor, six known analysis items, two optional custom analysis
assignments and wired Layer Mix float adapters now
use the scoped checks described in the [view plan](mix-view-mappings.md). The
current runtime activates one source/style profile at a time. Operation libraries
and Swap now have source/native and scoped hardware acceptance;
mixed-style slots and audio processing remain planned.
