"""Install compact actions in existing editors; never rebuild or open windows."""
action_views=(globals()['action_views'] if 'action_views' in globals() else [op('/inspector_below'),op('/inspector_popup')])
for view in action_views:
    if not view:continue
    popup=view.op('ui').module.popup_host(view)
    for editor in (view.op('container_scroll/container_content/editor_below'),popup.op('container_editor_content') or popup):
        if not editor:continue
        editor.par.h=178
        editor.op('text_heading').par.y=151
        editor.op('text_empty').par.y=64
        for label,field,y in [('label_Label','field_Label',120),('label_Destination','field_Destination',92),('label_Range','field_Minimum',64),('label_Value','field_Value',36)]:
            editor.op(label).par.y=editor.op(field).par.y=y
            editor.op(label).par.w=44
        editor.op('field_Maximum').par.y=64
        for index,name in enumerate(('ping','clear','cancel','apply')):
            button=editor.op(name)
            if not button:
                button=editor.create(containerCOMP,name);button.viewer=True
                button.par.fit='off';button.par.bgalpha=1
                for edge in ('leftborder','rightborder','topborder','bottomborder','leftborderi','rightborderi','topborderi','bottomborderi'):button.par[edge]='off'
                button.par.bgcolorr=button.par.bgcolorg=button.par.bgcolorb=.17
                label=button.create(textCOMP,'text_label');label.viewer=True
                label.par.fit='off';label.par.bgalpha=0;label.par.clickthrough=True
                label.par.x=label.par.y=0;label.par.h=22;label.par.w.expr='parent().width'
                label.par.alignx='center';label.par.aligny='center'
                label.par.fontsizeunits='panelunits';label.par.textpaddingl=label.par.textpaddingr=0
                label.par.fontcolorr=label.par.fontcolorg=label.par.fontcolorb=.86
                label.nodeX=0;label.nodeY=0
            button.par.h=24;button.par.w=24
            button.par.y=148 if name in ('ping','clear') else 6
            button.par.x.expr='parent().width-%d'%(66 if name in ('ping','cancel') else 36)
            button.op('text_label').par.h.expr='parent().height'
            view.op('ui').module.action_icon(button.op('text_label'),name)
            callback=editor.op('click_'+name) or editor.create(panelexecuteDAT,'click_'+name)
            callback.viewer=True;callback.par.language='python'
            callback.par.panels=name;callback.par.panelvalue='lselect rollover';callback.par.offtoon=True;callback.par.ontooff=True
            callback.par.whileon=False;callback.par.whileoff=False;callback.par.valuechange=False
            callback.text=("def onOffToOn(panelValue):\n"
                           "    if panelValue is not None and panelValue.name=='rollover':\n"
                           "        parent.InspectorDemo.Hint(%r,True)\n"
                           "    else:parent.InspectorDemo.Action(%r)\n"
                           "def onOnToOff(panelValue):\n"
                           "    if panelValue.name=='rollover':parent.InspectorDemo.Hint(%r,False)\n")%(name,name,name)
        status=editor.op('text_status');status.par.y=6;status.par.h=24;status.par.w.expr='max(1,parent().width-84)'
        status.par.type='multiline';status.par.wordwrap=True
        editor.op('text_heading').par.w.expr='max(1,parent().width-84)'
        # Retain the existing five-column network convention, with clear gaps.
        for index,child in enumerate(editor.children):child.nodeX=(index%5)*200;child.nodeY=-(index//5)*160
