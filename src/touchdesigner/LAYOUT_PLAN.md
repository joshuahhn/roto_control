# Multi-Track implementation update (2026-10-06)

The historical plan below describes v1 Layout-as-Plugin and is superseded by registry v2: Layout -> multiple Tracks -> one Plugin per Track -> mappings. Current contract and API: [Layouts and Tracks](docs/functions/layouts.md).

Implemented in existing external Python modules/DATs, without new persistent network operators: nested registry migration, stable Plugin identities, Track CRUD/menu, paged Track announcements, hardware/TD selection paths and Inspector context. v1 Layouts migrate independently with existing wire identities and removal records preserved. Layout count is no longer tied to a hardware Plugin page.

The user authorized implementation while away, with physical testing on return. Software/native acceptance may precede the physical gate under that instruction. Multi-Track hardware recall and LOCK behavior must still be tested; prior two-Plugin acceptance is not evidence for the new Track layer. Do not claim physical completion.

Return-test sequence: choose a test Layout; create EFFECT and VISUAL Tracks, both CUSTOM; learn the same physical knob to different parameters; switch EFFECT/VISUAL/EFFECT via hardware and TD; verify independent targets, current-value feedback, reconnect and empty mapping set. Then test LOCK selection/unlock and the ninth Track page. Never infer recall completion from a timer.

---

# Saved mapping Layouts — build plan

## Scope

Custom mode contains named, persisted mapping Layouts. Each Layout freely maps 8 knobs and 8 buttons across target COMPs. Its hardware Trackname defaults to EFFECT and Pluginname defaults to CUSTOM. Both are editable and remain fixed while controls are used. Layout name is the TD selector label, independently of these hardware names.

Layout changes switch routing, not effect parameter presets. Read current target values on activation; do not restore saved numeric values or fire Pulse callbacks. Hardware PUSH/TOGGLE configuration is external and must match adapters; switching Layout does not reconfigure hardware TYPE.

## Scout (2026-10-05)

Active project .35.toe in this repository; controller /roto_control_python/roto_python. Main network has 25 children, no wires/cycles and no operator errors. Existing extension, protocol, setup, Inspector and 16 target watchers supply the required routing. No new CHOP chain or external dependency is needed.

Main annotation extent X=0..1275, Y=-815..150. Inspector extent X=0..1580, Y=-248..150. These are occupied areas; new layout logic will use a separate internal baseCOMP if placement is needed.

At planning time persisted assignments and catalog are empty, assignment_device_id is None, and removal tombstones exist. Do not resurrect older saved assignments or assume the prior Knob 3 mapping still exists. Migration preserves the actual current configuration, including an empty collection.

## Identity and persistence

### Documentation checked

Primary protocol reference: repository `docs/ROTO-CONTROL_SYSEX_API_v1.6.pdf`, PDF pages below (not printed section page numbers).

| Reference | Documented behavior | Design consequence |
| --- | --- | --- |
| p17 §2.21 | SET CURRENT TRACK NAME accepts a 13-byte NUL-terminated ASCII string | Track display can be updated through this command; maximum payload text is 12 ASCII bytes. |
| p20 §3.5–3.6 | PLUGIN DETAILS carries index, 8-byte hash, enabled status and separate 13-byte name; DETAILS END terminates the list | Layout identity and display label can be separate. Mapping retention per custom hash is an implementation inference, not an explicit guarantee in this API document. |
| p20–21 §3.7–3.8 | Hardware selects by plugin index; DAW selects with index, macro page and Force flag | Handle both selection directions. Respect lock with Force=0 by default; do not silently override lock. |
| p21 §3.9 | LEARN state is sent FROM ROTO only | TD cannot use this command to enter/exit hardware LEARN. Reject Layout switch during LEARN as a product policy. |
| p21–22 §3.10–3.11 | ROTO sends CONTROL MAPPED for mapped controls on the current page; DAW responds with LEARN PARAM metadata | Recall refresh uses this existing exchange, not a made-up load-layout command. |
| p22 §3.11 | CONTROL MAPPED includes parameter index/hash, control type/index and macro flag, but no plugin/Layout hash | Acknowledgements alone do not identify the Layout. Same-target records across Layouts need transition ordering; do not claim unconditional stale-event rejection. |
| p22–23 §3.13–3.14 | Lock notification is FROM ROTO; UNMAP CONTROL affects the current page | Track lock state; wait for correct selection before replaying scoped unmaps. Switching is not clearing. |
| p35 appendix B.2 | Normal PLUGIN knobs/switches use fixed channel-16 CC numbers with no Layout ID | CC messages cannot be classified by Layout identity; stop routing during transition and test delayed input explicitly. |

TouchDesigner bundled `COMP Class → Storage` docs also confirm storage is saved/restored in toe/tox. Versioned registry and selection UI remain our application design, not ROTO protocol features.

### Repository implementation cross-check

Read `src/ableton/ROTO_CONTROL.py` and `src/logic/config.lua`; upstream files remain unchanged.

