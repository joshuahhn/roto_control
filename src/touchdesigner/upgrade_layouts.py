"""Small disconnected Layout upgrade; does not create demos or optional CHOPs."""
from pathlib import Path

def upgrade(controller,source_dir):
    if controller.ext.RotoPythonExt._process is not None:raise ValueError('Disconnect before Layout upgrade')
    extension=controller.ext.RotoPythonExt
    if getattr(extension,'_layouts',None) is not None:extension._layouts.capture(force=True)
    if getattr(extension,'_follow',None) is not None:extension._follow.refresh_links()
    source=Path(source_dir)
    page=next((p for p in controller.customPages if p.name=='Layouts'),None) or controller.appendCustomPage('Layouts')
    if getattr(controller.par,'Layout',None) is None:
        par=page.appendMenu('Layout',label='Layout')[0]
        par.menuNames=['custom'];par.menuLabels=['Custom'];par.default=par.val='custom'
    if getattr(controller.par,'Layoutname',None) is None:
        par=page.appendStr('Layoutname',label='Layout name')[0];par.default=par.val='Custom'
    for name,label in [('Newlayout','New empty Layout'),('Renamelayout','Rename Layout'),('Deletelayout','Delete Layout')]:
        if getattr(controller.par,name,None) is None:page.appendPulse(name,label=label)
    track_page=next((p for p in controller.customPages if p.name=='Tracks'),None) or controller.appendCustomPage('Tracks')
    if getattr(controller.par,'Track',None) is None:
        par=track_page.appendMenu('Track',label='Active Track')[0]
        par.menuNames=['track.custom'];par.menuLabels=['EFFECT'];par.default=par.val='track.custom'
    if getattr(controller.par,'Newtrackname',None) is None:
        par=track_page.appendStr('Newtrackname',label='New Track name')[0];par.default=par.val='TRACK'
    for name,label in [('Newtrack','New empty Track'),('Deletetrack','Delete Track')]:
        if getattr(controller.par,name,None) is None:track_page.appendPulse(name,label=label)
    dat=controller.op('layouts') or controller.create(textDAT,'layouts')
    dat.viewer=True;dat.par.language='python';dat.text=(source/'code/py/roto_python/layouts.py').read_text(encoding='utf-8')
    dat.par.file='';dat.par.syncfile=False;dat.par.loadonstart=False
    # Existing Binding annotation is cleaned using actual measured sizes afterward.
    dat.nodeX,dat.nodeY=540,-270
    follow=controller.op('text_comp_follow') or controller.create(textDAT,'text_comp_follow')
    follow.par.language='python';follow.par.file='';follow.par.syncfile=False;follow.par.loadonstart=False
    follow.text=(source/'code/py/roto_python/text_comp_follow.py').read_text(encoding='utf-8')
    follow.nodeX,follow.nodeY=540,-740
    follow.nodeWidth,follow.nodeHeight=130,90
    box=next((n for n in controller.children if n.OPType=='annotateCOMP' and n.par.Titletext.eval()=='Focus'),None)
    if box is None:
        box=controller.create(annotateCOMP,'annotate_focus');box.par.Titletext='Focus'
        box.nodeX,box.nodeY=515,-815;box.nodeWidth,box.nodeHeight=355,225
    for name in ('protocol','collection_protocol','binding','free_learn','RotoPythonExt','setup','lifecycle_callbacks'):
        controller.op(name).text=(source/'code/py/roto_python'/f'{name}.py').read_text(encoding='utf-8')
    metadata=controller.op('inspector/context_state') or controller.op('inspector').create(textDAT,'context_state')
    metadata.par.language='json';metadata.viewer=True;metadata.nodeX,metadata.nodeY=1050,-130
    controller.op('lifecycle_callbacks').par.projectpresave=True
    controller.op('inspector/inspector_data').text=(source/'code/py/roto_python/inspector/inspector_data.py').read_text(encoding='utf-8')
    controller.op('parameter_callbacks').par.pars='Value Trackname Pluginname Layout Track Newtrack Deletetrack Connect Disconnect Offerparameter Applybinding Newlayout Renamelayout Deletelayout'
    controller.op('setup').module.install_follow_ui(controller)
    controller.par.reinitextensions.pulse()
    controller.op('setup').module.configure_ui(controller)
    return controller
