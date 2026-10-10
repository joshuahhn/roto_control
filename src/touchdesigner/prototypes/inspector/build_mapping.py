"""Install one reusable Mapping section per editor; preserve manual base size."""
from pathlib import Path
inspector_source_dir=Path(globals().get('inspector_source_dir',Path(project.folder)/'prototypes/inspector'))
views=(globals()['action_views'] if 'action_views' in globals() else [op('/inspector_below'),op('/inspector_popup')])

def panel(parent,typ,name,x,y,w,h):
    o=parent.op(name) or parent.create(typ,name);o.name=name;o.viewer=True
    o.par.fit='off';o.par.x=x;o.par.y=y;o.par.w=w;o.par.h=h;o.par.bgalpha=0
    for edge in ('leftborder','rightborder','topborder','bottomborder','leftborderi','rightborderi','topborderi','bottomborderi'):o.par[edge]='off'
    return o

def text(parent,name,value,x,y,w,h,size=10):
    o=panel(parent,textCOMP,name,x,y,w,h)
    o.par.text=value;o.par.fontsize=size;o.par.fontsizeunits='panelunits'
    o.par.fontcolorr=o.par.fontcolorg=o.par.fontcolorb=.76
    o.par.alignx='left';o.par.aligny='center';o.par.textpaddingl=o.par.textpaddingr=0;o.par.clickthrough=True
    return o

def button(parent,name,label,action,x,y,w,h):
    o=panel(parent,containerCOMP,name,x,y,w,h);o.par.bgalpha=1
    o.par.bgcolorr=o.par.bgcolorg=o.par.bgcolorb=.17
    t=text(o,'text_label',label,0,0,w,h);t.par.w.expr='parent().width';t.par.h.expr='parent().height';t.par.alignx='center'
    cb=parent.op('click_'+name) or parent.create(panelexecuteDAT,'click_'+name)
    cb.viewer=True;cb.par.language='python';cb.par.panels=name;cb.par.panelvalue='lselect';cb.par.offtoon=True
    cb.par.ontooff=cb.par.whileon=cb.par.whileoff=cb.par.valuechange=False
    cb.text="def onOffToOn(panelValue):\n    parent.InspectorDemo.Action(%r)\n"%action
    return o

