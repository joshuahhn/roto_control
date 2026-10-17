import datetime
import errno
from enum import Enum, unique
import hashlib
import json
import os
from pathlib import Path
import plistlib
import select
import signal
import subprocess
import sys
import tempfile
import time

MAX_INPUT = 16384
MAX_OUTPUT = 65536
@unique
class SerialGet(Enum):
    FW_VERSION = (1, 1, 12)
    MODE = (1, 2, 4)
    PLUGIN_KNOB_CONFIG = (3, 9, 250)
    PLUGIN_SWITCH_CONFIG = (3, 10, 247)

    @property
    def response_size(self):
        return self.value[2]

    def packet(self, payload=b''):
        if (self in (SerialGet.FW_VERSION, SerialGet.MODE) and payload != b'') or (self in
                (SerialGet.PLUGIN_KNOB_CONFIG, SerialGet.PLUGIN_SWITCH_CONFIG) and
                (len(payload) != 9 or any(x > 127 for x in payload[:8]) or payload[8] > 7)):
            raise ReadError('invalid_request', 'Invalid GET payload')
        group, subtype, _ = self.value
        return bytes((0x5a, group, subtype, 0, len(payload))) + payload


MIDI_CONTROL_LEARNED = b'\x02\x0b'


class ReadError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _bytes(value, length):
    if not isinstance(value, list) or len(value) != length or any(type(x) is not int or not 0 <= x < 128 for x in value):
        raise ReadError('invalid_request', 'Expected a seven-bit identity hash')
    return bytes(value)


def request(value):
    if not isinstance(value, dict) or set(value) != {'version', 'request_id', 'serial_session_id', 'port', 'plugin_hash', 'controls'} or value['version'] != 1:
        raise ReadError('invalid_request', 'Expected one version-1 hardware read request')
    for key in ('request_id', 'serial_session_id'):
        if not isinstance(value[key], str) or not 1 <= len(value[key]) <= 64 or not value[key].isalnum():
            raise ReadError('invalid_request', 'Invalid request/session identity')
    port = value['port']
    if not isinstance(port, str) or not port.startswith('/dev/cu.') or len(port) > 256 or any(c.isspace() for c in port):
        raise ReadError('invalid_request', 'Specify the Roto /dev/cu. USB config endpoint')
    _bytes(value['plugin_hash'], 8)
    controls = value['controls']
    if not isinstance(controls, list) or not 1 <= len(controls) <= 16:
        raise ReadError('invalid_request', 'Register 1..16 controls on PLUGIN page 0 first')
    slots, indices, hashes, ids = set(), set(), set(), set()
    for control in controls:
        if not isinstance(control, dict) or set(control) != {'id', 'kind', 'slot', 'parameter_index', 'parameter_hash'}:
            raise ReadError('invalid_request', 'Invalid expected control shape')
        if control['kind'] not in ('knob', 'button') or type(control['slot']) is not int or not 1 <= control['slot'] <= 8:
            raise ReadError('invalid_request', 'Only explicit first-page slots 1..8 are supported')
        if type(control['parameter_index']) is not int or not 0 <= control['parameter_index'] < 16384:
            raise ReadError('invalid_request', 'Invalid mapped parameter index')
        if not isinstance(control['id'], str) or not 1 <= len(control['id']) <= 512:
            raise ReadError('invalid_request', 'Invalid registered control id')
        key = control['kind'], control['slot']
        hashed = _bytes(control['parameter_hash'], 6)
        if key in slots or control['parameter_index'] in indices or hashed in hashes or control['id'] in ids:
            raise ReadError('invalid_request', 'Expected controls must have unique identities')
        slots.add(key); indices.add(control['parameter_index']); hashes.add(hashed); ids.add(control['id'])
    return value


def _text(data):
    if len(data) != 13 or 0 not in data:
        raise ReadError('protocol_error', 'Expected a NULL-terminated 13-byte hardware string')
    end = data.index(0)
    if any(data[end:]) or any(x < 32 or x > 126 for x in data[:end]):
        raise ReadError('protocol_error', 'Invalid padded ASCII hardware string')
    return data[:end].decode('ascii')


