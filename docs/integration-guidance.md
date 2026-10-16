# ROTO-CONTROL integration guidance

Official guidance supplied by the project owner, preserved below in English. Use it as the hardware-capability reference for protocol design and feature reviews.

## The three layers, briefly

> The serial API is the configuration layer, and the only one of the three that is not MIDI at all. Over USB serial it writes whole setups and reads them back, which is how you generate mappings programmatically.
>
> SysEx is MIDI: the part of it set aside for messages specific to one manufacturer. It is live and two-way. Put your own text on the eight screens, push meter levels, and receive knob touches and page changes back.
>
> Ordinary MIDI needs nothing special. Every knob sends 14-bit CC on channel 16, with its own touch message, so anything that speaks MIDI can use it without knowing what a Roto-Control is.

## Detailed integration brief

> I want to write software that talks to a Melbourne Instruments Roto-Control, a motorized MIDI controller with 8 touch-sensitive knobs, 8 buttons and a screen above each knob, arranged in 4 switchable pages.
>
> There are three ways to talk to it, and I want you to read the specs before writing code:
>
> 1. Serial API (USB serial, 115200 8N1) - the configuration layer. Reads and writes all
>    64 MIDI setups of 32 knobs and 32 buttons: message type, channel, CC or NRPN number,
>    min and max, a 12-character name, a color from a fixed 83-entry palette, and the
>    haptics (smooth 300-degree sweep, a center indent, arbitrary indents, or 2-16 detents
>    with a label per detent).
> 2. SysEx API (USB MIDI, messages begin F0 00 22 03 02) - the live layer, bidirectional.
>    Push track names, RGB track colors, plugin parameter names, VU meter levels, and
>    arbitrary text to any of the 8 screens. The device pushes back knob selection, page
>    changes, mode changes and learn events.
> 3. Plain MIDI, no protocol needed - every knob sends 14-bit CC on channel 16, every
>    button sends 7-bit, and knob TOUCH is its own CC per knob. So it works as a
>    high-resolution touch-sensing surface for anything at all.
>
> Both specs, and the source of Melbourne Instruments' own integrations (an Ableton Live
> remote script, a Bitwig extension and a Logic Pro control surface), are at:
> https://github.com/Melbourne-Instruments/roto_control
>
> The unusual capability: the knobs are motorized, so they are an OUTPUT device as well as
> an input. Software can move the user's hands to a state rather than telling them about it.

## Applying the guidance in this project

- Assess hardware capability, the host's exposed functions and verification evidence separately. A capability in this guidance does not by itself mean the current tool implements it.
- For ordinary MIDI coverage, distinguish CC/touch message support from the current host's PLUGIN handshake, LEARN and matching-ACK workflow, and from the availability of an independent MIDI entry point.
- Read the protocol specifications for wire formats, mode-specific behavior and version constraints before implementation. Preserve the official guidance when recording implementation choices or coverage gaps.
- Keep current TouchDesigner implementation context in [CONTEXT.md](../src/touchdesigner/CONTEXT.md) and dated acceptance evidence in [HANDOFF.md](../src/touchdesigner/HANDOFF.md).

## Protocol specifications and reference integrations

- [Melbourne Instruments upstream repository](https://github.com/Melbourne-Instruments/roto_control)
- [Serial API v1.3](ROTO-CONTROL_SERIAL_API_v1.3.pdf)
- [SysEx API v1.6](ROTO-CONTROL_SYSEX_API_v1.6.pdf)
- [Ableton integration source](../src/ableton/ROTO_CONTROL.py)
- [Bitwig integration source](../src/bitwig/)
- [Logic Pro integration source](../src/logic/)
