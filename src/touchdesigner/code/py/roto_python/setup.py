"""Apply persisted TD configuration through the public binding interface."""


def configure_ui(controller):
    """Expose two workflows after migrating old single-target saved setups."""
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
