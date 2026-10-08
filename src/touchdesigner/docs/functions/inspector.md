# Mapping Inspector

Open `roto_python/inspector` in a floating viewer (right-click View) to see all 8 knobs and 8 buttons, including Unassigned slots. Use Page to choose All COMPs, a parameter owner COMP, or Python callbacks. Double-click editable cells to change target configuration or Value. Clear deletes the target registration after Yes/No confirmation; the target parameter itself and its value remain intact.

- Mapped: Yes means the current hardware session acknowledged this target; No means waiting/disconnected. Invalid means the binding is suspended; read Error.
- COMP / Parameter: actual destination of a parameter binding, independent of its display label or saved path. Registered rows retain COMP, Parameter, Value and bounds while disconnected or unmapped. The catalog is persisted in controller storage, mirrored in inspector/database, and read through GetControlCatalog(). Deleted/unavailable parameter owners retain their last known destination. Callback bindings show Python callback because callbacks have no implied COMP destination.
- Mode / Hardware: TD action mode and declared PUSH/TOGGLE input type are separate. Hardware type is configuration, not detected or changed by the Inspector.
- Value: registered target units, displayed to three decimal places. Pulse stays zero; consume its events. ID is the stable mapping identity.

The top line reports acknowledged/registered controls. Rows update from the controller's existing state publication; the input table is rewritten only when its projection changes. No separate polling DAT or outer diagnostic custom parameters are added. Lister config is external to the cloned component.

`controller.GetControlCatalog()` returns a detached persisted catalog, independent of MIDI connection. `controller.GetControlStates()` returns detached snapshots for all active targets, in registration order. Each snapshot also includes binding_type (`parameter`, `callback`, `value`), comp (current path or empty) and parameter (current name or empty). It does not expose Par handles or serialize callback destinations. GetControlState(id) returns the same fields for one target. Querying has no registration/write side effects.

Fresh builds include the Inspector through build_inspector.py. Embedded exports retain the UI and Inspector Python source; MIDI environment dependencies remain as described in portability.md.

If the optional UI refresh fails, its title shows Inspector unavailable and internal refresh_error storage records the reason; hardware transport and target dispatch remain active.

## Direct hardware LEARN

Open hardware LEARN, select a knob/button, then change a writable custom parameter anywhere under the controller's parent project branch. New COMPs are discovered automatically. No prior Inspector assignment is needed. Float/Int changes offer a knob target; Toggle/Pulse changes offer a button target. The pending offer has a parameter index/hash independent of the physical slot. Only a matching CONTROL MAPPED acknowledgement commits the hardware-reported slot and marks its destination COMP.

The global Parameter Execute observer is active only during connected PLUGIN LEARN. Discovery runs on LEARN entry and at most once per second while active, so adding a COMP during LEARN may need up to one second before its first edit is watched. Expression/export/readonly parameters and the controller's own internals are excluded. Per-frame batches prefer a changed parameter on the selected COMP, helping public BIND aliases take precedence over internal masters. Repeated slider updates do not repeatedly offer the same target; changing parameter or selecting a control allows another offer. Hardware control input during LEARN does not execute existing business actions.

API SetValue writes are excluded from this automatic offer path. Direct external Python writes to custom parameters can still look like user edits while LEARN is open; close LEARN while running automated edits. Hardware acknowledgement, rather than the offer alone, creates the saved assignment. Reconnect restores its parameter index as well as its identity.

## Assign any COMP parameter

Click a slot's **COMP** cell, choose a COMP, then choose its custom parameter. The picker scans the controller's parent branch on demand, including newly added and nested COMPs. Click an assigned row's **Parameter** cell to choose another parameter on the same COMP.

The Inspector calls `AssignParameter(kind, slot, parameter)`: infer label, Float/Int range or Toggle/Pulse mode, generate a stable ID and store the assignment in controller storage. No table editing, registration script or Apply binding is needed. Only the selected slot is replaced; other collection targets keep their mapping and runtime state. Duplicate parameters/shared bind masters and incompatible styles are rejected before changes.

