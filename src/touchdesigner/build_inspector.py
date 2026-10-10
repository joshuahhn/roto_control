"""Build the controller-owned compact Inspector; execute with native TD globals.

build(controller, source_dir, legacy_archive=None) is also the disconnected
upgrade entry point. Existing Lister presentation is archived before removal.
Catalog/metadata DATs retain their stable publication paths.
"""
from pathlib import Path
import hashlib

OLD_PRESENTATION = ('lister', 'listerConfig', 'listerConfig1', 'title',
                    'title_callbacks', 'list_events', 'toolbar_events',
                    'page_select', 'clear_all', 'clear_all_yes', 'clear_all_no')


def _execute(path, namespace):
    exec(compile(path.read_text(encoding='utf-8'), str(path), 'exec'), namespace)


def _source(dat, text):
    dat.par.syncfile = False
    dat.par.loadonstart = False
    dat.par.file = ''
    dat.par.language = 'python'
    dat.text = text
    dat.viewer = True


def _manifest(wrapper):
    return {node.path[len(wrapper.path)+1:]: hashlib.sha256(node.text.encode()).hexdigest()
            for node in wrapper.findChildren(type=DAT)
            if node.OPType in ('textDAT', 'parameterexecuteDAT', 'datexecuteDAT', 'panelexecuteDAT')
            and node.par.language.eval() == 'python'}


def _fingerprint(source):
    directory = source / 'prototypes/inspector'
    paths = sorted(directory.glob('*.py')) + [source/'build_inspector.py',
            source/'code/py/roto_python/inspector/inspector_data.py',
            source/'code/py/roto_python/inspector/owned_runtime.py',
            source/'cleanup_network.py',source/'scripts/td_project_docs.py',
            source/'README.md',directory/'README.md'] + sorted((source/'docs').rglob('*.md'))
    return hashlib.sha256(b''.join(str(p.relative_to(source)).encode()+b'\0'+p.read_bytes()
                                  for p in paths)).hexdigest()


def install_open_parameter(controller):
    page = next(p for p in controller.customPages if p.name == 'Connection')
    if getattr(controller.par, 'Openinspector', None) is None:
        page.appendPulse('Openinspector', label='Open Inspector')
    parameter = controller.par.Openinspector
    parameter.page = page
    parameter.label = 'Open Inspector'
    parameter.order = controller.par.Disconnect.order + 1
    callback = controller.op('parameter_callbacks')
    names = callback.par.pars.eval().split()
    callback.par.pars = ' '.join(names + ([] if 'Openinspector' in names else ['Openinspector']))


def archive_legacy(controller, destination):
    """Snapshot the untouched old UI before any upgrade source/settings writes."""
    wrapper=controller.op('inspector')
    if wrapper is None or wrapper.op('lister') is None:
        return None
    if destination is None:
        raise ValueError('Provide a new legacy_archive tox path before removing old Inspector')
    path=Path(destination).absolute()
    if path.exists() or path.suffix!='.tox':
        raise ValueError('Legacy Inspector archive must be a NEW tox')
    wrapper.save(str(path),createFolders=True)
    return dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                controller_id=controller.id,inspector_id=wrapper.id)


def _check_archive(controller,wrapper,receipt):
    path=Path(receipt['path'])
    if (receipt['controller_id']!=controller.id or receipt['inspector_id']!=wrapper.id
            or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=receipt['sha256']):
        raise ValueError('Legacy Inspector archive does not match this upgrade')


def _require_file_parameters(dat):
    for name in ('file','syncfile','loadonstart'):
        if getattr(dat.par,name,None) is None:
            raise ValueError('Required embedded source parameter missing: '+dat.path+'.'+name)


def _isolate_sources(component):
    """Embed supported DAT file parameters; annotation internals may lack them."""
    for dat in component.findChildren(type=DAT):
        for name,value in (('syncfile',False),('loadonstart',False),('file','')):
            parameter=getattr(dat.par,name,None)
            if parameter is not None:
                parameter.val=value
                if parameter.eval()!=value:
                    raise ValueError('Embedded source parameter did not settle: '+dat.path+'.'+name)


