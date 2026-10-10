"""Finite native Fold/Popup gestures on disconnected controller fixtures only."""
from pathlib import Path
import json,copy
m=op('/inspector_model');production=m.par.Controller.eval()
views=(op('/inspector_below'),op('/inspector_popup'))
saved=[(v.par.Presentation.eval(),v.ext.InspectorView.Key(),v.ext.InspectorView._follow_routing) for v in views]
before=production.GetControlCatalog();registry=copy.deepcopy(production.fetch('layout_registry'))
session=m.ext.InspectorModel.adapter.Session();routing=production.GetLayoutContext()['key']
result={};steps=[];index=0;holder=None;clone=None

def finish():
    try:
        for v in views:v.CloseEditor();v.op('window_editor').par.winclose.pulse();v.op('window_main').par.winclose.pulse()
        m.par.Controller=production;m.Sync();m.Flush()
        for v,(style,key,follow) in zip(views,saved):
            v.par.Presentation=style;u=v.ext.InspectorView;u.style=style;u._follow_routing=follow
            if not follow:u.ConfigureMenus(key);u.OnContext()
            v.Refresh()
        if holder:holder.destroy()
        views[0].Show()
        result['production_preserved']=production.GetControlCatalog()==before and production.fetch('layout_registry')==registry and production.GetLayoutContext()['key']==routing and m.ext.InspectorModel.adapter.Session()==session and production.State['Connected']
        result['two_subscribers']=m.Stats()['subscribers']==2
        result['no_errors']=not any(v.errors(recurse=True) for v in views)
        result['all_pass']=all(x for x in result.values() if type(x)is bool) and 'error' not in result
        Path(project.folder+'/prototypes/inspector/editor_dropdown_verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
    except Exception as error:print('Fixture restoration failed',str(error));raise

def step():
    global index
    try:
        if index>=len(steps):finish();return
        steps[index]();index+=1;run('args[0]()',step,delayFrames=3,delayRef=op.TDResources)
    except Exception as error:
        result['error']=str(error);finish();raise

try:
    holder=production.parent().create(baseCOMP,'base_inspector_dropdown_verification');holder.viewer=True;holder.nodeX=700;holder.nodeY=-700
    page=holder.appendCustomPage('Fixture');choice=page.appendMenu('Choice')[0]
    choice.menuNames=['a','b','c','d','e','f','g','h'];choice.menuLabels=['A','Same','Same','D','E','F','G','H'];choice.val='a'
    page.appendFloat('Amount');holder.par.Amount=.25
    clone=holder.copy(production,name='controller');clone.Disconnect();clone.par.Followcomp=False
    clone.op('registration').text="""def onRegister(controller):
    def changed(event):controller.store('fixture_events',controller.fetch('fixture_events',[])+[event])
    return controller.BindControls([dict(kind='knob',slot=1,id='fixture.menu',label='Menu',parameter=controller.parent().par.Choice),dict(kind='button',slot=1,id='fixture.callback',label='Callback',mode='toggle',button_type='toggle',on_change=changed)],group_id='dropdown.callback.fixture')
"""
    clone.par.Setupmode='callback';assert clone.Applybinding()
    menu_id='fixture.menu';button_id='fixture.callback'
    for v in views:v.CloseEditor();v.op('window_editor').par.winclose.pulse()
    m.par.Controller=clone;m.Sync();m.Flush()
    def add_view(v,style):
        box={};prefix=style+'_'
        def setup():
            v.par.Presentation=style;v.ext.InspectorView.style=style;v.Show();v.Action('slot0');u=v.ext.InspectorView
            box['u']=u;box['editor']=u._editors[0 if style=='below' else 1]
            box['root']=v if style=='below' else u._popup_host
            box['window']=v.op('window_main' if style=='below' else 'window_editor')
        def capture():
            win=box['window'];box['size']=(win.contentWidth,win.contentHeight);box['opens']=box['u']._window_opens
            box['editor_height']=box['editor'].height;box['corner']=(win.x,win.y+win.height)
            box['editor'].op('value_menu').interactMouse(.5,.5,left=True)
        def release_value():box['editor'].op('value_menu').interactMouse(.5,.5,left=False)
        def check_menu():
            u=box['u'];p=u._menu_panel;win=box['window']
            result[prefix+'first_release_opens']=u.ContextMenuOpen() and u._context_menu.details['name']=='Value'
            result[prefix+'in_existing_root']=u._menu_root==box['root'] and p.parent()==box['editor']
            result[prefix+'geometry_fits']=0<=p.y and p.y+p.height<=box['editor'].height and p.width<=box['editor'].width
            result[prefix+'opens_down']=p.y+p.height+2<=box['editor'].op('value_menu').y
            result[prefix+'editor_grows_for_menu']=box['editor'].height==box['editor_height']+92 and u._context_menu.capacity==4
            result[prefix+'four_rows_and_footer']=sum(p.op('row'+str(i)).par.display.eval() for i in range(8))==4 and p.op('base_footer').par.display.eval()
            u.PageContextMenu(1)
            result[prefix+'remaining_options_reachable']=u._context_menu.first==4 and p.op('row3/text_label').par.text.eval()=='H [7]'
            u.PageContextMenu(-1)
            growth=u._menu_window_extra if style=='popup' else 0
            result[prefix+'width_corner_and_open_count_preserved']=box['size'][0]==win.contentWidth and box['size'][1]+growth==win.contentHeight and box['corner']==(win.x,win.y+win.height) and box['opens']==u._window_opens
            result[prefix+'resource_menu_closed']=not op.TDResources.op('popMenu').IsOpen
            p.op('row1').interactMouse(.5,.5,left=True);box['row']=p.op('row1')
        def value_up():box['row'].interactMouse(.5,.5,left=False)
        def after_value():
            result[prefix+'single_item_press_live_value']=not box['u'].ContextMenuOpen() and holder.par.Choice.eval()=='b'
            result[prefix+'collapse_restores_size']=box['editor'].height==box['editor_height'] and box['size']==(box['window'].contentWidth,box['window'].contentHeight)
            box['editor'].op('value_menu').interactClear();box['row'].interactClear()
            holder.par.Choice='a';m.Sync();m.Flush();v.CloseEditor();v.Action('slot8');v.Action('mapping_toggle')
        def mode_down():
            box['size']=(box['window'].contentWidth,box['window'].contentHeight)
            box['mapping_before']=clone.GetControlState(button_id)
            box['editor'].op('container_mapping/choice_mode').interactMouse(.5,.5,left=True)
        def mode_up():box['editor'].op('container_mapping/choice_mode').interactMouse(.5,.5,left=False)
        def select_mode():
            u=box['u'];result[prefix+'mode_first_release_opens']=u.ContextMenuOpen() and u._context_menu.details['name']=='Mode'
            box['row']=u._menu_panel.op('row1');box['row'].interactMouse(.5,.5,left=True)
        def row_up():box['row'].interactMouse(.5,.5,left=False)
        def check_mode():
            u=box['u'];result[prefix+'mode_draft_only']=not u.ContextMenuOpen() and u._draft.par.Mapmode.eval()=='pulse' and clone.GetControlState(button_id)==box['mapping_before']
            box['row'].interactClear();box['editor'].op('container_mapping/choice_mode').interactClear()
            box['editor'].op('container_mapping/choice_input').interactMouse(.5,.5,left=True)
        def input_up():box['editor'].op('container_mapping/choice_input').interactMouse(.5,.5,left=False)
        def select_input():
            u=box['u'];result[prefix+'input_first_release_opens']=u.ContextMenuOpen() and u._context_menu.details['name']=='HW Type'
            box['row']=u._menu_panel.op('row1');box['row'].interactMouse(.5,.5,left=True)
        def check_input():
            u=box['u'];result[prefix+'input_draft_only']=not u.ContextMenuOpen() and u._draft.par.Mapinput.eval()=='push' and clone.GetControlState(button_id)==box['mapping_before']
            result[prefix+'mapping_menu_size_preserved']=box['size']==(box['window'].contentWidth,box['window'].contentHeight)
            box['row'].interactClear();box['editor'].op('container_mapping/choice_input').interactClear()
            v.Action('mapping_cancel');v.CloseEditor()
        def tall_window():
            if style=='popup':box['window'].par.winh=342
        def full_menu():
            if style=='popup':box['u'].OpenValueMenu()
        def check_full():
            if style=='popup':
                u=box['u'];p=u._menu_panel
                result[prefix+'tall_window_shows_all']=u._context_menu.capacity==8 and sum(p.op('row'+str(i)).par.display.eval() for i in range(8))==8 and not p.op('base_footer').par.display.eval()
                result[prefix+'full_menu_uses_existing_height']=u._menu_window_extra==0 and box['window'].contentHeight==342 and p.y+p.height<=box['editor'].op('value_menu').y
                u.CloseContextMenu();box['window'].par.winh=box['size'][1]
        steps.extend([setup,capture,release_value,check_menu,value_up,tall_window,full_menu,check_full,after_value,mode_down,mode_up,select_mode,row_up,check_mode,input_up,select_input,row_up,check_input])
    add_view(views[0],'below');add_view(views[1],'popup');step()
except Exception as error:
    result['error']=str(error);finish();raise
