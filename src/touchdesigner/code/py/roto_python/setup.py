"""Apply persisted TD configuration through the public binding interface."""
import copy
import posixpath


MIX_CUSTOM_PARAMETERS = tuple('Mixcustom' + str(i) for i in range(1, 7))
MIX_NO_OPERATION = '__none__'
MIX_DRAFT_PRESET = '__draft__'


def legacy_mix_choices(controller, libraries=None):
    """Preflight the old uncommitted draft before replacing any source/UI."""
    parameter = getattr(controller.par, 'Mixoperationlibrary', None)
    if parameter is None:
        return None
    if libraries is None:
        libraries = controller.op('mix_runtime').module.OPERATION_LIBRARIES
    library = parameter.eval()
    if library not in libraries:
        raise ValueError('Unknown legacy Operation library')
    choices = list(libraries[library]) + [getattr(controller.par, 'Mixcustom' + str(i)).eval()
        for i in range(1, 5) if getattr(controller.par, 'Mixcustom' + str(i)).eval() != MIX_NO_OPERATION]
    choices = list(dict.fromkeys(choices))
    if len(choices) > 6:
        raise ValueError('Legacy Operation draft has more than six choices; reduce it before upgrading. Applied MIX is unchanged.')
    return choices


def refresh_mix_presets_ui(controller):
    parameter = controller.par.Mixoperationpreset
    selected = parameter.eval()
    records = controller.ext.RotoPythonExt.GetMixOperationPresets()
    parameter.menuNames = [MIX_DRAFT_PRESET] + [r['id'] for r in records]
    parameter.menuLabels = ['Custom draft'] + [r['name'] for r in records]
    parameter.val = selected if selected in parameter.menuNames else MIX_DRAFT_PRESET


def set_mix_operation_draft(controller, choices):
    if len(choices) > 6:
        raise ValueError('This preset editor has six slots; the applied API profile is unchanged')
    refresh_mix_ui(controller)
    for index, name in enumerate(MIX_CUSTOM_PARAMETERS):
        parameter = getattr(controller.par, name)
        value = choices[index] if index < len(choices) else MIX_NO_OPERATION
        if value not in parameter.menuNames:
            parameter.menuNames = parameter.menuNames + [value]
            parameter.menuLabels = parameter.menuLabels + ['Unavailable: ' + value]
        parameter.val = value


def mix_draft_operations(controller):
    return controller.op('mix_descriptor').module.operation_choices(
        [getattr(controller.par, name).eval() for name in MIX_CUSTOM_PARAMETERS
         if getattr(controller.par, name).eval() != MIX_NO_OPERATION], 6)


def load_mix_preset_ui(controller):
    identity = controller.par.Mixoperationpreset.eval()
    if identity == MIX_DRAFT_PRESET:
        return
    record = next((r for r in controller.ext.RotoPythonExt.GetMixOperationPresets() if r['id'] == identity), None)
    if record is not None:
        set_mix_operation_draft(controller, record['operations'])
        controller.par.Mixpresetname.val = record['name']


def edit_mix_preset_ui(controller, action):
    extension = controller.ext.RotoPythonExt
    identity = controller.par.Mixoperationpreset.eval()
    if action == 'Deletemixpreset':
        extension.RemoveMixOperationPreset(identity)
    else:
        identity = extension.SaveMixOperationPreset(controller.par.Mixpresetname.eval(), mix_draft_operations(controller),
            preset_id=identity if action == 'Savemixpreset' else None)
        controller.par.Mixoperationpreset.val = identity


def refresh_mix_ui(controller):
    """Refresh draft choices only; preserve an unavailable choice until Apply."""
    source = controller.par.Mixsource.eval()
    names, labels = [MIX_NO_OPERATION], ['None']
    if source is not None and source.valid and source.OPType == 'layermixTOP':
        menu = source.par.operand
        for name, label in zip(menu.menuNames, menu.menuLabels):
            if name != 'opperlayer':
                names.append(name); labels.append(label)
    for name in MIX_CUSTOM_PARAMETERS:
        parameter = getattr(controller.par, name)
        value = parameter.eval()
        parameter.menuNames = names + ([value] if value not in names else [])
        parameter.menuLabels = labels + (['Unavailable: ' + value] if value not in names else [])
        parameter.val = value


