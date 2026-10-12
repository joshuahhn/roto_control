"""Manual size becomes the base; section deltas retain width and top-left."""
from pathlib import Path
import json
import runpy

# run_path supplies __file__; exec callers supply inspector_source_dir explicitly.
_probe_dir = globals().get('inspector_source_dir')
if _probe_dir is None:
    _probe_dir = Path(__file__).resolve().parent
globals().update(runpy.run_path(str(Path(_probe_dir) / 'popup_probe.py'))['prepare'](globals()))
saved=(p.contentWidth,p.contentHeight,p.x,p.y);stage=0;result={}
def step():
    global stage
    if stage==0:p.par.winw=376;p.par.winh=220
    elif stage==1:
        result['manual_size']=(p.contentWidth,p.contentHeight)==(376,220)
        result['corner']=(p.x,p.y+p.height);u._sync_popup_expansion(134)
    elif stage==2:
        result['expanded_correct']=(p.contentWidth,p.contentHeight)==(376,354)
        result['expanded_corner']=(p.x,p.y+p.height)==tuple(result['corner']);u._sync_popup_expansion(0)
    elif stage==3:
        result['collapsed_retains_manual_base']=(p.contentWidth,p.contentHeight)==(376,220)
        result['collapsed_corner']=(p.x,p.y+p.height)==tuple(result['corner'])
        p.par.winw=saved[0];p.par.winh=saved[1];p.par.winoffsetx=saved[2];p.par.winoffsety=saved[3]
    else:
        result['restored']=(p.contentWidth,p.contentHeight,p.x,p.y)==saved
        result['all_pass']=all(x for x in result.values() if type(x)is bool)
        write_result('popup_manual_base_verification.json',result);print(json.dumps(result));return
    stage+=1;run('args[0]()',step,delayFrames=4,delayRef=op.TDResources)
step()
