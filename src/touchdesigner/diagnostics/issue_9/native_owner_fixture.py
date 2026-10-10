"""Prepared native fixture; NOT executed evidence.

Run only in a coordinated disposable TD project with current source DATs installed.
Pass an empty fixture COMP and a disconnected, empty controller under that COMP.
This mutates only that disposable network; it does not save/export project binaries.
"""


def run(root, controller):
    import copy
    from pathlib import Path
    extension=controller.ext.RotoPythonExt
    if controller.parent()!=root or extension._process is not None:
        raise ValueError('Use a disconnected fixture controller under the supplied root')
    manager=extension._layout_manager()
    if any(p['targets'] or p['state'].get('page_targets') for p in manager.all_plugins()):
        raise ValueError('Fixture controller must have no user mappings')
    if any(child!=controller for child in root.children):
        raise ValueError('Fixture root must contain only the controller')
    expected=Path(__file__).resolve().parents[2]/'code/py/roto_python'
    for name in ('layouts','RotoPythonExt','text_comp_follow','free_learn'):
        dat=controller.op(name)
        assert dat.text.replace('\r\n','\n')==(expected/(name+'.py')).read_text().replace('\r\n','\n'),name
    # Do not enable Follow or MIDI. Test source/API behavior only.
    original=manager.data['active']
    left=root.create(baseCOMP,'left');right=root.create(baseCOMP,'right')
    a=left.create(baseCOMP,'same');b=right.create(baseCOMP,'same')
    child=a.create(baseCOMP,'ordinary_child')
    for comp in (a,b):
        comp.appendCustomPage('Fixture').appendFloat('Amount',label='Amount')
        comp.par.Amount.normMin=0;comp.par.Amount.normMax=10;comp.par.Amount.val=5
        comp.tags.add('roto_device')
    la=extension.RegisterComp(a);lb=extension.RegisterComp(b)
    assert la!=lb and extension.RegisterComp(a)==la
    assert child.fetch('roto_control_owner_id',None,search=False) is None
    assert manager.owner_ready(la)  # inherited parent storage must not appear as a clone
    assert manager.data['active']==original
    custom=extension.CreateLayout('Fixture Custom')
    extension.SelectLayout(custom);manual=extension.AssignParameter('knob',1,a.par.Amount)
    extension.SelectLayout(la);owned=extension.AssignParameter('knob',1,a.par.Amount)
    extension.ConfigureControl(owned['id'],minimum=2,maximum=8)
    a.par.Amount.val=7
    assert extension.GetPluginTargets(custom)[0]['value']==7
    assert extension.GetValue(owned['id'])==7
    extension.SelectLayout(custom)
    assert extension.GetValue(manual['id'])==7 and a.par.Amount.eval()==7
    assert extension.GetPluginTargets(la)[0]['maximum']==8
    a.name='renamed';extension._follow.refresh_links()
    assert extension.LookupCompLayout(a)==la
    variant=extension.CreatePlugin(la,manager.track(la)['id'],'Variant')
    extension._follow.set_plugin_link(la,manager.track(la)['id'],variant,a)
    assert extension.ValidateLayoutRegistry(extension.GetLayoutRegistry())
    clone=right.copy(a,name='copy')
    assert clone.fetch('roto_control_owner_id',None,search=False)==a.fetch('roto_control_owner_id',None,search=False)
    assert extension.LookupCompLayout(a) is None
    assert manager.layout(la)['owner']['state']=='conflict'
    lc=extension.RegisterComp(clone,new_identity=True)
    extension.RelinkLayoutOwner(la,a)
    extension.UnregisterLayoutOwner(lc)
    assert extension._follow.sync_tags(force=True)==[]
    assert manager.layout(lc)['owner']['state']=='unregistered'
    # Preserve this disposable state for a separate native save/reload check.
    return dict(evidence_class='native-source-api',physical=False,
                layouts=dict(a=la,b=lb,clone=lc,custom=custom),
                registry=copy.deepcopy(extension.GetLayoutRegistry()),
                pending=['native save/reload','generic tox sanitization','physical routing/ACK/LCD'])
