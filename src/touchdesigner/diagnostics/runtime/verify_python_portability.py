"""Run stages in live TD. Patch only portable interpreter resolution, retain mappings."""
import copy
import json
import os
from pathlib import Path

SOURCE = Path('/Users/huihongnin/project/roto_control/src/touchdesigner')
CANDIDATE = Path('/private/tmp/roto-control-issue15/src/touchdesigner')
RESULTS = SOURCE / 'diagnostics/runtime/results/python_portability'
RECOVERY = SOURCE / 'projects/archive/python-portability-recovery'
CONTROLLER = '/roto_clean_demo/roto_python'
EXPORT = SOURCE / 'exports/roto_python.portable.20261011.tox'


def snapshot(c):
    c.ext.RotoPythonExt._layout_manager().capture(force=True)
    registry = c.GetLayoutRegistry()
    registry.pop('revision', None)
    # Live readouts and consumed hardware-unmap queues are not mapping definitions.
    for layout in registry['records']:
        for track in layout['tracks']:
            for device in track['plugins']:
                state = device.get('state', {})
                targets = {target['id']: target for target in
                           state.get('page_targets', []) + device.get('targets', [])}
                for assignment in state.get('parameter_assignments', []):
                    target = targets.get(assignment['id'])
                    if target is not None:
                        for key in ('identity', 'menu_names', 'menu_labels'):
                            if key in target:
                                # Extension restoration hydrates metadata from saved targets.
                                assert assignment.get(key, target[key]) == target[key], key
                                assignment.setdefault(key, copy.deepcopy(target[key]))
                for key in ('control_catalog', 'pending_unmaps', 'pending_unmap_identities'):
                    state.pop(key, None)
    result = dict(registry=registry,
                snapshots=copy.deepcopy(c.fetch('snapshot_presets', None)),
                values={node.name: {p.name: p.eval() for p in node.customPars}
                        for node in c.parent().children if node.name in ('demo_A', 'demo_B')},
                geometry={node.path: [node.nodeX, node.nodeY, node.nodeWidth, node.nodeHeight]
                          for node in (c,) + tuple(c.findChildren())})
    return json.loads(json.dumps(result, default=str))


def write(name, data):
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / (name + '.json')).write_text(json.dumps(data, indent=2, default=str) + '\n')
    print(json.dumps(data if name != 'before' else {'recovery_saved': True, 'baseline_saved': True}, default=str))


def prepare():
    assert Path(project.folder) == SOURCE / 'projects/current'
    c = op(CONTROLLER)
    assert c.ext.RotoPythonExt._process is None
    RECOVERY.mkdir(parents=True, exist_ok=True)
    destination = RECOVERY / 'configured-controller.tox'
    assert not destination.exists()
    c.save(str(destination))
    before = snapshot(c)
    before['python'] = c.par.Python.eval()
    (RECOVERY / 'RotoPythonExt.py').write_text(c.op('RotoPythonExt').text)
    write('before', before)


def install():
    c = op(CONTROLLER)
    assert c.ext.RotoPythonExt._process is None
    original = (RECOVERY / 'RotoPythonExt.py').read_text()
    assert c.op('RotoPythonExt').text == original
    patched = (SOURCE / 'code/py/roto_python/RotoPythonExt.py').read_text()
    resolver = patched[patched.index('def resolve_python('):patched.index('class RotoPythonExt:')]
    old = ('        # Keep the venv entry-point symlink: resolving it loses venv discovery.\n'
           '        python = (folder / self.ownerComp.par.Python.eval()).absolute()\n'
           '        if not python.is_file():\n'
           '            raise FileNotFoundError("Configure a Python interpreter with mido and python-rtmidi")\n')
    assert original.count(old) == 1
    updated = original.replace('import subprocess\n', 'import shutil\nimport subprocess\n', 1)
    updated = updated.replace('class RotoPythonExt:', resolver + 'class RotoPythonExt:', 1)
    updated = updated.replace(old, '        python = resolve_python(self.ownerComp.par.Python.eval(), folder)\n', 1)
    c.op('RotoPythonExt').text = updated
    before = json.loads((RESULTS / 'before.json').read_text())
    c.par.Python.default = c.par.Python.val = os.path.relpath(before['python'], project.folder)
    c.initializeExtensions(0)
    c.Applybinding()
    # Embed only the changed Markdown snapshot through the documentation helper.
    path = CANDIDATE / 'scripts/td_project_docs.py'
    namespace = dict(globals())
    exec(compile(path.read_text(), str(path), 'exec'), namespace)
    content = dict(namespace['read_project_docs'](CANDIDATE)['functions'])['portability']
    namespace['_write_text_dat'](c.op('docs/fn_portability_md'), content, 'docs/functions/portability.md')
    after = snapshot(c)
    for key in ('registry', 'snapshots', 'values', 'geometry'):
        assert after[key] == before[key], key + ' changed during interpreter patch'
    write('installed', dict(python=c.par.Python.eval(), preserved=list(after),
                            path_command=c.op('RotoPythonExt').module.resolve_python('python3', project.folder)))


def export_generic():
    c = op(CONTROLLER)
    c.Disconnect()
    path = CANDIDATE / 'scripts/export_component.py'
    namespace = dict(globals())
    exec(compile(path.read_text(), str(path), 'exec'), namespace)
    namespace['export'](c, EXPORT)
    holder = op('/').create(baseCOMP, 'base_python_portability_verify')
    try:
        clone = holder.loadTox(str(EXPORT))
        clone.Applybinding()
        assert clone.par.Python.eval() == clone.par.Python.default == 'python3'
        assert clone.ext.RotoPythonExt._process is None
        assert not clone.State['Connected']
        assert not clone.par.Followcomp.eval()
        assert clone.GetControlCatalog() == []
        assert not clone.fetch('snapshot_presets', {}).get('records', [])
        assert all(not node.par.file.eval() for node in clone.findChildren(type=DAT)
                   if hasattr(node.par, 'file'))
        clone.op('inspector/owned_runtime').module.validate(clone)
        assert clone.op('docs/fn_portability_md').text == (CANDIDATE / 'docs/functions/portability.md').read_text()
        write('export', dict(path=str(EXPORT), python=clone.par.Python.eval(),
                             empty=True, disconnected=True, embedded=True, owned_inspector=True))
    finally:
        holder.destroy()


def verify_connection():
    c = op(CONTROLLER)
    assert c.State['Connected'] and c.State['Plugin'], c.State
    assert c.ext.RotoPythonExt._process.poll() is None
    before = json.loads((RESULTS / 'before.json').read_text())
    after = snapshot(c)
    for key in ('registry', 'snapshots', 'values', 'geometry'):
        assert after[key] == before[key], key + ' changed after reconnect'
    write('connection', dict(python=c.par.Python.eval(), state=c.State, mappings_preserved=True))
