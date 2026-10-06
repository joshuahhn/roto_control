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
    dat=controller.op('layouts') or controller.create(textDAT,'layouts')
    dat.viewer=True;dat.par.language='python';dat.text=(source/'code/py/roto_python/layouts.py').read_text(encoding='utf-8')
    dat.par.file='';dat.par.syncfile=False;dat.par.loadonstart=False
    # Existing Binding annotation is cleaned using actual measured sizes afterward.
    dat.nodeX,dat.nodeY=540,-270
    for name in ('protocol','RotoPythonExt'):
        controller.op(name).text=(source/'code/py/roto_python'/f'{name}.py').read_text(encoding='utf-8')
    controller.op('parameter_callbacks').par.pars='Value Trackname Pluginname Layout Connect Disconnect Offerparameter Applybinding Newlayout Renamelayout Deletelayout Confirmdelete Canceldelete'
    controller.par.reinitextensions.pulse()
    return controller
