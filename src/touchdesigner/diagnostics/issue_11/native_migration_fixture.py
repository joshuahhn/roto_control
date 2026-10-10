"""Prepared #11 native stages; NOT executed evidence.

The Inspector sole executor may call seed/run in one coordinated disposable
network. Never pass a production controller; never Connect or save here.
"""
import copy
from pathlib import Path


def seed(root, controller):
    e = controller.ext.RotoPythonExt
    m = e._layout_manager()
    if controller.parent() != root or e._process is not None or e._host.connected:
        raise ValueError('Use a completely disconnected fixture under the supplied root')
    if any(child != controller for child in root.children):
        raise ValueError('Disposable root must contain only the controller')
    if any(p['targets'] or p['state'].get('page_targets') for p in m.all_plugins()):
        raise ValueError('Fixture controller must contain no user mappings')
    expected = Path(__file__).resolve().parents[2] / 'code/py/roto_python'
    for name in ('layout_migration', 'RotoPythonExt', 'layouts', 'text_comp_follow'):
        assert controller.op(name).text.replace('\r\n', '\n') == (expected / (name + '.py')).read_text().replace('\r\n', '\n'), name
    a = root.create(baseCOMP, 'migration_a')
    b = root.create(baseCOMP, 'migration_b')
    for comp in (a, b):
        comp.viewer = True
        page = comp.appendCustomPage('Fixture')
        p = page.appendFloat('Amount')[0]
        p.normMin = 0; p.normMax = 10; p.val = 5
        page.appendPulse('Reset')
    a.nodeX, a.nodeY = -200, -250
    b.nodeX, b.nodeY = 0, -250
    owner_a = e.RegisterComp(a); owner_b = e.RegisterComp(b)
    # Saved explicit provider hook: reload reconstructs availability, not results.
    controller.op('registration').text += '''
def onRegisterActions(controller):
    def recall(event):
        controller.store('migration_demo_recalls', controller.fetch('migration_demo_recalls', 0) + 1)
        return dict(status='succeeded')
    controller.RegisterAction('migration.demo.clean.v1', 'Demo Clean', recall)
'''
    e._restore_actions()
    controller.store('migration_demo_recalls', 0)
    manual = e.CreateLayout('Manual')
    e.SelectLayout(manual); e.AssignParameter('knob', 1, a.par.Amount)
    e.ConfigureControl(e.GetControlStates()[0]['id'], minimum=1, maximum=9)
    legacy = e.CreateLayout('Legacy')
    e.SelectLayout(legacy); e.AssignParameter('knob', 1, a.par.Amount)
    e.AssignParameter('button', 1, a.par.Reset)
    e.AssignAction(2, 'migration.demo.clean.v1', id='migration.demo.action.mapping')
    e.SetPluginComp(legacy, m.track()['id'], m.plugin()['id'], a)
    first = list(m.context()['key'])
    device_b = e.CreatePlugin(legacy, first[1], 'B')
    e.SelectPlugin(legacy, first[1], device_b); e.AssignParameter('knob', 1, b.par.Amount)
    e.SetPluginComp(legacy, first[1], device_b, b)
    second = list(m.context()['key'])
    unlinked = e.CreatePlugin(legacy, first[1], 'UNKNOWN')
    variant = e.CreateLayout('Variant')
    e.SelectLayout(variant); e.AssignParameter('knob', 1, a.par.Amount)
    e.ConfigureControl(e.GetControlStates()[0]['id'], minimum=2, maximum=8)
    e.SetPluginComp(variant, m.track()['id'], m.plugin()['id'], a)
    e.RenamePlugin(variant, m.track()['id'], m.plugin()['id'], 'MANUAL A')
    third = list(m.context()['key'])
    e.SelectLayout(manual)
    # Fixture-only legacy database seed, not an inference/production operation.
    m.layout(legacy)['category'] = m.layout(variant)['category'] = 'LEGACY'
    m.save()
    rows = []
    for key, owner_layout in ((first, owner_a), (second, owner_b), (third, owner_a)):
        rows.append(dict(source=key, decision='move', owner_layout_id=owner_layout,
                         owner_id=m.layout(owner_layout)['owner']['id'],
                         evidence=dict(kind='registration-provenance', reference='native fixture seed: explicit source registration')))
    return dict(classifications=rows, owner_a=owner_a, owner_b=owner_b, manual=manual,
                source=legacy, unlinked=unlinked, variant=third, tools=[a.path, b.path])


def run(controller, fixture, recovery_path):
    e = controller.ext.RotoPythonExt
    before = e.GetLayoutRegistry()
    values = [controller.op(path).par.Amount.eval() for path in fixture['tools']]
    pending = e._pending
    action_state = e.GetActionState('migration.demo.clean.v1')
    recalls = controller.fetch('migration_demo_recalls')
    plan = e.PlanCompLayoutMigration('native-issue11-v1', fixture['classifications'],
                                     entries={fixture['owner_a']: fixture['variant'][2]},
                                     active_variants={fixture['owner_a']: fixture['variant'][2]})
    assert all(r['source'] == r['destination'] for r in plan['manifest'] if r['decision'] == 'retain')
    assert e.GetLayoutRegistry() == before
    result = e.ApplyCompLayoutMigration(plan, recovery_path=recovery_path)
    after = e.GetLayoutRegistry()
    assert result['changed'] and e._pending == pending
    assert e.GetActionState('migration.demo.clean.v1') == action_state
    assert controller.fetch('migration_demo_recalls') == recalls
    assert [controller.op(path).par.Amount.eval() for path in fixture['tools']] == values
    assert next(l for l in before['records'] if l['id'] == fixture['manual']) == next(l for l in after['records'] if l['id'] == fixture['manual'])
    source = next(l for l in after['records'] if l['id'] == fixture['source'])
    assert any(p['id'] == fixture['unlinked'] for t in source['tracks'] for p in t['plugins'])
    recovery_bytes = Path(recovery_path).read_bytes()
    assert not e.ApplyCompLayoutMigration(plan, recovery_path=recovery_path)['changed']
    assert Path(recovery_path).read_bytes() == recovery_bytes
    return dict(evidence_class='native-source-migration', physical=False,
                fixture=fixture, before=before, after=after, plan=copy.deepcopy(plan), result=result,
                pending=['project/managed tox save-load', 'rerun after native reload', 'generic export/load',
                         'failure injection/recovery', 'Pulse observer zero writes', 'physical recall without re-LEARN'])
