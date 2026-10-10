"""Local Inspector lifecycle. Opening a window never invokes a controller action."""

VIEW_NAMES = ('inspector_below', 'inspector_popup')
OBSERVER_NAMES = ('controller_catalog', 'controller_registry',
                  'controller_parameters', 'controller_changed')


def components(controller):
    if controller.valid is not True:
        raise ValueError('Inspector controller is invalid')
    wrapper = controller.op('inspector')
    if wrapper is None or wrapper.valid is not True or wrapper.parent() != controller:
        raise ValueError('Owned Inspector wrapper is unavailable')
    model = wrapper.op('inspector_model')
    if model is None or model.valid is not True or model.parent() != wrapper:
        raise ValueError('Owned Inspector model is unavailable')
    views = tuple(wrapper.op(name) for name in VIEW_NAMES)
    if any(view is None or view.valid is not True or view.parent() != wrapper for view in views):
        raise ValueError('Owned Inspector views are unavailable')
    return wrapper, model, views


def _owner(extension, component, message):
    owner = extension.ownerComp
    if owner is None or owner.valid is not True or owner != component:
        raise ValueError(message)


def _bindings(controller):
    """Preflight every reference before changing any subscription or observer.

    A previous Python generation is local only when its still-valid native
    owner equals the current model COMP. Paths are never identity evidence.
    """
    wrapper, model, views = components(controller)
    target = model.par.Controller.eval()
    if target is None or target.valid is not True or target != controller:
        raise ValueError('Inspector model belongs to another controller')
    current = model.extensions[0]
    if current is not None:
        if model.ext.InspectorModel is not current:
            raise ValueError('Inspector model namespace is stale')
        _owner(current, model, 'Cannot use a foreign Inspector model')
    bindings = []
    generations = [] if current is None else [current]
    for view in views:
        target = view.par.Model.eval()
        if target is None or target.valid is not True or target != model:
            raise ValueError('Inspector view belongs to another model')
        extension = view.extensions[0]
        if extension is not None:
            if view.ext.InspectorView is not extension:
                raise ValueError('Inspector view namespace is stale')
            _owner(extension, view, 'Cannot use a foreign Inspector view')
            bound = extension._model
            if bound is not None:
                if current is None:
                    raise ValueError('Inspector subscription has no current local model')
                _owner(bound, model, 'Cannot quiesce a foreign Inspector subscription')
                if not any(bound is generation for generation in generations):
                    generations.append(bound)
            bindings.append((view, extension))
    return wrapper, model, views, current, bindings, generations


def validate(controller):
    wrapper, model, views, current, bindings, _ = _bindings(controller)
    if current is None or len(bindings) != len(views):
        raise ValueError('Owned Inspector extensions are unavailable')
    if current._closed:
        raise ValueError('Owned Inspector model is shut down')
    if any(extension._model is not current for _, extension in bindings):
        raise ValueError('Inspector view is not attached to the current model')
    return wrapper, model, views


def open_inspector(controller):
    _, _, views = validate(controller)
    # The Fold view owns its separate popup editor. The alternate presentation
    # remains available, but Open Inspector always opens the primary window.
    views[0].ext.InspectorView.Show()


def attach_views(controller, expected_model=None, expected_view=None):
    """Called by native onInitTD, never by a timer or a MIDI callback."""
    _, _, views, current, bindings, generations = _bindings(controller)
    if current is None or len(bindings) != len(views):
        raise ValueError('Owned Inspector extensions are unavailable')
    if expected_model is not None and current is not expected_model:
        raise ValueError('Inspector model lifecycle callback is stale')
    if expected_view is not None and not any(extension is expected_view for _, extension in bindings):
        raise ValueError('Inspector view lifecycle callback is stale')
    # A queued native init callback must not undo an explicit local quiesce.
    if current._closed:
        return
    changed = [extension for _, extension in bindings if extension._model is not current]
    # Detach all old callbacks before shutting their generation down. Shutdown
    # cancels queued observations; it does not invoke controller business APIs.
    for extension in changed:
        extension.Disconnect()
    for generation in generations:
        if generation is not current:
            generation.onDestroyTD()
    for extension in changed:
        extension.Connect(preserve_context=True)
    validate(controller)


def quiesce(controller):
    """Stop proven local generations; a foreign/unreadable reference aborts first."""
    _, model, views, _, bindings, generations = _bindings(controller)
    for _, extension in bindings:
        extension.Disconnect()
    for view in views:
        for name in ('window_main', 'window_editor'):
            window = view.op(name)
            if window.isOpen:
                window.par.winclose.pulse()
    for name in OBSERVER_NAMES:
        observer = model.op(name)
        if observer is not None:
            observer.par.active = False
    for generation in generations:
        generation.onDestroyTD()


def initialize(controller):
    """Rebuild transient subscriptions from relative, clone-local parameters."""
    quiesce(controller)
    _, model, views = components(controller)
    model.par.Controller.expr = 'parent().parent()'
    model.initializeExtensions(0)
    for view in views:
        view.par.Model.expr = "parent().op('inspector_model')"
        view.initializeExtensions(0)
    model.ext.InspectorModel.RefreshWatchers()
    validate(controller)


def sanitize(controller):
    """Scrub detached generic UI state after the controller's mappings are empty.

    Source DATs and static UI labels survive. No live source instance or target
    is written; the caller must supply the detached export clone.
    """
    wrapper, model, views = components(controller)
    quiesce(controller)
    marker = wrapper.fetch('owned_inspector_sources', None)
    for node in (wrapper,) + tuple(wrapper.findChildren()):
        node.storage.clear()
    wrapper.store('owned_inspector_sources', marker)
    for view in views:
        draft = view.op('base_draft')
        for parameter in draft.customPars:
            parameter.val = parameter.default
        for name in ('Layout', 'Track', 'Device'):
            parameter = getattr(view.par, name)
            parameter.menuNames = ['unconfigured']
            parameter.menuLabels = ['Unconfigured']
            parameter.default = parameter.val = 'unconfigured'
        # Hidden detail/picker readouts can contain old native paths even when
        # the normal sixteen-slot projection has already become empty.
        for node in view.findChildren():
            if node.OPType == 'textCOMP' and (node.name in (
                    'text_name', 'text_value', 'text_status', 'text_details',
                    'text_count', 'text_check') or
                    node.name.startswith('value') or node.name.startswith('menu_name')):
                node.par.text.expr = ''
                node.par.text.val = ''
        extension=view.ext.InspectorView
        for editor in extension._editors:
            editor.op('mapping_toggle/text_label').par.text='MAPPING  ▸'
        draft.par.Label = ''
        draft.par.Destination = ''
    for name in ('targets', 'database', 'context_state'):
        node = wrapper.op(name)
        if node is not None:
            node.text = ''
    initialize(controller)
    # Parameter Execute caches use native absolute paths at runtime. Do not
    # serialize those paths into a portable tox; model initialization restores
    # the current local watcher set on load.
    watcher = model.op('controller_parameters')
    watcher.par.active = False
    watcher.par.op.expr = ''
    watcher.par.op = ''
    watcher.par.pars = ''
    model.ext.InspectorModel._watch_signature = None
