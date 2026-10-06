"""Small disconnected Layout upgrade; does not create demos or optional CHOPs."""
from pathlib import Path

def upgrade(controller,source_dir):
    if controller.ext.RotoPythonExt._process is not None:raise ValueError('Disconnect before Layout upgrade')
    source=Path(source_dir)
    page=next((p for p in controller.customPages if p.name=='Layouts'),None) or controller.appendCustomPage('Layouts')
    if getattr(controller.par,'Layout',None) is None:
        par=page.appendMenu('Layout',label='Layout')[0]
        par.menuNames=['custom'];par.menuLabels=['Custom'];par.default=par.val='custom'
    if getattr(controller.par,'Layoutname',None) is None:
        par=page.appendStr('Layoutname',label='Layout name')[0];par.default=par.val='Custom'
    for name,label in [('Newlayout','New empty Layout'),('Renamelayout','Rename Layout'),('Deletelayout','Delete Layout'),('Confirmdelete','Yes, delete Layout'),('Canceldelete','No, keep Layout')]:
        if getattr(controller.par,name,None) is None:page.appendPulse(name,label=label)
    controller.par.Confirmdelete.enable=controller.par.Canceldelete.enable=False
    track_page=next((p for p in controller.customPages if p.name=='Tracks'),None) or controller.appendCustomPage('Tracks')
    if getattr(controller.par,'Track',None) is None:
        par=track_page.appendMenu('Track',label='Active Track')[0]
        par.menuNames=['track.custom'];par.menuLabels=['EFFECT'];par.default=par.val='track.custom'
    if getattr(controller.par,'Newtrackname',None) is None:
        par=track_page.appendStr('Newtrackname',label='New Track name')[0];par.default=par.val='TRACK'
    for name,label in [('Newtrack','New empty Track'),('Deletetrack','Delete Track'),('Confirmtrackdelete','Yes, delete Track'),('Canceltrackdelete','No, keep Track')]:
        if getattr(controller.par,name,None) is None:track_page.appendPulse(name,label=label)
    controller.par.Confirmtrackdelete.enable=controller.par.Canceltrackdelete.enable=False
    dat=controller.op('layouts') or controller.create(textDAT,'layouts')
    dat.viewer=True;dat.par.language='python';dat.text=(source/'code/py/roto_python/layouts.py').read_text(encoding='utf-8')
    dat.par.file='';dat.par.syncfile=False;dat.par.loadonstart=False
    # Existing Binding annotation is cleaned using actual measured sizes afterward.
    dat.nodeX,dat.nodeY=540,-270
    for name in ('protocol','binding','free_learn','RotoPythonExt','setup'):
        controller.op(name).text=(source/'code/py/roto_python'/f'{name}.py').read_text(encoding='utf-8')
    controller.op('inspector/inspector_data').text=(source/'code/py/roto_python/inspector/inspector_data.py').read_text(encoding='utf-8')
    controller.op('parameter_callbacks').par.pars='Value Trackname Pluginname Layout Track Newtrack Deletetrack Confirmtrackdelete Canceltrackdelete Connect Disconnect Offerparameter Applybinding Newlayout Renamelayout Deletelayout Confirmdelete Canceldelete'
    controller.par.reinitextensions.pulse()
    controller.op('setup').module.configure_ui(controller)
    return controller
