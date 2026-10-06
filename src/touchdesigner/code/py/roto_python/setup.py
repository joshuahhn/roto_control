"""Apply persisted TD configuration through the public binding interface."""
import copy


def install_follow_ui(controller):
    """Create opt-in Follow and the active Device's optional COMP reference."""
    binding = next(p for p in controller.customPages if p.name == 'Binding')
    if getattr(controller.par, 'Followcomp', None) is None:
        par = binding.appendToggle('Followcomp', label='Follow selected COMP')[0]
        par.default = par.val = False
    controller.par.Followcomp.enableExpr = "me.par.Setupmode == 'collection'"
    page = next((p for p in controller.customPages if p.name in ('Device', 'Layout', 'Layouts')), None)
    if page is None:
        page = controller.appendCustomPage('Layout')
    if getattr(controller.par, 'Focuscomp', None) is None:
        page.appendOP('Focuscomp', label='Device Focus COMP')
    controller.par.Focuscomp.label='Device Focus COMP'
    controller.par.Focuscomp.enableExpr = "me.par.Setupmode == 'collection'"
    callbacks = controller.op('parameter_callbacks')
    names = callbacks.par.pars.eval().split()
    callbacks.par.pars = ' '.join(names + [n for n in ('Followcomp', 'Focuscomp') if n not in names])


def install_device_ui(controller):
    page=next(p for p in controller.customPages if p.name in ('Device','Layout','Layouts'))
    if getattr(controller.par,'Plugin',None) is None:
        par=page.appendMenu('Plugin',label='Active Device')[0]
        par.menuNames=['plugin.custom'];par.menuLabels=['CUSTOM'];par.default=par.val='plugin.custom'
    if getattr(controller.par,'Newpluginname',None) is None:
        par=page.appendStr('Newpluginname',label='New Device name')[0];par.default=par.val='DEVICE'
    for name,label in (('Newplugin','New empty Device'),('Deleteplugin','Delete Device')):
        if getattr(controller.par,name,None) is None:page.appendPulse(name,label=label)
    for name in ('Layout','Track','Plugin','Focuscomp','Newpluginname','Newplugin','Deleteplugin'):
        getattr(controller.par,name).enableExpr="me.par.Setupmode == 'collection'"
    callbacks=controller.op('parameter_callbacks');names=callbacks.par.pars.eval().split()
    callbacks.par.pars=' '.join(names+[n for n in ('Plugin','Newplugin','Deleteplugin') if n not in names])


def combine_context_pages(controller):
    """Separate Device controls from the Layout/Track mapping-set page."""
    names = ('Layout', 'Layoutname', 'Newlayout', 'Renamelayout', 'Deletelayout',
             'Track', 'Trackname', 'Newtrackname', 'Newtrack', 'Deletetrack',
             'Plugin', 'Focuscomp', 'Pluginname', 'Newpluginname', 'Newplugin', 'Deleteplugin')
    if any(getattr(controller.par, name, None) is None for name in names):
        raise ValueError('Install Layout and Track parameters before combining pages')
    page = next((p for p in controller.customPages if p.name == 'Layout'), None)
    if page is None:
        page = next((p for p in controller.customPages if p.name == 'Layouts'), None) or controller.appendCustomPage('Layout')
        page.name = 'Layout'
    device = next((p for p in controller.customPages if p.name == 'Device'), None) or controller.appendCustomPage('Device')
    for order, name in enumerate(names):
        parameter = getattr(controller.par, name)
        parameter.page = page if order<10 else device
        parameter.order = order if order<10 else order-10
        parameter.startSection = name == 'Track'
    controller.par.Layout.label = 'Active Layout (mapping set)'
    controller.par.Track.label = 'Active Track group (FUNC)'
    controller.par.Plugin.label = 'Active Device (SEL)'
    controller.par.Layoutname.label = 'New / rename Layout'
    controller.par.Trackname.label = 'Track group name'
    controller.par.Pluginname.label = 'Device name'
    for name in ('Confirmdelete', 'Canceldelete', 'Confirmtrackdelete', 'Canceltrackdelete'):
        parameter = getattr(controller.par, name, None)
        if parameter is not None:
            parameter.destroy()
    for old in list(controller.customPages):
        if old.name in ('Display', 'Layouts', 'Tracks') and not old.pars:
            old.destroy()


