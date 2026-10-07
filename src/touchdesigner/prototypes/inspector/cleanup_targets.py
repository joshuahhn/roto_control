"""Measured grouping for target picker, typed fields and shared discovery."""
from pathlib import Path
import json
namespace=dict(globals());exec(Path(project.folder+'/prototypes/inspector/cleanup_health.py').read_text(),namespace)
annotate=namespace['annotate']

def grid(nodes,x=0):
    for i,o in enumerate(nodes):o.nodeX=x+(i%5)*200;o.nodeY=-(i//5)*160+130-o.nodeHeight

def verify(nodes,groups):
    for i,a in enumerate(nodes):
        for b in nodes[i+1:]:assert a.nodeX+a.nodeWidth<=b.nodeX or b.nodeX+b.nodeWidth<=a.nodeX or a.nodeY+a.nodeHeight<=b.nodeY or b.nodeY+b.nodeHeight<=a.nodeY
    for i,a in enumerate(groups):
        for b in groups[i+1:]:assert a.nodeX+a.nodeWidth+20<=b.nodeX or b.nodeX+b.nodeWidth+20<=a.nodeX or a.nodeY+a.nodeHeight+20<=b.nodeY or b.nodeY+b.nodeHeight+20<=a.nodeY
    for o in nodes:
        assert not o.inputConnectors or all(not connector.connections for connector in o.inputConnectors),o.path

model=op('/inspector_model');targets=model.op('base_targets')
annotate(model,'annotate_targets','Targets',[targets])
group=annotate(targets,'annotate_targets','Targets',[targets.op('TargetCatalog')]);verify([targets.op('TargetCatalog')],[group])
c=model.op('base_commands');annotate(c,'annotate_commands','Commands',[o for o in c.children if o.OPType!='annotateCOMP'])
results=[]
for view in [op('/inspector_below'),op('/inspector_popup')]:
    for editor in view.ext.InspectorView._editors:
        mapping=[editor.op(n) for n in ('container_mapping','mapping_toggle','click_mapping_toggle')]
        picker=[editor.op('container_picker')]
        details=[editor.op(n) for n in ('container_details','details_toggle','click_details_toggle') if editor.op(n)]
        fields=[o for o in editor.children if o not in mapping+picker+details and o.OPType!='annotateCOMP']
        grid(fields);grid(mapping,max(o.nodeX+o.nodeWidth for o in fields)+70);grid(picker,max(o.nodeX+o.nodeWidth for o in mapping)+70)
        if details:grid(details,max(o.nodeX+o.nodeWidth for o in picker)+70)
        groups=[annotate(editor,'annotate_fields','Fields',fields),annotate(editor,'annotate_mapping','Mapping',mapping),annotate(editor,'annotate_picker','Picker',picker)]
        if details:groups.append(annotate(editor,'annotate_details','Details',details))
        # Mapping has one COMP followed by a toggle and callback, all in a row.
        top=max(a.nodeY+a.nodeHeight for a in groups)
        for a in groups:a.nodeHeight=top-a.nodeY
        verify(fields+mapping+picker+details,groups)
        for name in ('container_mapping','container_picker','container_details'):
            if not editor.op(name):continue
            section=editor.op(name);nodes=[o for o in section.children if o.OPType!='annotateCOMP'];grid(nodes)
            group=annotate(section,'annotate_section',name.removeprefix('container_').title(),nodes)
            for old in section.children:
                if old.OPType=='annotateCOMP' and old!=group:old.destroy()
            verify(nodes,[group])
        results.append(dict(editor=editor.path,nodes=len(fields+mapping+picker+details),picker_rows=6,no_overlap=True))
    host=view.op('ui').module.popup_host(view)
    annotate(host,'annotate_viewport','Viewport',[host.op('container_editor_content'),host.op('scroll_wheel')])
    annotate(view.op('base_popup'),'annotate_popup','Popup',[host])
annotations=[o for o in model.children if o.OPType=='annotateCOMP'];verify([],annotations)
assert not any(o.errors(recurse=True) for o in [model,op('/inspector_below'),op('/inspector_popup')])
Path(project.folder+'/prototypes/inspector/targets_network.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results))