for view in views:
    if not view:continue
    module=view.op('editor_state') or view.create(textDAT,'editor_state')
    module.viewer=True;module.par.language='python';module.text=Path(inspector_source_dir/'editor_state.py').read_text()
    module.nodeX=1135;module.nodeY=0;module.nodeWidth=130;module.nodeHeight=90
    draft=view.op('base_draft');page=draft.customPages[0]
    for name in ('Mapminimum','Mapmaximum'):
        if not hasattr(draft.par,name):page.appendFloat(name)
    for name in ('Mapmode','Mapinput'):
        if not hasattr(draft.par,name):page.appendStr(name)
    popup=view.op('ui').module.popup_host(view);content=popup.op('container_editor_content')
    if not content:
        # Copy native panel nodes and their existing callbacks together; all field
        # bindings/actions already use the view's depth-independent shortcut.
        old=list(popup.children)
        content=popup.create(containerCOMP,'container_editor_content');content.viewer=True
        for child in old:
            # Text COMP copy carries its docked callback DAT automatically.
            if child.OPType!='textDAT':content.copy(child,name=child.name)
        for child in old:
            if child.valid:child.destroy()
    # Also finish an interrupted migration whose docked callbacks were removed
    # with their owner before the old-child deletion loop completed.
    for child in list(popup.children):
        if child.valid and child.name not in ('container_editor_content','scroll_wheel'):child.destroy()
    callbacks={o.par.callbacks.eval() for o in content.children if o.OPType=='textCOMP'}
    for child in list(content.children):
        if child.OPType=='textDAT' and '_callbacks' in child.name and child not in callbacks:child.destroy()
    popup.par.crop='on';popup.par.mousewheel=True;popup.par.pvscrollbar='auto';popup.par.scrollbarthickness=6
    # A fixed-size Window operator constrains native resizing to its aspect.
    # Let the viewport itself follow its floating window, on both axes.
    popup.par.sizefromwindow=True;popup.par.fixedaspect='off'
    popup.par.w.expr='';popup.par.h.expr=''
    popup.par.w=view.op('window_editor').par.winw.eval();popup.par.h=view.op('window_editor').par.winh.eval()
    content.par.fit='off';content.par.bgalpha=0;content.par.x=0;content.par.w.expr='parent().width-6'
    content.par.y.expr='parent().height-me.height';content.par.h=178
    content.nodeX=0;content.nodeY=0;content.nodeWidth=160;content.nodeHeight=130
    wheel=popup.op('scroll_wheel') or popup.create(panelexecuteDAT,'scroll_wheel')
    wheel.viewer=True;wheel.par.language='python';wheel.par.panels='';wheel.par.panels.expr='parent()'
    wheel.par.panelvalue='wheel';wheel.par.offtoon=False;wheel.par.valuechange=True
    wheel.text="def onValueChange(panelValue,prev):\n    parent.InspectorDemo.PopupScrollWheel(panelValue.val)\n"
    wheel.nodeX=200;wheel.nodeY=0
    for editor in (view.op('container_scroll/container_content/editor_below'),content):
        field=editor.op('field_Value');callback=field.par.callbacks.eval()
        callback.par.language='python';callback.text=Path(inspector_source_dir/'value_callbacks.py').read_text()
        for name in ('cancel','apply'):editor.op(name).par.display=False
        editor.op('text_status').par.w.expr='max(1,parent().width-24)'
        toggle=button(editor,'mapping_toggle','MAPPING  ▸','mapping_toggle',12,64,186,22)
        toggle.par.w.expr='parent().width-24';toggle.op('text_label').par.alignx='left';toggle.op('text_label').par.textpaddingl=6
        section=panel(editor,containerCOMP,'container_mapping',0,6,210,128);section.par.w.expr='parent().width';section.par.display=False
        text(section,'label_range','Range',12,94,44,22)
        for i,name in enumerate(('minimum','maximum')):
            f=text(section,'field_'+name,'',62,94,65,22,11)
            f.par.clickthrough=False;f.par.editmode='editable';f.par.type='float';f.par.bgalpha=1
            f.par.bgcolorr=f.par.bgcolorg=f.par.bgcolorb=.08;f.par.textpaddingl=f.par.textpaddingr=6
            f.par.w.expr='(parent().width-80)/2';f.par.x.expr='62+%d*(me.width+6)'%i
            f.par.text.bindExpr="parent.InspectorDemo.op('base_draft').par.Map%s"%name
        for name,caption,y in [('mode','Mode',66),('input','HW Type',38)]:
            text(section,'label_'+name,caption,12,y,44,22)
            b=button(section,'choice_'+name,'','mapping_'+name,62,y,136,22);b.par.w.expr='parent().width-74'
            b.op('text_label').par.text.expr="(parent.InspectorDemo.op('base_draft').par.Map%s.eval().upper() or '—') + (' ▾' if parent().par.enable.eval() else '')"%name
        status=text(section,'text_status','',12,6,132,24,9);status.par.w.expr='max(1,parent().width-84)';status.par.type='multiline';status.par.wordwrap=True
        for name,label,x in [('mapping_cancel','×',66),('mapping_apply','✓',36)]:
            b=button(section,name,label,name,0,6,24,24);b.par.x.expr='parent().width-%d'%x
            view.op('ui').module.action_icon(b.op('text_label'),'cancel' if name=='mapping_cancel' else 'apply')
        # Existing controls keep their established grid; new grouping lives beside it.
        toggle.nodeX=1335;toggle.nodeY=-40;toggle.nodeWidth=160;toggle.nodeHeight=130
        editor.op('click_mapping_toggle').nodeX=1510;editor.op('click_mapping_toggle').nodeY=0
        section.nodeX=1135;section.nodeY=-40;section.nodeWidth=160;section.nodeHeight=130
        for i,child in enumerate(section.children):child.nodeX=(i%5)*200;child.nodeY=-(i//5)*160
    for name in ('Layout','Track','Device'):view.op('context_'+name+'/text_cycle').par.text='▾'
    view.op('context_Device').par.y.expr='parent().height-40-me.height'
    for name in ('Layout','Track'):view.op('context_'+name).par.y.expr='parent().height-74-me.height'
exec(Path(inspector_source_dir/'native_editor_layout.py').read_text(),dict(globals(),layout_views=views))
print('Mapping sections installed; native window dimensions retained')

# Header dropdown callbacks: release mouse capture before transferring focus.
header_scope={}
exec(Path(inspector_source_dir/'context_callbacks.py').read_text(),header_scope)
for view in views:
    if not view:continue
    for name in ('Device','Layout','Track'):
        cb=view.op('click_context_'+name)
        cb.par.offtoon=False;cb.par.ontooff=True
        cb.par.whileon=cb.par.whileoff=cb.par.valuechange=False
        cb.par.language='python'
        cb.text=header_scope['header_callback_source'](name)
