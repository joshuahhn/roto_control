"""Reopen immediately after collapsing a settled expanded native Popup."""
from pathlib import Path
import json
v=op('/inspector_below');u=v.ext.InspectorView;p=u._popup;m=u._model;c=m.ownerComp.par.Controller.eval()
base=(p.contentWidth,p.contentHeight);before=c.GetControlCatalog();session=m.adapter.Session();index=0;stage=0;samples=[]
cycles=globals().get('cycles',5);label=globals().get('label','before')
def step():
    global index,stage
    if stage==0:
        if u.selected is None:v.Action('slot0')
        v.Action('mapping_toggle');stage=1
    else:
        if stage==1:
            v.CloseEditor();p.par.winclose.pulse();v.Action('slot0');stage=2
        else:
            samples.append(dict(actual=p.contentHeight,opening=p.par.winh.eval(),content=u._editors[1].height,width=p.contentWidth));index+=1
            if index>=cycles:
                result=dict(baseline=base,samples=samples,all_pass=all(s['actual']==base[1] and s['opening']==base[1] and s['content']==178 and s['width']==base[0] for s in samples),production_preserved=c.GetControlCatalog()==before and m.adapter.Session()==session)
                Path(project.folder+'/prototypes/inspector/popup_reopen_height_'+label+'.json').write_text(json.dumps(result,indent=2));print(json.dumps(result));return
            stage=0
    run('args[0]()',step,delayFrames=4,delayRef=op.TDResources)
step()
