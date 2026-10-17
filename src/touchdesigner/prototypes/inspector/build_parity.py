"""Compact filter footer and reusable Details section; no new windows."""
from pathlib import Path

try:
    from parity import DETAIL_GROUPS
except ModuleNotFoundError:
    DETAIL_GROUPS=None


def install_hardware_snapshot(editor):
    content=editor.op('container_details/container_readout/container_info')
    if content is None:raise ValueError('Existing Details content is required')
    def panel(parent,kind,name,x,y,w,h):
        node=parent.op(name)
        if node is not None and node.OPType!=kind:raise ValueError('Unexpected Hardware snapshot node type: '+name)
        node=node or parent.create(kind,name);node.viewer=True
        node.par.fit='off';node.par.x=x;node.par.y=y;node.par.w=w;node.par.h=h;node.par.bgalpha=0
        return node
    def anchors(node,left,right):
        node.par.hmode='anchors';node.par.leftanchor=0;node.par.rightanchor=1
        node.par.leftoffset=left;node.par.rightoffset=right
    def text(parent,name,value,x,y,w,h,size=10):
        node=panel(parent,'textCOMP',name,x,y,w,h);node.par.text=value;node.par.fontsize=size
        node.par.fontsizeunits='panelunits';node.par.alignx='left';node.par.aligny='top'
        node.par.type='multiline';node.par.wordwrap=True;node.par.scaletofit='never'
        node.par.fontcolorr=node.par.fontcolorg=node.par.fontcolorb=.88
        node.par.clickthrough=False;node.par.editmode='selectonly'
        return node
    group=panel(content,'containerCOMP','group3',0,0,204,100);anchors(group,0,0)
    group.nodeX=780;group.nodeY=0
    title,capacity=DETAIL_GROUPS[3]
    heading=text(group,'text_heading',title,12,82,180,18,12);anchors(heading,12,-12);heading.par.typeface='Bold'
    for i in range(capacity):
        label=text(group,'label'+str(i),'',12,0,78,18,9)
        label.par.fontcolorr=label.par.fontcolorg=label.par.fontcolorb=.58
        value=text(group,'value'+str(i),'',92,0,100,18,11);anchors(value,92,-12)
    caption=text(group,'text_endpoint','Serial endpoint (/dev/cu.…) ',12,66,180,18,9);anchors(caption,12,-12)
    field=text(group,'field_endpoint','',12,36,180,26,11);anchors(field,12,-12)
    field.par.type='string';field.par.wordwrap=False;field.par.editmode='editable'
    field.par.bgalpha=1;field.par.bgcolorr=field.par.bgcolorg=field.par.bgcolorb=.08
    field.par.textpaddingl=field.par.textpaddingr=6
    callback=field.par.callbacks.eval()
    if callback is None:
        callback=group.op('endpoint_callbacks') or group.create('textDAT','endpoint_callbacks');field.par.callbacks=callback
    callback.par.syncfile=False;callback.par.loadonstart=False;callback.par.file='';callback.par.language='python'
    callback.text=("def onTextEdit(comp):parent.InspectorDemo.HardwareEndpoint(comp.editText,comp)\n"
                   "def onTextEditEnd(comp,value,prevValue):parent.InspectorDemo.HardwareEndpoint(value,comp)\n"
                   "def onValueChange(comp,value,prevValue):pass\n")
    action=panel(group,'containerCOMP','read_hardware',12,6,180,24);anchors(action,12,-12)
    action.par.bgalpha=1;action.par.bgcolorr=action.par.bgcolorg=action.par.bgcolorb=.17
    label=text(action,'text_label','Read hardware',0,0,180,24,11)
    label.par.w.expr='parent().width';label.par.h.expr='parent().height';label.par.alignx=label.par.aligny='center';label.par.clickthrough=True
    click=group.op('click_read_hardware') or group.create('panelexecuteDAT','click_read_hardware');click.par.language='python'
    click.par.panels='read_hardware';click.par.panelvalue='lselect';click.par.offtoon=True
    click.par.ontooff=click.par.whileon=click.par.whileoff=click.par.valuechange=False
    click.text="def onOffToOn(panelValue):parent.InspectorDemo.Action('read_hardware')\n"
    return group


def build():
    directory=Path(globals().get('inspector_source_dir',Path(project.folder)/'prototypes/inspector'))
    m=globals().get('model_comp') or op('/inspector_model');commands=m.op('base_commands')
    module=commands.op('parity') or commands.create(textDAT,'parity')
    module.viewer=True;module.par.language='python'
    source=(directory/'parity.py').read_text(encoding='utf-8')
    parity_namespace={};exec(source,parity_namespace)
    globals()['DETAIL_GROUPS']=parity_namespace['DETAIL_GROUPS']
    if module.text!=source:module.text=source
    module.nodeX=175;module.nodeY=0
    helpers=dict(globals(),inspector_source_dir=directory,model_comp=m);exec((directory/'build_mapping.py').read_text(encoding='utf-8').split('for view in views:')[0],helpers)
    panel,text,button=[helpers[n] for n in ('panel','text','button')]
    def anchors(o,left,right,l=0,r=1):
        o.par.x.expr='';o.par.w.expr='';o.par.hmode='anchors';o.par.leftanchor=l;o.par.rightanchor=r;o.par.leftoffset=left;o.par.rightoffset=right
    for view in (globals()['parity_views'] if 'parity_views' in globals() else [op('/inspector_below'),op('/inspector_popup')]):
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
            for g,title in enumerate(title for title,capacity in DETAIL_GROUPS[:3]):
                group=panel(content,containerCOMP,'group'+str(g),0,0,204,100);anchors(group,0,0)
                heading=text(group,'text_heading',title,12,82,180,18,12);anchors(heading,12,-12)
                heading.par.typeface='Bold';heading.par.fontcolorr=heading.par.fontcolorg=heading.par.fontcolorb=.90
                for i in range(DETAIL_GROUPS[g][1]):
                    label=text(group,'label'+str(i),'',12,0,78,18,9)
                    label.par.fontcolorr=label.par.fontcolorg=label.par.fontcolorb=.58
                    label.par.aligny='top';label.par.type='multiline';label.par.wordwrap=True
                    value=text(group,'value'+str(i),'',92,0,100,18,11);anchors(value,92,-12)
                    value.par.fontcolorr=value.par.fontcolorg=value.par.fontcolorb=.88
                    value.par.aligny='top';value.par.type='multiline';value.par.wordwrap=True
                    value.par.clickthrough=False;value.par.editmode='selectonly'
                group.nodeX=g*260;group.nodeY=0
                for i,o in enumerate(group.children):o.nodeX=(i%5)*200;o.nodeY=-(i//5)*160+130-o.nodeHeight
            install_hardware_snapshot(editor)
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

if 'project' in globals():build()
