"""Finite in-window dropdown paging, dismissal and stale-selection checks."""
from pathlib import Path
import json
view=op('/inspector_below');u=view.ext.InspectorView;m=u._model
Dropdown=view.op('context_menu').module.Dropdown
panel=view.op('container_context_menu');controller=m.ownerComp.par.Controller.eval()
saved_key=u.Key();saved_follow=u._follow_routing;catalog=controller.GetControlCatalog()
routing=controller.GetLayoutContext()['key'];session=m.adapter.Session()
size=(view.op('window_main').contentWidth,view.op('window_main').contentHeight)
count=len(view.findChildren());result={};stage=0

def finish():
    u.CloseContextMenu();view.interactClear();panel.interactClear()
    for name in ('next','previous'):panel.op('base_footer/'+name).interactClear()
    u.ConfigureMenus(saved_key);u.OnContext();u._follow_routing=saved_follow;u.Refresh()
    result['window_size_preserved']=size==(view.op('window_main').contentWidth,view.op('window_main').contentHeight)
    result['routing_session_catalog_preserved']=controller.GetLayoutContext()['key']==routing and m.adapter.Session()==session and controller.GetControlCatalog()==catalog
    result['operator_count_preserved']=len(view.findChildren())==count
    result['all_pass']=all(value for value in result.values() if type(value)is bool) and 'error' not in result
    Path(project.folder+'/prototypes/inspector/inline_menu_verification.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result))

def step():
    global stage
    try:
        if stage==0:u.OpenContextMenu('Device')
        elif stage==1:
            result['same_panel_root']=panel.panelRoot==view
            result['no_resource_menu_window']=not op.TDResources.op('popMenu').IsOpen
            view.interactMouse(.05,.96,leftClick=1)
            result['outside_click_closes']=not u.ContextMenuOpen();view.interactClear()
            u.OpenContextMenu('Device')
        elif stage==2:
            # Native focus ownership updates on the next frame after reload.
            # Wait before reading the keyboard expression or sending Escape.
            view.setFocus()
        elif stage==3:
            keyboard=panel.op('keyboard_escape')
            result['escape_listener_scoped']=keyboard.par.active.eval()
            keyboard.par.callbacks.eval().module.onKey(keyboard,'esc',chr(27),False,False,False,False,False,False,False,False,False,True,0)
            result['escape_closes']=not u.ContextMenuOpen() and not keyboard.par.active.eval()
            u.OpenContextMenu('Device');details=u._context_menu.details
            u._context_menu=Dropdown(tuple('Fixture '+str(i) for i in range(17)),details)
            u._render_context_menu()
            result['eight_rows']=sum(panel.op('row'+str(i)).par.display.eval() for i in range(8))==8
        elif stage==4:
            # interactMouse(wheel=...) did not emit a wheel panel event in this
            # TD build. Exercise the actual Panel Execute boundary instead;
            # this checks the callback, not physical mouse-wheel delivery.
            panel.panel.wheel=0;panel.panel.wheel=-1
        elif stage==5:
            result['first_after_wheel']=u._context_menu.first
            result['native_wheel_callback']=u._context_menu.first==1
            panel.op('base_footer/next').interactMouse(.5,.5,leftClick=1)
        elif stage==6:
            result['first_after_page']=u._context_menu.first
            result['native_page']=u._context_menu.first==9 and panel.op('row0/text_label').par.text.eval()=='Fixture 9'
            panel.op('base_footer/previous').interactMouse(.5,.5,leftClick=1)
        elif stage==7:
            result['first_after_previous']=u._context_menu.first
            result['previous_page']=u._context_menu.first==1
            u.CloseContextMenu();u.OpenContextMenu('Device');u._menu_generation+=1
            result['stale_callback_rejected']=not u.SelectContextItem(0) and not u.ContextMenuOpen()
            u.OpenContextMenu('Device');u.Disconnect()
            result['disconnect_closes']=not u.ContextMenuOpen();u.Connect()
        else:finish();return
        stage+=1;run('args[0]()',step,delayFrames=3,delayRef=op.TDResources)
    except Exception as error:
        result['error']=str(error);finish();raise
step()
