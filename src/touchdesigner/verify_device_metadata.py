"""Run verify(controller) in TD; exercise deletion/rename without hardware I/O."""
from pathlib import Path
import json


def verify(controller):
    holder = controller.parent().create(baseCOMP, 'base_device_metadata_verification')
    holder.nodeX, holder.nodeY = 700, -500
    holder.viewer = holder.display = True
    try:
        clone = holder.copy(controller, name='controller')
        clone.nodeX, clone.nodeY = 0, 0
        clone.Disconnect()
        clone.par.Followcomp = False
        for name in ('layouts', 'protocol'):
            clone.op(name).text = Path(project.folder, 'code/py/roto_python', name+'.py').read_text(encoding='utf-8')
        clone.par.reinitextensions.pulse()
        clone.Applybinding()
        e = clone.ext.RotoPythonExt
        packets = []
        e._host.send = lambda message: packets.append(list(message))
        for deleted_active in (False, True):
            layout = e.CreateLayout('Metadata verification')
            e.SelectLayout(layout)
            m = e._layout_manager()
            track = m.track()['id']
            a = m.plugin()['id']
            b = e.CreatePlugin(layout, track, 'B')
            c = e.CreatePlugin(layout, track, 'C')
            e.SelectPlugin(layout, track, a if deleted_active else b)
            e._host.connected = e._host.plugin = True
            e.RemovePlugin(layout, track, a)
            assert m.plugin()['id'] == b and e._host.plugin_index == 0
            e._host.send = lambda message: packets.append(list(message))
            e._host.connected = e._host.plugin = True
            packets.clear()
            e.RenamePlugin(layout, track, b, 'Renamed B')
            details = [p for p in packets if p[5:7] == [11, 5]]
            assert details and all(p[7] == 0 for p in details[:1]), details
            assert [p['id'] for p in m.track()['plugins']] == [b, c]
            packets.clear()
            e.RenameTrack(layout, track, 'Renamed')
            assert m.track()['name'] == 'Renamed'
            assert not any(p[5:7] == [11, 5] for p in packets)
            e._host.connected = e._host.plugin = False
        assert not clone.errors(recurse=True)
        result = dict(native_build=str(app.build), deletion_reindexed=True,
                      active_deletion_reindexed=True, subsequent_device_rename_index=0,
                      track_rename_no_device_details=True, physical_acceptance=False, errors='')
        Path(project.folder, 'device_metadata_native_verification.json').write_text(
            json.dumps(result, indent=2), encoding='utf-8')
        return result
    finally:
        holder.op('controller').Disconnect()
        holder.destroy()