For the shortest flow, open hardware LEARN and select the control first, then choose COMP/parameter in its row. The new metadata is offered automatically. If LEARN is closed, the assignment is still saved; select the control in hardware LEARN and click Learn afterwards. Registration waits for a matching acknowledgement before reporting Mapped. Software assignment cannot select hardware controls or enable hardware LEARN.

Numeric parameters use knobs; Toggle/Pulse parameters use buttons. Button assignments retain that slot's declared hardware type when present; empty Pulse slots default to PUSH and empty Toggle slots to TOGGLE. The Hardware column must match Roto-Setup TYPE; choosing a TD parameter does not reconfigure hardware.

Assignments survive Disconnect, extension reload and normal project saves. Inspector assignments override the corresponding slot in the existing saved table/hook; callbacks in other slots remain registered. Clear deletes this assignment and prevents its previous target from returning on restore. The fresh exported COMP strips user assignments.

## Learn / Re-learn

Each assigned row has a Learn button (Re-learn when mapped, previously mapped or requiring new metadata). Open hardware LEARN, touch the matching knob or press the matching button to select that slot, then click the row's Learn button. It calls `Offerparameter(id)` to send exactly that registered target's identity, label, value/range semantics and button state labels. The title reports the offer or the reason it could not be sent. Pulse offers never execute the target action.

Registration and Inspector layout changes alone do not transmit assignments. An offer requires connected PLUGIN, hardware LEARN and a valid target. The button does not enable hardware LEARN or choose a physical control remotely. A matching hardware acknowledgement is required before Mapped becomes Yes and Needs re-LEARN clears; sending metadata alone is not success. Empty slots have no Learn action. No Clear/unmap or value write occurs when clicking Learn.

## Clear

Click Clear, then Yes or No in the same cell. Clear All uses the toolbar confirmation. Exactly two clicks are required. Confirmation expires when registration, configuration or connection changes.

The UI calls `RemoveControl(id)` or `RemoveAllControls()`: delete the saved target record, disable its watcher, remove callback routing/config overrides, and suppress its saved registration hook. The slot stays visible as Unassigned. These actions work offline; hardware unmap requests are replayed when PLUGIN becomes ready. Exit LEARN and release the affected control first. Other controls retain their registrations. Explicit public registration can opt a removed ID back in; ordinary Applybinding/reinit/reconnect cannot.

The underlying hardware command has no acknowledgement. Local removal rejects stale mapping acknowledgements, rotation and button input, and cannot auto-offer the old target; verify physical LCD removal separately. `ClearLearn(id)` and `ClearAllLearn()` remain lower-level hardware-only APIs that retain registration. The Inspector deliberately uses the removal APIs instead.

## Mapped COMP marks

Acknowledged, valid parameter mappings add `roto_mapped` to the destination COMP and set its node color to cyan `(0.20, 0.55, 0.70)`. The built-in Value marks its controller COMP; callback bindings do not imply a COMP. Registration without hardware acknowledgement does not mark a node.

Several controls or controllers can share one destination; the mark remains while any active mapping still owns it. Clearing the last mapping or Disconnect releases that owner's claims. Original color and preexisting tags are retained; restoration changes color only if it still matches the applied cyan, preserving a subsequent manual color edit. Marker state/errors are internal storage. Rename uses live destination paths and runtime operator IDs; no saved absolute path is used as a parameter reference.

Clear removes the registration and leaves an Unassigned slot. Disconnect releases the active COMP marks while retaining the catalog.

## Editable target configuration

Min / Max show registered target-unit bounds even while unmapped. Double-click a knob's Min or Max to edit. Limits must be finite, min < max, include the current value, and respect native parameter clamp/integer constraints. Button bounds are fixed at 0 / 1.

