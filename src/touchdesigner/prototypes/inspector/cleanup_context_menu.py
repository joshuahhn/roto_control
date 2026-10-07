"""Annotate only the new dropdown groups and verify measured containment."""
from pathlib import Path
import json
scope=dict(globals())
exec(Path(project.folder+'/prototypes/inspector/cleanup_health.py').read_text().split('results=[]')[0],scope)
annotate=scope['annotate'];results=[]
def check(parent):
    nodes=[o for o in parent.children if o.OPType!='annotateCOMP']
    for i,a in enumerate(nodes):
        for b in nodes[i+1:]:
            assert a.nodeX+a.nodeWidth<=b.nodeX or b.nodeX+b.nodeWidth<=a.nodeX or a.nodeY+a.nodeHeight<=b.nodeY or b.nodeY+b.nodeHeight<=a.nodeY,(a.path,b.path)
    return nodes
for view in (op('/inspector_below'),op('/inspector_popup')):
    nodes=[view.op(n) for n in ('container_context_menu','context_menu','context_outside_click','context_focus')]
    group=annotate(view,'annotate_context_menu','Dropdown',nodes)
    for other in view.children:
        if other.OPType=='annotateCOMP' and other!=group:
            assert group.nodeX+group.nodeWidth+20<=other.nodeX or other.nodeX+other.nodeWidth+20<=group.nodeX or group.nodeY+group.nodeHeight+20<=other.nodeY or other.nodeY+other.nodeHeight+20<=group.nodeY
    panels=[view.op('container_context_menu')]
    for editor in view.ext.InspectorView._editors:
        panel=editor.op('container_context_menu');panels.append(panel)
        group=annotate(editor,'annotate_context_menu','Dropdown',[panel])
        for other in editor.children:
            if other.OPType=='annotateCOMP' and other!=group:
                assert group.nodeX+group.nodeWidth+20<=other.nodeX or other.nodeX+other.nodeWidth+20<=group.nodeX or group.nodeY+group.nodeHeight+20<=other.nodeY or other.nodeY+other.nodeHeight+20<=group.nodeY
    popup=view.ext.InspectorView._popup_host
    annotate(popup,'annotate_context_events','Dropdown events',[popup.op('context_focus'),popup.op('context_outside_click')])
    for panel in panels:
        for component in [panel,panel.op('base_footer')]+[panel.op('row'+str(i)) for i in range(8)]:
            nodes=check(component);annotate(component,'annotate_dropdown','Dropdown',nodes)
    assert not view.errors(recurse=True)
    results.append(dict(view=view.path,pools=3,rows_per_pool=8,no_overlap=True,contained=True,menu_windows=0))
Path(project.folder+'/prototypes/inspector/context_menu_network.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results))
