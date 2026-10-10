"""Use native anchors for editor geometry, with fixed font/icon/row sizes."""
views=(globals()['layout_views'] if 'layout_views' in globals() else [op('/inspector_below'),op('/inspector_popup')])

def anchors(o,left,right,lanchor=0,ranchor=1):
    o.par.x.expr='';o.par.w.expr='';o.par.hmode='anchors'
    o.par.leftanchor=lanchor;o.par.rightanchor=ranchor
    o.par.leftoffset=left;o.par.rightoffset=right

def top(o,inset,height):
    o.par.y.expr='';o.par.h.expr='';o.par.vmode='anchors'
    o.par.bottomanchor=o.par.topanchor=1
    o.par.bottomoffset=-inset-height;o.par.topoffset=-inset

for view in views:
    if not view:continue
    for name,inset,height in [('text_title',8,24),('text_brand',8,24),('context_Device',40,30),('context_Layout',74,28),('context_Track',74,28),('text_style',110,24),('learn',110,24),('text_status',138,18)]:top(view.op(name),inset,height)
    anchors(view.op('text_title'),12,-68)
    anchors(view.op('text_brand'),-56,-12,1,1)
    anchors(view.op('text_style'),12,-96)
    anchors(view.op('learn'),-84,-12,1,1)
    for name in ('context_Device','text_status','text_footer'):anchors(view.op(name),12,-12)
    anchors(view.op('context_Layout'),12,-3,0,.5)
    anchors(view.op('context_Track'),3,-12,.5,1)
    for name in ('Device','Layout','Track'):
        context=view.op('context_'+name)
        anchors(context.op('text_value'),58 if name=='Device' else 8,-24)
        anchors(context.op('text_cycle'),-18,-4,1,1)
    viewport=view.op('container_scroll');anchors(viewport,0,0)
    viewport.par.y.expr='';viewport.par.h.expr='';viewport.par.vmode='anchors'
    viewport.par.bottomanchor=0;viewport.par.topanchor=1;viewport.par.bottomoffset=18;viewport.par.topoffset=-156
    rows=viewport.op('container_content');anchors(rows,0,-6);top(rows,0,rows.par.h.eval())
    for row in rows.ops('slot*'):
        anchors(row,12,-12);anchors(row.op('text_name'),32,-60)
        anchors(row.op('text_value'),-58,-18,1,1);anchors(row.op('text_arrow'),-12,0,1,1)
    anchors(rows.op('editor_below'),12,-12)
    for panel in view.panelChildren+rows.panelChildren:
        panel.par.fit='off';panel.par.scalex=panel.par.scaley=1
        if panel.OPType=='textCOMP':panel.par.scaletofit='never';panel.par.fontsizeunits='panelunits'
    popup=view.op('ui').module.popup_host(view);content=popup.op('container_editor_content')
    anchors(content,0,-6)
    content.par.y.expr='';content.par.h.expr='';content.par.vmode='anchors'
    content.par.topanchor=content.par.bottomanchor=1
    content.par.topoffset=0;content.par.bottomoffset=-content.par.h.eval()
    for editor in (view.op('container_scroll/container_content/editor_below'),content):
        for o in editor.findChildren(maxDepth=3):
            if o.OPType in ('containerCOMP','textCOMP') and o.name!='annotation':
                o.par.fit='off';o.par.scalex=o.par.scaley=1;o.par.sizefromwindow=False
                if o.OPType=='textCOMP':o.par.scaletofit='never';o.par.fontsizeunits='panelunits'
        for name in ('field_Label','field_Destination','field_Value'):anchors(editor.op(name),62,-12)
        anchors(editor.op('text_heading'),12,-72)
        anchors(editor.op('text_status'),12,-12)
        anchors(editor.op('mapping_toggle'),12,-12)
        for name,right in [('ping',42),('clear',12),('cancel',42),('apply',12)]:anchors(editor.op(name),-right-24,-right,1,1)
        for name in ('field_Minimum','field_Maximum'):
            anchors(editor.op(name),62 if name=='field_Minimum' else 28,22 if name=='field_Minimum' else -12,0 if name=='field_Minimum' else .5,.5 if name=='field_Minimum' else 1)
        section=editor.op('container_mapping');anchors(section,0,0)
        for name in ('choice_mode','choice_input'):anchors(section.op(name),62,-12)
        anchors(section.op('field_minimum'),62,22,0,.5)
        anchors(section.op('field_maximum'),28,-12,.5,1)
        anchors(section.op('text_status'),12,-72)
        for name,right in [('mapping_cancel',42),('mapping_apply',12)]:anchors(section.op(name),-right-24,-right,1,1)
        for parent in [editor.op(n) for n in ('ping','clear','cancel','apply','mapping_toggle')]+[section.op(n) for n in ('choice_mode','choice_input','mapping_cancel','mapping_apply')]:
            label=parent.op('text_label');label.par.w.expr='';label.par.h.expr=''
            label.par.hmode=label.par.vmode='fill'
    print(view.path,'native editor anchors installed')
