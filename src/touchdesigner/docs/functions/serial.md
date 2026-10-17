# Read stored hardware configuration

The optional Serial API reads the stored PLUGIN configuration for the current
Device's controls. It uses a separate, one-shot Python worker and an explicit
Serial endpoint. It works while MIDI is disconnected. Connect remains the MIDI
connection action.

```python
controller = op('roto_python')
controller.ReadHardwareConfig(port='/dev/cu.usbmodem1101')
# Existing TD frame callbacks service the worker.
result = controller.GetHardwareConfig()
```

The endpoint above is an example from the accepted machine. Its numeric suffix
is not a device identity. The worker verifies Roto-Control USB ancestry before
opening the endpoint. This first version supports macOS through standard-library
POSIX transport. Other platforms return an unsupported-backend error. No extra
Python package is installed or required for Serial reads.

## Inspector Details

Select a registered control and open Details. In Hardware snapshot, enter the
current Serial endpoint and click Read hardware. Refresh hardware takes another
explicit snapshot. Each Inspector view shares its endpoint draft between its
inline and popup editors; another view has its own draft. Opening, selecting,
typing, Browse and the Technical Refresh action never start a Serial read.

The readout separates detected settings from the declared button input adapter.
It includes capture time, source endpoint, USB/firmware and Serial session.
Captured means a historical observation. An exact-identity stale snapshot retains
its settings and reason; another Device or incomplete/changed control identity
withholds them. Errors clear superseded settings. A blocked or finishing worker
shows a reason and requires an explicit retry after cleanup.

Serial updates leave Value/Mapping drafts, their tokens and pending Clear intact.
Endpoint drafts and observations are transient. Configured reload starts at
never_read with empty inputs; generic exports also clear detected readout text.
The additive `upgrade/upgrade_inspector_hardware.py` installs this section into
an existing owned Inspector after project/ownership/transport checks and a new
recovery export. It does not rebuild the Inspector or restart TD.

## Results

Both methods return detached dictionaries. `GetHardwareConfig()` observes state
without opening a port or starting a refresh. The result status is one of:

| Status | Meaning |
| --- | --- |
| `never_read` | No read has started in this extension instance. |
| `reading` | A bounded read is in progress. |
| `captured` | The complete requested set passed identity and context checks. |
| `stale` | A known context or lifecycle change invalidated the capture. |
| `error` | The read failed. `error` contains a code and message. |

Repeating the same refresh while it is reading returns the current request.
Another refresh returns a busy error until the owned worker finishes cleanup.
Requests are not queued.

A captured snapshot includes the endpoint, physical USB identity, firmware,
Serial session, capture time, requested Device, and detected controls.
Configuration fields describe stored hardware settings. They do not change
declared button adapters, mapping readiness, or target values.

The worker closes its port after each read. A snapshot is a historical
observation, not continuous monitoring. External edits after the capture window
are unknown until another explicit read. Known binding, page, routing, mode, and
lifecycle changes make the snapshot stale. Stale data remains historical evidence
and must not be associated with another Device's slots.

## Read boundary

This version supports PLUGIN page offset zero and at most eight knobs and eight
buttons. Each reply must match the Plugin hash, physical control index, mapped
parameter index, and parameter hash. A slot number or display name alone cannot
establish a match. Another hardware page returns an unsupported-page error.

The worker sends firmware GET, mode GET, PLUGIN knob GET, and PLUGIN switch GET
only. It never starts a configuration transaction, changes settings, enters
LEARN, or updates firmware. Mode checks before and after the batch reject a
changed page or mode. A failed control rejects the whole snapshot.

Replies have no command ID. A timeout or uncertain frame therefore retires the
endpoint for that USB incarnation. Ordinary refresh, Disconnect, and extension
reload do not make ambiguous delayed replies safe. A verified new USB incarnation
after physical reconnection is the recovery boundary. There is no automatic retry.

Serial failures remain in this API's result. They do not set the MIDI error,
disconnect MIDI, or write mappings, parameter values, Layouts, or the catalog.
Disconnect and extension destruction stop any owned read worker. Project load
and generic export start without a Serial connection or saved observation.

Known haptic codes retain their protocol meaning. Unknown codes remain unknown.
The PLUGIN code named top-indent does not establish a measured physical feel.
See the [feasibility evidence](../plans/serial-readback-feasibility.md) for packet
offsets, the old plugin reference, and physical acceptance limits.