def _verify_runtime_sources(controller,source):
    names=('RotoPythonExt','protocol','collection_protocol','controls','binding',
           'free_learn','layouts','layout_migration','text_comp_follow','setup',
           'parameter_callbacks','lifecycle_callbacks','target_callbacks','learn_parameters')
    for name in names:
        node=controller.op(name)
        path=source/'code/py/roto_python'/f'{name}.py'
        if node is None or node.text!=path.read_text(encoding='utf-8'):
            raise ValueError('Upgrade runtime source before Inspector: '+name)
        _require_file_parameters(node)
    # These callbacks are embedded inside the controller's target component.
    sources={'base_targets/mapping_marks':'base_targets/mapping_marks.py'}
    sources.update({f'base_targets/watch_{kind}{slot}':'control_callbacks.py'
                    for kind in ('knob','button') for slot in range(1,9)})
    for name,filename in sources.items():
        node=controller.op(name)
        if node is None or node.text!=(source/'code/py/roto_python'/filename).read_text(encoding='utf-8'):
            raise ValueError('Upgrade runtime source before Inspector: '+name)
        _require_file_parameters(node)
    helper=controller.op('midi_process')
    if helper is None or helper.text!=(source/'midi_process.py').read_text(encoding='utf-8'):
        raise ValueError('Embed the current MIDI helper before Inspector')
    _require_file_parameters(helper)


