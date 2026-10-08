"""Attach the compact Inspector to an existing controller, without rebinding it."""
from pathlib import Path
controller=op(globals().get('controller_path','/roto_control_python/roto_python'))
assert controller and hasattr(controller,'GetControlCatalog'),'Choose an existing Roto controller'
m=op('/inspector_model');assert m,'Build the shared model first'
views=[op('/inspector_below'),op('/inspector_popup')]
for c in views:
    if c and c.extensions[0] is not None:c.Disconnect()
old=m.extensions[0]
if old is not None:old.onDestroyTD()
if not hasattr(m.par,'Controller'):
    page=m.appendCustomPage('Data');page.appendOP('Controller',label='Controller')
m.par.Controller=controller
for name in ('Stepvalues','Resetdemo'):m.par[name].enable=False
if m.op('demo_actions'):m.op('demo_actions').par.active=False
command_namespace=dict(globals())
exec(Path(project.folder+'/prototypes/inspector/build_commands.py').read_text(),command_namespace)
exec(Path(project.folder+'/prototypes/inspector/build_targets.py').read_text(),dict(globals(),targets_only=True))
source=m.op('live_model') or m.create(textDAT,'live_model');source.viewer=True;source.par.language='python'
source.text=Path(project.folder+'/prototypes/inspector/live_model.py').read_text();source.nodeX=275;source.nodeY=-160
m.par.ext0object="op('./live_model').module.InspectorModel(me)";m.par.ext0promote=True;m.par.initextonstart=True
for parent in [m.op('base_commands')]+[v for v in views if v]:
    dat=parent.op('parity') or parent.create(textDAT,'parity');dat.viewer=True;dat.par.language='python';dat.text=Path(project.folder+'/prototypes/inspector/parity.py').read_text()
m.initializeExtensions(0)
# Existing controller catalog emits DAT changes only when its contents change.
cb=m.op('controller_catalog') or m.create(datexecuteDAT,'controller_catalog');cb.viewer=True;cb.par.active=False
cb.par.dat.expr='parent.InspectorModel.ControllerData()';cb.par.tablechange=True
for n in ('rowchange','colchange','cellchange','sizechange'):cb.par[n]=False
cb.text="def onTableChange(dat):\n    parent.InspectorModel.RequestSync()\n";cb.nodeX=475;cb.nodeY=0
watch=m.op('controller_parameters') or m.create(parameterexecuteDAT,'controller_parameters');watch.viewer=True;watch.par.active=False
watch.par.custom=True;watch.par.builtin=True;watch.par.valuechange=True;watch.par.onpulse=False;watch.par.modechange=True
watch.par.op.expr='';watch.par.op=' '.join(o.path for o in m.WatchOwners());watch.par.pars=m.WatchPars()
watch.text="def onValueChange(par,prev):\n    parent.InspectorModel.RequestSync()\ndef onModeChange(par,prev):\n    parent.InspectorModel.RefreshDefinitions()\n    parent.InspectorModel.RequestSync()\n";watch.nodeX=475;watch.nodeY=-160
config=m.op('controller_changed') or m.create(parameterexecuteDAT,'controller_changed');config.viewer=True
config.par.op.expr='parent.InspectorModel';config.par.pars='Controller';config.par.custom=True;config.par.builtin=False
config.text="def onValueChange(par,prev):\n    parent.InspectorModel.RequestSync()\n";config.nodeX=475;config.nodeY=-320
exec(Path(project.folder+'/prototypes/inspector/build_parity.py').read_text(),dict(globals(),parity_views=views))
for c in views:
    if c:c.op('ui').text=Path(project.folder+'/prototypes/inspector/ui.py').read_text()
exec(Path(project.folder+'/prototypes/inspector/isolate_popup.py').read_text(),dict(globals(),isolate_views=views))
action_namespace=dict(globals(),action_views=views)
exec(Path(project.folder+'/prototypes/inspector/build_editor_actions.py').read_text(),action_namespace)
exec(Path(project.folder+'/prototypes/inspector/build_mapping.py').read_text(),dict(globals(),action_views=views))
exec(Path(project.folder+'/prototypes/inspector/build_targets.py').read_text(),dict(globals(),target_views=views))
exec(Path(project.folder+'/prototypes/inspector/build_parity.py').read_text(),dict(globals(),parity_views=views))
exec(Path(project.folder+'/prototypes/inspector/build_definition_edit.py').read_text(),dict(globals()))
exec(Path(project.folder+'/prototypes/inspector/build_context_menu.py').read_text(),dict(globals(),context_views=views,reload_context_views=False))
for c in views:
    if not c:continue
    c.par.Presentation.menuLabels=['Fold','Popup']
    c.op('window_main').par.title='Inspector / '+('Fold' if c.par.Presentation.eval()=='below' else 'Popup')
    for target,action in [('text_style','presentation'),('text_brand','follow')]:
        c.op(target).par.clickthrough=False
        click=c.op('click_'+action) or c.create(panelexecuteDAT,'click_'+action);click.viewer=True
        click.par.panels=target;click.par.panelvalue='lselect';click.par.offtoon=True
        click.text="def onOffToOn(panelValue):\n    parent.InspectorDemo.Action(%r)\n"%action
        click.nodeX=1135 if action=='follow' else 1310;click.nodeY=-210
    c.op('window_opened').nodeX=1485;c.op('window_opened').nodeY=-210
    for i in range(16):c.op('container_scroll/container_content/slot'+str(i)+'/text_slot').par.fontsize=9
    c.initializeExtensions(0)
m.RefreshWatchers();cb.par.active=True;watch.par.active=True
m.Sync();m.Flush()
for c in views:
    if c:
        c.CloseEditor();c.op('window_editor').par.winclose.pulse()
        if c.name=='inspector_popup':c.op('window_main').par.winclose.pulse()
op('/inspector_below').Show()
print(m.Stats())
print(watch.par.op.evalOPs())

# Embed authoritative prototype Markdown; the export has no file dependency.
doc_namespace=dict(globals())
exec(Path(project.folder+'/scripts/td_project_docs.py').read_text(),doc_namespace)
readme=doc_namespace['embed_project_docs'](m,project.folder+'/prototypes/inspector')['readme_md']
readme.nodeX=25;readme.nodeY=-30

m.op('InspectorModel').nodeX=275;m.op('InspectorModel').nodeY=0
m.op('demo_actions').nodeX=675;m.op('demo_actions').nodeY=0
