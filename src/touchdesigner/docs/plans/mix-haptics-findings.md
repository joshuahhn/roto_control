# MIX haptic detents

Reviewed 2026-10-17 against source `2bcf0ad` and the official sources below.
The upstream repository was at `2d43a72c6699983080f8765292498502ff08be57`;
its latest published API PDFs match the local files byte-for-byte.

## Finding and implementation decision

The published APIs do not expose configurable N-position detents, arbitrary
indent positions or resistance strength for MIX controls. This is a limit on the
documented host interface, not proof that the motor hardware cannot do it.

MIX does have firmware-defined haptics. The official v3.1.0 release notes added
0 dB indents for Volume in Ableton Live/Bitwig and Volume/Send in Logic Pro,
including FUNC Track Focus. Those fixed mixer reference points do not configure
six detents for an Operation list or two detents for Swap. Their physical feel
and positions in our TD session were not tested in this investigation.

Keep the current MIX Menu/Toggle value quantization and motor recall. Do not
advertise physical detents or add a haptic-strength setting. Native mixer
indents also must not be described as a TD parameter's neutral value: our
Opacity, Threshold and Brightness mappings reuse native mixer addresses without
changing their firmware haptic semantics.

If physical steps become a requirement, the documented alternative is a
separate PLUGIN assignment with LEARN metadata, accepting its different views
and the absence of accepted native VU bars there. Staying in MIX requires a
manufacturer-confirmed interface or firmware addition. Do not send PLUGIN
configuration while in MIX or push motor feedback against a held touch to
imitate resistance. No such workaround was implemented or tested.

## Protocol and firmware evidence

| Source | Relevant scope and result |
| --- | --- |
| [SysEx API v1.6](../../../../docs/ROTO-CONTROL_SYSEX_API_v1.6.pdf), sections 2–4 | General and MIX commands contain no haptic setter. Section 3.10, `0B 0A LEARN PARAM`, carries centre-indent and step-count metadata for PLUGIN parameters. Its hexadecimal `02..18` means 2..24 steps; step strings are sent only up to 16. It is not a MIX command. |
| [Serial API v1.3](../../../../docs/ROTO-CONTROL_SERIAL_API_v1.3.pdf), sections 2–4 | Haptic mode, indent positions and step count belong to MIDI group `02` and PLUGIN group `03` knob configurations. Its N-step field specifies 2..16. General Get/Set Mode recognizes MIX, but there is no MIX control-configuration group or resistance-strength field. |
| [Official support FAQ](https://www.melbourneinstruments.com/roto), “How do I change the haptics on the knobs?” | Roto-Setup customization is scoped to MIDI and PLUGIN. The page lists firmware 3.3.0 dated 2 October 2026. |
| [Firmware v3.1.0 release notes](https://static1.squarespace.com/static/61516d07b4fcfe7439d39b38/t/699ba0e19eb3336c6cc415a9/1771806945526/ROTO-SETUP-Release-Notes-3-1-0.pdf), 23 February 2026 | Documents the fixed MIX 0 dB indents described above, including FUNC Focus. It does not describe arbitrary MIX step counts or force settings. |
| [Firmware v3.3.0 release notes](https://www.melbourneinstruments.com/s/Roto-Control-Release-Notes-3-3-0.pdf), 2 October 2026 | Lists LEARN/clear interaction and touch-sensitivity changes. It adds no documented MIX haptic configuration. This is an incremental release note, not a complete firmware specification. |
| [User manual v1.1.4](https://www.melbourneinstruments.com/s/ROTO-UserManual-V1-1-4-April2025.pdf), printed page 18 | Historical corroboration: Roto-Setup customizes MIDI/PLUGIN, while MIX is configured from the active Live Set. This older manual predates the v3.1 MIX indent addition. |

Official reference integrations at the checked upstream commit corroborate the
PLUGIN path. [Ableton `_learn_parameter`](https://github.com/Melbourne-Instruments/roto_control/blob/2d43a72c6699983080f8765292498502ff08be57/src/ableton/ROTO_CONTROL.py#L1106)
and [Logic LEARN construction](https://github.com/Melbourne-Instruments/roto_control/blob/2d43a72c6699983080f8765292498502ff08be57/src/logic/config.lua#L1881)
send haptic metadata through `PLUGIN_COMMAND_GROUP / LEARN_PARAM`.
[Bitwig `getLearnSysEx`](https://github.com/Melbourne-Instruments/roto_control/blob/2d43a72c6699983080f8765292498502ff08be57/src/bitwig/src/main/java/com/bitwig/extensions/controllers/melbourneinstruments/device/RotoParameter.java#L94)
uses the same `0B 0A` message. No MIX haptic-configuration path was found in these
integrations.

## Evidence boundary

This was a read-only specification/source review. No MIDI/serial commands,
parameter writes, firmware changes or live TD operations were performed.
Existing Operation/Swap hardware acceptance proves discrete values and motor
recall, not physical detents. No runtime source, saved toe/tox or receipts need
changing for this finding. General Float step sizes remain a separate feature.