def install_mix_ui(controller):
    """Install an explicit-Apply draft editor without changing MIX assignments."""
    legacy_choices = legacy_mix_choices(controller)
    new_editor = getattr(controller.par, 'Mixoperationpreset', None) is None
    page = next((p for p in controller.customPages if p.name == 'MIX'), None)
    page = page if page is not None else controller.appendCustomPage('MIX')
    new_source = getattr(controller.par, 'Mixsource', None) is None
    definitions = [('Mixstyle', 'Menu', 'Draft style', 'analysis'),
                   ('Mixsource', 'OP', 'Draft source', ''),
                   ('Mixoperationpreset', 'Menu', 'Operation preset', MIX_DRAFT_PRESET)]
    definitions += [(name, 'Menu', 'Custom blend ' + str(i), MIX_NO_OPERATION)
                    for i, name in enumerate(MIX_CUSTOM_PARAMETERS, 1)]
    definitions += [('Mixpresetname', 'Str', 'Preset name', ''),
                    ('Newmixpreset', 'Pulse', 'Add Operation preset', None),
                    ('Savemixpreset', 'Pulse', 'Save preset edits / name', None),
                    ('Deletemixpreset', 'Pulse', 'Delete preset', None),
                    ('Applymix', 'Pulse', 'Apply MIX draft', None),
                    ('Clearmix', 'Pulse', 'Clear MIX assignments', None),
                    ('Mixsummary', 'Str', 'Applied MIX', 'Unassigned')]
    for order, (name, kind, label, default) in enumerate(definitions):
        parameter = getattr(controller.par, name, None)
        new_parameter = parameter is None
        if new_parameter:
            parameter = getattr(page, 'append' + kind)(name, label=label)[0]
        if name == 'Mixstyle':
            parameter.menuNames = ['analysis', 'layers']
            parameter.menuLabels = ['Analysis (Low / Mid)', 'Layer Mix inputs']
        elif name == 'Mixoperationpreset' and new_parameter:
            parameter.menuNames = [MIX_DRAFT_PRESET]
            parameter.menuLabels = ['Custom draft']
        elif kind == 'Menu' and new_parameter:
            parameter.menuNames = [MIX_NO_OPERATION]
            parameter.menuLabels = ['None']
        if new_parameter:
            if default is not None:
                parameter.default = parameter.val = default
        parameter.order = order
        parameter.help = 'Draft only. Apply MIX draft replaces the current MIX profile without changing target values or PLUGIN mappings.'
    for name in ('Mixoperationpreset', *MIX_CUSTOM_PARAMETERS, 'Mixpresetname', 'Newmixpreset', 'Savemixpreset', 'Deletemixpreset'):
        getattr(controller.par, name).enableExpr = "me.par.Mixstyle == 'layers'"
    controller.par.Mixoperationpreset.startSection = True
    controller.par.Applymix.startSection = True
    controller.par.Mixsummary.readOnly = True
    controller.par.Mixsummary.help = 'Currently applied profile. Draft edits take effect only after Apply. Audio Gain/Mute is not available yet.'
    if legacy_choices is not None:
        set_mix_operation_draft(controller, legacy_choices)
        controller.par.Mixoperationlibrary.destroy()
    elif new_editor:
        saved = controller.fetch('mix_profile', None, search=False)
        if saved:
            descriptor = saved['descriptor']
            scope = controller.op(saved['scope'])
            source = scope.op(descriptor['source']) if scope is not None else None
            controller.par.Mixstyle.val = descriptor['style']
            if source is not None and new_source:
                # Custom OP parameters resolve from the containing network.
                controller.par.Mixsource.val = posixpath.relpath(source.path, controller.parent().path)
            refresh_mix_ui(controller)
            if descriptor['style'] == 'layers':
                choices = next((item['controls']['operation']['choices'] for item in descriptor['items']
                                if 'operation' in item['controls']), [])
                if len(choices) <= 6:
                    set_mix_operation_draft(controller, choices)
    refresh_mix_ui(controller)
    refresh_mix_presets_ui(controller)
    callbacks = controller.op('parameter_callbacks')
    watched = callbacks.par.pars.eval().split()
    callbacks.par.pars = ' '.join(watched + [name for name in ('Mixsource', 'Mixstyle', 'Mixoperationpreset', 'Newmixpreset',
        'Savemixpreset', 'Deletemixpreset', 'Applymix', 'Clearmix') if name not in watched])
    controller.ext.RotoPythonExt._sync_mix_summary()


