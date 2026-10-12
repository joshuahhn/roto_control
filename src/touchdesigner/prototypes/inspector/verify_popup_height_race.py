"""Finite same-tick section/dropdown churn; no production data writes."""
from pathlib import Path
import json
import runpy

# run_path supplies __file__; exec callers supply inspector_source_dir explicitly.
_probe_dir = globals().get('inspector_source_dir')
if _probe_dir is None:
    _probe_dir = Path(__file__).resolve().parent
globals().update(runpy.run_path(str(Path(_probe_dir) / 'popup_probe.py'))['prepare'](globals()))
before=controller.GetControlCatalog();session=m.ext.InspectorModel.adapter.Session()
cycles=globals().get('cycles',20);label=globals().get('label','after');index=0;samples=[]
base=(p.contentWidth,p.contentHeight);corner=(p.x,p.y+p.height);opens=u._window_opens

def finish(error=None):
    u.CloseContextMenu();v.CloseEditor()
    result=dict(label=label,cycles=len(samples),baseline=base,samples=samples,all_heights_restored=all(s['actual_height']==base[1] and s['opening_height']==base[1] for s in samples),width_corner_preserved=all(s['width']==base[0] and tuple(s['corner'])==corner for s in samples),no_reopen=u._window_opens==opens,production_catalog_session_preserved=controller.GetControlCatalog()==before and m.ext.InspectorModel.adapter.Session()==session,error=error)
    result['all_pass']=result['all_heights_restored'] and result['width_corner_preserved'] and result['no_reopen'] and result['production_catalog_session_preserved'] and not error
    write_result('popup_height_race_'+label+'.json',result);print(json.dumps({k:x for k,x in result.items() if k!='samples'}))

def step():
    global index
    try:
        if index:
            samples.append(dict(actual_height=p.contentHeight,opening_height=p.par.winh.eval(),editor_height=u._editors[1].height,width=p.contentWidth,corner=(p.x,p.y+p.height)))
        if index>=cycles:finish();return
        if u.selected is None:v.Action('slot0')
        # Native resize processing may still show the old dimensions between
        # every call below. Final intent is always a collapsed 178px editor.
        for name in ('mapping_toggle','details_toggle','target_picker','mapping_toggle','mapping_toggle','value_menu'):
            v.Action(name)
        u.CloseContextMenu();v.CloseEditor();v.Action('slot0')
        index+=1;run('args[0]()',step,delayFrames=4,delayRef=op.TDResources)
    except Exception as error:finish(str(error));raise
step()
