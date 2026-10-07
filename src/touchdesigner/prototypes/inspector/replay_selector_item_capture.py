"""Replay captured native callback ordering, not the macOS input system.

Run against historical floating-menu checkpoint .19/.20, not the current inline UI.
This reproduces the missing first selection at the Lister seam. It cannot
validate whether a header timing change fixes physical event delivery.
"""
from pathlib import Path
import json

view=op('/inspector_below');u=view.ext.InspectorView;m=u._model
menu=op.TDResources.op('popMenu');native=menu.op('lister').ext.ListerExt
saved_key=u.Key();saved_follow=u._follow_routing
controller=m.ownerComp.par.Controller.eval();routing=controller.GetLayoutContext()['key'];session=m.adapter.Session()
events=json.loads(Path(project.folder+'/prototypes/inspector/selector_item_capture.json').read_text())['events']
gesture=[e for e in events if e['kind']=='native_list_selection'][:4]
assert [(e['data']['start'],e['data']['end']) for e in gesture]==[(False,True),(True,False),(True,False),(False,True)]
accepted=[];had_override='SelectContextMenu' in vars(u);previous=vars(u).get('SelectContextMenu');original=u.SelectContextMenu
def callback(info):
    result=original(info);accepted.append(bool(result));return result
u.SelectContextMenu=callback
u.ConfigureMenus(m.ActiveContext());u.OnContext();u.OpenContextMenu('Device')

def finish():
    try:
        lister=menu.op('lister');lister.interactMouse(.5,.75)
        for i,event in enumerate(gesture):
            d=event['data'];lister.panel.click=d['click']
            native.onSelect(d['startrow'],d['startcol'],(.5,.5),d['endrow'],d['endcol'],(.5,.5),d['start'],d['end'])
            if i==1:first=dict(menu_open=menu.IsOpen,accepted_callbacks=len(accepted))
        result=dict(source='selector_item_capture.json',native_callback_replay_only=True,
                    first_gesture=first,second_gesture=dict(menu_open=menu.IsOpen,accepted_callbacks=len(accepted)),
                    missing_first_selection_reproduced=first['menu_open'] and first['accepted_callbacks']==0 and accepted==[True],
                    physical_timing_fix_verified=False)
    finally:
        menu.CloseAll();menu.op('lister').interactClear()
        if had_override:u.SelectContextMenu=previous
        else:delattr(u,'SelectContextMenu')
        u.ConfigureMenus(saved_key);u.OnContext();u._follow_routing=saved_follow;u.Refresh()
    result['routing_session_preserved']=controller.GetLayoutContext()['key']==routing and m.adapter.Session()==session
    Path(project.folder+'/prototypes/inspector/selector_item_replay.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result))
run('args[0]()',finish,delayFrames=3,delayRef=op.TDResources)
