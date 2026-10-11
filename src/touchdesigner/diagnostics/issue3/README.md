# Issue #3 verification

`verify_native.py` runs against an isolated freshly built controller with no MIDI
process. It verifies equal-valued destination identity, range drift, injected
late commit failure, native watcher/table/library restoration and subsequent ACK.
`native.json` records the passing checks.

Physical evidence records Alpha baseline, same-value Assign replacement to Beta,
and same-value Free Learn offer/ACK replacement back to Alpha. The user confirmed
input/LCD behavior. Original mappings/values/context were restored afterward.

Recovery tox exports and original configuration snapshots are retained locally;
they are not published as generic components. The native runner creates a test
COMP and requires its caller to disconnect and remove the isolated fixture.
