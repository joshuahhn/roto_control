import copy
from dataclasses import dataclass
import json
import os
import subprocess
import sys
import time
import uuid

MAX_RESULT = 65536


@dataclass(frozen=True)
class ReadContext:
    host: object
    signature: tuple
    manifest: dict
    public: dict

    def matches(self, other):
        return self.host is other.host and self.signature == other.signature


class HardwareConfig:
    def __init__(self, *, spawn=subprocess.Popen, clock=time.monotonic):
        self.spawn, self.clock = spawn, clock
        self.generation = 0
        self.context = None
        self.job = None
        self.result = dict(status='never_read', request_id=None, error=None,
                           invalidation_reason=None, snapshot=None)

    @property
    def active(self):
        return self.job is not None

    def observe(self, context):
        if self.context is not None and not self.context.matches(context):
            self.invalidate('Registered Device/control context changed')
        self.context = context

    def invalidate(self, reason):
        self.generation += 1
        if self.result['status'] in ('captured', 'reading'):
            self.result.update(status='stale', error=None, invalidation_reason=reason)
        if self.job is not None:
            self._retire()

    def fail(self, code, message):
        self.result.update(status='error', error=dict(code=code, message=str(message)[:1024]),
                           invalidation_reason=None, snapshot=None)
        if self.job is not None:
            self._retire()
        return copy.deepcopy(self.result)

    def read(self, context, *, port, python, worker_source):
        try:
            self.observe(context)
            if self.job is not None:
                if self.result['status'] == 'reading' and port == self.job['request']['port']:
                    return copy.deepcopy(self.result)
                result = copy.deepcopy(self.result)
                result['error'] = dict(code='busy', message='A Serial worker is still finishing; retry after Tick completes cleanup')
                return result
            if sys.platform != 'darwin':
                return self.fail('unsupported_backend', 'Serial read-back currently requires macOS. Run this API on the connected Mac; no backend is installed automatically.')
            if not isinstance(port, str) or not port.startswith('/dev/cu.') or len(port) > 256 or any(c.isspace() for c in port):
                return self.fail('invalid_request', 'Specify the Roto /dev/cu. USB config endpoint')
            if not worker_source or not worker_source.strip():
                return self.fail('missing_worker', 'Install the embedded serial_read_process DAT before reading hardware')
            request_id, session_id = uuid.uuid4().hex, uuid.uuid4().hex
            request = dict(version=1, request_id=request_id, serial_session_id=session_id, port=port, **copy.deepcopy(context.manifest))
            encoded = json.dumps(request, separators=(',', ':'), allow_nan=False).encode()
            if len(encoded) > 16384:
                return self.fail('invalid_request', 'Expected hardware identities exceeded request size limit')
            process = self.spawn([str(python), '-u', '-c', worker_source], stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)
            self.job = dict(process=process, request=request, context=context, generation=self.generation,
                            pending=encoded, output=b'', stderr=b'', eof=False, stderr_eof=False, deadline=self.clock() + 25,
                            stopping=None, killed=False)
            for stream in (process.stdin, process.stdout, process.stderr):
                os.set_blocking(stream.fileno(), False)
            self.result = dict(status='reading', request_id=request_id, error=None, invalidation_reason=None, snapshot=None)
        except Exception as exc:
            self.fail('worker_error', exc)
        return copy.deepcopy(self.result)

    def snapshot(self, context):
        try:
            self.observe(context)
        except Exception as exc:
            self.fail('context_error', exc)
        return copy.deepcopy(self.result)

    def _retire(self):
        job = self.job
        if job['stopping'] is None:
            job['stopping'] = self.clock() + .2
            try:
                if job['process'].poll() is None:
                    job['process'].terminate()
            except Exception:
                pass

    def _reap(self):
        process = self.job['process']
        for stream in (process.stdin, process.stdout, process.stderr):
            try:
                stream.close()
            except Exception:
                pass
        self.job = None

    def close(self, reason):
        self.invalidate(reason)
        if self.job is None:
            return
        process = self.job['process']
        try:
            try:
                process.wait(timeout=.05)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=.05)
        except Exception as exc:
            self.result.update(status='error', error=dict(code='cleanup_error', message=str(exc)[:1024]), snapshot=None)
            return
        self._reap()

    def _accept(self, job):
        raw = job['output']
        if not job['eof'] or not raw.endswith(b'\n') or raw.count(b'\n') != 1 or job['stderr']:
            raise ValueError('Expected exactly one terminal Serial result and clean EOF')
        event = json.loads(raw)
        request = job['request']
        if (not isinstance(event, dict) or event.get('version') != 1 or
                event.get('request_id') != request['request_id'] or event.get('serial_session_id') != request['serial_session_id'] or
                type(event.get('ok')) is not bool):
            raise ValueError('Serial result request/session mismatch')
        if not event['ok']:
            if set(event) != {'version', 'request_id', 'serial_session_id', 'ok', 'error'}:
                raise ValueError('Invalid Serial error envelope')
            error = event['error']
            if not isinstance(error, dict) or set(error) != {'code', 'message'} or any(not isinstance(error[k], str) for k in error):
                raise ValueError('Invalid Serial worker error')
            self.fail(error['code'], error['message'])
            return
        if set(event) != {'version', 'request_id', 'serial_session_id', 'ok', 'snapshot'}:
            raise ValueError('Invalid Serial result envelope')
        snapshot = event['snapshot']
        if not isinstance(snapshot, dict) or set(snapshot) != {'controls', 'provenance'}:
            raise ValueError('Invalid Serial snapshot')
        controls, provenance = snapshot['controls'], snapshot['provenance']
        if not isinstance(controls, list) or len(controls) != len(request['controls']) or not isinstance(provenance, dict):
            raise ValueError('Incomplete Serial control set')
        for expected, actual in zip(request['controls'], controls):
            if (not isinstance(actual, dict) or any(actual.get(k) != v for k, v in expected.items()) or
                    actual.get('plugin_hash') != request['plugin_hash'] or actual.get('control_index') != expected['slot'] - 1):
                raise ValueError('Serial result control identity mismatch')
            if set(actual) != {'id', 'kind', 'slot', 'parameter_index', 'plugin_hash', 'parameter_hash', 'control_index',
                               'macro', 'haptics', 'button', 'name', 'minimum', 'maximum', 'color'}:
                raise ValueError('Invalid detected control shape')
            if not isinstance(actual['name'], str) or len(actual['name']) > 12 or not actual['name'].isascii():
                raise ValueError('Invalid detected control name')
            limit = 16383 if expected['kind'] == 'knob' else 127
            if any(type(actual[k]) is not int for k in ('minimum', 'maximum', 'color')) or not 0 <= actual['minimum'] <= actual['maximum'] <= limit or not 0 <= actual['color'] <= 82:
                raise ValueError('Invalid detected control range/color')
            setting = actual['haptics'] if expected['kind'] == 'knob' else actual['button']
            if not isinstance(setting, dict) or type(setting.get('steps')) is not int or not 0 <= setting['steps'] <= 16 or not isinstance(setting.get('labels'), list) or len(setting['labels']) != setting['steps'] or any(not isinstance(x, str) or len(x) > 12 or not x.isascii() for x in setting['labels']):
                raise ValueError('Invalid detected haptic/button settings')
            if expected['kind'] == 'knob':
                if (actual['button'] is not None or type(actual['macro']) is not int or actual['macro'] not in (0, 1)
                        or set(setting) != {'mode', 'raw_mode', 'steps', 'indent_positions', 'labels', 'physical_feel_verified'}
                        or type(setting['raw_mode']) is not int or not 0 <= setting['raw_mode'] <= 255
                        or setting['mode'] != {0: 'smooth', 1: 'steps', 2: 'plugin_top_indent'}.get(setting['raw_mode'], 'unknown')
                        or setting['physical_feel_verified'] is not False
                        or not isinstance(setting['indent_positions'], list) or len(setting['indent_positions']) != 2
                        or any(x is not None and (type(x) is not int or not 0 <= x <= 127) for x in setting['indent_positions'])
                        or setting['raw_mode'] == 1 and not 2 <= setting['steps'] <= 16
                        or setting['raw_mode'] in (0, 2) and setting['steps'] != 0):
                    raise ValueError('Invalid detected knob settings')
            elif (actual['haptics'] is not None or actual['macro'] is not None
                  or set(setting) != {'mode', 'raw_mode', 'steps', 'led_on', 'led_off', 'labels'}
                  or type(setting['raw_mode']) is not int or setting['raw_mode'] not in (0, 1)
                  or setting['mode'] != ('push', 'toggle')[setting['raw_mode']]
                  or setting['steps'] not in (0, *range(2, 17))
                  or any(type(setting[k]) is not int or not 0 <= setting[k] <= 82 for k in ('led_on', 'led_off'))):
                raise ValueError('Invalid detected button settings')
        if (provenance.get('request_id') != request['request_id'] or provenance.get('serial_session_id') != request['serial_session_id'] or
                provenance.get('endpoint') != request['port'] or provenance.get('page_offset') != 0 or
                provenance.get('observation') != 'snapshot_only' or provenance.get('worker_closed') is not True or
                not isinstance(provenance.get('physical_device'), dict) or not isinstance(provenance.get('firmware'), dict) or
                any(not isinstance(provenance.get(k), str) for k in ('started_at_utc', 'captured_at_utc', 'observed_through_utc'))):
            raise ValueError('Invalid Serial capture provenance')
        snapshot = copy.deepcopy(snapshot)
        snapshot['context'] = copy.deepcopy(job['context'].public)
        snapshot['provenance']['device_id'] = job['context'].public['device_id']
        self.result.update(status='captured', error=None, invalidation_reason=None, snapshot=snapshot)

    def tick(self, context):
        try:
            self.observe(context)
            job = self.job
            if job is None:
                return
            process = job['process']
            if job['stopping'] is not None:
                if process.poll() is not None:
                    self._reap()
                elif self.clock() >= job['stopping'] and not job['killed']:
                    process.kill(); job['killed'] = True
                return
            if self.clock() >= job['deadline']:
                self.fail('timeout', 'Serial worker exceeded its total deadline; physically reconnect Roto before retrying')
                return
            if job['pending']:
                try:
                    count = os.write(process.stdin.fileno(), job['pending'])
                    job['pending'] = job['pending'][count:]
                except BlockingIOError:
                    pass
                if not job['pending']:
                    process.stdin.close()
            for key, stream in (('output', process.stdout), ('stderr', process.stderr)):
                for _ in range(4):
                    try:
                        chunk = os.read(stream.fileno(), 16384)
                    except BlockingIOError:
                        break
                    if not chunk:
                        job['eof' if key == 'output' else 'stderr_eof'] = True
                        break
                    job[key] += chunk
                    if len(job[key]) > (MAX_RESULT if key == 'output' else 4096):
                        raise ValueError('Serial worker pipe exceeded size limit')
            code = process.poll()
            if code is not None:
                if code != 0:
                    raise ValueError('Serial worker exited with code ' + str(code))
                if not job['eof'] or not job['stderr_eof']:
                    return
                if job['generation'] == self.generation:
                    self._accept(job)
                self._reap()
        except Exception as exc:
            self.fail('worker_error', exc)
