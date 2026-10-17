"""Execute in TD: export(controller, destination). Source COMP stays untouched.

The tox embeds TD code and the MIDI helper. Python with MIDI dependencies
remains an explicit runtime requirement; no repository files are needed.
"""
from pathlib import Path
import uuid


def reset_mapping_storage(clone):
    """Sanitize only a detached export clone, never its external owner COMPs."""
    defaults={'layout_registry':None,'layout_registry_suspended':False,
              'roto_control_owner_id':None,'pending_unmap_identities':[],
              'assignment_device_id':None,'parameter_assignments':[],
              'page_targets':[],'control_catalog':[],'removed_controls':[],
              'pending_unmaps':[],'control_overrides':{},'needs_relearn':(),
              'snapshot_presets':dict(version=2,records=[],deleted=[]), 'mix_profile':None,
              'mix_operation_presets':dict(version=1,records=[])}
    for key,value in defaults.items():clone.store(key,value)


def reset_registration(clone):
    """Sanitize both consumer hooks and runtime entries on an export clone."""
    clone.ext.RotoPythonExt._actions = None
    clone.ext.RotoPythonExt._snapshots = None
    clone.ext.RotoPythonExt._snapshot_error = ''
    clone.ext.RotoPythonExt._mix = None
    clone.ext.RotoPythonExt._hardware_config = None
    clone.ext.RotoPythonExt._hardware_observation = None
    clone.ext.RotoPythonExt._hardware_revision = 0
    if getattr(getattr(clone, 'par', None), 'Mixsource', None) is not None:
        clone.op('setup').module.reset_mix_ui(clone)
    clone.op('registration').text = (
        'def onRegister(controller):\n'
        '    # Register your parameters/callbacks here, then select Python registration.\n'
        '    raise ValueError("Configure registration.onRegister first")\n'
        '\ndef onRegisterActions(controller):\n    pass\n'
)


def export(controller, destination):
    if controller.ext.RotoPythonExt._process is not None:
        raise ValueError('Disconnect before exporting')
    hardware = getattr(controller.ext.RotoPythonExt, '_hardware_config', None)
    if hardware is not None and hardware.active:
        raise ValueError('Finish or disconnect Serial read before exporting')
    follower = getattr(controller.ext.RotoPythonExt, '_follow', None)
    if follower is not None:
        follower.refresh_links()
    destination = Path(destination).absolute()
    if destination.suffix != '.tox':
        raise ValueError('Export destination must end in .tox')
    if destination.exists():
        raise FileExistsError(destination)
    resolver = getattr(controller.op('RotoPythonExt').module, 'resolve_python', None)
    if not callable(resolver):
        raise ValueError('Upgrade the controller runtime before generic export; '
                         'the exported python3 command requires PATH resolution')
    resolver(controller.par.Python.eval(), project.folder)
    for name in ('hardware_config', 'serial_read_process'):
        node = controller.op(name)
        if node is None or not node.text.strip():
            raise ValueError('Embed ' + name + ' before exporting')
    holder = controller.parent().create(baseCOMP, 'base_export_' + uuid.uuid4().hex[:8])
    holder.viewer = holder.display = True
    try:
        clone = holder.copy(controller, name='roto_python')
        # Generic exports must not retain arbitrary controller storage backups
        # (including old verification snapshots containing user mappings).
        # The documented empty runtime/configuration fields are rebuilt below.
        clone.storage.clear()
        for dat in clone.findChildren(type=DAT):
            file_par = getattr(dat.par, 'file', None)
            if file_par is not None:
                sync = getattr(dat.par, 'syncfile', None)
                if sync is not None:
                    sync.val = False
                load = getattr(dat.par, 'loadonstart', None)
                if load is not None:
                    load.val = False
                file_par.val = ''
        helper = clone.op('midi_process')
        if helper is None or not helper.text.strip():
            raise ValueError('Embed midi_process before exporting')
        # Optional CHOP monitoring is outside the portable tool interface.
        for name in ('parameter_values', 'null_values', 'out_values',
                     'select_controls', 'null_controls', 'out_controls'):
            node = clone.op(name)
            if node is not None:
                node.destroy()
        clone.par.Helper.default = clone.par.Helper.val = ''
        clone.par.Helper.enable = False
        # A generic tox must not serialize the exporting machine's venv path.
        clone.par.Python.default = clone.par.Python.val = 'python3'
        clone.ext.RotoPythonExt._layouts = None
        clone.par.Followcomp.default = clone.par.Followcomp.val = False
        clone.par.Focuscomp.val = ''
        clone.ext.RotoPythonExt._follow.handles.clear()
        clone.ext.RotoPythonExt._follow.invalidate()
        reset_mapping_storage(clone)
        clone.op('inspector').store('pending_clear', None)
        clone.op('inspector').store('clear_press', None)
        for name, value in (('Trackname', 'EFFECT'), ('Pluginname', 'CUSTOM')):
            par = getattr(clone.par, name)
            par.default = par.val = value
        clone.ext.RotoPythonExt.SetLayoutNames('EFFECT', 'CUSTOM')
        clone.par.Setupmode = 'collection'
        for name in ('Targetcomp', 'Targetpar', 'Bindingid', 'Targetlabel'):
            parameter = getattr(clone.par, name, None)
            if parameter is not None:
                parameter.val = ''
        clone.par.Groupid = 'roto.controls.v1'
        clone.ext.RotoPythonExt._value_parameter().val = .5
        table = clone.op('base_targets/targets')
        columns = [cell.val for cell in table.row(0)]
        table.clear()
        table.appendRow(columns)
        reset_registration(clone)
        clone.ext.RotoPythonExt.BindControls([], group_id=clone.par.Groupid.eval(), _allow_empty=True)
        # A newly copied extension may not have completed its first Tick.
        # Rebuild after clearing: capture preserves unavailable old targets by
        # design, so it cannot be used to sanitize a generic export.
        clone.ext.RotoPythonExt._layout_ready = True
        clone.ext.RotoPythonExt._layouts = None
        clone.store('layout_registry', None)
        clone.store('page_targets', [])
        clone.ext.RotoPythonExt._layout_manager()
        clone.op('setup').module.configure_ui(clone)
        clone.ext.RotoPythonExt.Disconnect()
        runtime = clone.op('inspector/owned_runtime')
        if runtime is None:
            raise ValueError('Install the owned Inspector before exporting')
        runtime.module.sanitize(clone)
        clone.save(str(destination), createFolders=True)
    finally:
        holder.destroy()
    return str(destination)
