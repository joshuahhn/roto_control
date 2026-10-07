"""Read-only picker workload; excludes OS rendering and MIDI cost."""
from pathlib import Path
from time import perf_counter
import json

m=op('/inspector_model');controller=m.par.Controller.eval()
before=controller.GetControlCatalog();session=m.ext.InspectorModel.adapter.Session()
views=[op('/inspector_below'),op('/inspector_popup')]
for v in views:v.CloseEditor();v.op('window_editor').par.winclose.pulse()
t=m.op('base_targets').ext.InspectorTargets;t.Reset()
unit_source=t.source.Units;scans=[];steps=[];results=[]

def units(scope,kind):
    scans.append((scope,kind))
    yield from unit_source(scope,kind)

def drain():
    for _ in range(1000):
        if not t.jobs:return
        for identity,job in list(t.jobs.items()):
            if job['pending']:job['pending'].kill()
            started=perf_counter();t._step(identity,job['serial']);steps.append((perf_counter()-started)*1000)
    raise AssertionError('Unbounded discovery')

try:
    t.source.Units=units
    # Actual target subtree and project-level discovery, including empty COMPs.
    for scope in dict.fromkeys([m.TargetScope(),controller.parent().path]):
        started=perf_counter();t.Start('profile',scope,'knob',lambda *result:results.append(result),True)
        steps.append((perf_counter()-started)*1000);drain()
    cold_scans=len(scans)
    cached=[]
    for _ in range(100):
        started=perf_counter();t.Start('profile',m.TargetScope(),'knob',lambda *result:None)
        cached.append((perf_counter()-started)*1000)
    assert len(scans)==cold_scans
    view=views[0];u=view.ext.InspectorView
    view.Action('slot0');view.Action('target_picker');drain()
    operators=len(view.findChildren())
    queries=[]
    for i in range(100):
        started=perf_counter();u.PickerQuery('Sort' if i%2 else '')
        queries.append((perf_counter()-started)*1000)
    assert len(scans)==cold_scans and len(view.findChildren())==operators
    for _ in range(20):view.Action('picker_cancel');view.Action('target_picker');drain()
    assert len(view.findChildren())==operators and t.Stats()['jobs']==0
    view.CloseEditor();view.op('window_editor').par.winclose.pulse()
    sync=[];writes=[v.Stats()['text_writes'] for v in views]
    for _ in range(100):
        started=perf_counter();m.Sync();m.Flush();sync.append((perf_counter()-started)*1000)
    assert writes==[v.Stats()['text_writes'] for v in views]
    p95=lambda values:sorted(values)[max(0,int(len(values)*.95)-1)]
    result=dict(discovery_scans=cold_scans,cold_result_counts=[len(r[0]) for r in results],
                discovery_step_p95_ms=p95(steps),discovery_step_max_ms=max(steps),
                cached_open_p95_ms=p95(cached),query_ui_p95_ms=p95(queries),sync_p95_ms=p95(sync),
                cache=t.Stats(),queries_no_rescan=True,reopen_node_count_stable=True,idle_text_write_delta=0,
                native_render_and_midi_measured=False,long_duration_memory_measured=False)
finally:
    t.source.Units=unit_source
    for v in views:v.CloseEditor();v.op('window_editor').par.winclose.pulse()
assert controller.GetControlCatalog()==before and m.ext.InspectorModel.adapter.Session()==session
assert m.Stats()['subscribers']==2 and not m.Stats()['subscriber_errors']
result['production_catalog_session_preserved']=True
Path(project.folder+'/prototypes/inspector/targets_performance.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result))
