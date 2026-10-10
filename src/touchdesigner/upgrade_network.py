"""Execute in TD; upgrade(explicit_project_parent, source_dir), while disconnected."""
import os
from pathlib import Path


def upgrade(parent_comp, source_dir):
    source = Path(source_dir).resolve()
    comp = parent_comp.op('roto_python')
    if comp is None:
        raise ValueError('Build roto_python first')
    display_page = next((p for p in comp.customPages if p.name == "Display"), None) or comp.appendCustomPage("Display")
    for name, value in (("Trackname", "EFFECT"), ("Pluginname", "CUSTOM")):
        if getattr(comp.par, name, None) is None:
            par = display_page.appendStr(name)[0]
            par.default = par.val = value
    state = comp.op('base_state') or comp.create(baseCOMP, 'base_state')
    state.viewer = True
    state.par.parentshortcut = 'RotoState'
    state.nodeX, state.nodeY = 925, -40
    page = next((p for p in state.customPages if p.name == 'State'), None) or state.appendCustomPage('State')
    fields = {'Toggle': ('Connected','Plugin','Mapped','Touched','Learning','Bindingvalid'),
              'Int': ('Rx','Tx','Rejected','Echoblocked'),
              'Str': ('Status','Lasterror','Targetid'), 'Float': ('Value','Targetvalue')}
    for style,names in fields.items():
        for name in names:
            if getattr(state.par,name,None) is None:
                par = getattr(page,'append'+style)(name)[0]
                old = getattr(comp.par,name,None)
                if old is not None:
                    par.val = old.eval()
                par.readOnly = True
    old_page = next((p for p in comp.customPages if p.name == 'Status'), None)
    if old_page is not None:
        old_page.destroy()
    page = next((p for p in comp.customPages if p.name == 'Binding'), None) or comp.appendCustomPage('Binding')
    if getattr(comp.par,'Setupmode',None) is None:
        par = page.appendMenu('Setupmode',label='Binding mode')[0]
        par.menuNames = ['value','parameter','callback']
        par.menuLabels = ['Built-in Value','Custom parameter','Registration hook']
        par.default = par.val = 'value'
        page.appendOP('Targetcomp',label='Target COMP')
        for name,label in [('Targetpar','Custom parameter'),('Bindingid','Stable target ID'),('Targetlabel','Label (optional)')]:
            page.appendStr(name,label=label)
        par = page.appendToggle('Useparrange',label='Use parameter range')[0]
        par.default = par.val = True
        page.appendFloat('Minimum')
        par = page.appendFloat('Maximum')[0]
        par.default = par.val = 1
        page.appendPulse('Applybinding',label='Apply binding')
    for name in ('Targetcomp','Targetpar','Bindingid','Targetlabel','Useparrange'):
        parameter = getattr(comp.par,name,None)
        if parameter is not None:
            parameter.enableExpr = "me.par.Setupmode == 'parameter'"
    for name in ('Minimum','Maximum'):
        parameter = getattr(comp.par,name,None)
        if parameter is not None:
            parameter.enableExpr = "me.par.Setupmode == 'parameter' and not me.par.Useparrange"
    if comp.op('registration') is None:
        hook = comp.create(textDAT,'registration')
        hook.viewer = True
        hook.nodeX,hook.nodeY = 550,-420
        hook.par.language = 'python'
        hook.text = 'def onRegister(controller):\n    # Replace this demo call with your Extension/DAT registration.\n    demo = controller.parent().op("base_callback_demo")\n    controller.BindCallback(id="demo.callback.speed", label="Callback", minimum=0, maximum=10, value=demo.par.Speed.eval(), on_change=demo.op("demo_callbacks").module.on_change)\n'
    for name, kind, pos in [('setup', textDAT, (725,-420)), ('binding', textDAT, (550,-210)),
                            ('snapshots', textDAT, (725,-315)),
                            ('target_callbacks', parameterexecuteDAT, (725,-210))]:
        dat = comp.op(name) or comp.create(kind, name)
        dat.viewer = True
        dat.nodeX, dat.nodeY = pos
        dat.par.language = 'python'
        f = source/'code/py/roto_python'/f'{name}.py'
        dat.text = f.read_text()
        dat.par.file = os.path.relpath(f, project.folder)
        dat.par.syncfile = True
        dat.par.loadonstart = True
    watcher = comp.op('target_callbacks')
    watcher.par.active = False
    watcher.par.op = ''
    watcher.par.pars = ''
    watcher.par.custom = True
    watcher.par.builtin = False
    watcher.par.valuechange = True
    watcher.par.valueschanged = False
    watcher.par.onpulse = False
    output = comp.op('out_values') or comp.create(outCHOP, 'out_values')
    output.viewer = True
    output.nodeX, output.nodeY = 350, 0
    output.inputConnectors[0].connect(comp.op('null_values'))
    comp.op('parameter_values').par.ops.expr = "parent.RotoPython.op('base_state')"
    comp.op('parameter_values').par.parameter = 'Value Targetvalue Connected Plugin Mapped Touched Learning Bindingvalid Rx Tx Rejected Echoblocked'
    names = 'Value Targetvalue Connected Plugin Mapped Touched Learning Bindingvalid Rx Tx Rejected Echoblocked'
    comp.op('parameter_values').par.renamefrom = ' '.join('*:'+name for name in names.split())
    comp.op('parameter_values').par.renameto = names
    comp.display = True
    for name, shortcut, y in [('base_parameter_demo','ParameterDemo',0),
                               ('base_callback_demo','CallbackDemo',-210)]:
        demo = parent_comp.op(name) or parent_comp.create(baseCOMP,name)
        demo.viewer = True
        demo.display = True
        demo.par.parentshortcut = shortcut
        demo.nodeX, demo.nodeY = 335,y
        page = next((p for p in demo.customPages if p.name=='Demo'), None) or demo.appendCustomPage('Demo')
        if getattr(demo.par,'Speed',None) is None:
            p = page.appendFloat('Speed')[0]
            p.default = p.val = 5
            p.min = p.normMin = 0
            p.max = p.normMax = 10
            p.clampMin = p.clampMax = True
        if getattr(demo.par,'Usebinding',None) is None:
            page.appendPulse('Usebinding',label='Use this binding')
        if shortcut == 'CallbackDemo':
            if getattr(demo.par,'Setvalue',None) is None:
                page.appendPulse('Setvalue',label='Send Speed to controller')
            for name2,style in [('Received','Float'),('Events','Int'),('Origin','Str')]:
                if getattr(demo.par,name2,None) is None:
                    p = getattr(page,'append'+style)(name2)[0]
                    p.readOnly = True
        dat = demo.op('demo_callbacks')
        if dat is None:
            dat = demo.create(parameterexecuteDAT,'demo_callbacks')
            # Generated demo callbacks are embedded before source/binding writes.
            # Existing user callback sources and their file settings stay intact.
            dat.par.syncfile = False
            dat.par.loadonstart = False
            dat.par.file = ''
            dat.par.language = 'python'
            f = source/'code/py'/('parameter_demo.py' if shortcut=='ParameterDemo' else 'callback_demo.py')
            dat.text = f.read_text()
        dat.viewer = True
        dat.nodeX, dat.nodeY = 0,0
        dat.par.op.expr = 'parent.'+shortcut
        dat.par.pars = 'Usebinding Setvalue'
        dat.par.custom = True
        dat.par.builtin = False
        dat.par.valuechange = False
        dat.par.onpulse = True
    comp.op('parameter_callbacks').par.pars = 'Value Trackname Pluginname Connect Disconnect Offerparameter Applybinding'
    comp.par.reinitextensions.pulse()
    return comp
