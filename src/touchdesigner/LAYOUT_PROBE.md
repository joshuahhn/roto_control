# Layout protocol hardware gate

This is an isolated probe, not the Layout registry implementation. It has three advertised plugins: PROBE A, PROBE B and PROBE EMPTY. A/B each contain a synthetic normalized numeric target on Knob 1, with independent plugin and parameter hashes. No user COMP values are read or written; no UNMAP command is sent.

## Start and restore

1. Exit hardware LEARN and release knobs. Disconnect the production TD controller; verify its external MIDI process is absent. Do not run Roto-Setup simultaneously.
2. Run `.venv/bin/python layout_protocol_probe.py --td-disconnected --log /tmp/roto-layout-probe-unique.jsonl` from this directory. The explicit flag is a human/operator assertion, not an automatic TD process check. The log must not exist already.
3. The probe announces A/B/EMPTY on PLUGIN readiness, then requests A with Force=0. `requested` is not confirmation. No arbitrary wait establishes successful selection. A matching CONTROL MAPPED enables only that synthetic target's routing.
4. When finished send `stop` or interrupt the process. Context managers close both MIDI ports. Verify the process exited, then Connect the unchanged production TD controller. Probe-only hardware mappings are retained under distinct identities; production storage/targets are never replaced.

## Physical sequence (operator coordinates each step)

- A: enable hardware LEARN, touch Knob 1, then operator sends `offer`. Confirm LEARNED / Probe A, exit LEARN, rotate Knob 1. Ordered log must include the exact A hash acknowledgement and input event plugin A.
- Operator sends `select B`. Repeat LEARN/touch/offer for Probe B on Knob 1, exit and rotate. Confirm B identity and B input.
- Operator sends `select A` without LEARN. Require actual A CONTROL MAPPED and A input; then B and A again. A/B retention is accepted only from captured hardware messages and physical input, never from simulated tests.
- Lock selected plugin on hardware. TD-origin `select B` must reject before any send/state mutation. Hardware-origin selection under lock is recorded separately. Unlock and capture selection/recall again.
- Send `select EMPTY`. Record hardware display and the entire RX sequence. It remains requested-only because no mapping can acknowledge it; absence of a message is not selection proof. Then select A and require its matching acknowledgement.

Commands: `select A`, `select B`, `select EMPTY`, `offer`, `status`, `stop`. Log sequence includes every RX/TX with monotonic timestamps, rejected operations, requested vs control-confirmed selection, inputs, hardware lock and mode/session resets. Invalid SysEx is rejected; global touch is tracked even while dispatch is suspended. MIX/restart suspends old routing. Display flushing is rate-limited using the existing host path.

## Limits

CONTROL MAPPED and ordinary CC contain no plugin identity. Distinct parameter hashes reject A/B cross-acknowledgements in this probe; same-parameter legacy Layout ambiguity is unresolved. Even with distinct hashes, a delayed CC after a new acknowledgement cannot be identified as old input. Do not generalize this probe's results into unconditional stale-message rejection. First touch before the process starts cannot be inferred until a touch/release message arrives; release controls before starting.
