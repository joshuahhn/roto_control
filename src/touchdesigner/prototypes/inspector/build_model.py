"""Create/refresh the single shared demo model through live TD."""
from pathlib import Path
model=op('/inspector_model')
source=Path(project.folder+'/prototypes/inspector/model.py').read_text()
if not model:
    model=op('/').create(baseCOMP,'inspector_model');model.nodeX=100;model.nodeY=-300;model.viewer=True
    model.par.opshortcut='InspectorModel';model.par.parentshortcut='InspectorModel'
    page=model.appendCustomPage('Demo')
    page.appendPulse('Stepvalues',label='Step demo values')
    page.appendPulse('Resetdemo',label='Reset demo')
    dat=model.create(textDAT,'InspectorModel');dat.viewer=True;dat.par.language='python';dat.nodeY=-125
    dat.text=source
    model.seq.ext.numBlocks=1;model.par.initextonstart=True
    model.par.ext0object="op('./InspectorModel').module.InspectorModel(me)";model.par.ext0promote=True
    model.initializeExtensions(0)
    cb=model.create(parameterexecuteDAT,'demo_actions');cb.viewer=True;cb.nodeX=200;cb.nodeY=0
    cb.par.op.expr='parent.InspectorModel';cb.par.pars='Stepvalues Resetdemo';cb.par.builtin=False
    cb.text="def onPulse(par):\n    if par.name=='Stepvalues': parent.InspectorModel.StepDemo()\n    elif par.name=='Resetdemo': parent.InspectorModel.ResetDemo()\n"
elif model.op('InspectorModel').text!=source:
    for path in ['/inspector_below','/inspector_popup']:
        view=op(path)
        if view and view.extensions[0] is not None:view.ext.InspectorView.Disconnect()
    if model.extensions[0] is not None:model.ext.InspectorModel.onDestroyTD()
    model.op('InspectorModel').text=source;model.initializeExtensions(0)
    for path in ['/inspector_below','/inspector_popup']:
        view=op(path)
        if view and view.extensions[0] is not None:view.Connect()
model.seq.ext.numBlocks=1;model.par.initextonstart=True
if model.extensions[0] is None:model.initializeExtensions(0)
print(model.Stats())