def build(controller, source_dir, legacy_archive=None, legacy_receipt=None):
    if controller.ext.RotoPythonExt._process is not None:
        raise ValueError('Disconnect before installing Inspector')
    source = Path(source_dir).resolve()
    directory = source / 'prototypes/inspector'
    _verify_runtime_sources(controller,source)
    fingerprint = _fingerprint(source)
    wrapper = controller.op('inspector')
    install_open_parameter(controller)
    if wrapper is not None:
        marker = wrapper.fetch('owned_inspector_sources', None)
        if marker and marker['build'] == fingerprint and marker['dat'] == _manifest(wrapper):
            wrapper.op('owned_runtime').module.validate(controller)
            return wrapper
        if wrapper.op('lister') is not None:
            receipt=legacy_receipt or archive_legacy(controller,legacy_archive)
            _check_archive(controller,wrapper,receipt)
        if wrapper.op('owned_runtime') is not None:
            wrapper.op('owned_runtime').module.quiesce(controller)
    else:
        wrapper = controller.create(containerCOMP, 'inspector')
    wrapper.par.parentshortcut = 'RotoInspector'
    wrapper.par.opshortcut = ''
    wrapper.viewer = True
    wrapper.par.w = 600
    wrapper.par.h = 430
    for name in OLD_PRESENTATION:
        node = wrapper.op(name)
        if node is not None:
            node.destroy()
    # Finish existing controller/helper FILE isolation before model/view init.
    _isolate_sources(controller)
    # Retain the publication DATs, including pending projection identity.
    for name, kind, language in [('targets', tableDAT, 'plain'),
            ('database', textDAT, 'json'), ('context_state', textDAT, 'json')]:
        node = wrapper.op(name) or wrapper.create(kind, name)
        if kind == textDAT:
            node.par.language = language
        node.viewer = True
    for name in ('inspector_data', 'owned_runtime'):
        node = wrapper.op(name) or wrapper.create(textDAT, name)
        _source(node, (source/'code/py/roto_python/inspector'/f'{name}.py').read_text())
    # Build commands/Targets before initializing the controller-backed model.
    model = wrapper.op('inspector_model') or wrapper.create(baseCOMP, 'inspector_model')
    model.par.parentshortcut = 'InspectorModel'
    model.par.opshortcut = ''
    model.viewer = True
    if getattr(model.par, 'Controller', None) is None:
        model.appendCustomPage('Data').appendOP('Controller', label='Local controller')
    model.par.Controller.expr = 'parent().parent()'
    for name, filename in [('InspectorModel', 'model.py'), ('live_model', 'live_model.py')]:
        dat = model.op(name) or model.create(textDAT, name)
        _source(dat, (directory/filename).read_text())
    scope = dict(globals(), inspector_source_dir=directory, model_comp=model,
                 prototype_parent=wrapper, model_expression="parent().op('inspector_model')")
    _execute(directory/'build_commands.py', scope)
    _execute(directory/'build_targets.py', dict(scope, targets_only=True))
    model.seq.ext.numBlocks = 1
    model.par.ext0object = "op('./live_model').module.InspectorModel(me)"
    model.par.ext0promote = True
    model.par.initextonstart = True
    model.initializeExtensions(0)
    views = []
    for name, style in [('inspector_below', 'below'), ('inspector_popup', 'popup')]:
        _execute(directory/'build.py', dict(scope, prototype_name=name, prototype_style=style))
        views.append(wrapper.op(name))
    scope.update(inspector_views=views, action_views=views, parity_views=views,
                 target_views=views, context_views=views, activation_views=views)
    _execute(directory/'build_definition_edit.py', scope)
    _execute(directory/'build_activation.py', scope)
    # These are the same event-driven observers as the accepted live builder.
    definitions = (
        ('controller_catalog', datexecuteDAT, 'dat', 'parent.InspectorModel.ControllerData()',
         "def onTableChange(dat):\n    parent.InspectorModel.RequestSync()\n"),
        ('controller_registry', datexecuteDAT, 'dat', 'parent.InspectorModel.ControllerMetadata()',
         "def onTableChange(dat):\n    parent.InspectorModel.RequestSync()\n"),
        ('controller_parameters', parameterexecuteDAT, 'op', '',
         "def onValueChange(par,prev):\n    parent.InspectorModel.RequestSync()\ndef onModeChange(par,prev):\n    parent.InspectorModel.RefreshDefinitions()\n    parent.InspectorModel.RequestSync()\n"),
        ('controller_changed', parameterexecuteDAT, 'op', 'parent.InspectorModel',
         "def onValueChange(par,prev):\n    parent.InspectorModel.RequestSync()\n"))
    for name, kind, parameter, expression, text in definitions:
        node = model.op(name) or model.create(kind, name)
        node.par.active = False
        _source(node, text)
        getattr(node.par, parameter).expr = expression
        if kind == datexecuteDAT:
            node.par.tablechange = True
            for flag in ('rowchange', 'colchange', 'cellchange', 'sizechange'):
                getattr(node.par, flag).val = False
        else:
            node.par.custom = True
            node.par.builtin = name == 'controller_parameters'
            node.par.valuechange = True
            node.par.onpulse = False
            node.par.modechange = name == 'controller_parameters'
            node.par.pars = 'Controller' if name == 'controller_changed' else ''
        if name == 'controller_changed':
            node.par.active = True
    for view in views:
        # Preserve the accepted LIVE/BROWSE and presentation controls.
        for target, action in [('text_style', 'presentation'), ('text_brand', 'follow')]:
            view.op(target).par.clickthrough = False
            click = view.op('click_'+action) or view.create(panelexecuteDAT, 'click_'+action)
            click.par.panels = target
            click.par.panelvalue = 'lselect'
            click.par.offtoon = True
            _source(click, "def onOffToOn(panelValue):\n    parent.InspectorDemo.Action(%r)\n" % action)
    # Final subscriptions use current local model/view instances, never siblings.
    wrapper.op('owned_runtime').module.initialize(controller)
    controller.ext.RotoPythonExt._publish_inspector(force=True)
    # All generated source callbacks are embedded; neither packaging nor load
    # depends on the developer's source directory or Palette Lister clone.
    _isolate_sources(wrapper)
    docs=dict(globals())
    _execute(source/'scripts/td_project_docs.py',docs)
    docs['embed_project_docs'](model,directory)
    docs['embed_project_docs'](controller,source)
    cleanup=dict(globals())
    _execute(source/'cleanup_network.py',cleanup)
    cleanup['apply'](controller)
    wrapper.store('owned_inspector_sources', dict(build=fingerprint, dat=_manifest(wrapper)))
    return wrapper