Click a button's Mode ▾ to open the Toggle / Pulse drop-down menu. Native parameter style must match (Toggle / Pulse); the incompatible menu option is disabled. Callback targets may switch either way. A native release opens the menu directly, and selection refreshes the row. Double-click Hardware to enter `toggle` or `push`; this declares the input adapter and does not configure the hardware TYPE. Use Roto-Setup to match it. Knob Mode/Hardware and Pulse Value are not editable. Value edits call SetValue, with no re-LEARN or hardware callback echo.

Configuration edits use public `ConfigureControl(id, minimum=..., maximum=..., mode=..., button_type=...)`. All validation happens before replacing a target. An input Hardware adapter change preserves mapping and needs no re-LEARN. A range/Mode change to a mapped target is unmapped using the existing hardware command; other targets keep their mappings and values. That row becomes amber and Error shows `Needs re-LEARN`. A matching new mapping acknowledgement clears the prompt/highlight. Invalid edits preserve existing configuration and the title reports why.

Configuration overrides persist in controller storage by stable target ID and apply after table/hook registration on restore; fresh reusable exports clear these overrides. The saved targets table and registration hook remain the original registration source. Editable configuration currently requires a collection; built-in single Value remains fixed at 0 / 1.

`ClearAllLearn()` preflights connection, LEARN and touch before any unmap command, and returns the registered IDs. A transport failure during the batch can leave a partially cleared batch; hardware offers no atomic clear-all acknowledgement. Confirmation belongs to the Inspector UI, while ClearLearn / ClearAllLearn remain direct APIs.


## Menu parameters

Custom Menu parameters support knobs (quantized option selection) and buttons (Cycle: advance and wrap on each press). Use hardware LEARN, select the destination, then change the menu. Inspector pickers support both kinds. PUSH ignores release/held duplicates; TOGGLE accepts each latched press. Menu ranges are fixed at indices 0..N-1, and SetValue uses those indices. State includes menu_names, menu_labels and value_label. LCD feedback uses the option label. Menu options must have 2..24 unique names and matching labels, following the official Ableton quantized-step limit. Changing names, labels or order suspends the binding; assign and re-learn it.

## Projection scheduling

Runtime publication keeps authoritative catalog/control state synchronous. Optional Inspector JSON/table projection compares a transient signature of data, context, page, confirmation, action status and Follow status. Changed inputs schedule at most one owned end-frame render that reads the latest snapshot; direct UI commands still refresh immediately. Disconnect forces the final disconnected projection and cancels the callback, including during export/destruction. No persistent user mapping cache or extra polling loop is added.

## Compact Popup restart size

Compact views save their temporary section-height offset separately from the native Window size. Startup closes drafts and subtracts only that offset, retaining the user's manual base width/height. Expanding Mapping adds134px again; saved expanded size cannot become the next collapsed base. Generic UI exports carry offset0 and a178px closed host. No callback, token or connected session is persisted.

Compact editor input-only PUSH/TOGGLE changes retain the target identity/ACK and send no unmap/re-LEARN request; the declaration must match the hardware TYPE chosen in Roto-Setup. Physical B1 Menu/Cycle acceptance covers three corrected TOGGLE presses and twelve PUSH press/release pairs, each with one dispatch per press and no release/extra dispatch. Original hardware/TD TOGGLE and Value1 were restored. Raw traces and scope are recorded in prototypes/inspector/REPLACEMENT_REPORT.md.

Each synchronous publication now shares one detached control-state snapshot between catalog/ACK processing and mapping marks. Native controls_values channel identities remain stable during Value updates; only changed samples are written. Target schema or output replacement rebuilds channels. Catalog and output publication stay synchronous; the optional legacy UI projection remains the only deferred observer. See prototypes/inspector/PERFORMANCE_REPORT.md for fixed-deadline/native profiling and the still-open full-rate cadence gate.

## Compact native parameter workspace

