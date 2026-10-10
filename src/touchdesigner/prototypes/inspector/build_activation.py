"""Add compact context activation in the existing Inspector footer."""
from pathlib import Path
inspector_source_dir=Path(globals().get('inspector_source_dir',Path(project.folder)/'prototypes/inspector'))
helpers=dict(globals())
exec(Path(inspector_source_dir/'build_mapping.py').read_text().split('for view in views:')[0],helpers)
for view in (globals()['activation_views'] if 'activation_views' in globals() else [op('/inspector_below'),op('/inspector_popup')]):
    follow=helpers['button'](view,'follow_comp','Follow COMP: —','follow_comp',0,0,88,24)
    follow.par.hmode='anchors';follow.par.leftanchor=follow.par.rightanchor=1
    follow.par.leftoffset=-150;follow.par.rightoffset=-62
    follow.par.y.expr='parent().height-8-me.height'
    follow.par.enable=False;follow.op('text_label').par.fontsize=8
    follow.nodeX=575;follow.nodeY=-800
    view.op('text_title').par.w.expr='parent().width-164'
    click=view.op('click_follow_comp');click.nodeX=2010;click.nodeY=-420
    click.par.panelvalue='lselect rollover';click.par.offtoon=click.par.ontooff=True
    click.text="def onOffToOn(panelValue):\n    if panelValue.name=='rollover':parent.InspectorDemo.FollowCompHint(True)\ndef onOnToOff(panelValue):\n    if panelValue.name=='rollover':parent.InspectorDemo.FollowCompHint(False)\n    elif parent().op('follow_comp').panel.inside:parent.InspectorDemo.Action('follow_comp')\n"
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
