"""Eight reusable dropdown rows inside each existing Inspector window."""
from pathlib import Path
source_dir=Path(project.folder)/'prototypes/inspector'
helpers=dict(globals())
exec((source_dir/'build_mapping.py').read_text().split('for view in views:')[0],helpers)
panel=helpers['panel']
def text(*args,**kwargs):
    label=helpers['text'](*args,**kwargs)
    callback=label.par.callbacks.eval();label.par.callbacks=''
    if callback and callback.parent()==label.parent() and callback.name==label.name+'_callbacks':callback.destroy()
    return label
header={};exec((source_dir/'context_callbacks.py').read_text(),header)
views=globals().get('context_views',[op('/inspector_below'),op('/inspector_popup')])

def click(parent,name,target,action):
    cb=parent.op(name) or parent.create(panelexecuteDAT,name)
    cb.viewer=True;cb.par.language='python';cb.par.panels=target;cb.par.panelvalue='lselect'
    cb.par.offtoon=True;cb.par.ontooff=cb.par.whileon=cb.par.whileoff=cb.par.valuechange=False
    cb.text='def onOffToOn(panelValue):\n    parent.InspectorDemo.%s\n'%action
    return cb

for view in views:
    if not view:continue
    old=view.ext.InspectorView if view.extensions[0] is not None else None
    saved=(old.Key(),old._follow_routing) if old else None
    if old and globals().get('reload_context_views',True):old.Disconnect()
    module=view.op('context_menu') or view.create(textDAT,'context_menu')
    module.viewer=True;module.par.language='python'
    if module.text!=(source_dir/'context_menu.py').read_text():module.text=(source_dir/'context_menu.py').read_text()
    module.nodeX=2270;module.nodeY=0
    dropdown=panel(view,containerCOMP,'container_context_menu',12,120,216,52)
    dropdown.par.w.expr='max(1,parent().width-24)';dropdown.par.display=False
    dropdown.par.layer=100;dropdown.par.crop='on';dropdown.par.mousewheel=True
    dropdown.par.bgalpha=1;dropdown.par.bgcolorr=dropdown.par.bgcolorg=dropdown.par.bgcolorb=.15
    dropdown.nodeX=2095;dropdown.nodeY=-40;dropdown.nodeWidth=160;dropdown.nodeHeight=130
    for i in range(8):
        row=panel(dropdown,containerCOMP,'row'+str(i),2,0,212,24)
        row.par.w.expr='max(1,parent().width-4)';row.par.display=False;row.par.bgalpha=1
        row.par.bgcolorr=row.par.bgcolorg=row.par.bgcolorb=.12
        row.par.bgcolorr.expr='.19 if me.panel.rollover else .12'
        row.par.bgcolorg.expr=row.par.bgcolorb.expr='me.par.bgcolorr'
        row.nodeX=0;row.nodeY=-i*160-40;row.nodeWidth=160;row.nodeHeight=130
        label=text(row,'text_label','',24,0,184,24,11);label.par.w.expr='max(1,parent().width-28)'
        check=text(row,'text_check','',2,0,20,24,15)
        view.op('ui').module.action_icon(check,'apply');check.par.display=False
        label.nodeX=0;label.nodeY=0;check.nodeX=175;check.nodeY=0
        cb=click(dropdown,'click_row'+str(i),'row'+str(i),'SelectContextItem(%d)'%i)
        cb.nodeX=175;cb.nodeY=-i*160
    footer=panel(dropdown,containerCOMP,'base_footer',2,2,212,24)
    footer.par.w.expr='max(1,parent().width-4)';footer.par.display=False
    footer.nodeX=350;footer.nodeY=-40;footer.nodeWidth=160;footer.nodeHeight=130
    count=text(footer,'text_count','',4,0,140,24,9);count.par.w.expr='max(1,parent().width-56)'
    count.nodeX=0;count.nodeY=0
    for name,icon,offset,direction in [('previous','\U000f0143',48,-1),('next','\U000f0140',24,1)]:
        button=panel(footer,containerCOMP,name,0,0,24,24);button.par.x.expr='parent().width-%d'%offset
        label=text(button,'text_label',icon,0,0,24,24,15);label.par.font='Material Design Icons';label.par.alignx='center'
        cb=click(footer,'click_'+name,name,'PageContextMenu(%d)'%direction)
        button.nodeX=175 if direction<0 else 350;button.nodeY=-40;button.nodeWidth=160;button.nodeHeight=130
        cb.nodeX=175 if direction<0 else 350;cb.nodeY=-165
    wheel=dropdown.op('scroll_wheel') or dropdown.create(panelexecuteDAT,'scroll_wheel')
    wheel.viewer=True;wheel.par.language='python';wheel.par.panels.expr='parent()';wheel.par.panelvalue='wheel'
    wheel.par.offtoon=False;wheel.par.valuechange=True
    wheel.text='def onValueChange(panelValue,prev):\n    parent.InspectorDemo.ScrollContextMenu(panelValue.val)\n'
    wheel.nodeX=350;wheel.nodeY=-165
    keyboard=dropdown.op('keyboard_escape') or dropdown.create(keyboardinDAT,'keyboard_escape')
    keyboard.viewer=True;keyboard.par.active=False
    keyboard.par.keys='esc escape';keyboard.par.maxlines=2
    keyboard.par.active.expr='parent().par.display and parent.InspectorDemo.MenuFocus()'
    cb=keyboard.par.callbacks.eval() or dropdown.create(textDAT,'keyboard_escape_callbacks')
    cb.viewer=True;cb.par.language='python';keyboard.par.callbacks=cb
    cb.text="def onKey(dat,key,character,alt,lAlt,rAlt,ctrl,lCtrl,rCtrl,shift,lShift,rShift,state,time):\n    if state and (key.lower() in ('esc','escape') or character=='\\x1b'):\n        parent.InspectorDemo.ContextMenuEscape()\n"
    keyboard.nodeX=525;keyboard.nodeY=0;cb.nodeX=525;cb.nodeY=-165
    outside=click(view,'context_outside_click','', 'ContextMenuOutsideClick(parent())')
    outside.par.panels.expr='parent()';outside.nodeX=2095;outside.nodeY=-210
    focus=view.op('context_focus') or view.create(panelexecuteDAT,'context_focus')
    focus.viewer=True;focus.par.language='python';focus.par.panels.expr='parent()';focus.par.panelvalue='focusselect'
    focus.par.offtoon=False;focus.par.valuechange=True
    focus.text='def onValueChange(panelValue,prev):\n    if not panelValue.val:parent.InspectorDemo.ContextMenuFocusLost(parent())\n'
    focus.nodeX=2270;focus.nodeY=-210
    for name in ('Device','Layout','Track'):
        cb=view.op('click_context_'+name);cb.par.offtoon=False;cb.par.ontooff=True
        cb.par.whileon=cb.par.whileoff=cb.par.valuechange=False
        cb.par.language='python';cb.text=header['header_callback_source'](name)
    popup=view.op('ui').module.popup_host(view)
    editors=(view.op('container_scroll/container_content/editor_below'),popup.op('container_editor_content') or popup)
    for editor in editors:
        old_pool=editor.op('container_context_menu')
        if old_pool:old_pool.destroy()
        pool=editor.copy(dropdown,name='container_context_menu')
        pool.nodeX=2470;pool.nodeY=-40;pool.par.y.expr='';pool.par.y=0
        for parent_widget,name,action in [(editor,'value_menu','value_menu'),(editor.op('container_mapping'),'choice_mode','mapping_mode'),(editor.op('container_mapping'),'choice_input','mapping_input')]:
            cb=parent_widget.op('click_'+name)
            cb.par.offtoon=False;cb.par.ontooff=True
            cb.par.whileon=cb.par.whileoff=cb.par.valuechange=False
            cb.text='def onOnToOff(panelValue):\n    if parent().op(%r).panel.inside:\n        parent.InspectorDemo.Action(%r)\n'%(name,action)
    outside=click(popup,'context_outside_click','','ContextMenuOutsideClick(parent())')
    outside.par.panels.expr='parent()';outside.nodeX=2645;outside.nodeY=0
    focus=popup.op('context_focus') or popup.create(panelexecuteDAT,'context_focus')
    focus.viewer=True;focus.par.language='python';focus.par.panels.expr='parent()';focus.par.panelvalue='focusselect'
    focus.par.offtoon=focus.par.ontooff=focus.par.whileon=focus.par.whileoff=False;focus.par.valuechange=True
    focus.text='def onValueChange(panelValue,prev):\n    if not panelValue.val:parent.InspectorDemo.ContextMenuFocusLost(parent())\n'
    focus.nodeX=2820;focus.nodeY=0
    if globals().get('reload_context_views',True):
        view.op('ui').text=(source_dir/'ui.py').read_text()
        view.initializeExtensions(0)
        if saved and not saved[1]:
            view.ext.InspectorView.ConfigureMenus(saved[0]);view.ext.InspectorView.OnContext();view.ext.InspectorView._follow_routing=False
        view.CloseEditor();view.op('window_editor').par.winclose.pulse()
print('In-window dropdowns installed; fixed eight-row pools, no menu Window')