def apply_mix_ui(controller):
    source = controller.par.Mixsource.eval()
    if source is None or not source.valid:
        raise ValueError('Choose an existing MIX source')
    style = controller.par.Mixstyle.eval()
    if style == 'analysis':
        if not source.isCOMP or any(getattr(source.par, band + suffix, None) is None
                                    for band in ('Low', 'Mid') for suffix in ('thresh', 'gain', 'add', 'smooth', 'active')):
            raise ValueError('Choose an audioAnalysis COMP with Low/Mid controls')
        return controller.ConfigureMixAnalysis(source.parent(), source.name)
    if style == 'layers':
        return controller.ConfigureMixLayers(source.parent(), source.name,
            operation_choices=mix_draft_operations(controller))
    raise ValueError('Choose Analysis or Layer Mix; audio processing remains planned')


def reset_mix_ui(controller):
    """Remove user source references from a generic export clone's draft."""
    controller.par.Mixstyle.val = 'analysis'
    controller.par.Mixsource.val = ''
    controller.par.Mixpresetname.val = ''
    controller.par.Mixoperationpreset.val = MIX_DRAFT_PRESET
    for name in MIX_CUSTOM_PARAMETERS:
        getattr(controller.par, name).val = MIX_NO_OPERATION
    refresh_mix_ui(controller)
    refresh_mix_presets_ui(controller)
    controller.ext.RotoPythonExt._sync_mix_summary()


# SysEx API v1.6 Appendix A. Index 47 prints a non-hex G component, BO;
# retain its palette identity instead of inventing an RGB value.
TRACK_COLOR_LABELS = (
    "00 / #FF94A0 / dark text",
    "01 / #FFA527 / dark text",
    "02 / #D39925 / dark text",
    "03 / #FFF477 / dark text",
    "04 / #C6FB00 / dark text",
    "05 / #1BFF2D / dark text",
    "06 / #26FFA2 / dark text",
    "07 / #5FFFDF / dark text",
    "08 / #90C5F6 / dark text",
    "09 / #5780DB / dark text",
    "10 / #97A7F6 / dark text",
    "11 / #E06CDB / dark text",
    "12 / #ED539A / dark text",
    "13 / #FFFFF6 / dark text",
    "14 / #FF3634 / dark text",
    "15 / #FF6C02 / dark text",
    "16 / #9E6248 / dark text",
    "17 / #FFF032 / dark text",
    "18 / #8CFF63 / dark text",
    "19 / #3FC300 / dark text",
    "20 / #00BFA8 / dark text",
    "21 / #19E9F6 / dark text",
    "22 / #10A4E5 / dark text",
    "23 / #007DB9 / dark text",
    "24 / #8D6CDB / dark text",
    "25 / #BD77BF / dark text",
    "26 / #FF39CC / dark text",
    "27 / #D8D0C8 / dark text",
    "28 / #EC6856 / dark text",
    "29 / #FFA36F / dark text",
    "30 / #DBAD6D / dark text",
    "31 / #F6FFA7 / dark text",
    "32 / #DAE492 / dark text",
    "33 / #C1D06F / dark text",
    "34 / #A1C488 / dark text",
    "35 / #DCFDD9 / dark text",
    "36 / #D4F1EF / dark text",
    "37 / #C0C1DA / dark text",
    "38 / #D4BBDB / dark text",
    "39 / #B498DC / dark text",
    "40 / #EDDCD9 / dark text",
    "41 / #AFA9A3 / dark text",
    "42 / #EE9286 / dark text",
    "43 / #BE8252 / dark text",
    "44 / #9E8366 / dark text",
    "45 / #C6BA65 / dark text",
    "46 / #ACBE00 / dark text",
    "47 / RGB unavailable / dark text",
    "48 / #8DC2B3 / dark text",
    "49 / #A1B3BD / dark text",
    "50 / #8AA5BF / dark text",
    "51 / #8893C4 / dark text",
    "52 / #AB95AE / dark text",
    "53 / #C69FB7 / dark text",
    "54 / #C37190 / dark text",
    "55 / #7F7B76 / dark text",
    "56 / #B53331 / light text",
    "57 / #AF512F / light text",
    "58 / #764F3E / light text",
    "59 / #E3C300 / light text",
    "60 / #8A961D / light text",
    "61 / #569F2F / light text",
    "62 / #0A9C88 / light text",
    "63 / #24637F / light text",
    "64 / #1B2F90 / light text",
    "65 / #30529C / light text",
    "66 / #654BA6 / light text",
    "67 / #A94BA6 / light text",
    "68 / #D32E6A / light text",
    "69 / #3E3C39 / light text",
    "70 / #101010 / light text",
    "71 / #FF0000 / light text",
    "72 / #00FF00 / dark text",
    "73 / #FFFF00 / dark text",
    "74 / #0000F6 / light text",
    "75 / #FF00F6 / light text",
    "76 / #00FFF6 / dark text",
    "77 / #840000 / light text",
    "78 / #848000 / dark text",
    "79 / #008000 / light text",
    "80 / #00807B / dark text",
    "81 / #00007B / light text",
    "82 / #84007B / light text",
)


