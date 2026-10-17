# Named Serial and SysEx commands

The command identity belongs to a named Enum member. Callers build payloads and
retain their existing send, framing, routing and session policies. This replaces
the raw group/id APIs in current TD code without changing supported capabilities.

## SysEx

`protocol.SysExCommand` binds each used group/id pair to one name and emits a
complete message. `SysExGroup` names the three groups, including group ownership
for unknown commands. Definitions remain in the existing protocol module.

```python
from protocol import SysExCommand, text13

host._send(SysExCommand.DAW_STARTED.message())
host._send(SysExCommand.SET_CURRENT_TRACK_NAME.message(text13(label)))
```

`SysExCommand.identify(frame)` reads identity only and returns a member or None.
It does not validate the manufacturer header, F7, payload or target identity.
Each receiving parser keeps its original guards, including deliberately loose
queue/Follow filters and unknown MIX-group ownership. Do not use identity lookup
as a substitute for those guards.

## Serial

The standalone worker owns `SerialGet`. Its four members bind a GET identity,
request framing and response length. `ReadSession.get()` accepts a member;
registered control kinds are converted at the validated request boundary.

```python
frame = session.get(SerialGet.MODE)
frame = session.get(SerialGet.PLUGIN_SWITCH_CONFIG, plugin_hash_and_index)
```

Serial and SysEx remain separate transport implementations. The Serial worker
needs no TD-module import or new dependency. Naming commands adds no SET support,
automatic retry, configuration transaction or public configuration editor.

## Migration boundary

The old `sysex`, Host `_command`, MIX `command`, Serial `_packet`/`COMMANDS` and
string GET selectors are removed together with their callers. No compatibility
wrapper or numeric overload remains. Payload construction, packet order,
seven-bit validation, ACK/session checks, queue ownership and retirement policy
retain their existing owners.

Current runtime, scripts, builders/upgraders, verifiers, tests, diagnostics and
prototype Python are included. Raw inbound/expected wire fixtures remain
independent test oracles. Inherited Ableton/Bitwig/Logic integrations and historical
project/archive snapshots are preserved as references.

The pre-migration corpus records 158 packets and eight payload-error outcomes.
Two invalid raw-selector cases are retired separately because the raw API itself
is removed. Source-pattern checks, wire equivalence, behavior tests and native
module/import verification establish different parts of the migration contract.
Final commands, counts and artifact identity are recorded in HANDOFF and receipts.

## Repeatable gate

Run from the checkout root:

```sh
python3 src/touchdesigner/verify/verify_named_commands.py --json /tmp/named-commands.json
```

The final migration scans 253 Python files and 69 literal executable snippets.
All eight categories must be zero. Exact negative-test and inert DAT fixture
exceptions, two unrelated diagnostic CLI syntax exceptions, and 187 unresolved
dynamic executable expressions are listed individually in the report. The gate
checks the maintained source roots and declared lexical patterns. It does not
prove arbitrary reflection, generated code or historical binary contents.
