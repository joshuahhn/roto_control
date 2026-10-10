# Issue 12 actual Action provider-error token seam

## Preserved native evidence

Attempt4 `/var/folders/5q/krg7wb4d4lsgpmlmgqvywj_w0000gn/T/roto-issue12-r6-native-20261008T200258Z-7kmvo1uj/attempt4`:

- native_scheduled_same_status.json e1ea4e79cc9c6821f7d8d2ec328c435c1c1d7b12f06254cac4bbf365bbc54fe4: actual same-status.71→.72 PASS, automatic Sync5→6, unchanged targets/token, both resolved WeakMethod views. This closes the original bounded notification symptom; no full native claim.
- native_burst_token_failure.json 53966110596a50b5e0f9f3dcf98de5a41b2bd324898a069093588c708a8faafd: final partial/error/revision/readback delivered to both views, one observation/Sync, but metadata256 and token changed.
- scheduled_verify_burst_value_failure.json 4eb04266b7f8b3f3c780a6b346bed01351016c57e9526521a8fd45aac542b260: exact token equality FAIL; holder retained.

No evidence or old source bundle is erased/reclassified. Qualified r5 template/source packaging history remains. Root controls restoration/resume; lifecycle/physical/#11 held, #13 blocked.

## Correct red seam and prior blind spot

From src/touchdesigner/prototypes/inspector:

```sh
python3 -m unittest -q test_scheduled_action_details.ScheduledActionDetailsTests.test_real_action_partial_error_and_clear_keep_assignment_token_scheduled
```

Repeated before-fix RED: callbacks(256,256) != expected(256,0). The prior notification-only burst fixture used an action_result dictionary and never called GetControlState, leaving error empty. Stronger source replay invokes real RecallAction/Actions, GetControlState/catalog, actual TDControllerAdapter.Read and metadata_signature, builder DAT observer/callback configuration, RequestSync/SyncController and real WeakMethod subscriber dispatch. Only TD operators/pars/DAT events/end-frame runner and custom-par/CHOP publication are fake; RecallAction automatically invokes the normal Inspector publisher. No manual Sync delivers the tested provider update. Both view callbacks read final Info during dispatch; the same chain is tested disconnected/unacknowledged and acknowledged, retaining actual requires_relearn health/fences. Actual TD event timing/parameter handles/view UI remain native gates.

Final regression loaded immutable r6 GetControlState/catalog/fingerprint functions from exact tree e820f6476971f68a03551ee6b9dc320732d75905 in memory and reproduced the same RED, without altering r6.

## Ranked falsifiable hypotheses and boundary probes

1. Generic META_FIELDS.error conflates provider observations with mapping failure: predict only error changes while identity/ACK/valid/availability/session stable. Confirmed: error became partial: native partial details, only metadata error differed, slot revision9→17, other token dimensions stable.
2. Software partial accidentally suspends binding/readiness: predict valid/mapped/availability/relearn drift. Excluded: true/true/true/false identical before/after.
3. Session/owner/identity changed: predict other token dimensions/identity signature drift. Excluded in source replay; public source guards unchanged.
4. Burst ordering/duplicate callbacks: predict multiple Syncs/observations. Excluded: one Sync, one observation, both views one(256,256) callback.

## Bounded correction

Current GetControlState/catalog and Action library previews emit explicit mapping_error provenance before provider-error fallback. Complete visible error, structured result and health remain unchanged. Owner/unavailable/real binding/controller failure populate mapping_error. Action metadata_signature uses it when an authoritative string is present; absent/unknown provenance falls back to generic error. Parameter/callback error semantics remain generic. Action availability is metadata; provider result/error is display-only. No string guessing, blanket removal of error, global token freeze or diagnostics masking.

Software partial/error→succeeded/error-clear with same mapping/provider identity/availability/ACK emits display256/metadata0 and stable token, final structured status/error/revision/readback/entries to both WeakMethod views. Hardware failure still suspends/unmaps its Button, produces mapping_error and invalidates stale commands; explicit repair plus matching ACK required. Unavailable/owner/quarantine/true mapping or parameter descriptor/definition/identity/session mutation retain rejection. r6 notification payload, scheduled coalescing/one scoped owner observation/current/inactive slots and public dispatch remain intact.

Source regression suite includes actual software error projection/clear, actual hardware suspend/repair/fresh ACK, conservative unknown provenance/generic error/descriptor/session and true mapping/availability/identity fences, current catalog error refresh and inactive library provenance without registry mutation. Supplemental descriptor/session signal tests replay existing builder parameter watcher mode/value callbacks; they do not substitute for the actual Action scheduled regression. Full runtime311/Inspector223 pass, source-only.

## Native first gate and packaging

New full source must be sealed from exact GitTREE, not copied wholesale from old subset mirrors with generated caches/missing ancillary paths. Preserve all old mirrors/caches/attempts. Root must verify new tree/complete patch/delta/manifest, restore fresh full original checkpoint, explicitly resume sole Inspector. First gate: actual software succeeded→three same-frame partial/error/revision4/readback.75→succeeded/error-clear with unchanged mapping/provider identity/availability/ACK fields; both real resolved WeakMethod views update honest error/health/readback, one Sync/owner observation per burst, display256/metadata0, exact unchanged assignment token. No manual Sync or periodic workaround. Preserve already accepted original same-status symptom and recheck source/DAT parity. Separately verify hardware-failure readiness/repair and true mutation fences without repeating unrelated accepted physical gates. Dependent actual tox/reload/export/physical remain held until root acceptance/restoration; no #10/#11/#13 implementation or GitHub transition from this source handoff.
