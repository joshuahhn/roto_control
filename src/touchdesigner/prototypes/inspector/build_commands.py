"""Install the shared command module before initializing the live model."""
from pathlib import Path
model=op('/inspector_model');assert model
component=model.op('base_commands') or model.create(baseCOMP,'base_commands')
component.viewer=component.display=True;component.par.parentshortcut='InspectorCommands'
component.nodeX=875;component.nodeY=-40;component.nodeWidth=160;component.nodeHeight=130
if not hasattr(component.par,'Model'):component.appendCustomPage('Data').appendOP('Model')
component.par.Model.expr='parent.InspectorModel'
helper=component.op('parity') or component.create(textDAT,'parity')
helper.viewer=True;helper.par.language='python';helper_source=Path(project.folder+'/prototypes/inspector/parity.py').read_text()
if helper.text!=helper_source:helper.text=helper_source
helper.nodeX=175;helper.nodeY=0;helper.nodeWidth=130;helper.nodeHeight=90
definition=component.op('parameter_definition') or component.create(textDAT,'parameter_definition')
definition.viewer=True;definition.par.language='python'
definition_source=Path(project.folder+'/prototypes/inspector/parameter_definition.py').read_text()
if definition.text!=definition_source:definition.text=definition_source
definition.nodeX=350;definition.nodeY=0;definition.nodeWidth=130;definition.nodeHeight=90
edit=component.op('definition_edit') or component.create(textDAT,'definition_edit')
edit.viewer=True;edit.par.language='python'
edit_source=Path(project.folder+'/prototypes/inspector/definition_edit.py').read_text()
if edit.text!=edit_source:edit.text=edit_source
edit.nodeX=525;edit.nodeY=0;edit.nodeWidth=130;edit.nodeHeight=90
style=component.op('style_migration') or component.create(textDAT,'style_migration')
style.viewer=True;style.par.language='python'
style_source=Path(project.folder+'/prototypes/inspector/style_migration.py').read_text()
if style.text!=style_source:style.text=style_source
style.nodeX=700;style.nodeY=0;style.nodeWidth=130;style.nodeHeight=90
module=component.op('InspectorCommands') or component.create(textDAT,'InspectorCommands')
module.viewer=True;module.par.language='python'
source=Path(project.folder+'/prototypes/inspector/commands.py').read_text();changed=module.text!=source
if changed:module.text=source
module.nodeX=0;module.nodeY=0;module.nodeWidth=130;module.nodeHeight=90
component.par.ext0object="op('./InspectorCommands').module.InspectorCommands(me)"
component.par.ext0promote=True;component.par.initextonstart=True
if changed or component.extensions[0] is None:component.initializeExtensions(0)

for parent,name,title,x,y,w,h,body in [(model,'annotate_commands','Commands',850,-65,210,215,'Shared capabilities and guarded controller commands'),(component,'annotate_commands','Commands',-25,-25,880,175,'Embedded command modules; on-demand native definitions')]:
    annotation=parent.op(name) or parent.create(annotateCOMP,name)
    annotation.name=name
    annotation.viewer=True;annotation.par.Mode='annotate';annotation.par.Titletext=title;annotation.par.Bodytext=body
    annotation.nodeX=x;annotation.nodeY=y;annotation.nodeWidth=w;annotation.nodeHeight=h
    annotation.color=(.28,.28,.28)
