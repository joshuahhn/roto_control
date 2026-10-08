"""Compact filter footer and reusable Details section; no new windows."""
from pathlib import Path
directory=Path(project.folder)/'prototypes/inspector'
m=op('/inspector_model');commands=m.op('base_commands')
module=commands.op('parity') or commands.create(textDAT,'parity')
module.viewer=True;module.par.language='python'
source=(directory/'parity.py').read_text()
if module.text!=source:module.text=source
module.nodeX=175;module.nodeY=0
helpers=dict(globals());exec((directory/'build_mapping.py').read_text().split('for view in views:')[0],helpers)
panel,text,button=[helpers[n] for n in ('panel','text','button')]
def anchors(o,left,right,l=0,r=1):
    o.par.x.expr='';o.par.w.expr='';o.par.hmode='anchors';o.par.leftanchor=l;o.par.rightanchor=r;o.par.leftoffset=left;o.par.rightoffset=right
for view in globals().get('parity_views',[op('/inspector_below'),op('/inspector_popup')]):
    module=view.op('parity') or view.create(textDAT,'parity')
    module.viewer=True;module.par.language='python'
    if module.text!=source:module.text=source
    module.nodeX=1310;module.nodeY=0;module.nodeWidth=130;module.nodeHeight=90
    footer=view.op('text_footer');anchors(footer,12,-96);footer.par.clickthrough=False
    cb=view.op('click_filter') or view.create(panelexecuteDAT,'click_filter')
    cb.viewer=True;cb.par.language='python';cb.par.panels='text_footer';cb.par.panelvalue='lselect';cb.par.offtoon=True
    cb.text="def onOffToOn(panelValue):parent.InspectorDemo.Action('filter')\n"
    clear=button(view,'clear_device','Clear Device','clear_device',0,1,80,16);anchors(clear,-92,-12,1,1);clear.op('text_label').par.fontsize=8
    popup=view.op('ui').module.popup_host(view)
    for editor in (view.op('container_scroll/container_content/editor_below'),popup.op('container_editor_content')):
        info=button(editor,'details_toggle','','details_toggle',0,148,24,24);anchors(info,-96,-72,1,1)
        info.op('text_label').par.font='Material Design Icons';info.op('text_label').par.fontsize=15;info.op('text_label').par.text='\U000f02fd'
        anchors(editor.op('text_heading'),12,-102)
        section=panel(editor,containerCOMP,'container_details',0,6,210,218);anchors(section,0,0);section.par.display=False
        details=text(section,'text_details','',12,36,186,178,9);anchors(details,12,-12)
        details.par.type='multiline';details.par.wordwrap=True;details.par.aligny='top';details.par.editmode='selectonly';details.par.clickthrough=False
        details.par.mousewheel=True;details.par.pvscrollbar='auto'
        details.par.display=False  # Scalar diagnostic mirror; rendered fields have separate type hierarchy.
        viewport=panel(section,containerCOMP,'container_readout',0,36,210,178);anchors(viewport,0,0)
        viewport.par.crop='on';viewport.par.mousewheel=True;viewport.par.pvscrollbar='auto';viewport.par.scrollbarthickness=4
        wheel=viewport.op('scroll_wheel') or viewport.create(panelexecuteDAT,'scroll_wheel')
        wheel.viewer=True;wheel.par.language='python';wheel.par.panels.expr='parent()';wheel.par.panelvalue='wheel'
        wheel.par.offtoon=False;wheel.par.valuechange=True
        wheel.text="def onValueChange(panelValue,prev):parent.InspectorDemo.DetailsScrollWheel(panelValue.val)\n"
        wheel.nodeX=200;wheel.nodeY=0
        content=panel(viewport,containerCOMP,'container_info',0,0,204,380);anchors(content,0,-6)
        content.par.y.expr='parent().height-me.height'
        for g,title in enumerate(('Mapping','Hardware routing','Technical · Refresh snapshot')):
            group=panel(content,containerCOMP,'group'+str(g),0,0,204,100);anchors(group,0,0)
            heading=text(group,'text_heading',title,12,82,180,18,12);anchors(heading,12,-12)
            heading.par.typeface='Bold';heading.par.fontcolorr=heading.par.fontcolorg=heading.par.fontcolorb=.90
            for i in range((3,5,6)[g]):
                label=text(group,'label'+str(i),'',12,0,78,18,9)
                label.par.fontcolorr=label.par.fontcolorg=label.par.fontcolorb=.58
                label.par.aligny='top';label.par.type='multiline';label.par.wordwrap=True
                value=text(group,'value'+str(i),'',92,0,100,18,11);anchors(value,92,-12)
                value.par.fontcolorr=value.par.fontcolorg=value.par.fontcolorb=.88
                value.par.aligny='top';value.par.type='multiline';value.par.wordwrap=True
                value.par.clickthrough=False;value.par.editmode='selectonly'
            group.nodeX=g*260;group.nodeY=0
            for i,o in enumerate(group.children):o.nodeX=(i%5)*200;o.nodeY=-(i//5)*160+130-o.nodeHeight
        native=panel(content,containerCOMP,'container_native',0,0,204,100);anchors(native,0,0)
        native.nodeX=695;native.nodeY=0;native.nodeWidth=160;native.nodeHeight=130
        heading=text(native,'text_heading','Native parameter',12,82,180,18,12);anchors(heading,12,-12)
        heading.par.typeface='Bold';heading.par.fontcolorr=heading.par.fontcolorg=heading.par.fontcolorb=.90
        for i in range(8):
            label=text(native,'label'+str(i),'',12,0,78,18,9)
            label.par.fontcolorr=label.par.fontcolorg=label.par.fontcolorb=.58
            label.par.aligny='top';label.par.type='multiline';label.par.wordwrap=True
            value=text(native,'value'+str(i),'',92,0,100,18,11);anchors(value,92,-12)
            value.par.fontcolorr=value.par.fontcolorg=value.par.fontcolorb=.88
            value.par.aligny='top';value.par.type='multiline';value.par.wordwrap=True
            value.par.clickthrough=False;value.par.editmode='selectonly'
        for i,o in enumerate(native.children):o.nodeX=(i%5)*200;o.nodeY=-(i//5)*210+130-o.nodeHeight
        # Codepoints verified against TD's bundled MaterialDesignIconsMeta.json.
        actions=[('refresh','details_refresh','\U000f0450'),('reveal','details_reveal','\U000f01a4'),
                 ('repair','details_repair','\U000f0be0'),('native_values','native_values','\U000f066a'),
                 ('native_definition','native_definition','\U000f04f0')]
        for i,(name,action,icon) in enumerate(actions):
            b=button(section,name,'',action,0,6,24,24)
            anchors(b,-156+i*30,-132+i*30,1,1)
            label=b.op('text_label');label.par.font='Material Design Icons';label.par.fontsize=15;label.par.text=icon
            cb=section.op('click_'+name);cb.par.panelvalue='lselect rollover';cb.par.offtoon=cb.par.ontooff=True
            cb.text=("def onOffToOn(panelValue):\n"
                     "    if panelValue.name=='rollover':parent.InspectorDemo.Hint(%r,True)\n"
                     "def onOnToOff(panelValue):\n"
                     "    if panelValue.name=='rollover':parent.InspectorDemo.Hint(%r,False)\n"
                     "    elif parent().op(%r).panel.inside:parent.InspectorDemo.Action(%r)\n")%(action,action,name,action)
        for o in section.findChildren(maxDepth=5)+[info]:
            if o.OPType in ('textCOMP','containerCOMP'):
                o.par.fit='off';o.par.scalex=o.par.scaley=1
                if o.OPType=='textCOMP':o.par.scaletofit='never';o.par.fontsizeunits='panelunits'
        for i,o in enumerate(section.children):o.nodeX=(i%5)*200;o.nodeY=-(i//5)*160+130-o.nodeHeight
        for i,name in enumerate(('native_values','native_definition')):
            section.op(name).nodeX=1130+i*200;section.op(name).nodeY=0
            section.op('click_'+name).nodeX=1130+i*200;section.op('click_'+name).nodeY=-210
print('Compact filters, Details and Clear Device installed')
