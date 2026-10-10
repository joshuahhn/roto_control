"""Measure, annotate and verify editor networks after the Mapping upgrade."""
from pathlib import Path
import json
ns=dict(globals());exec(Path(project.folder+'/prototypes/inspector/cleanup_health.py').read_text(),ns)
annotate=ns['annotate']

def clean_grid(parent):
    nodes=[o for o in parent.children if o.OPType!='annotateCOMP']
    for i,o in enumerate(nodes):o.nodeX=(i%5)*200;o.nodeY=-(i//5)*160+130-o.nodeHeight
    return nodes

def check(nodes):
    for i,a in enumerate(nodes):
        for b in nodes[i+1:]:
            assert a.nodeX+a.nodeWidth<=b.nodeX or b.nodeX+b.nodeWidth<=a.nodeX or a.nodeY+a.nodeHeight<=b.nodeY or b.nodeY+b.nodeHeight<=a.nodeY

results=[]
for view in [op('/inspector_below'),op('/inspector_popup')]:
    for editor in view.ext.InspectorView._editors:
        mapping=[editor.op(n) for n in ('container_mapping','mapping_toggle','click_mapping_toggle')]
        fields=[o for o in editor.children if o not in mapping and o.OPType!='annotateCOMP']
        for i,o in enumerate(fields):o.nodeX=(i%5)*200;o.nodeY=-(i//5)*160+130-o.nodeHeight
        groups=[annotate(editor,'annotate_fields','Fields',fields),annotate(editor,'annotate_mapping','Mapping',mapping)]
        top=max(a.nodeY+a.nodeHeight for a in groups)
        for a in groups:a.nodeHeight=top-a.nodeY
        check(fields+mapping)
        for i,a in enumerate(groups):
            for b in groups[i+1:]:assert a.nodeX+a.nodeWidth+20<=b.nodeX or b.nodeX+b.nodeWidth+20<=a.nodeX
        section=editor.op('container_mapping');nodes=clean_grid(section);check(nodes)
        annotate(section,'annotate_mapping','Mapping',nodes)
        results.append(dict(editor=editor.path,nodes=len(fields+mapping),mapping_nodes=len(nodes),no_overlap=True))
    popup=view.op('ui').module.popup_host(view);nodes=[popup.op('container_editor_content'),popup.op('scroll_wheel')]
    check(nodes);annotate(popup,'annotate_viewport','Viewport',nodes)
    if view.op('base_popup'):annotate(view.op('base_popup'),'annotate_popup','Popup',[popup])
assert not any(c.errors(recurse=True) for c in [op('/inspector_model'),op('/inspector_below'),op('/inspector_popup')])
Path(project.folder+'/prototypes/inspector/mapping_network.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results))
