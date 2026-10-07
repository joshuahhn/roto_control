"""Idempotent collection upgrade; run disconnected after upgrade_network."""
import os
from pathlib import Path


def upgrade(parent_comp, source_dir):
    source = Path(source_dir).resolve()
    comp = parent_comp.op('roto_python')
    if comp.ext.RotoPythonExt._process is not None:
        raise ValueError('Disconnect before upgrading controls')
    page = next(p for p in comp.customPages if p.name == 'Binding')
    comp.par.Setupmode.menuNames = ['value', 'parameter', 'callback', 'collection']
    comp.par.Setupmode.menuLabels = ['Built-in Value', 'Custom parameter', 'Registration hook', 'Multiple controls']
    if getattr(comp.par, 'Groupid', None) is None:
        p = page.appendStr('Groupid', label='Stable collection ID')[0]
        p.default = p.val = 'demo.controls.v1'
    comp.par.Groupid.enableExpr = "me.par.Setupmode == 'collection'"
    for name, pos in [('collection_protocol', (1150,-300)), ('controls', (1325,-300))]:
        dat = comp.op(name) or comp.create(textDAT, name)
        dat.viewer = True
        dat.nodeX, dat.nodeY = pos
        dat.par.language = 'python'
        path = source/'code/py/roto_python'/f'{name}.py'
        dat.text = path.read_text()
        dat.par.file = os.path.relpath(path, project.folder)
        dat.par.syncfile = True
        dat.par.loadonstart = True
    base = comp.op('base_targets') or comp.create(baseCOMP, 'base_targets')
    base.par.parentshortcut = 'RotoTargets'
    base.viewer = True
    base.nodeX, base.nodeY = 1150,-40
    base.nodeWidth, base.nodeHeight = 160,130
    marker = base.op('mapping_marks') or base.create(textDAT, 'mapping_marks')
    marker.viewer=True
    marker.nodeX,marker.nodeY=1100,-210
    marker.par.language='python'
    marker_path=source/'code/py/roto_python/base_targets/mapping_marks.py'
    marker.text=marker_path.read_text()
    marker.par.file=os.path.relpath(marker_path,project.folder)
    marker.par.loadonstart=True
    marker.par.syncfile=False
    demo = parent_comp.op('base_controls_demo') or parent_comp.create(baseCOMP, 'base_controls_demo')
    demo.par.parentshortcut = 'ControlsDemo'
    demo.viewer = True
    demo.nodeX, demo.nodeY = 600,0
    page = next((p for p in demo.customPages if p.name == 'Controls'), None) or demo.appendCustomPage('Controls')
    for slot in range(1,9):
        if getattr(demo.par, f'Knob{slot}', None) is None:
            p = page.appendFloat(f'Knob{slot}')[0]
            p.default = p.val = 5
            p.min = p.normMin = 0
            p.max = p.normMax = 10
            p.clampMin = p.clampMax = True
        if getattr(demo.par, f'Button{slot}', None) is None:
            # Alternating modes gives first/last-slot coverage of both modes.
            getattr(page, 'appendToggle' if slot%2 else 'appendPulse')(f'Button{slot}', label=f'Button {slot} '+('Toggle' if slot%2 else 'Pulse'))
    targets = base.op('targets')
    if targets is None:
        targets = base.create(tableDAT, 'targets')
        targets.clear()
        targets.appendRow(['kind','slot','id','comp','parameter','mode','minimum','maximum','label'])
        for kind in ('knob','button'):
            for slot in range(1,9):
                targets.appendRow([kind,slot,f'demo.{kind}{slot}', '../base_controls_demo',
                                   f'{kind.capitalize()}{slot}', 'value' if kind=='knob' else 'toggle' if slot%2 else 'pulse',
                                   '', '', f'{kind.capitalize()} {slot}'])
    columns = [cell.val for cell in targets.row(0)]
    if 'button_type' not in columns:
        saved_rows = [[cell.val for cell in row] for row in targets.rows()[1:]]
        kind_column = columns.index('kind')
        targets.clear()
        targets.appendRow(columns + ['button_type'])
        for row in saved_rows:
            targets.appendRow(row + ['toggle' if row[kind_column] == 'button' else ''])
    state = base.op('state') or base.create(tableDAT, 'state')
    trace = base.op('rx_events')
    if trace is None:
        trace = base.create(tableDAT,'rx_events')
        trace.clear()
        trace.appendRow(['time','kind','bytes'])
    trace.viewer=True
    trace.nodeX,trace.nodeY=1100,90
    trace.nodeWidth,trace.nodeHeight=280,180
    for dat,y in ((targets,0),(state,-210)):
        dat.viewer = True
        dat.nodeX, dat.nodeY = 0,y
        dat.nodeWidth, dat.nodeHeight = 250,180
    for index in range(16):
        kind,slot = ('knob',index+1) if index<8 else ('button',index-7)
        dat = base.op(f'watch_{kind}{slot}') or base.create(parameterexecuteDAT, f'watch_{kind}{slot}')
        dat.viewer = True
        dat.nodeX,dat.nodeY = 350+(index%4)*175,90-(index//4)*210
        dat.par.active = False
        dat.par.language = 'python'
        path = source/'code/py/roto_python/control_callbacks.py'
        dat.text = path.read_text()
        # One common source, read-only file loading; per-DAT sync writes could
        # clobber the shared file when several watchers are created together.
        dat.par.file = os.path.relpath(path,project.folder)
        dat.par.loadonstart = True
        dat.par.syncfile = False
        dat.par.custom = True
        dat.par.builtin = False
        dat.par.valuechange = True
        dat.par.valueschanged = False
        dat.par.onpulse = True
    values = base.op('controls_values') or base.create(scriptCHOP, 'controls_values')
    values.par.modoutsidecook = True
    values.par.callbacks = ''
    unused = base.op('controls_values_callbacks')
    if unused is not None:
        unused.destroy()
    for name,kind,x,upstream in [('controls_values',scriptCHOP,0,None),('null_controls',nullCHOP,175,values),('out_controls',outCHOP,350,None)]:
        node = base.op(name) or base.create(kind,name)
        node.viewer = True
        node.nodeX,node.nodeY = x,-840
        if upstream is not None:
            node.inputConnectors[0].connect(upstream)
    base.op('out_controls').inputConnectors[0].connect(base.op('null_controls'))
    select = comp.op('select_controls') or comp.create(selectCHOP,'select_controls')
    select.par.chop = 'base_targets/out_controls'
    for name,kind,x in [('select_controls',selectCHOP,0),('null_controls',nullCHOP,175),('out_controls',outCHOP,350)]:
        node = comp.op(name) or comp.create(kind,name)
        node.viewer = True
        node.nodeX,node.nodeY = x,-600
    comp.op('null_controls').inputConnectors[0].connect(select)
    comp.op('out_controls').inputConnectors[0].connect(comp.op('null_controls'))
    events = demo.op('pulse_events')
    if events is None:
        events = demo.create(tableDAT,'pulse_events')
        events.clear()
        events.appendRow(['parameter','count'])
        for slot in (2,4,6,8):events.appendRow([f'Button{slot}',0])
    events.viewer=True
    events.nodeX,events.nodeY=175,0
    dat=demo.op('pulse_callbacks') or demo.create(parameterexecuteDAT,'pulse_callbacks')
    dat.viewer=True
    dat.nodeX,dat.nodeY=0,0
    dat.text=(source/'code/py/controls_demo.py').read_text()
    dat.par.op.expr='parent.ControlsDemo'
    dat.par.pars='Button2 Button4 Button6 Button8'
    dat.par.custom=True
    dat.par.builtin=False
    dat.par.valuechange=False
    dat.par.onpulse=True
    free_ns = dict(globals())
    free_path = source/'build_free_learn.py'
    exec(compile(free_path.read_text(),str(free_path),'exec'),free_ns)
    free_ns['install'](comp,source)
    # Refresh existing source DATs only after dependencies exist.
    for name in ('setup','RotoPythonExt'):
        comp.op(name).text=(source/'code/py/roto_python'/f'{name}.py').read_text()
    layout_ns = dict(globals())
    path = source/"layout_controls.py"
    exec(compile(path.read_text(),str(path),"exec"),layout_ns)
    layout_ns["layout"](parent_comp)
    comp.par.reinitextensions.pulse()
    if comp.op('layouts') is not None:
        comp.op('setup').module.configure_ui(comp)
    return comp
