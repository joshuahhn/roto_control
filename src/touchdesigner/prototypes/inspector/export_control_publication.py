"""Export/reload a generic controller; check after native end-frame settlement.

Run with phase='start', then phase='finish' in a later MCP call. Existing exports
are reloaded read-only, so a verification retry never overwrites a tox.
"""
from pathlib import Path
import json

c=op('/roto_control_python/roto_python')
destination=Path(project.folder)/'exports/roto_python.42.tox'
if phase=='start':
    assert not c.parent().op('base_control_publication_export')
    holder=c.parent().create(baseCOMP,'base_control_publication_export')
    holder.viewer=True;holder.nodeX=1100;holder.nodeY=-650
    holder.store('baseline',c.GetControlCatalog())
    # TD storage is serialized during tox saves; Popen contains thread locks.
    holder.store('process_pid',c.ext.RotoPythonExt._process.pid)
    try:
        if not destination.exists():
            offline=holder.copy(c,name='source');offline.Disconnect()
            assert offline.ext.RotoPythonExt._process is None
            ns=dict(globals());exec(Path(project.folder+'/export_component.py').read_text(),ns)
            ns['export'](offline,destination)
            offline.destroy()
        loaded=holder.loadTox(str(destination));loaded.initializeExtensions(0);loaded.Applybinding()
        holder.store('loaded',loaded)
        holder.store('start_frame',int(absTime.frame))
        holder.store('initial_projection_queued',loaded.ext.RotoPythonExt._inspector_refresh_run is not None)
    except Exception:
        holder.destroy()
        raise
    print('Generic export loaded; waiting for its one owned end-frame projection')
elif phase=='finish':
    holder=c.parent().op('base_control_publication_export');assert holder
    try:
        loaded=holder.fetch('loaded')
        elapsed=int(absTime.frame)-holder.fetch('start_frame');assert elapsed>=3
        assert not loaded.State['Connected'] and loaded.GetControlCatalog()==[]
        assert loaded.ext.RotoPythonExt._process is None and not loaded.ext.RotoPythonExt._pending
        assert loaded.ext.RotoPythonExt._inspector_refresh_run is None
        assert loaded.op('RotoPythonExt').text==Path(project.folder+'/code/py/roto_python/RotoPythonExt.py').read_text()
        assert loaded.op('base_targets/controls_values').numChans==0
        assert not loaded.errors(recurse=True)
        assert c.State['Connected'] and c.GetControlCatalog()==holder.fetch('baseline')
        assert c.ext.RotoPythonExt._process.pid==holder.fetch('process_pid')
        result=dict(export=str(destination),reloaded=True,disconnected=True,empty_catalog=True,
            empty_channels=True,embedded_source_current=True,no_process_pending_or_projection_callback=True,
            initial_projection_queued=holder.fetch('initial_projection_queued'),settled_frames=elapsed,
            production_catalog_and_session_preserved=True,errors=[])
        Path(project.folder+'/prototypes/inspector/control_publication_export.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result))
    finally:
        holder.destroy()
else:
    raise ValueError(phase)
