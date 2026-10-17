"""Execute in TouchDesigner: build(controller, source_dir). External Lister config."""
from pathlib import Path
import os


def build(controller, source_dir):
    source = Path(source_dir)
    if controller.op('inspector') is not None:
        raise FileExistsError('inspector already exists')
    inspector = controller.create(containerCOMP,'inspector')
    inspector.par.parentshortcut = 'RotoInspector'
    inspector.viewer = inspector.display = True
    inspector.par.w, inspector.par.h, inspector.par.alignorder = 1830, 580, 0
    inspector.nodeX,inspector.nodeY,inspector.nodeWidth,inspector.nodeHeight = 1530,-40,280,170
    config = inspector.copy(op.TDTox.op('lister').par.Configcomp.eval(),name='listerConfig')
    config.viewer = True
    config.nodeX,config.nodeY = 0,-400
    table = inspector.create(tableDAT,'targets');table.viewer=True
    table.nodeX,table.nodeY,table.nodeWidth,table.nodeHeight=350,-170,280,130
    module = inspector.create(textDAT,'inspector_data');module.viewer=True
    module.nodeX,module.nodeY = 700,-130
    module.par.language='python'
    path=source/'code/py/roto_python/inspector/inspector_data.py'
    module.text=path.read_text()
    module.par.file=os.path.relpath(path,project.folder)
    module.par.loadonstart=True
    module.par.syncfile=False
    title=inspector.create(textCOMP,'title')
    title.viewer=True
    title.nodeX,title.nodeY=0,0
    title.par.w.expr='parent.RotoInspector.par.w-160'
    title.par.h=36
    title.par.y.expr='parent.RotoInspector.par.h-36'
    title.par.text='ROTO Mapping Inspector'
    title.par.fontsize=13
    title.par.fontcolorr=title.par.fontcolorg=title.par.fontcolorb=.9
    title.par.bgcolorr=title.par.bgcolorg=title.par.bgcolorb=.10
    title.par.display=True
    module.module.refresh(inspector,controller.GetControlCatalog())
    lister=inspector.copy(op.TDTox.op('lister'),name='lister')
    lister.viewer=True
    lister.nodeX,lister.nodeY=350,0
    lister.par.clone.expr="op.TDTox.op('lister')"
    lister.par.ext0object="op('./ListerExt').module.ListerExt(me)"
    lister.par.ext0promote=True
    lister.par.parentshortcut='Lister'
    lister.par.callbacks="parent.RotoInspector.op('list_events').path" # expression below
    lister.par.callbacks.expr="parent.RotoInspector.op('list_events').path"
    lister.par.Configcomp.expr="me.parent().op('listerConfig').path"
    lister.par.Autodefinecols=False
    lister.par.Advancedcallbacks=True
    lister.par.Allowundo=False
    lister.par.Inputtabledat.expr="parent.RotoInspector.op('targets').path"
    lister.par.Inputtablehasheaders=True
    lister.par.Refreshoninputchange=True
    lister.par.Autosyncinputtable=False
    lister.par.w.expr='parent.RotoInspector.par.w'
    lister.par.h.expr='parent.RotoInspector.par.h-72'
    columns=[('Control',90),('Mapped',75),('Learn',85),('ClearLearn',150),('COMP',350),('Parameter',105),('Mode',75),
             ('Hardware',85),('Min',75),('Max',75),('Value',80),('ID',185),('Error',220)]
    coldef=config.op('colDefine')
    row_names=[row[0].val for row in coldef.rows()]
    assert len(row_names)==19
    coldef.clear()
    for field in row_names:
        values=[]
        for name,width in columns:
            values.append({'column':name,'columnLabel':'Clear' if name=='ClearLearn' else name,'sourceData':name,'sourceDataMode':'string',
                           'width':width,'stretch':int(name=='COMP'),'sizable':1,'editable':2 if name in ('Min','Max','Hardware','Value') else 0,
                           'selectRow':int(name not in ('ClearLearn','Learn','COMP','Parameter')),'cellLook':'button' if name in ('ClearLearn','Learn') else '',
                           'justify':'CENTER' if name in ('ClearLearn','Learn') else 'CENTERLEFT',
                           'help':'Click to choose any COMP/custom parameter; assignment is saved automatically' if name in ('COMP','Parameter') else 'Delete target registration and hardware mapping; retain empty slot' if name=='ClearLearn' else 'Open hardware LEARN; select this slot, then send its registered target metadata' if name=='Learn' else '*'}.get(field,''))
        coldef.appendRow([field,*values])
    callback_path=source/'code/py/roto_python/inspector/lister_callbacks.py'
    config.op('callbacks').text=callback_path.read_text()
    config.op('callbacks').par.file=os.path.relpath(callback_path,project.folder)
    config.op('callbacks').par.loadonstart=True
    config.op('callbacks').par.syncfile=False
    config.op('callbacks').par.language='python'
    for name in ('list_events','toolbar_events'):
        dat=inspector.create(textDAT if name=='list_events' else panelexecuteDAT,name)
        dat.viewer=True
        dat.nodeX,dat.nodeY=700 if name=='list_events' else 1050,-280
        path=source/('code/py/roto_python/inspector/'+name+'.py')
        dat.text=path.read_text();dat.par.language='python'
        dat.par.file=os.path.relpath(path,project.folder)
        dat.par.loadonstart=True;dat.par.syncfile=False
        if name=='toolbar_events':
            dat.par.panels='clear_all* page_select'
            dat.par.panelvalue='lselect';dat.par.offtoon=True
            dat.par.whileon=False;dat.par.whileoff=False;dat.par.ontooff=False;dat.par.valuechange=False
    for index,(name,label,width,offset) in enumerate([
            ('clear_all','Clear All',150,150),('clear_all_yes','Yes',73,150),('clear_all_no','No',73,73)]):
        button=inspector.create(buttonCOMP,name);button.name=name;button.viewer=True
        button.nodeX,button.nodeY=1050+index*175,0
        button.par.label=label;button.par.buttontype='momentary'
        button.par.w=width;button.par.h=30
        button.par.x.expr='parent.RotoInspector.par.w-'+str(offset)
        button.par.y.expr='parent.RotoInspector.par.h-33'
        button.par.display=name=='clear_all'
    database=inspector.create(textDAT,'database');database.viewer=True
    database.par.language='json';database.nodeX,database.nodeY=350,-360
    page_button=inspector.create(buttonCOMP,'page_select');page_button.name='page_select';page_button.viewer=True
    page_button.nodeX,page_button.nodeY=1050,-150
    page_button.par.label='Page: All COMPs v';page_button.par.buttontype='momentary'
    page_button.par.w=800;page_button.par.h=30
    page_button.par.y.expr='parent.RotoInspector.par.h-69'
    inspector.store('pending_clear',None)
    confirmation=config.create(containerCOMP,'confirm_buttons')
    confirmation.viewer=True;confirmation.par.w=150;confirmation.par.h=24
    confirmation.nodeX,confirmation.nodeY=0,-600
    for name,label,x in [('yes','Yes',0),('no','No',77)]:
        button=confirmation.create(buttonCOMP,name);button.name=name;button.viewer=True
        button.par.label=label;button.par.w=73;button.par.h=24;button.par.x=x
        button.nodeX,button.nodeY=x*3,0
    graphic=config.create(opviewerTOP,'confirm_view');graphic.viewer=True
    graphic.nodeX,graphic.nodeY=175,-600
    graphic.par.opviewer='confirm_buttons';graphic.par.outputresolution='custom';graphic.par.resolutionw=150;graphic.par.resolutionh=24
    output=config.create(nullTOP,'null_confirm');output.viewer=True
    output.nodeX,output.nodeY=350,-600;output.inputConnectors[0].connect(graphic)
    orphan=inspector.op('listerConfig1')
    if orphan is not None and lister.par.Configcomp.eval()!=orphan:
        orphan.destroy()
    lister.par.reinitextensions.pulse()
    lister.par.Refresh.pulse()
    module.module.refresh(inspector,controller.GetControlCatalog())
    callback=inspector.op('title_callbacks')
    if callback is not None:
        callback.nodeX,callback.nodeY=0,-175
    boxes=[x for x in controller.ops('*',includeUtility=True) if x.type=='annotate' and x.par.Titletext.eval()=='Inspector']
    box=boxes[0] if boxes else controller.create(annotateCOMP,'annotate_inspector')
    for extra in boxes[1:]:
        extra.destroy()
    box.utility=False
    box.par.Mode='networkbox'
    box.par.Titletext='Inspector'
    box.nodeX,box.nodeY,box.nodeWidth,box.nodeHeight=1505,-65,330,255
    return inspector