- Ableton `_process_return_plugin_names` (line 1786) explicitly uses a class-only digest for devices supporting preset recall so presets share mappings; other devices use class/name combinations. Display name is a separate field. This is concrete implementation evidence that identity determines mapping reuse; unique stable Layout IDs are our adaptation, not a named upstream Layout API.
- Ableton `_update_selected_device` / `_send_selected_device_update` (923–953) suppress automatic selection under lock or LEARN, clear value listeners, update the device page if necessary, and send DAW SELECT PLUGIN with Force=0 (`MACRO_FORCE_PLUGIN=0`, line 110). `__on_selected_device_changed` (1063) refreshes device details, releases mappings for hardware-origin selection and distinguishes selection direction to avoid redundant selection feedback.
- Ableton hardware selection handler (1480) clears listeners, selects the corresponding Live device and updates the locked-device reference if lock is active. Lock does not mean all hardware-origin selection is forbidden. The TD implementation must distinguish explicit hardware selection from automatic TD following.
- Ableton CONTROL MAPPED handler (1521–1634) resolves the parameter in the current selected device using the hash, with index fallback for repeated names and index routing for macros; then connects the physical control and installs a value listener. Invalid parameters release the corresponding control. There is no script-owned bank of hardware mappings loaded by the DAW: the hardware reports stored controls, and the host reconnects their targets.
- Logic `generate_plugin_details` (841) hashes the plugin name with its own 8-byte algorithm (`get_hash`, 1211), then sends the display name separately. Unlike our proposed Layout identity, renaming the source name changes this Logic hash. Do not copy this coupling into customizable TD names.
- Logic ROTO_CONTROL_SELECT_DEVICE (1073) enters MODE_START to prevent feedback, selects the Logic slot and optionally opens its window. `select_plugin` (1150) clears names/learn state/count before repopulation. SET_PLUGIN_LOCK (1113) changes `popup_lock`, affecting window opening; this is not the Ableton locked-device behavior.
- Logic learning (1760–1917) uses parameter sweep, generated name hash, LEARN_PARAM and cached value restoration. Its PLUGIN_LEARN_COMPLETE handler (1104) restores cached MIDI position. This file has no CONTROL_MAPPED handler; DAW_SELECT_PLUGIN is declared but not sent. It is a separate Logic integration path and is not a drop-in recall reference for the existing TD host.

Result: use Ableton's device-announcement/selection/hardware-report/reconnect sequence for TD Layouts. Do not clone its naming-dependent digest literally, introduce a host-side hardware-mapping upload, or adopt Logic sweep/delays as a substitute for recall. Physical custom-ID A/B/A acceptance remains to be measured.

Existing protocol announces an 8-byte digest(device_id), separately from display name. CollectionHost derives device_id from stable group_id; acknowledgements validate parameter identity hash, index, kind and slot. Upstream Ableton code also distinguishes device digest from display name. This supports independent Layout identities, but physical A/B/A recall is still unverified.

Persist a versioned layout registry in controller storage. Each record has stable layout ID/group ID, display names, parameter records with relative owner paths, wire indices/identities, settings overrides, removed IDs, pending unmaps and needs_relearn. Catalog is derived data, not the routing authority. Never persist Mapped=True as proof of an active hardware session.

Migration retains current group/device identity for the first Custom Layout so existing valid mappings can recall. New Layouts receive unique stable identities; renaming does not change them. Store configuration edits automatically in the active record; normal TD save persists the registry to toe/tox. Generic tox contains one empty Custom Layout, disconnected, with no user targets or identities.

Python callbacks require a registration/factory reference that reconstructs runtime objects. Do not serialize callable objects or silently drop callback bindings. Resolve this contract before claiming full callback Layout support.

## Public surface

Layout dropdown, Trackname, Pluginname, plus minimal New/Rename/Delete actions. Inspector continues showing 16 slots for the active Layout; COMP pages remain filters inside that Layout. Diagnostics stay internal. Delete Layout uses one Yes/No confirmation and cannot delete the last Layout. Clear/Clear All affect active Layout only.

Proposed API: GetLayouts(), SelectLayout(id), CreateLayout(name), RenameLayout(id, name), RemoveLayout(id), SetLayoutNames(track_name, plugin_name). Keep layout IDs separate from labels and existing Setupmode.

## Switch sequence

1. Reject switching during hardware LEARN or while a knob is touched; show a useful Inspector message.
2. Persist current configuration. Resolve and validate destination records before changing routing. Missing targets remain visible as unavailable, with routing disabled.
3. Disable old watchers and clear pending FreeLearn offers, input halves, button edge/debounce state and display queues. Suspend control dispatch while transitioning. The protocol has no session/Layout token on CONTROL MAPPED or ordinary CC messages, so input draining and transition completion need evidence from a captured exchange.
4. Install the destination collection and activate its stable device identity and fixed display names. Scope tombstones/unmaps to this Layout; switching must not clear another Layout's hardware mappings.
5. Send PLUGIN DETAILS/DETAILS END then DAW SELECT PLUGIN with Force=0. Account for hardware lock: do not display the new Layout as active if selection remains locked. Handle hardware ROTO SELECT PLUGIN too. Respond to current-page CONTROL MAPPED with LEARN PARAM and value feedback. No selection-complete or mapping-list-end command is documented in these sections; establish completion behavior empirically before finalizing the transition state machine. Publish actual parameter values and LED state after acknowledgement; activation does not dispatch actions.
6. Refresh Inspector and COMP marks. On failure restore the prior configuration, keep unsafe routing disabled and report the error.

