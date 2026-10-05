"""Saved mixed parameter setup for the user's pixelSortV3 and fractal_pop COMPs.

Run install(controller) in TD while disconnected. It validates before replacing
saved configuration, and deliberately leaves physical LEARN to the user.
"""
TARGETS = (
    ('knob',1,'pixelsort.low','pixelSortV3','Lowthresh','value','Low Threshold',''),
    ('knob',2,'pixelsort.high','pixelSortV3','Highthresh','value','High Threshold',''),
    ('knob',3,'pixelsort.chunk','pixelSortV3','Spanpercent','value','Max Chunk',''),
    ('knob',4,'pixelsort.mix','pixelSortV3','Mix','value','Effect Mix',''),
    ('knob',5,'fractal.power','fractal_pop','Power','value','Fractal Power',''),
    ('knob',6,'fractal.iterations','fractal_pop','Iterations','value','Iterations',''),
    ('knob',7,'fractal.bailout','fractal_pop','Bailout','value','Bailout',''),
    ('knob',8,'fractal.tumble','fractal_pop','Tumblemult','value','Tumble Speed',''),
    ('button',1,'pixelsort.bypass','pixelSortV3','Bypass','toggle','Bypass','toggle'),
    ('button',2,'pixelsort.persistence','pixelSortV3','Persistence','toggle','Hold / Fade','toggle'),
    ('button',3,'fractal.autorotate','fractal_pop','Autorotate','toggle','Auto Rotate','toggle'),
    ('button',4,'fractal.reset','fractal_pop','Reset','pulse','Reset Camera','toggle'),
    ('button',8,'pixelsort.clear','pixelSortV3','Clearhistory','pulse','Clear History','push'),
)
GROUP_ID = 'real.components.v1'


def specs(controller):
    root=controller.parent()
    result=[]
    for kind,slot,id,comp,name,mode,label,button_type in TARGETS:
        target=root.op(comp)
        if target is None:
            raise ValueError('Missing target COMP: '+comp)
        parameter=getattr(target.par,name,None)
        if parameter is None:
            raise ValueError('Missing custom parameter: '+comp+'.'+name)
        spec=dict(kind=kind,slot=slot,id=id,parameter=parameter,mode=mode,label=label)
        if button_type:spec['button_type']=button_type
        result.append(spec)
    return result


def install(controller):
    if controller.State['Connected']:
        raise ValueError('Disconnect before replacing the saved setup')
    candidates=specs(controller)
    controller.BindControls(candidates,group_id=GROUP_ID)
    table=controller.op('base_targets/targets')
    columns=('kind','slot','id','comp','parameter','mode','minimum','maximum','label','button_type')
    table.clear();table.appendRow(columns)
    for spec in candidates:
        parameter=spec['parameter']
        # Existing saved-table paths resolve relative to the controller. Aliases stay
        # targeted at the public COMP parameter, not its internal bind master.
        table.appendRow([spec['kind'],spec['slot'],spec['id'],
                         '../'+parameter.owner.name,parameter.name,spec['mode'],
                         '','',spec['label'],spec.get('button_type','')])
    controller.par.Groupid=GROUP_ID
    controller.par.Setupmode='collection'
    controller.Applybinding()
    return controller.GetControlCatalog()