def decode_control(frame, expected, plugin_hash):
    kind = expected['kind']
    command = SerialGet.PLUGIN_KNOB_CONFIG if kind == 'knob' else SerialGet.PLUGIN_SWITCH_CONFIG
    if len(frame) != command.response_size or frame[:2] != b'\xa5\x00':
        raise ReadError('protocol_error', 'Incorrect control response length/status')
    if (frame[2:10] != bytes(plugin_hash) or frame[10] != expected['slot'] - 1 or
            int.from_bytes(frame[11:13], 'big') != expected['parameter_index'] or
            frame[13:19] != bytes(expected['parameter_hash'])):
        raise ReadError('identity_mismatch', 'Hardware PH/CI/MI/MH does not match the registered control')
    result = {key: expected[key] for key in ('id', 'kind', 'slot', 'parameter_index')}
    result.update(plugin_hash=list(frame[2:10]), parameter_hash=list(frame[13:19]), control_index=frame[10])
    if kind == 'knob':
        minimum, maximum = int.from_bytes(frame[20:22], 'big'), int.from_bytes(frame[22:24], 'big')
        name, color, mode, steps, start = _text(frame[24:37]), frame[37], frame[38], frame[41], 42
        if frame[19] not in (0, 1) or any(x > 127 and x != 255 for x in frame[39:41]):
            raise ReadError('protocol_error', 'Invalid macro or indent field')
        if mode == 1 and not 2 <= steps <= 16 or mode in (0, 2) and steps != 0:
            raise ReadError('protocol_error', 'Invalid knob step count')
        haptics = dict(mode={0: 'smooth', 1: 'steps', 2: 'plugin_top_indent'}.get(mode, 'unknown'),
                       raw_mode=mode, steps=steps, indent_positions=[None if x == 255 else x for x in frame[39:41]],
                       physical_feel_verified=False)
        result.update(macro=frame[19], haptics=haptics, button=None)
        limit = 16383
    else:
        minimum, maximum = frame[19:21]
        name, color, mode, steps, start = _text(frame[21:34]), frame[34], frame[37], frame[38], 39
        if mode not in (0, 1) or steps not in (0, *range(2, 17)) or frame[35] > 82 or frame[36] > 82:
            raise ReadError('protocol_error', 'Invalid switch mode, LEDs or step count')
        result.update(macro=None, haptics=None, button=dict(mode=('push', 'toggle')[mode], raw_mode=mode,
                      led_on=frame[35], led_off=frame[36], steps=steps))
        limit = 127
    if not 0 <= minimum <= maximum <= limit or color > 82 or steps > 16:
        raise ReadError('protocol_error', 'Invalid control range, color or step count')
    labels = [_text(frame[start + i * 13:start + (i + 1) * 13]) for i in range(16)]
    result['haptics' if kind == 'knob' else 'button']['labels'] = labels[:steps]
    result.update(name=name, minimum=minimum, maximum=maximum, color=color)
    return result