def track_color_rgb(index):
    """Normalized palette background, or None where the official RGB is invalid."""
    if type(index) is not int or not 0 <= index < len(TRACK_COLOR_LABELS):
        raise ValueError('Track color must be a palette index from 0 to 82')
    color = TRACK_COLOR_LABELS[index].split(' / ')[1]
    if not color.startswith('#'):
        return None
    return tuple(int(color[offset:offset + 2], 16) / 255.0 for offset in (1, 3, 5))


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
    color=getattr(controller.par,'Trackcolor',None)
    new_color=color is None
    if color is None:
        color=page.appendMenu('Trackcolor',label='Track color')[0]
    color.menuNames=[str(index) for index in range(len(TRACK_COLOR_LABELS))]
    color.menuLabels=list(TRACK_COLOR_LABELS)
    if new_color:color.default=color.val='0'
    color.enableExpr="me.par.Setupmode == 'collection'"
    preview_names=('Trackcolorpreviewr','Trackcolorpreviewg','Trackcolorpreviewb')
    if getattr(controller.par,preview_names[0],None) is None:
        page.appendRGB('Trackcolorpreview',label='Track BG preview')
    for channel,name in enumerate(preview_names):
        parameter=getattr(controller.par,name)
        parameter.default=track_color_rgb(0)[channel]
        parameter.expr="(me.op('setup').module.track_color_rgb(int(me.par.Trackcolor)) or (0, 0, 0))["+str(channel)+"]"
        parameter.readOnly=True
        parameter.enableExpr="me.par.Setupmode == 'collection' and me.par.Trackcolor != '47'"
        parameter.help='Read-only palette background preview. Palette 47 has an invalid RGB component in the official tables; its disabled preview is unavailable.'
    callbacks=controller.op('parameter_callbacks');watched=callbacks.par.pars.eval().split()
    callbacks.par.pars=' '.join(watched+['Trackcolor'] if 'Trackcolor' not in watched else watched)
    names=names[:7]+('Trackcolor',)+preview_names+names[7:]
    for order, name in enumerate(names):
        parameter = getattr(controller.par, name)
        parameter.page = page if order<14 else device
        parameter.order = order if order<14 else order-14
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
    install_mix_ui(controller)
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
