"""Read-only final baseline checks, after actual recovery load and MIDI handoff.

External orchestration only: never installs source, clears tokens or fabricates ACK.
Derived DAT output differences are reported rather than overwritten.
"""
from pathlib import Path
import hashlib
import json
import os


def verify(folder):
    folder = Path(folder)
    baseline = json.loads((folder / 'live_baseline.json').read_text())
    c = op(baseline['controller'])
    e = c.ext.RotoPythonExt
    failures = []
    def compare(label, expected, actual):
        if json.dumps(expected, sort_keys=True, default=str) != json.dumps(actual, sort_keys=True, default=str):
            failures.append(dict(field=label, expected=expected, actual=actual))
    compare('routing', baseline['routing']['key'], c.GetLayoutContext()['key'])
    compare('Follow preference', baseline['follow']['enabled'], c.GetCompContext()['enabled'])
    compare('registry', baseline['registry'], c.fetch('layout_registry'))
    for name, value in baseline['materialized'].items():
        compare('materialized.' + name, value, c.fetch(name, None))
    for key, row in baseline['native_targets'].items():
        owner = op(row['owner'])
        par = getattr(owner.par, row['name'], None) if owner else None
        if par is None:
            failures.append(dict(field=key, reason='native parameter absent'))
            continue
        for name in ('style', 'label', 'default', 'normMin', 'normMax', 'min', 'max', 'clampMin', 'clampMax'):
            compare(key + '.' + name, row[name], getattr(par, name))
        compare(key + '.menuNames', row['menuNames'], list(par.menuNames or ()))
        compare(key + '.menuLabels', row['menuLabels'], list(par.menuLabels or ()))
        if row['style'] != 'Pulse':
            compare(key + '.value', row['value'], par.eval())
    tokens = json.loads((folder / 'owner_tokens_baseline.json').read_text())
    for path, row in tokens.items():
        comp = op(path)
        if comp is None:
            failures.append(dict(field=path, reason='original COMP absent'))
            continue
        actual = dict(present='roto_control_owner_id' in comp.storage,
                      value=comp.fetch('roto_control_owner_id', None, search=False))
        compare(path + '.local_token', row, actual)
    source_deltas = []
    for row in baseline['sources']:
        dat = op(row['path'])
        if dat is None:
            failures.append(dict(field=row['path'], reason='original DAT absent'))
            continue
        expected = (folder / 'live_sources' / (row['path'].lstrip('/') + '.txt')).read_text()
        actual = dat.text.replace('\r\n', '\n')
        if actual != expected.replace('\r\n', '\n'):
            language = dat.par.language.eval() if hasattr(dat.par, 'language') else ''
            delta = dict(path=dat.path, language=language,
                         actual_sha256=hashlib.sha256(actual.encode()).hexdigest())
            source_deltas.append(delta)
            if language == 'python':
                failures.append(dict(field=dat.path, reason='Python source differs'))
    compare('physical fixture removed', False, bool(op('/roto_control_python/base_physical_test')))
    compare('recorder removed', False, bool(getattr(e, '_tab_layout_probe', None)))
    record = dict(td_pid=os.getpid(), project=project.name, failures=failures,
                  source_deltas=source_deltas, source_count=len(baseline['sources']),
                  midi_pid=getattr(e._process, 'pid', None), state=dict(c.State),
                  routing=c.GetLayoutContext(), follow=c.GetCompContext())
    (folder / 'final_restoration_comparison.json').write_text(json.dumps(record, indent=2, default=str) + '\n')
    return record
