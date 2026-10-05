"""Apply persisted TD configuration through the public binding interface."""


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
