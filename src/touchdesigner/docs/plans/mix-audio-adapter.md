# MIX audio adapter decision

Status: isolated native prototype, 2026-10-18. This records the first design
slice of [issue #26](https://github.com/joshuahhn/roto_control/issues/26).
Production audio routing remains unimplemented.

Deferred at the user's explicit request later on 2026-10-18. Findings are saved
in [issue #26](https://github.com/joshuahhn/roto_control/issues/26#issuecomment-6237791526).
Resume only after a later user request; the first production slice below is a
future proposal.

## Keep Gain and Mute separate

An audio item needs an existing Float Gain target, a separate Toggle Mute target
and an explicit Level source. Gain is the retained setting. Mute changes the
effective output without replacing Gain or stopping playback or capture.

The recommended supplied stage has one native Math CHOP multiplying its input
by `0 if Mute else Gain`, followed by a named Null CHOP. Level reads that output
with `rms_dbfs`, independently of the Gain knob range. This is a small optional
stage that a user inserts and wires explicitly. Configuring MIX only describes
existing targets and signals; it does not insert the stage or reroute audio.

An existing component with equivalent public Gain and Mute parameters can serve
the same descriptor. It does not need another processing stage. The adapter
must not infer Mute from a source's playback or capture toggle.

## Why not control source Volume alone

Native readback of the current project confirms that `audiofilein1` exposes
Volume, while `audiodevin1` is an `audiodeviceinCHOP` with Active and no
Gain or Mute parameter. Their existing meter Null CHOPs are directly downstream.
Those sources and wires remain unchanged throughout the experiment.

Two variants share a switcher in the throwaway fixture. The first drives a
temporary Audio File In's Volume from retained Gain and Mute parameters. The
second keeps file Volume at 1 and applies Gain and Mute in a downstream Math
CHOP. A separate input selector chooses the stereo file or a deterministic
mono fixture. The Volume variant works for the file but has no destination for
the mono path. Its output stays at 0.25 even when Mute is true. The downstream
variant controls both paths through the same stage.

## Native observations

TD 2025.33230 runs 20 cases: two variants, two input forms and five ordered
states. Those states are unity, half Gain, Mute, editing Gain to 1.5 while
muted, then unmute. Each sample follows a native frame boundary after the
parameter change. The fixture has no audio output device or MIDI connection.

The temporary 48 kHz stereo WAV contains constant samples 0.25 and 0.125.
Its cooked blocks contain 800 samples per channel. These deliberately fixed
samples make Gain scaling observable without source-level variation. They are
not measurements of the user's file or microphone.

With the downstream stage, half Gain produces 0.125 and 0.0625. Mute produces
zero samples while Gain remains 0.5. Changing Gain to 1.5 while muted keeps
the output at zero. Unmute produces 0.375 and 0.1875. File Volume remains 1
and Play remains true. The mono fixture follows the same ratios.

The existing `Signal.sample('rms_dbfs')` reads the post-stage output. Stereo
unity reports approximately -12.041 and -18.062 dBFS. Half Gain lowers each
by approximately 6.021 dB. Mono duplicates the same reading into both returned
meter values. Silence reaches the existing calculation floor of -240 dBFS.
These are CHOP and RMS observations, not physical ROTO bar acceptance.

A native temporary tox save and reload retains Gain 1.5 and Mute true, with
zero output. Unmute after reload restores the corresponding 1.5-scaled output.
The reloaded fixture has no scoped errors.

## First production slice

Use the existing explicit `SetMixProfile(scope, descriptor)` boundary for
already-wired stages. The current schema accepts `audio`, but runtime
configuration rejects it and audio projections are empty. The first slice
needs to admit audio and map its Gain to overview Volume and first-Focus
Knob 1. Pan and Send remain unassigned. Projection must handle the single
Gain key without indexing a nonexistent second key.

Overview On/Off buttons map to Mute. Mute true uses native Mute-on polarity;
the existing Analysis Active route uses the opposite polarity. Focus buttons
retain no TD business assignment. The common fresh-touch, complete-pair,
identity, mode, session and once-per-press paths remain authoritative.

The stage prototype uses linear Gain with a 0..2 normalized range to compare
the two mechanisms. That is not a production dB curve or a fixed range for all
audio targets. Explicit descriptor ranges or validated target normalization
continue to define the knob range. A separate meter range and a post-Gain/Mute
stage label define Level.

Regression coverage must establish retained Gain through Mute, current-value
motor feedback without echo writes, exact Mute polarity, unassigned Pan/Send,
wrong or replaced targets, missing meters, stale gestures and profile reload.
Native acceptance must exercise a real stage through the controller API.
Physical Gain, Mute LED, bars, motor return and PLUGIN return remain separate
acceptance work. The present prototype does not enable runtime audio support.

## Evidence and preservation

Scratch artifacts are under system temp `roto-26-audio-chs9j0w9`. The folder
contains `build_probe.py`, `measure_probe.py`, `measurements.json`, the temporary
WAV, `prototype.tox`, reload results and before/after preservation snapshots.
The fixture is throwaway and has been removed from the open project.

All 4,602 original nodes, 1,281 DAT hashes, controller storage and static custom
values match the fresh baseline. Only evaluated values of the same three live
Low-signal readbacks are normalized, as in earlier preservation checks. The
original file's Volume and Play, device Active and both meter input wires also
match their pre-experiment observations. The #28 working project and generic
export retain their artifact hashes. TD remains open and disconnected.

Exhaust the Design Space drove the two variants behind one switcher.
Model the Domain kept retained Gain, Mute and read-only Level distinct.
Prove It Works required native samples and an actual tox reload.
Explain the Number kept the fixed waveform and sample counts beside the RMS
readings. No performance or physical-audio claim follows from these values.