def physical_device(port):
    if sys.platform != 'darwin':
        raise ReadError('unsupported_backend', 'Serial read-back currently requires macOS. Use this API on the connected Mac; no backend is installed automatically.')
    try:
        run = subprocess.run(['/usr/sbin/ioreg', '-a', '-r', '-c', 'IOUSBHostDevice', '-l'],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=2, check=True)
        if len(run.stdout) > 4 * 1024 * 1024:
            raise ValueError('USB inventory exceeded limit')
        roots = plistlib.loads(run.stdout) if run.stdout else []
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        raise ReadError('usb_inventory', 'Cannot verify Roto USB ancestry: ' + str(exc)) from exc
    def walk(node, device=None):
        if (node.get('IOObjectClass') == 'IOUSBHostDevice' and node.get('USB Vendor Name') == 'Melbourne Instruments'
                and node.get('USB Product Name') in ('Roto_Control', 'Roto-Control')):
            device = node
        if node.get('IOCalloutDevice') == port and device is not None:
            identity = {key: device.get(key) for key in ('USB Serial Number', 'USB Vendor Name', 'USB Product Name',
                                                        'idVendor', 'idProduct', 'locationID', 'IORegistryEntryID', 'sessionID')}
            if not identity['IORegistryEntryID'] or not identity['sessionID']:
                raise ReadError('usb_inventory', 'USB incarnation is unavailable; reconnect the controller and retry')
            identity['endpoint_registry_id'] = node.get('IORegistryEntryID')
            identity['dialin_endpoint'] = node.get('IODialinDevice')
            return identity
        for child in node.get('IORegistryEntryChildren', []):
            found = walk(child, device)
            if found is not None:
                return found
    for root in roots:
        found = walk(root)
        if found is not None:
            return found
    raise ReadError('wrong_device', 'Endpoint is absent or has no Melbourne Instruments Roto USB ancestor. Specify its current /dev/cu. endpoint.')


class Retirement:
    def __init__(self, port, physical, directory=None):
        directory = Path(directory or (Path(tempfile.gettempdir()) / ('roto-serial-read-' + str(os.getuid()))))
        directory.mkdir(mode=0o700, exist_ok=True)
        stat = directory.lstat()
        if directory.is_symlink() or stat.st_uid != os.getuid() or stat.st_mode & 0o077:
            raise ReadError('retirement_unavailable', 'Serial safety directory must be owned by this user with mode 0700')
        key = json.dumps([port, physical['IORegistryEntryID'], physical['sessionID'], physical['endpoint_registry_id']], separators=(',', ':'))
        self.path = directory / (hashlib.sha256(key.encode()).hexdigest() + '.json')
        self.armed = False
        if self.path.exists():
            raise ReadError('retired_session', 'This USB endpoint has an uncertain prior reply. Physically unplug and reconnect Roto before reading again. Restarting TD does not recover this session.')

    def arm(self):
        if self.armed:
            return
        try:
            fd = os.open(str(self.path), os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0), 0o600)
        except FileExistsError as exc:
            raise ReadError('retired_session', 'This USB incarnation is busy or retired. Finish its read or physically reconnect Roto.') from exc
        with os.fdopen(fd, 'wb') as stream:
            stream.write(b'{"uncertain_reply":true}\n')
            stream.flush(); os.fsync(stream.fileno())
        self.armed = True

    def complete(self):
        if self.armed:
            self.path.unlink()
            self.armed = False