Details now begins with native definition metadata: name/Label/Page/Style, default value and default evaluation mode, slider versus clamp limits, evaluation ownership/Bind master and bounded Menu preview. It reads on section open/Refresh, with no extra per-frame polling. The existing fixed Details section scrolls internally; metadata length does not grow the Window. Five24px native MDI actions provide Refresh, Reveal, Repair, Values and Definition with hover names/reasons.

Values opens the assigned owner's TD parameter dialog; Definition opens TD's custom parameter editor. LEARN/touch and stale target/session guards apply, while readonly metadata inspection supports inactive/disconnected mappings. Native dialog opening does not itself write Value, change Mapping Range or offer a hardware mapping. Native changes become visible after Refresh/reopen and may require repairing/relearning a changed definition. Guarded native metadata drafts are described below; the guarded native Float/Int Style slice is described below; other Style conversions remain later work. See prototypes/inspector/ADVANCED_REPORT.md for native/OS verification and scope.

Reveal (crosshair) shows the target COMP node in its parent network using an existing open Network Editor, and centers that node at a readable 1:1 zoom. It supports Follow on by clearing the destination network's saved child selection before navigation; Follow preference and controller routing remain unchanged. If the current pane is not a Network Editor, it reuses another existing open Network Editor. No native target/editor gives an explicit reason.

The Details pencil opens a separate native Label/default draft for independent scalar custom Float/Int parameters. ✓ Apply validates native definition fingerprint plus fresh hardware/session/context; × Cancel discards it. It changes neither live Value nor Mapping Label/range, IDs or ACK state. Unsupported group/clone/Bind/evaluation ownership gives reasons; TD Definition remains available. Form stays inside the fixed Details viewport.

BOUNDS expands inside that draft to edit native Slider min/max, Limits min/max and Clamp Min/Max switches. Window height stays fixed with internal scrolling. Apply checks current constant/raw Value, Default and every matching saved mapping in the linked controller library (active/inactive/page targets,4096 scan cap), rejecting conflicts before native setters. Controller Mapping Range/identity/ACKs stay unchanged; other controllers/external writers are outside that library scope.

Static Menu labels use the same pencil draft for2–24 choices, with fixed internal names/order/default/Value and scrolling rows. Apply rebuilds the active binding through ConfigureControl, preserving stable ID/index/range/mode/input but clearing the old hardware semantics and requiring re-LEARN. No-op/Cancel never unmap or offer. Related inactive Devices show Needs re-LEARN and reject old identities on activation. Dynamic menuSource and shared ownership remain TD Definition workflows. All24 labels are fingerprinted; generic exports scrub every row/local draft. See prototypes/inspector/DEFINITION_MENU_REPORT.md. Physical LCD/re-LEARN acceptance for changed labels remains pending.

Native Float/Int **Style** dropdown in the definition draft previews TD's actual type conversion. It differs from the live Value input's Float/Int format preference. Apply preserves Value, native identity/definition and stable mapping ID/index/range/mode/input, but changes wire numeric semantics and requires re-LEARN across related active/inactive/page registrations. Int rejects decimals/default/bounds/fractional Mapping endpoints; no rounding. Fresh preview Value/runtime binding, exact native/library fingerprints and foreign-controller ownership checks precede mutation. Other styles/shared/hidden/group/evaluation ownership use TD Definition. Fixed Details viewport/window uses internal scroll. See prototypes/inspector/STYLE_MIGRATION_REPORT.md; remaining physical gates are grouped in prototypes/inspector/ACCEPTANCE_BATCH.md.

### Context activation

`ActivationToken(context)` captures session generation, full destination and observed active context. `ActivationCapability(context)` supplies enabled/reason. `Activate(context, token)` Syncs and rejects stale intent/guards, calls the adapter once, verifies actual active context and Syncs even on failure. TD adapter delegates to existing `SelectPlugin(layout, track, device)`; there are no Value, Follow preference, pane selection or LEARN setters. Failed native install reports failure and existing controller flush recovers the routing fence after successful rollback; failed rollback remains paused.
