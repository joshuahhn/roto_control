"""Install event-driven free LEARN observer; all operators stay in controller."""
import os
from pathlib import Path


def install(controller, source_dir):
    if controller.ext.RotoPythonExt._process is not None:
        raise ValueError('Disconnect before installing free LEARN')
    source=Path(source_dir)
    for name,kind,x in [('free_learn',textDAT,1530),('learn_parameters',parameterexecuteDAT,1705)]:
        dat=controller.op(name) or controller.create(kind,name)
        dat.viewer=True;dat.nodeX=x;dat.nodeY=-400
        dat.par.language='python'
        path=source/'code/py/roto_python'/f'{name}.py'
        dat.text=path.read_text()
        dat.par.file=os.path.relpath(path,project.folder)
        dat.par.syncfile=False;dat.par.loadonstart=True
    watcher=controller.op('learn_parameters')
    watcher.par.active=False
    watcher.par.op.expr='';watcher.par.op.val=''
    watcher.par.pars='*'
    watcher.par.custom=True;watcher.par.builtin=False
    watcher.par.valuechange=False;watcher.par.valueschanged=True;watcher.par.onpulse=True
    for name in ('expressionchange','exportchange','enablechange','modechange'):
        getattr(watcher.par,name).val=False
    box=controller.op('annotate_free_learn') or controller.create(annotateCOMP,'annotate_free_learn')
    box.name='annotate_free_learn';box.utility=False
    box.par.Titletext='Free Learn'
    box.nodeX,box.nodeY,box.nodeWidth,box.nodeHeight=1505,-425,355,175
    box.viewer=True
    return watcher
