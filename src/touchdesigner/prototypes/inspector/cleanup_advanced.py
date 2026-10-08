"""Measure/group Advanced nodes without changing UI parameters or callbacks."""
from pathlib import Path
import json

scope=dict(globals())
exec(Path(project.folder+'/prototypes/inspector/cleanup_health.py').read_text().split('results=[]')[0],scope)
annotate=scope['annotate']

def check(nodes,annotations):
    for i,a in enumerate(nodes):
        for b in nodes[i+1:]:
            assert a.nodeX+a.nodeWidth<=b.nodeX or b.nodeX+b.nodeWidth<=a.nodeX or a.nodeY+a.nodeHeight<=b.nodeY or b.nodeY+b.nodeHeight<=a.nodeY,(a.path,b.path)
    for i,a in enumerate(annotations):
        for b in annotations[i+1:]:
            assert a.nodeX+a.nodeWidth+20<=b.nodeX or b.nodeX+b.nodeWidth+20<=a.nodeX or a.nodeY+a.nodeHeight+20<=b.nodeY or b.nodeY+b.nodeHeight+20<=a.nodeY

def grid(nodes):
    for i,o in enumerate(nodes):o.nodeX=(i%5)*200;o.nodeY=-(i//5)*210+130-o.nodeHeight

commands=op('/inspector_model/base_commands')
nodes=[o for o in commands.children if o.OPType!='annotateCOMP']
for old in [o for o in commands.children if o.OPType=='annotateCOMP']:old.destroy()
group=annotate(commands,'annotate_commands','Commands',nodes);check(nodes,[group])
results=[]
for view in (op('/inspector_below'),op('/inspector_popup')):
    draft=view.op('base_draft');watch=draft.op('native_draft_changed')
    if watch:
        watch.nodeX=watch.nodeY=0
        for old in [o for o in draft.children if o.OPType=='annotateCOMP']:old.destroy()
        a=annotate(draft,'annotate_draft','Draft', [watch]);check([watch],[a])
    for editor in view.ext.InspectorView._editors:
        section=editor.op('container_details')
        actions=[section.op(name) for name in ('native_values','native_definition','click_native_values','click_native_definition')]
        existing=[o for o in section.children if o.OPType!='annotateCOMP' and o not in actions]
        grid(existing)
        right=max(o.nodeX+o.nodeWidth for o in existing)
        # Derived20px annotation gap, including both25px side insets.
        x=right+70
        for i,name in enumerate(('native_values','native_definition')):
            section.op(name).nodeX=x+i*200;section.op(name).nodeY=0
            section.op('click_'+name).nodeX=x+i*200;section.op('click_'+name).nodeY=-210
        for old in [o for o in section.children if o.OPType=='annotateCOMP']:old.destroy()
        groups=[annotate(section,'annotate_section','Details',existing),annotate(section,'annotate_native','Native',actions)]
        top=max(a.nodeY+a.nodeHeight for a in groups)
        for a in groups:a.nodeHeight=top-a.nodeY
        check(existing+actions,groups)
        content=section.op('container_readout/container_info');native=content.op('container_native')
        prior=[o for o in content.children if o.OPType!='annotateCOMP' and o!=native]
        native.nodeX=max(o.nodeX+175 for o in prior);native.nodeY=0
        for group in prior+[native]:
            nodes=[o for o in group.children if o.OPType!='annotateCOMP'];grid(nodes)
            for old in [o for o in group.children if o.OPType=='annotateCOMP']:old.destroy()
            a=annotate(group,'annotate_readout','Readout',nodes);check(nodes,[a])
        form=native.op('container_edit')
        if form:
            nodes=[o for o in form.children if o.OPType!='annotateCOMP'];grid(nodes)
            for old in [o for o in form.children if o.OPType=='annotateCOMP']:old.destroy()
            a=annotate(form,'annotate_edit','Definition draft',nodes);check(nodes,[a])
        for old in [o for o in content.children if o.OPType=='annotateCOMP']:old.destroy()
        a=annotate(content,'annotate_groups','Groups',prior+[native]);check(prior+[native],[a])
        results.append(dict(editor=editor.path,native_rows=8,footer_actions=5,measured_containment=True,no_overlap=True,
            section_groups=[dict(name=a.name,x=a.nodeX,y=a.nodeY,w=a.nodeWidth,h=a.nodeHeight) for a in groups]))
assert not any(o.errors(recurse=True) for o in (op('/inspector_model'),op('/inspector_below'),op('/inspector_popup')))
Path(project.folder+'/prototypes/inspector/advanced_network.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results))
