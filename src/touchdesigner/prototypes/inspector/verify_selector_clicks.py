"""Finite native virtual-mouse loop. Tests opening, not macOS click delivery."""
from pathlib import Path
import json

view=op('/inspector_below');menu=view.ext.InspectorView;controller=op('/inspector_model').par.Controller.eval()
key=controller.GetLayoutContext()['key'];session=op('/inspector_model').ext.InspectorModel.adapter.Session()
view.Show();menu.CloseContextMenu()
names=('Device','Layout','Track')*10;observations=[];index=0

def finish():
    menu.CloseContextMenu()
    for n in ('Device','Layout','Track'):view.op('context_'+n).interactClear()
    result=dict(virtual_mouse_only=True,macos_physical_click_delivery_verified=False,
                single_click_results=observations,all_opened_once=all(r['open'] and r['menu_name']==r['button'] for r in observations),
                routing_session_preserved=controller.GetLayoutContext()['key']==key and op('/inspector_model').ext.InspectorModel.adapter.Session()==session)
    Path(project.folder+'/prototypes/inspector/selector_click_verification.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(dict(samples=len(observations),all_opened_once=result['all_opened_once'],routing_session_preserved=result['routing_session_preserved'])))

def check():
    global index
    observations.append(dict(button=names[index],open=menu.ContextMenuOpen(),menu_name=menu._context_menu.details.get('name') if menu._context_menu else None))
    index+=1
    if index<len(names):click()
    else:finish()

def click():
    view.op('context_'+names[index]).interactMouse(.5,.5,leftClick=1)
    run('args[0]()',check,delayFrames=3,delayRef=op.TDResources)

click()
