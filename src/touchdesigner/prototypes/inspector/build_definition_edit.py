"""Compact native Label/default draft inside the existing Details scroll area."""
from pathlib import Path
helpers=dict(globals())
exec(Path(project.folder+'/prototypes/inspector/build_mapping.py').read_text().split('for view in views:')[0],helpers)
panel,text,button=[helpers[n] for n in ('panel','text','button')]
def anchors(o,left,right,l=0,r=1):
    o.par.x.expr='';o.par.w.expr='';o.par.hmode='anchors'
    o.par.leftanchor=l;o.par.rightanchor=r;o.par.leftoffset=left;o.par.rightoffset=right
def release(button,action):
    cb=button.parent().op('click_'+button.name)
    cb.par.offtoon=False;cb.par.ontooff=True
    cb.text="def onOnToOff(panelValue):\n    if parent().op(%r).panel.inside:parent.InspectorDemo.Action(%r)\n"%(button.name,action)
for view in (op('/inspector_below'),op('/inspector_popup')):
    draft=view.op('base_draft')
    for key,name in view.op('ui').module.DEFINITION_FIELDS+view.op('ui').module.MENU_FIELDS+view.op('ui').module.STYLE_FIELDS:
        toggle=key.startswith('clamp')
        if not hasattr(draft.par,name):
            getattr(draft.customPages[0],'appendToggle' if toggle else 'appendStr')(name)
        draft.par[name]=False if toggle else ''
    popup=view.op('ui').module.popup_host(view)
    for editor in (view.op('container_scroll/container_content/editor_below'),popup.op('container_editor_content')):
        native=editor.op('container_details/container_readout/container_info/container_native')
        edit=button(native,'edit','','definition_edit',0,0,24,18);anchors(edit,-36,-12,1,1)
        edit.par.y.expr='parent().height-18'
        label=edit.op('text_label');label.par.font='Material Design Icons';label.par.fontsize=13;label.par.text='\U000f03eb'
        release(edit,'definition_edit');native.op('text_heading').par.rightoffset=-42
        form=panel(native,containerCOMP,'container_edit',0,0,204,118);anchors(form,0,0);form.par.display=False
        for name,caption,y,draft_name in [('label','Label',90,'Nativelabel'),('default','Default',62,'Nativedefault')]:
            text(form,'label_'+name,caption,12,y,44,22,9)
            field=text(form,'field_'+name,'',62,y,130,22,11);anchors(field,62,-12)
            field.par.editmode='editable';field.par.type='string';field.par.clickthrough=False
            field.par.bgalpha=1;field.par.bgcolorr=field.par.bgcolorg=field.par.bgcolorb=.08
            field.par.textpaddingl=field.par.textpaddingr=6
            field.par.text.bindExpr="parent.InspectorDemo.op('base_draft').par."+draft_name
        style_label=text(form,'label_style','Style',12,34,44,22,9)
        style=button(form,'style','Float ▾','definition_style',62,34,130,22);anchors(style,62,-12)
        style.op('text_label').par.fontsize=11;release(style,'definition_style')
        caption=text(form,'text_status','',12,6,108,24,8);anchors(caption,12,-84);caption.par.display=False
        toggle=button(form,'bounds','BOUNDS ▸','definition_bounds',12,6,108,24);anchors(toggle,12,-84)
        toggle.op('text_label').par.fontsize=9;release(toggle,'definition_bounds')
        for row,caption,y,fields in [('slider','Slider',90,(('slidermin','Nativeslidermin'),('slidermax','Nativeslidermax'))),
                                    ('limits','Limits',62,(('limitmin','Nativelimitmin'),('limitmax','Nativelimitmax')))]:
            label=text(form,'label_'+row,caption,12,y,44,22,9);label.par.display=False
            for i,(name,par_name) in enumerate(fields):
                field=text(form,'field_'+name,'',0,y,65,22,11)
                anchors(field,62 if i==0 else 28,22 if i==0 else -12,0 if i==0 else .5,.5 if i==0 else 1)
                field.par.editmode='editable';field.par.type='string';field.par.clickthrough=False;field.par.display=False
                field.par.bgalpha=1;field.par.bgcolorr=field.par.bgcolorg=field.par.bgcolorb=.08
                field.par.textpaddingl=field.par.textpaddingr=6
                field.par.text.bindExpr="parent.InspectorDemo.op('base_draft').par."+par_name
        label=text(form,'label_clamps','Clamp',12,34,44,22,9);label.par.display=False
        for i,name in enumerate(('min','max')):
            b=button(form,'clamp_'+name,'','definition_clamp_'+name,0,34,65,22)
            anchors(b,62 if i==0 else 28,22 if i==0 else -12,0 if i==0 else .5,.5 if i==0 else 1)
            b.par.display=False;b.op('text_label').par.fontsize=9;release(b,'definition_clamp_'+name)
        for i,(key,par_name) in enumerate(view.op('ui').module.MENU_FIELDS):
            label=text(form,'menu_name'+str(i),'',12,0,84,22,8);label.par.display=False
            field=text(form,'menu_label'+str(i),'',100,0,92,22,11);anchors(field,100,-12)
            field.par.editmode='editable';field.par.type='string';field.par.clickthrough=False;field.par.display=False
            field.par.bgalpha=1;field.par.bgcolorr=field.par.bgcolorg=field.par.bgcolorb=.08
            field.par.textpaddingl=field.par.textpaddingr=6
            field.par.text.bindExpr="parent.InspectorDemo.op('base_draft').par."+par_name
        for name,action,icon,left in [('definition_cancel','definition_cancel','cancel',-66),('definition_apply','definition_apply','apply',-36)]:
            b=button(form,name,'',action,0,6,24,24);anchors(b,left,left+24,1,1)
            view.op('ui').module.action_icon(b.op('text_label'),icon);release(b,action)
        for host in (native,form):
            for i,o in enumerate(c for c in host.children if c.OPType!='annotateCOMP'):
                o.nodeX=(i%5)*200;o.nodeY=-(i//5)*210+130-o.nodeHeight
        for o in form.findChildren(maxDepth=2)+[edit]:
            if o.OPType in ('containerCOMP','textCOMP'):
                o.par.fit='off';o.par.scalex=o.par.scaley=1
                if o.OPType=='textCOMP':o.par.scaletofit='never';o.par.fontsizeunits='panelunits'
print('Four inline native definition drafts installed; no new windows')

for view in (op('/inspector_below'),op('/inspector_popup')):
    draft=view.op('base_draft')
    watch=draft.op('native_draft_changed') or draft.create(parameterexecuteDAT,'native_draft_changed')
    watch.viewer=True;watch.par.op.expr="parent.InspectorDemo.op('base_draft')"
    watch.par.pars=' '.join(name for key,name in view.op('ui').module.DEFINITION_FIELDS+view.op('ui').module.STYLE_FIELDS)
    watch.par.custom=True;watch.par.builtin=False;watch.par.valuechange=True
    watch.text="def onValueChange(par,prev):\n    parent.InspectorDemo.OnDefinitionDraftChange()\n"
    watch.nodeX=0;watch.nodeY=0
