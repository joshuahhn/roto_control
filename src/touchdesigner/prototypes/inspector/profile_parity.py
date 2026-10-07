"""Bounded read-only Python workload; OS drawing/MIDI/long soak are excluded."""
from pathlib import Path
from time import perf_counter
import json
m=op('/inspector_model');c=m.par.Controller.eval();before=c.GetControlCatalog();session=m.ext.InspectorModel.adapter.Session()
views=[op('/inspector_below'),op('/inspector_popup')]
styles=[v.ext.InspectorView.style for v in views]
counts=[len(v.findChildren()) for v in views]
def measure(action,n=100):
    samples=[]
    for _ in range(n):
        start=perf_counter();action();samples.append((perf_counter()-start)*1000)
    return dict(p95_ms=sorted(samples)[int(n*.95)-1],max_ms=max(samples),samples=n)
try:
    for v in views:v.CloseEditor();v.op('window_editor').par.winclose.pulse()
    writes=[v.Stats()['text_writes'] for v in views]
    idle=measure(lambda:(m.Sync(),m.Flush()))
    assert writes==[v.Stats()['text_writes'] for v in views]
    v=views[0];u=v.ext.InspectorView;u.style='below';v.Action('slot0');v.Action('details_toggle')
    opened=measure(lambda:(m.Sync(),m.Flush()))
    refresh=measure(lambda:v.Action('details_refresh'))
    toggle=measure(lambda:(v.Action('details_toggle'),v.Action('details_toggle')))
    assert counts==[len(v.findChildren()) for v in views]
    assert m.Stats()['subscribers']==2 and not m.Stats()['scheduled'] and not m.Stats()['subscriber_errors']
    assert m.op('base_targets').Stats()['jobs']==0
    result=dict(idle_sync=idle,details_open_sync=opened,details_refresh=refresh,details_toggle_pair=toggle,
                idle_row_text_write_delta=0,operator_count_stable=True,subscribers=2,discovery_jobs=0,
                native_render_and_midi_measured=False,long_duration_memory_measured=False)
finally:
    for v,style in zip(views,styles):v.ext.InspectorView.style=style;v.CloseEditor();v.op('window_editor').par.winclose.pulse()
assert c.GetControlCatalog()==before and m.ext.InspectorModel.adapter.Session()==session
result['production_catalog_session_preserved']=True
Path(project.folder+'/prototypes/inspector/parity_performance.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result))
