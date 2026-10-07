"""Annotate existing view groups and verify measured network containment."""
import json
from pathlib import Path

def annotate(parent,name,title,operators):
    x=min(o.nodeX for o in operators)-25;y=min(o.nodeY for o in operators)-25
    right=max(o.nodeX+o.nodeWidth for o in operators)+25
    top=max(o.nodeY+o.nodeHeight for o in operators)+60
    a=parent.op(name) or parent.create(annotateCOMP,name)
    a.name=name
    a.viewer=True;a.par.Mode='annotate';a.par.Titletext=title;a.par.Bodytext=title+' components and callbacks'
    a.nodeX=x;a.nodeY=y;a.nodeWidth=right-x;a.nodeHeight=top-y;a.color=(.28,.28,.28)
    for o in operators:
        assert o.nodeX>=a.nodeX+25 and o.nodeX+o.nodeWidth<=a.nodeX+a.nodeWidth-25
        assert o.nodeY>=a.nodeY+25 and o.nodeY+o.nodeHeight<=a.nodeY+a.nodeHeight-60
    return a

results=[]
for view in [op('/inspector_below'),op('/inspector_popup')]:
    events=[view.op(n) for n in ('click_follow','click_presentation','window_opened')]
    state=[view.op('editor_state')] if view.op('editor_state') else []
    operators=[o for o in view.children if o not in events+state and o.OPType!='annotateCOMP']
    groups=[annotate(view,'annotate_view','View',operators),annotate(view,'annotate_events','Events',events)]
    if state:groups.append(annotate(view,'annotate_state','State',state))
    all_ops=operators+events+state
    for i,a in enumerate(all_ops):
        for b in all_ops[i+1:]:
            assert a.nodeX+a.nodeWidth<=b.nodeX or b.nodeX+b.nodeWidth<=a.nodeX or a.nodeY+a.nodeHeight<=b.nodeY or b.nodeY+b.nodeHeight<=a.nodeY
    for i,a in enumerate(groups):
        for b in groups[i+1:]:assert a.nodeX+a.nodeWidth+20<=b.nodeX or b.nodeX+b.nodeWidth+20<=a.nodeX or a.nodeY+a.nodeHeight+20<=b.nodeY or b.nodeY+b.nodeHeight+20<=a.nodeY
    results.append(dict(view=view.path,functional_nodes=len(all_ops),no_overlap=True,groups=[[a.par.Titletext.eval(),a.nodeX,a.nodeY,a.nodeWidth,a.nodeHeight] for a in groups]))
model=op('/inspector_model')
annotations=[o for o in model.children if o.OPType=='annotateCOMP']
for i,a in enumerate(annotations):
    for b in annotations[i+1:]:
        assert a.nodeX+a.nodeWidth+20<=b.nodeX or b.nodeX+b.nodeWidth+20<=a.nodeX or a.nodeY+a.nodeHeight+20<=b.nodeY or b.nodeY+b.nodeHeight+20<=a.nodeY
assert not any(o.errors(recurse=True) for o in [model,op('/inspector_below'),op('/inspector_popup')])
Path(project.folder+'/prototypes/inspector/health_network.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results))