Device announcements can trigger callbacks while changing state; transitions must be serialized rather than relying on an immediate synchronous recall.

## Operators and data flow

One internal baseCOMP base_layouts, proposed position (1300, -40), size 160x130, parent shortcut Layouts. Inside: layouts textDAT (Python module, 25,0), database textDAT (JSON diagnostic mirror, 200,0). External source remains authoritative. Annotate the new group after placement, leaving 20px from existing annotation extent. Verify actual bounds before building.

RotoPythonExt calls the layout module through the existing controller reference. Module owns registry/validation; extension owns host/watchers/session transition. Existing parameter_callbacks handles public parameter edits. Inspector uses the common API; no second routing implementation. No additional signal wires or per-frame registry scanning.

## Phases and acceptance

1. Display metadata plus isolated protocol probe: configurable names independent of hashes; packet tests and live name update. Prepare two distinct virtual plugins/identities with the documented list and selection commands, recording ordered RX/TX. Do not build the registry/UI yet.
2. Hardware gate: learn one distinct target on the same slot in A and B, switch A/B/A, verify recalled parameter identities and physical input routing. Test lock/unlock and an empty plugin without using arbitrary elapsed time as proof of selection. Pause for the user's physical LEARN actions when required. Restore the original active session after the probe; do not clear existing hardware mappings.
3. Registry/API after gate: migration, unique IDs, parameter restore, callback reconstruction, active-only edits/removal, version validation. Unit tests cover A/B isolation and invalid destination rollback.
4. Switching and minimal UI: simulated matching/stale acknowledgements, no Pulse or parameter writes on activation, dropdown/management actions, disconnected editing and reopen persistence. Verify knob motor, Toggle LED, Pulse/PUSH and Menu labels physically.
5. Review migration against table registrations, direct assignments and callback hooks, not only parameter_assignments. Until callback reconstruction is implemented, reject unsupported conversion before any mutation and keep the existing callback API functional.
6. Embed docs, clean layout, inspect errors, run python3 -m unittest discover -q in src/touchdesigner and git diff --check. Save through live TD; export disconnected generic tox and verify empty registry/template reload.

## Required evidence before implementation expansion

First capture a minimal two-plugin identity/selection exchange using the documented commands, preserving current project configuration. Verify A/B/A mapping retention, lock behavior, callback/message ordering and whether current firmware emits enough events to establish safe activation. Do not implement the registry/UI as if these behaviors were already guaranteed. New Layout ID generation, CRUD, blocked-touch switching and automatic configuration persistence are proposed TD product policies. The extra baseCOMP/operator layout is provisional until the switching contract is validated; the docs do not require additional operators.

This document is a plan only. No live network, runtime source, mapping or export changes were made during planning.

## Review decision (2026-10-06)

Approved for phase 1 and the phase-2 hardware gate, not an unconditional registry/UI rollout. Corrected the earlier contradictory ordering that put registry/UI before required hardware evidence. Re-scout live state before capture; the empty assignment snapshot above is historical, not migration input.

Further constraints for implementation:

- A TD-origin switch while locked must be rejected before replacing the active host/watchers. Hardware-origin selection has its own path, following Ableton's behavior.
- Distinguish requested Layout from active/confirmed per-control routing. An empty destination cannot produce CONTROL MAPPED; do not invent a completion acknowledgement or treat a timeout as confirmation.
- Identify delayed messages carrying the same parameter hash/index as an explicit unresolved protocol limitation. Namespaced identities for newly created Layout parameters may reduce ambiguity, but legacy migration must preserve existing identities. A generic promise of stale-message rejection is insufficient.
- Reuse one external Python module/DAT for the probe where practical. base_layouts and its placement are provisional, not required for the first phase. No new extension is needed merely to hold two strings.
- Validate hardware display strings as at most 12 ASCII bytes, with visible validation rather than silent identity-changing normalization. TD Layout labels can remain independent of wire display constraints.
- Every accepted stage must update source builders and embedded code consistently; never report the generic export as updated if it still contains old code. Keep a recoverable pre-change source/live snapshot. No commit or push is authorized.

## Hardware gate result (2026-10-06)

See layout_hardware_verification.json and HANDOFF: A/B/A recall and actual A/B input observed; empty destination visually confirmed; empty-to-A recall observed. Proceed with registry/API and minimal UI. Lock coverage proves host-side prevention after actual LOCK notification, not firmware rejection. Hardware-origin selection while locked remains untested. Do not require an imaginary global completion message for empty layouts: configuration selection and per-control mapping readiness must remain distinct.
