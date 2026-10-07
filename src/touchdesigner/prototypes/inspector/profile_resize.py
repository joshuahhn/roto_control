"""Temporary 20-second frame/resize observer; finish removes every probe OP."""
from pathlib import Path
from time import perf_counter
import json
phase=globals().get('phase','start')
probe=op('/base_resize_measure')
if phase=='start':
    assert probe is None,'Resize probe already running'
    probe=op('/').create(baseCOMP,'base_resize_measure');probe.viewer=probe.display=True
    probe.par.parentshortcut='ResizeProbe';probe.nodeX=1500;probe.nodeY=-800
    perform=probe.create(performCHOP,'perform_frame');perform.viewer=True;perform.par.fps=True;perform.par.cook=True
    output=probe.create(nullCHOP,'null_frame');output.viewer=True;output.nodeX=175;output.inputConnectors[0].connect(perform.outputConnectors[0])
    callback=probe.create(executeDAT,'sample_frame');callback.viewer=True;callback.par.language='python';callback.nodeY=-210
    callback.par.framestart=False;callback.par.frameend=True
    callback.text="""from time import perf_counter
def onFrameEnd(frame):
    owner=parent.ResizeProbe;now=perf_counter();previous=owner.fetch('previous',now)
    owner.store('previous',now)
    data=owner.fetch('samples');p=owner.op('null_frame')
    windows=[op('/inspector_below/'+name) for name in ('window_main','window_editor')]
    data.append(dict(gap_ms=(now-previous)*1000,metrics={c.name:float(c[0]) for c in p.chans()},sizes=[(w.contentWidth,w.contentHeight) for w in windows]))
    if now-owner.fetch('start')>=20 or len(data)>=1200:me.par.active=False
"""
    probe.store('start',perf_counter());probe.store('samples',[])
    print('Temporary frame/resize capture started; stops after 20 seconds')
elif phase=='finish':
    assert probe is not None,'No resize probe'
    probe.op('sample_frame').par.active=False
    try:
        samples=probe.fetch('samples');gaps=sorted(s['gap_ms'] for s in samples[1:])
        changing=[s for i,s in enumerate(samples[1:],1) if s['sizes']!=samples[i-1]['sizes']]
        result=dict(samples=len(samples),resize_frames=len(changing),gap_p95_ms=gaps[int((len(gaps)-1)*.95)] if gaps else None,max_gap_ms=max(gaps) if gaps else None,latest_metrics=samples[-1]['metrics'] if samples else {},resize_max_gap_ms=max((s['gap_ms'] for s in changing),default=None),native_drag_visual_verified=False)
        Path(project.folder+'/prototypes/inspector/resize_frame_profile.json').write_text(json.dumps(result,indent=2))
        print(json.dumps(result))
    finally:probe.destroy()
else:raise ValueError('Unknown phase')
