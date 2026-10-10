"""Finite native held/release/drag-out test for the deferred menu opening."""
from pathlib import Path
import json
view=op('/inspector_below');menu=view.ext.InspectorView
m=view.ext.InspectorView._model;controller=m.ownerComp.par.Controller.eval()
routing=controller.GetLayoutContext()['key'];session=m.adapter.Session()
names=('Device','Layout','Track');rows=[];index=0

def finish():
    menu.CloseContextMenu()
    for name in names:view.op('context_'+name).interactClear()
    result=dict(virtual_mouse_only=True,physical_item_fix_verified=False,samples=rows,
                all_pass=all(not r['opened_while_held'] and r['opened_after_release'] and r['drag_out_cancelled'] for r in rows),
                routing_session_preserved=controller.GetLayoutContext()['key']==routing and m.adapter.Session()==session)
    Path(project.folder+'/prototypes/inspector/context_release_verification.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result))

def cancelled():
    global index
    rows[-1]['drag_out_cancelled']=not menu.ContextMenuOpen()
    index+=1
    if index<len(names):press()
    else:finish()

def cancel_release():
    view.op('context_'+names[index]).interactMouse(-1,-1,left=False)
    run('args[0]()',cancelled,delayFrames=4,delayRef=op.TDResources)

def opened():
    rows[-1]['opened_after_release']=menu.ContextMenuOpen() and menu._context_menu.details['name']==names[index]
    menu.CloseContextMenu()
    view.op('context_'+names[index]).interactMouse(.5,.5,left=True)
    run('args[0]()',cancel_release,delayFrames=3,delayRef=op.TDResources)

def release():
    rows.append(dict(button=names[index],opened_while_held=menu.ContextMenuOpen()))
    view.op('context_'+names[index]).interactMouse(.5,.5,left=False)
    run('args[0]()',opened,delayFrames=4,delayRef=op.TDResources)

def press():
    menu.CloseContextMenu()
    view.op('context_'+names[index]).interactMouse(.5,.5,left=True)
    run('args[0]()',release,delayFrames=3,delayRef=op.TDResources)

for name in names:view.op('context_'+name).interactClear()
menu.CloseContextMenu()
run('args[0]()',press,delayFrames=3,delayRef=op.TDResources)
