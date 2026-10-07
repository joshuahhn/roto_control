"""Install the shared command module before initializing the live model."""
from pathlib import Path
model=op('/inspector_model');assert model
component=model.op('base_commands') or model.create(baseCOMP,'base_commands')
component.viewer=component.display=True;component.par.parentshortcut='InspectorCommands'
component.nodeX=875;component.nodeY=-40;component.nodeWidth=160;component.nodeHeight=130
if not hasattr(component.par,'Model'):component.appendCustomPage('Data').appendOP('Model')
component.par.Model.expr='parent.InspectorModel'
module=component.op('InspectorCommands') or component.create(textDAT,'InspectorCommands')
module.viewer=True;module.par.language='python'
source=Path(project.folder+'/prototypes/inspector/commands.py').read_text();changed=module.text!=source
if changed:module.text=source
module.nodeX=0;module.nodeY=0;module.nodeWidth=130;module.nodeHeight=90
component.par.ext0object="op('./InspectorCommands').module.InspectorCommands(me)"
component.par.ext0promote=True;component.par.initextonstart=True
if changed or component.extensions[0] is None:component.initializeExtensions(0)

for parent,name,title,x,y,w,h,body in [(model,'annotate_commands','Commands',850,-65,210,215,'Shared capabilities and guarded controller commands'),(component,'annotate_commands','Commands',-25,-25,180,175,'Embedded command module; no frame polling')]:
    annotation=parent.op(name) or parent.create(annotateCOMP,name)
    annotation.name=name
    annotation.viewer=True;annotation.par.Mode='annotate';annotation.par.Titletext=title;annotation.par.Bodytext=body
    annotation.nodeX=x;annotation.nodeY=y;annotation.nodeWidth=w;annotation.nodeHeight=h
    annotation.color=(.28,.28,.28)