class PosixPort:
    def __init__(self, port, physical):
        import fcntl
        import termios
        self.fd, self.saved = None, None
        self.termios = termios
        aliases = [port] + ([physical['dialin_endpoint']] if physical.get('dialin_endpoint') else [])
        try:
            busy = subprocess.run(['/usr/sbin/lsof', '-t', '--', *aliases], stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, timeout=2)
            if busy.returncode not in (0, 1):
                raise ReadError('port_busy', 'Cannot check port ownership. Close Roto-Setup and retry.')
            if busy.stdout.strip():
                raise ReadError('port_busy', 'Roto Serial endpoint is in use. Close Roto-Setup or the other Serial owner and retry.')
            self.fd = os.open(port, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
            fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            fcntl.ioctl(self.fd, termios.TIOCEXCL)
            self.saved = termios.tcgetattr(self.fd)
            attrs = list(self.saved); attrs[6] = list(attrs[6])
            attrs[0] = attrs[1] = attrs[3] = 0
            attrs[2] = termios.CLOCAL | termios.CREAD | termios.CS8
            attrs[4] = attrs[5] = termios.B115200
            attrs[6][termios.VMIN] = attrs[6][termios.VTIME] = 0
            termios.tcsetattr(self.fd, termios.TCSANOW, attrs)
            if self.read(0):
                raise ReadError('protocol_error', 'Unsolicited bytes on a new Serial session; reconnect Roto before retrying')
        except OSError as exc:
            self.close()
            if exc.errno in (errno.EBUSY, errno.EAGAIN, errno.EWOULDBLOCK, errno.EACCES):
                raise ReadError('port_busy', 'Roto Serial port is busy or inaccessible. Close Roto-Setup and check access before retrying.') from exc
            raise ReadError('port_unavailable', 'Roto Serial endpoint is unavailable. Check the USB connection and current /dev/cu. path.') from exc
        except Exception:
            self.close()
            raise

    def write(self, packet, deadline):
        while packet:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not select.select([], [self.fd], [], max(0, remaining))[1]:
                raise ReadError('timeout', 'Serial GET write timed out. Physically reconnect Roto before retrying.')
            try:
                count = os.write(self.fd, packet)
                if count <= 0:
                    raise ReadError('port_closed', 'Serial endpoint closed during GET')
                packet = packet[count:]
            except BlockingIOError:
                continue

    def read(self, timeout):
        if not select.select([self.fd], [], [], max(0, timeout))[0]:
            return b''
        try:
            data = os.read(self.fd, 4096)
        except BlockingIOError:
            return b''
        if not data:
            raise ReadError('port_closed', 'Roto USB Serial endpoint closed; reconnect and refresh')
        return data

    def close(self):
        if self.fd is not None:
            try:
                if self.saved is not None:
                    self.termios.tcsetattr(self.fd, self.termios.TCSANOW, self.saved)
            finally:
                os.close(self.fd)
                self.fd = None


class ReadSession:
    def __init__(self, transport, retirement, clock=time.monotonic):
        self.transport, self.retirement, self.clock = transport, retirement, clock
        self.buffer = b''
        self.events = self.received = 0
        self.deadline = clock() + 20

    def _notification(self):
        if len(self.buffer) < 5:
            return False
        length = int.from_bytes(self.buffer[3:5], 'big')
        if length > 512:
            raise ReadError('protocol_error', 'Async frame exceeded 512 bytes')
        if len(self.buffer) < 5 + length:
            return False
        frame, self.buffer = self.buffer[:5 + length], self.buffer[5 + length:]
        self.events += 1
        if self.events > 64:
            raise ReadError('protocol_error', 'Async event limit exceeded')
        # MIDI setup learn is unrelated to the requested PLUGIN records.
        if (frame[1:3] != MIDI_CONTROL_LEARNED or len(frame) != 8 or frame[5] > 63 or frame[6] not in (0, 1) or frame[7] > 31):
            raise ReadError('context_changed', 'Serial context/config notification interrupted an outstanding GET. Physically unplug and reconnect Roto before retrying')
        return True

    def _receive(self, timeout):
        data = self.transport.read(timeout)
        self.buffer += data; self.received += len(data)
        if len(self.buffer) > 8192 or self.received > 32768:
            raise ReadError('protocol_error', 'Serial receive budget exceeded')

    def _drain_notifications(self):
        self._receive(0)
        deadline = min(self.deadline, self.clock() + 1)
        while self.buffer:
            self.retirement.arm()
            if self.buffer[0] != 0x5a:
                raise ReadError('protocol_error', 'Unsolicited trailing reply before next GET')
            if self._notification():
                self.retirement.complete()
                self._receive(0)
                continue
            remaining = deadline - self.clock()
            if remaining <= 0:
                raise ReadError('timeout', 'Partial async Serial frame timed out; physically reconnect Roto')
            self._receive(remaining)

    def get(self, command, payload=b''):
        if not isinstance(command, SerialGet):
            raise TypeError('Expected a SerialGet command')
        packet = command.packet(payload)
        self._drain_notifications()
        self.retirement.arm()
        deadline = min(self.deadline, self.clock() + 1)
        self.transport.write(packet, deadline)
        while True:
            if self.buffer:
                if self.buffer[0] == 0x5a:
                    if self._notification():
                        continue
                elif self.buffer[0] == 0xa5:
                    if len(self.buffer) >= 2:
                        if self.buffer[1]:
                            if len(self.buffer) == 2:
                                self.retirement.complete()
                            raise ReadError('device_error', 'Roto rejected GET with response code %02x' % self.buffer[1])
                        size = command.response_size
                        if len(self.buffer) >= size:
                            frame, self.buffer = self.buffer[:size], self.buffer[size:]
                            self.retirement.complete()
                            return frame
                else:
                    raise ReadError('protocol_error', 'Unframed or unsolicited Serial reply')
            remaining = min(deadline, self.deadline) - self.clock()
            if remaining <= 0:
                raise ReadError('timeout', 'Serial GET timed out. Physically unplug and reconnect Roto before retrying this endpoint.')
            self._receive(remaining)

    def finish(self):
        self._drain_notifications()


def capture(value, *, inventory=physical_device, open_port=PosixPort, retirement_factory=Retirement):
    value = request(value)
    physical = inventory(value['port'])
    retired = retirement_factory(value['port'], physical)
    transport = None
    started = utc()
    try:
        transport = open_port(value['port'], physical)
        session = ReadSession(transport, retired)
        fw = session.get(SerialGet.FW_VERSION)
        git = fw[5:12].decode('ascii')
        if any(c not in '0123456789abcdefABCDEF' for c in git):
            raise ReadError('protocol_error', 'Invalid firmware revision')
        mode = session.get(SerialGet.MODE)
        if mode[2:] != b'\x01\x00':
            raise ReadError('unsupported_page', 'Select PLUGIN first page on Roto. This read-only API never changes hardware mode/page.')
        controls = [decode_control(session.get(SerialGet.PLUGIN_KNOB_CONFIG if c['kind'] == 'knob' else SerialGet.PLUGIN_SWITCH_CONFIG, bytes(value['plugin_hash']) + bytes((c['slot'] - 1,))),
                                   c, value['plugin_hash']) for c in value['controls']]
        if session.get(SerialGet.MODE)[2:] != mode[2:]:
            raise ReadError('context_changed', 'Hardware mode/page changed during capture')
        session.finish()
        if inventory(value['port']) != physical:
            raise ReadError('context_changed', 'Roto USB incarnation changed during capture')
        captured = utc()
        result = dict(controls=controls, provenance=dict(physical_device=physical, endpoint=value['port'],
            serial_session_id=value['serial_session_id'], request_id=value['request_id'], page_offset=0,
            firmware=dict(major=fw[2], minor=fw[3], patch=fw[4], git=git, version='.'.join(str(x) for x in fw[2:5])),
            started_at_utc=started, captured_at_utc=captured, observed_through_utc=captured,
            observation='snapshot_only', worker_closed=True))
    except BaseException as exc:
        if getattr(exc, 'code', None) in ('protocol_error', 'timeout', 'port_closed'):
            retired.arm()
        raise
    finally:
        if transport is not None:
            transport.close()
    return result


def main():
    value = {}
    def cancelled(signum, frame):
        raise ReadError('cancelled', 'Serial read cancelled')
    signal.signal(signal.SIGTERM, cancelled)
    try:
        raw = sys.stdin.buffer.read(MAX_INPUT + 1)
        if len(raw) > MAX_INPUT:
            raise ReadError('invalid_request', 'Hardware request exceeded size limit')
        value = json.loads(raw)
        result = dict(ok=True, snapshot=capture(value))
    except Exception as exc:
        result = dict(ok=False, error=dict(code=getattr(exc, 'code', 'worker_error'), message=str(exc)[:1024]))
    result.update(version=1, request_id=value.get('request_id') if isinstance(value, dict) else None,
                  serial_session_id=value.get('serial_session_id') if isinstance(value, dict) else None)
    encoded = json.dumps(result, separators=(',', ':'), allow_nan=False)
    if len(encoded.encode()) > MAX_OUTPUT:
        raise RuntimeError('Serial output exceeded limit')
    print(encoded, flush=True)


if __name__ == '__main__':
    main()
