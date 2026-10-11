"""Collection layout, independent of connection and extension registration."""
def layout(parent_comp):
    comp = parent_comp.op('roto_python')
    base = comp.op('base_targets')
    boxes = [(comp,'Collection',1130,-325,355,480),
             (comp,'Control output',-25,-625,530,175),
             (base,'Saved targets and runtime',-25,-235,300,475),
             (base,'Parameter watchers',325,-565,705,805),
             (base,'Button / mapping RX',1075,65,355,230),
             (base,'COMP tags',1075,-235,355,175),
             (base,'Target unit output',-25,-865,530,175),
             (parent_comp,'8 knobs / 8 buttons',575,-25,260,215),
             (parent_comp.op('base_controls_demo'),'Pulse actions',-25,-25,420,175)]
    for parent,label,x,y,width,height in boxes:
        matches = [n for n in parent.ops('*', includeUtility=True) if n.type == 'annotate' and n.par.Titletext.eval()==label]
        node = matches[0] if matches else parent.create(annotateCOMP)
        for duplicate in matches[1:]:
            duplicate.destroy()
        node.utility = False
        node.par.Mode='networkbox'
        node.par.Titletext=label
        node.nodeX,node.nodeY,node.nodeWidth,node.nodeHeight=x,y,width,height