def remove_control_ui(controller):
    """Retain the normalized compatibility value internally, removing its page."""
    control_page = next((p for p in controller.customPages if p.name == 'Control'), None)
    if control_page is not None and controller.ext.RotoPythonExt._process is not None:
        raise ValueError('Disconnect before removing the Control page')
    state = controller.op('base_state')
    legacy = getattr(controller.par, 'Value', None)
    if getattr(state.par, 'Manualvalue', None) is None:
        page = next((p for p in state.customPages if p.name == 'Compatibility'), None) or state.appendCustomPage('Compatibility')
        backing = page.appendFloat('Manualvalue', label='Legacy normalized value')[0]
        backing.default = .5
        backing.val = legacy.eval() if legacy is not None else .5
        backing.min = backing.normMin = 0
        backing.max = backing.normMax = 1
        backing.clampMin = backing.clampMax = True

    def migrate(value):
        if isinstance(value, dict):
            if value.get('parameter') == 'Value' and value.get('comp') in ('.', '', controller.path):
                destination = controller.path + '/base_state' if value.get('comp') == controller.path else 'base_state'
                value.update(comp=destination, parameter='Manualvalue')
            for child in value.values():
                migrate(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                migrate(child)

    registry = copy.deepcopy(controller.fetch('layout_registry', None))
    migrate(registry)
    changed = registry != controller.fetch('layout_registry', None)
    if changed:
        controller.store('layout_registry', registry)
        manager = controller.ext.RotoPythonExt._layout_manager()
        manager.data = copy.deepcopy(registry)
        if not manager.legacy:
            manager.restore()
    for name in ('parameter_assignments', 'page_targets', 'control_catalog'):
        records = copy.deepcopy(controller.fetch(name, []))
        migrate(records)
        controller.store(name, records)

    # The compatibility value is backing state, rather than another UI input.
    # Parameter bindings retain their own watcher; avoid a second dispatch path.
    callbacks = controller.op('parameter_callbacks')
    callbacks.par.op.expr = 'parent.RotoPython'
    callbacks.par.pars = ' '.join(name for name in callbacks.par.pars.eval().split()
                                if name not in ('Value', 'Manualvalue', 'Offerparameter',
                                                'Confirmdelete', 'Canceldelete', 'Confirmtrackdelete', 'Canceltrackdelete'))
    if control_page is not None:
        control_page.destroy()


def configure_ui(controller):
    """Expose two workflows after migrating old single-target saved setups."""
    if any(page.name == 'Control' for page in controller.customPages) and controller.ext.RotoPythonExt._process is not None:
        raise ValueError('Disconnect before removing the Control page')
    mode = controller.par.Setupmode.eval()
    if mode not in ('collection', 'callback'):
        extension = controller.ext.RotoPythonExt
        if extension._process is not None:
            raise ValueError('Disconnect before migrating a legacy Binding setup')
        if controller.Applybinding() is False:
            raise ValueError('Apply a valid legacy binding before upgrading its UI')
        extension._layout_manager().restore()
        mode = 'collection'
    controller.par.Setupmode.menuNames = ['collection', 'callback']
    controller.par.Setupmode.menuLabels = ['Parameter mapping', 'Python registration']
    controller.par.Setupmode.default = 'collection'
    controller.par.Setupmode.val = mode
    controller.par.Applybinding.label = 'Apply setup'
    controller.par.Groupid.enableExpr = "me.par.Setupmode == 'callback'"
    # Runtime compatibility APIs remain; obsolete saved single-target fields do not.
    for name in ('Targetcomp', 'Targetpar', 'Bindingid', 'Targetlabel',
                 'Useparrange', 'Minimum', 'Maximum'):
        parameter = getattr(controller.par, name, None)
        if parameter is not None:
            parameter.destroy()
    remove_control_ui(controller)
    install_follow_ui(controller)
    install_device_ui(controller)
    combine_context_pages(controller)
    manager=getattr(controller.ext.RotoPythonExt,'_layouts',None)
    if manager is not None:manager.menu()
    return mode


def restore(controller):
    par = controller.par
    mode = par.Setupmode.eval()
    if mode == 'value':
        controller.Unbind()
        return 'Value'
    if mode == 'parameter':
        target = par.Targetcomp.eval()
        if target is None or not target.valid or not target.isCOMP:
            raise ValueError('Choose a valid Target COMP')
        name = par.Targetpar.eval().strip()
        parameter = getattr(target.par, name, None) if name else None
        if parameter is None:
            raise ValueError('Target custom parameter does not exist: ' + name)
        limits = {} if par.Useparrange.eval() else {
            'minimum': par.Minimum.eval(), 'maximum': par.Maximum.eval()}
        return controller.BindParameter(parameter, id=par.Bindingid.eval().strip(),
                                        label=par.Targetlabel.eval().strip() or None, **limits)
    if mode == 'collection':
        return controller.BindControls(controller.op('controls').module.from_table(controller), group_id=par.Groupid.eval(), _allow_empty=True)
    if mode == 'callback':
        hook = controller.op('registration')
        if hook is None:
            raise ValueError('Missing registration DAT')
        before = controller.ext.RotoPythonExt._binding
        collection_before = getattr(controller.ext.RotoPythonExt, "_collection", None)
        hook.module.onRegister(controller)
        # A saved hook may register parameters, callbacks or a mixed collection.
        # It must replace the registration rather than silently retain old state.
        binding = controller.ext.RotoPythonExt._binding
        collection = getattr(controller.ext.RotoPythonExt, "_collection", None)
        if collection is not None and collection is not collection_before:
            return tuple(collection.ids)
        if binding is None or binding is before:
            raise ValueError('onRegister must call BindParameter, BindCallback or BindControls')
        return binding.id
    raise ValueError('Unknown setup mode: ' + str(mode))
