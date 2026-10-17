"""Empirical bounds check for collection groups; run in TD."""
def verify(parent_comp):
    comp=parent_comp.op('roto_python')
    base=comp.op('base_targets')
    groups=[(comp,'Collection',['base_targets','collection_protocol','controls']),
            (comp,'Control output',['select_controls','null_controls','out_controls']),
            (base,'Saved targets and runtime',['targets','state']),
            (base,'Parameter watchers',[f'watch_{kind}{i}' for kind in ('knob','button') for i in range(1,9)]),
            (base,'Button / mapping RX',['rx_events']),
            (base,'Target unit output',['controls_values','null_controls','out_controls']),
            (parent_comp,'8 knobs / 8 buttons',['base_controls_demo']),
            (parent_comp.op('base_controls_demo'),'Pulse actions',['pulse_callbacks','pulse_events'])]
    checked=0
    for parent,title,names in groups:
        boxes=[n for n in parent.children if n.type=='annotate' and n.par.Titletext.eval()==title]
        assert len(boxes)==1,(title,len(boxes))
        a=boxes[0]
        for name in names:
            n=parent.op(name)
            assert n.nodeX>=a.nodeX+20 and n.nodeY>=a.nodeY+20,(title,name,'lower edge')
            assert n.nodeX+n.nodeWidth<=a.nodeX+a.nodeWidth-20,(title,name,'right edge')
            assert n.nodeY+n.nodeHeight<=a.nodeY+a.nodeHeight-20,(title,name,'upper edge')
            checked+=1
    for parent in (comp,base):
        boxes=[n for n in parent.children if n.type=='annotate']
        for i,a in enumerate(boxes):
            for b in boxes[i+1:]:
                assert (a.nodeX+a.nodeWidth+20<=b.nodeX or b.nodeX+b.nodeWidth+20<=a.nodeX or
                        a.nodeY+a.nodeHeight+20<=b.nodeY or b.nodeY+b.nodeHeight+20<=a.nodeY), (a.path,b.path,'overlap')
    return dict(groups=len(groups),operators=checked,padding=20)
