"""Add compact context activation in the existing Inspector footer."""
from pathlib import Path
helpers=dict(globals())
exec(Path(project.folder+'/prototypes/inspector/build_mapping.py').read_text().split('for view in views:')[0],helpers)
for view in globals().get('activation_views',[op('/inspector_below'),op('/inspector_popup')]):
    button=helpers['button'](view,'activate_device','Activate','activate_device',0,1,80,16)
    button.par.hmode='anchors';button.par.leftanchor=button.par.rightanchor=1
    button.par.leftoffset=-92;button.par.rightoffset=-12
    button.par.display=False;button.par.enable=False
    button.op('text_label').par.fontsize=8
    button.nodeX=400;button.nodeY=-800;button.nodeWidth=160;button.nodeHeight=130
    callback=view.op('click_activate_device');callback.nodeX=1835;callback.nodeY=-420
    callback.par.panelvalue='lselect rollover';callback.par.offtoon=callback.par.ontooff=True
    callback.text="def onOffToOn(panelValue):\n    if panelValue.name=='rollover':parent.InspectorDemo.ActivationHint(True)\ndef onOnToOff(panelValue):\n    if panelValue.name=='rollover':parent.InspectorDemo.ActivationHint(False)\n    elif parent().op('activate_device').panel.inside:parent.InspectorDemo.Action('activate_device')\n"
    annotation=view.op('annotate_events')
    if annotation:annotation.nodeY=-445;annotation.nodeHeight=385
