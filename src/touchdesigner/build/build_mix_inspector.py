NODES={'inspection_mode':'containerCOMP','inspection_mode/text_label':'textCOMP',
       'click_inspection_mode':'panelexecuteDAT','container_mix':'containerCOMP',
       'container_mix/text_mix_document':'textCOMP','mix_scroll_wheel':'panelexecuteDAT'}


def validate(view):
    for name,kind in dict(NODES,text_title='textCOMP',text_style='textCOMP',
                          container_scroll='containerCOMP',container_context_menu='containerCOMP').items():
        current=view.op(name)
        if current is None and name not in NODES:
            raise ValueError('Existing Inspector panel is missing: '+name)
        if current is not None and current.OPType!=kind:
            raise ValueError('MIX Inspector node has wrong type: '+current.path)


def install(view):
    validate(view)
    def node(parent, kind, name):
        current=parent.op(name)
        if current is not None and current.OPType!=kind:
            raise ValueError('MIX Inspector node has wrong type: '+current.path)
        return current or parent.create(kind,name)
    def panel(parent,kind,name):
        current=node(parent,kind,name)
        current.par.fit='off';current.par.bgalpha=0
        return current
    def source(current,text):
        current.par.language='python';current.par.file=''
        current.par.syncfile=False;current.par.loadonstart=False;current.text=text
    button=panel(view,'containerCOMP','inspection_mode')
    button.par.x=12;button.par.y.expr='parent().height-32'
    button.par.w.expr='max(76,parent().width-164)';button.par.h=24
    button.par.bgalpha=1;button.par.bgcolorr=button.par.bgcolorg=button.par.bgcolorb=.12
    label=panel(button,'textCOMP','text_label')
    label.par.x=0;label.par.y=0;label.par.w.expr='parent().width';label.par.h=24
    label.par.text='Auto: PLUGIN ▾';label.par.fontsize=8;label.par.fontsizeunits='panelunits'
    label.par.alignx=label.par.aligny='center';label.par.clickthrough=True
    label.par.fontcolorr=label.par.fontcolorg=label.par.fontcolorb=.86
    click=node(view,'panelexecuteDAT','click_inspection_mode')
    click.par.panels='inspection_mode';click.par.panelvalue='lselect';click.par.offtoon=True
    source(click,"def onOffToOn(panelValue):parent.InspectorDemo.Action('inspection_mode')\n")
    document=panel(view,'containerCOMP','container_mix')
    document.par.x=0;document.par.y=0;document.par.w.expr='parent().width'
    document.par.h.expr='max(1,parent().height-40)';document.par.display=False
    document.par.crop='on';document.par.mousewheel=True
    document.par.pvscrollbar='auto';document.par.scrollbarthickness=6
    text=panel(document,'textCOMP','text_mix_document')
    text.par.x=12;text.par.y.expr='parent().height-me.height'
    text.par.w.expr='max(1,parent().width-30)';text.par.h=100
    text.par.type='multiline';text.par.wordwrap=True
    text.par.fontsize=11;text.par.fontsizeunits='panelunits'
    text.par.alignx='left';text.par.aligny='top';text.par.clickthrough=True
    text.par.text='';text.par.textpaddingl=text.par.textpaddingr=0
    text.par.fontcolorr=text.par.fontcolorg=text.par.fontcolorb=.86
    wheel=node(view,'panelexecuteDAT','mix_scroll_wheel')
    wheel.par.panels='container_mix';wheel.par.panelvalue='wheel';wheel.par.offtoon=False;wheel.par.valuechange=True
    source(wheel,"def onValueChange(panelValue,prev):parent.InspectorDemo.MixScrollWheel(panelValue.val)\n")
    view.op('text_title').par.display=False
    return document
