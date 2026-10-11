"""Live TD packaging check from the organized source tree; no hardware test I/O."""
from pathlib import Path
import hashlib
import json

SOURCE = Path(__file__).resolve().parents[2]
RESULTS = SOURCE / 'diagnostics/validation/builder_recheck'
ROOT = '/base_builder_recheck'
MAIN = '/roto_clean_demo/roto_python'


def run_script(name):
    path = SOURCE / 'scripts' / name
    ns = dict(globals())
    exec(compile(path.read_text(), str(path), 'exec'), ns)
    return ns


def write(name, data):
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / (name + '.json')).write_text(json.dumps(data, indent=2, default=str) + '\n')
    print(json.dumps(data, default=str))


def main_state():
    c = op(MAIN)
    return dict(sources={n.path[len(c.path):]: hashlib.sha256(n.text.encode()).hexdigest()
                        for n in c.findChildren(type=DAT) if n.OPType == 'textDAT'},
                registry=c.GetLayoutRegistry(), catalog=c.GetControlCatalog(),
                connected=c.ext.RotoPythonExt._host.connected,
                pid=c.ext.RotoPythonExt._process.pid if c.ext.RotoPythonExt._process else None)


def start():
    assert project.folder == '/Users/huihongnin/project/roto_control/src/touchdesigner/projects/current'
    assert op(ROOT) is None
    before = main_state()
    holder = op('/').create(baseCOMP, ROOT[1:])
    holder.store('main_before', before)
    holder.nodeX, holder.nodeY = 1600, -1600
    source_before = {str(p.relative_to(SOURCE)): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in (SOURCE/'code/py').rglob('*.py')}
    c = run_script('build_network.py')['build'](holder, SOURCE)
    assert source_before == {str(p.relative_to(SOURCE)): hashlib.sha256(p.read_bytes()).hexdigest()
                             for p in (SOURCE/'code/py').rglob('*.py')}
    holder.store('source_before', source_before)
    assert not c.errors(recurse=True)
    assert c.ext.RotoPythonExt._process is None
    assert not c.ext.RotoPythonExt._restore_pending
    assert c.ext.RotoPythonExt._layout_ready
    # Isolated worktree has no private venv; explicitly configure the existing interpreter.
    c.par.Python = '/Users/huihongnin/project/roto_control/src/touchdesigner/.venv/bin/python'
    assert c.op('midi_process').text == (SOURCE/'scripts/midi_process.py').read_text()
    assert c.op('readme_md').text == (SOURCE/'README.md').read_text()
    assert c.op('docs/overview_md').text == (SOURCE/'docs/overview.md').read_text()
    model = c.op('inspector/inspector_model').ext.InspectorModel
    assert model.adapter.controller == c
    c.op('inspector/owned_runtime').module.validate(c)
    page = holder.appendCustomPage('Builder test')
    par = page.appendFloat('Amount')[0]
    par.min = par.normMin = 0; par.max = par.normMax = 1; par.val = .35
    record = c.AssignParameter('knob', 1, par)
    holder.store('mapping_id', record['id'])
    write('build', dict(entry='scripts/build_network.py', errors=c.errors(recurse=True),
                       embedded_midi=True, embedded_docs=True, local_controller=True, source_bytes_preserved=True,
                       hardware_process=False, explicit_python=c.par.Python.eval()))


def upgrade():
    holder = op(ROOT); c = holder.op('roto_python')
    assert c.ext.RotoPythonExt._process is None
    before = c.GetLayoutRegistry()
    mapping_id = holder.fetch('mapping_id')
    run_script('upgrade_layouts.py')['upgrade'](c, SOURCE)
    c.Applybinding()
    assert any(r['id'] == mapping_id for r in c.GetControlCatalog())
    assert c.GetLayoutRegistry()['active'] == before['active']
    assert holder.par.Amount.eval() == .35
    c.op('inspector/owned_runtime').module.validate(c)
    # Real TD Par numeric equality must not suppress a destination replacement.
    page = holder.customPages[-1]
    alternate = page.appendFloat('Alternate')[0]
    alternate.min = alternate.normMin = 0; alternate.max = alternate.normMax = 1
    alternate.val = holder.par.Amount.eval()
    assert alternate == holder.par.Amount
    replaced = c.AssignParameter('knob', 1, alternate)
    assert replaced['id'] != mapping_id
    assert c.ext.RotoPythonExt._collection.bindings['knob',1].parameter.name == 'Alternate'
    restored = c.AssignParameter('knob', 1, holder.par.Amount)
    assert restored['id'] != replaced['id']
    assert c.ext.RotoPythonExt._collection.bindings['knob',1].parameter.name == 'Amount'
    holder.store('mapping_id', restored['id'])
    wrapper = c.op('inspector')
    marker = wrapper.fetch('owned_inspector_sources')
    same = run_script('build_inspector.py')['build'](c, SOURCE)
    assert same == wrapper and same.fetch('owned_inspector_sources') == marker
    record = c.SaveSnapshot('Builder save/load', [('knob', 1)])
    holder.store('snapshot_id', record['id'])
    assert holder.par.Amount.eval() == .35
    write('upgrade', dict(entry='scripts/upgrade_layouts.py', mapping_retained=True,
                         layout_retained=True, inspector_idempotent=True, native_equal_value_reassignment=True,
                         snapshot_no_write=True, errors=c.errors(recurse=True)))


