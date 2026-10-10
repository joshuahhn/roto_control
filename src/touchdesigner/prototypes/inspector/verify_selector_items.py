"""Finite native menu-item clicks; not proof of physical macOS delivery.

Run in an isolated TD namespace. Browse existing alternatives only; restore the
Inspector context/follow flag and preserve the production routing/session.
"""
from pathlib import Path
import json

view=op('/inspector_below');u=view.ext.InspectorView
menu=view.op('container_context_menu');m=u._model;controller=m.ownerComp.par.Controller.eval()
saved_key=u.Key();saved_follow=u._follow_routing
active=m.ActiveContext();routing=controller.GetLayoutContext()['key'];session=m.adapter.Session()
names=('Device','Layout','Track')*10;rows=[];index=0

def finish():
    u.CloseContextMenu()
    for i in range(8):menu.op('row'+str(i)).interactClear()
    for name in ('Device','Layout','Track'):view.op('context_'+name).interactClear()
    u.ConfigureMenus(saved_key);u.OnContext();u._follow_routing=saved_follow;u.Refresh()
    result=dict(virtual_mouse_only=True,physical_item_selection_verified=False,
                samples=rows,all_selected_once=all(r['selected_once'] for r in rows),
                routing_session_preserved=controller.GetLayoutContext()['key']==routing and m.adapter.Session()==session)
    Path(project.folder+'/prototypes/inspector/selector_item_verification.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(dict(samples=len(rows),all_selected_once=result['all_selected_once'],routing_session_preserved=result['routing_session_preserved'])))

def check():
    global index
    result=rows[-1];result['actual']=view.par[names[index]].eval()
    result['selected_once']=result['actual']==result['expected'] and not u.ContextMenuOpen()
    index+=1
    if index<len(names):open_menu()
    else:finish()

def click_item():
    state=u._context_menu;choices=state.details['choices'];current=view.par[names[index]].eval()
    item,value=next((label,key) for label,key in choices.items() if key!=current)
    row=menu.op('row'+str(state.rows().index(item)))
    rows.append(dict(button=names[index],item=item,expected=value,menu_open_before_item=u.ContextMenuOpen(),menu_generation=u._menu_generation,model_generation=m.Stats()['generation']))
    row.interactMouse(.5,.5,left=True)
    run('args[0]()',lambda:release_item(row),delayFrames=3,delayRef=op.TDResources)

def release_item(row):
    row.interactMouse(.5,.5,left=False)
    run('args[0]()',check,delayFrames=3,delayRef=op.TDResources)

def open_menu():
    u.CloseContextMenu()
    for i in range(8):menu.op('row'+str(i)).interactClear()
    u.ConfigureMenus(active);u.OnContext();u._follow_routing=True;u.Refresh()
    view.op('context_'+names[index]).interactMouse(.5,.5,left=True)
    run('args[0]()',release_header,delayFrames=3,delayRef=op.TDResources)

def release_header():
    view.op('context_'+names[index]).interactMouse(.5,.5,left=False)
    run('args[0]()',click_item,delayFrames=5,delayRef=op.TDResources)

open_menu()
