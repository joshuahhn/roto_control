"""Move existing Details actions to bottom-right without rebuilding editors."""
names=('refresh','reveal','repair','native_values','native_definition')
for view in (op('/inspector_below'),op('/inspector_popup')):
    popup=view.op('ui').module.popup_host(view)
    for editor in (view.op('container_scroll/container_content/editor_below'),popup.op('container_editor_content')):
        section=editor.op('container_details')
        for i,name in enumerate(names):
            b=section.op(name)
            b.par.x.expr='';b.par.w.expr=''
            b.par.hmode='anchors';b.par.leftanchor=b.par.rightanchor=1
            b.par.leftoffset=-156+i*30;b.par.rightoffset=-132+i*30
            assert b.par.h.eval()==24 and b.par.y.eval()==6
        assert section.op(names[-1]).par.rightoffset.eval()==-12
print('Four Details footers right-aligned; five 24px icons, 6px gaps, 12px right inset')