def exports():
    holder = op(ROOT); c = holder.op('roto_python')
    configured = RESULTS / 'configured_fixture.tox'
    generic = RESULTS / 'generic_controller.tox'
    assert not configured.exists() and not generic.exists()
    c.op('inspector/owned_runtime').module.quiesce(c)
    runner = holder.fetch('builder_recheck_module')
    holder.unstore('builder_recheck_module')
    holder.save(str(configured), createFolders=True)
    holder.store('builder_recheck_module', runner)
    before = dict(catalog=c.GetControlCatalog(), registry=c.GetLayoutRegistry(),
                  snapshots=c.GetSnapshots(), value=holder.par.Amount.eval())
    run_script('export_component.py')['export'](c, generic)
    after = dict(catalog=c.GetControlCatalog(), registry=c.GetLayoutRegistry(),
                 snapshots=c.GetSnapshots(), value=holder.par.Amount.eval())
    assert before == after
    loaded = op('/').loadTox(str(configured))
    loaded.store('builder_recheck_clone', True)
    holder.store('configured_clone', loaded.path)
    restored = loaded.op('roto_python')
    restored.Applybinding()
    assert restored.ext.RotoPythonExt._process is None
    assert any(r['id'] == holder.fetch('mapping_id') for r in restored.GetControlCatalog())
    assert len(restored.GetSnapshots()) == 1 and loaded.par.Amount.eval() == .35
    assert restored.ext.RotoPythonExt._collection.bindings['knob',1].parameter.owner == loaded
    restored.op('inspector/owned_runtime').module.validate(restored)
    assert restored.op('inspector/inspector_model').ext.InspectorModel.adapter.controller == restored
    generic_parent = op('/').create(baseCOMP, 'base_builder_generic_reload')
    generic_parent.store('builder_recheck_clone', True)
    holder.store('generic_parent', generic_parent.path)
    clean = generic_parent.loadTox(str(generic))
    clean.Applybinding()
    assert clean.ext.RotoPythonExt._process is None
    assert clean.GetControlCatalog() == [] and clean.GetSnapshots() == []
    assert clean.fetch('parameter_assignments') == [] and clean.fetch('page_targets') == []
    assert clean.fetch('snapshot_presets')['records'] == []
    clean.op('inspector/owned_runtime').module.validate(clean)
    for node in clean.findChildren(type=DAT):
        if getattr(node.par, 'file', None) is not None:
            assert node.par.file.eval() == '', node.path
            if getattr(node.par, 'syncfile', None) is not None: assert not node.par.syncfile.eval(), node.path
            if getattr(node.par, 'loadonstart', None) is not None: assert not node.par.loadonstart.eval(), node.path
    assert not loaded.errors(recurse=True) and not generic_parent.errors(recurse=True)
    write('exports', dict(configured_save_load=True, restored_local_target=True,
                         restored_local_model=True, snapshot_restored=True,
                         generic_export_load=True, generic_empty_mappings=True,
                         generic_empty_snapshots=True, generic_embedded_sources=True,
                         export_source_preserved=True, errors='', hardware_process=False,
                         artifacts=[dict(path=str(p), sha256=hashlib.sha256(p.read_bytes()).hexdigest())
                                    for p in (configured, generic)]))


def finish():
    holder = op(ROOT)
    before = holder.fetch('main_before')
    assert holder.fetch('source_before') == {str(p.relative_to(SOURCE)): hashlib.sha256(p.read_bytes()).hexdigest()
                                           for p in (SOURCE/'code/py').rglob('*.py')}
    for path in (holder.fetch('configured_clone', ''), holder.fetch('generic_parent', ''), ROOT):
        node = op(path) if path else None
        if node is None:continue
        c = node.op('roto_python')
        if c is None: c = next((n for n in node.children if n.op('RotoPythonExt')), None)
        if c is not None:
            c.op('inspector/owned_runtime').module.quiesce(c)
            c.Disconnect()
        node.destroy()
    after = main_state()
    # Live input values may change while the user's main controller stays connected.
    assert before['sources'] == after['sources']
    assert before['registry'] == after['registry']
    assert before['pid'] == after['pid'] and after['connected']
    assert not op(MAIN).errors(recurse=True)
    write('finish', dict(main_sources_preserved=True, main_registry_preserved=True,
                         main_process_preserved=True, fixtures_removed=op(ROOT) is None,
                         errors='', physical_retest=False))
