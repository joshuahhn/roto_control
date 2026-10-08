"""Compact views over a shared demo or real controller catalog."""
from time import monotonic
from collections import Counter
from editor_state import MappingDraft
from parity import ClearRequest,filter_choices,visible_slots,detail_groups
from context_menu import Dropdown,placement_for,editor_space_for
ROW=26
EDITOR=178
MAPPING=134
PICKER=250
DETAILS=224
BASE=(.085,.085,.085)
SURFACE=(.12,.12,.12)
ACCENT=(.76,.76,.76)
TEXT=(.86,.86,.86)
MUTED=(.50,.50,.50)
FIELDS=('Label','Destination','Minimum','Maximum','Value')
ICON_FONT='Material Design Icons'
# Codepoints from TD's bundled MaterialDesignIconsMeta.json.
ICONS=dict(ping='\U000f0003',clear='\U000f0b5c',cancel='\U000f0156',apply='\U000f012c',confirm='\U000f0625')

def action_icon(label,name):
    label.par.font=ICON_FONT
    label.par.text=ICONS[name]
    label.par.fontsize=15
    label.par.fontsizeunits='panelunits'
    label.par.alignx=label.par.aligny='center'

def paint(o,rgb):o.par.bgcolorr,o.par.bgcolorg,o.par.bgcolorb=rgb

def ink(o,rgb):o.par.fontcolorr,o.par.fontcolorg,o.par.fontcolorb=rgb

def popup_host(view):return view.op('base_popup/editor_popup') or view.op('editor_popup')

class InspectorView:
    def __init__(self,ownerComp):
        self.ownerComp=ownerComp
        self.style=ownerComp.par.Presentation.eval()
        self.selected=None
        self._model=None
        self._context=None
        self._token=None
        self._original=None
        self._identity=ownerComp.id
        self._display={}
        self._dirty=65535
        self._metadata_dirty=65535
        self._notifications=0
        self._writes=0
        self._window_opens=0
        self._error=''
        self._clear_pending=None
        self._editor_display=None
        self._main_message=None
        self._mapping=MappingDraft()
        self._picker=None
        self._filter='all'
        self._details_open=False
        self._details_display=None
        self._diagnostics=None
        self._clear_device_request=None
        self._device_message=''
        self._picker_generation=0
        self._menu_generation=0
        self._context_menu=None
        self._menu_panel=None
        self._menu_root=None
        self._menu_callback=None
        self._menu_extra=0
        self._menu_window_extra=0
        self._value_scope=None
        self._value_type=None
        self._popup_extra=0
        self._popup_size_pending=False
        self._popup_geometry=None
        self._popup_geometry_settle=None
        self._popup_geometry_generation=0
        self._follow_routing=True
        self._configuring=False
        self._rows=ownerComp.op('container_scroll/container_content')
        self._viewport=ownerComp.op('container_scroll')
        self._draft=ownerComp.op('base_draft')
        self._main=ownerComp.op('window_main')
        self._popup=ownerComp.op('window_editor')
        popup=popup_host(ownerComp)
        self._popup_host=popup
        self._editors=(self._rows.op('editor_below'),popup.op('container_editor_content') or popup)
        self._row_refs=[dict(row=self._rows.op('slot'+str(i)),name=self._rows.op('slot'+str(i)+'/text_name'),value=self._rows.op('slot'+str(i)+'/text_value'),slot=self._rows.op('slot'+str(i)+'/text_slot'),arrow=self._rows.op('slot'+str(i)+'/text_arrow')) for i in range(16)]
        for editor in self._editors:
            for name in ('ping','clear','cancel','apply'):
                if editor.op(name):action_icon(editor.op(name+'/text_label'),name)
            for name,icon in [('mapping_cancel','cancel'),('mapping_apply','apply')]:
                label=editor.op('container_mapping/'+name+'/text_label')
                if label:action_icon(label,icon)
        self.Connect()

    def Key(self):return tuple(self.ownerComp.par[n].eval() for n in ('Layout','Track','Device'))

    def _filter_info(self):return tuple(self._model.Info(self._context,i) for i in range(16))
    def _visible_slots(self):
        return visible_slots(self._filter_info(),getattr(self,'_filter','all')) if self.IsLive() else tuple(range(16))
    def _normalize_filter(self):
        if not self.IsLive():return
        previous=getattr(self,'_filter','all')
        if previous not in dict(filter_choices(self._filter_info())):
            self._filter='all'
        if self.selected is not None and self.selected not in self._visible_slots():self.CloseEditor()
        elif previous!=self._filter or self._filter!='all':self._editor_layout()
        self._update_filter()
    def _update_filter(self):
        if not self.ownerComp.op('clear_device'):return
        choices=dict(filter_choices(self._filter_info())) if self.IsLive() else {'all':'All controls'}
        label=choices.get(getattr(self,'_filter','all'),'All controls')
        if label.startswith('/'):label=label.rsplit('/',1)[-1]
        self.ownerComp.op('text_footer').par.text=label+' ▾'
        self.ownerComp.op('clear_device').par.enable=self.IsLive()
    def OpenFilter(self):
        if not self.IsLive():return False
        choices=filter_choices(self._filter_info())
        items=[label+' ['+str(i)+']' for i,(key,label) in enumerate(choices)]
        self._menu_generation+=1
        details=dict(context=self._context,generation=self._menu_generation,choices=dict(zip(items,(key for key,label in choices))))
        op.TDResources.op('popMenu').Open(items=items,callback=self.SelectFilter,callbackDetails=details,autoClose=1)
        return True
    def SelectFilter(self,info):
        if self.Key()!=self._context:self.Refresh();return False
        d=info.get('details',{});choice=d.get('choices',{}).get(info.get('item'))
        if d.get('context')!=self._context or d.get('generation')!=self._menu_generation:return False
        if choice not in dict(filter_choices(self._filter_info())):return False
        self.CloseEditor();self._filter=choice;self._device_message='';self._menu_generation+=1
        self._editor_layout();self._update_main_status();return True
    def RequestClearDevice(self):
        if not self.IsLive():return False
        if self.Key()!=self._context:self.Refresh();return False
        try:
            confirmation=self._model.PrepareClearDevice(self._context)
            self._clear_device_request=ClearRequest(confirmation)
            self._menu_generation+=1
            labels=[]
            for name,index in [('Layout',0),('Track',1),('Device',2)]:labels.append(dict(self._model.Choices(name,self._context)).get(self._context[index],self._context[index]))
            label='Clear '+str(len(confirmation['ids']))+' registrations · '+' / '.join(labels)
            details=dict(generation=self._menu_generation,request=self._clear_device_request,label=label)
            op.TDResources.op('popMenu').Open(items=['Cancel',label],callback=self.ConfirmClearDevice,callbackDetails=details,autoClose=1)
            return True
        except (ValueError,RuntimeError) as error:self._device_message=str(error);self._update_main_status();return False
    def ConfirmClearDevice(self,info):
        if self.Key()!=self._context:self.Refresh();return False
        d=info.get('details',{});request=getattr(self,'_clear_device_request',None)
        if request is None or d.get('request') is not request or d.get('generation')!=self._menu_generation:return False
        self._clear_device_request=None;self._menu_generation+=1
        if info.get('item')!=d.get('label'):return False
        try:
            confirmation=request.Consume()
            result=self._model.ClearDevice(self._context,confirmation)
            self.CloseEditor()
            self._device_message='Removed '+str(len(result['removed']))+' · '+str(len(result['remaining']))+' remain'+(' · '+result['error'] if result['error'] else '')
            self._update_main_status();return not bool(result['error'] or result['remaining'])
        except (ValueError,RuntimeError) as error:self._device_message=str(error);self._update_main_status();return False
    def _update_details(self):
        if not getattr(self,'_details_open',False) or self.selected is None or not self.IsLive():return
        info=self._model.Info(self._context,self.selected);status=self._model.Status
        def labels(key):
            return tuple(dict(self._model.Choices(n,key)).get(key[i],str(key[i])) for i,n in enumerate(('Layout','Track','Device')))
        active=tuple(status.get('Active') or self._model.ActiveContext())
        route=labels(active)
        selected_key=(active[0],status.get('SelectedTrack') or active[1],status.get('SelectedDevice') or active[2])
        try:selected=labels(selected_key)[1:]
        except (ValueError,RuntimeError):selected=tuple(str(n) for n in selected_key[1:])
        groups=detail_groups(info,self._model.Health(self._context,self.selected),status,self._diagnostics,labels(self._context),route,selected,self._follow_routing)
        fresh=self._token==self._model.GetToken(self._context,self.selected)
        reveal=bool(info.get('parameter') and not status.get('Follow') and fresh)
        repair=self._model.Capabilities(self._context,self.selected)['assign']['enabled']
        signature=(groups,reveal,repair)
        if getattr(self,'_details_display',None)==signature:return
        self._details_display=signature
        message='\n'.join(title+'\n'+'\n'.join(label+'  '+value for label,value,kind in rows) for title,rows in groups)
        for editor in self._editors:
            section=editor.op('container_details')
            if not section:continue
            if section.op('text_details').par.text.eval()!=message:section.op('text_details').par.text=message
            content=section.op('container_readout/container_info')
            if content:
                total=sum(18+sum(48 if kind=='long' else 18 for label,value,kind in rows)+6 for title,rows in groups)
                content.par.h=total
                top=total
                for g,(title,rows) in enumerate(groups):
                    group=content.op('group'+str(g));height=18+sum(48 if kind=='long' else 18 for label,value,kind in rows)
                    group.par.y=top-height;group.par.h=height;top-=height+6
                    group.op('text_heading').par.y=height-18
                    y=height-18
                    for i in range((3,5,6)[g]):
                        label_node=group.op('label'+str(i));value_node=group.op('value'+str(i));shown=i<len(rows)
                        label_node.par.display=value_node.par.display=shown
                        if not shown:value_node.par.text='';continue
                        label,value,kind=rows[i];h=48 if kind=='long' else 18;y-=h
                        label_node.par.y=y+h-12 if kind=='long' else y;label_node.par.h=12 if kind=='long' else h
                        value_node.par.y=y;value_node.par.h=h-14 if kind=='long' else h
                        value_node.par.leftoffset=12 if kind=='long' else 92
                        label_node.par.text=label
                        if value_node.par.text.eval()!=value:value_node.par.text=value
                        value_node.par.fontsize=10 if kind=='long' else 11
            section.op('reveal').par.enable=reveal
            section.op('repair').par.enable=repair

    def Connect(self):
        self.Disconnect()
        self._value_scope=None
        self._mapping.Close();self._menu_generation+=1
        self._clear_device_request=None;self._device_message=''
        component=self.ownerComp.par.Model.eval()
        if not component:
            self.ownerComp.op('text_status').par.text='Load the shared model first'
            return False
        self._model=component.ext.InspectorModel
        if self.IsLive():self.ConfigureMenus(self._model.ActiveContext())
        self._context=self.Key()
        self._model.Subscribe(self._identity,self._context,self.OnModelChange)
        self.selected=None;self._token=None;self._original=None;self._display={}
        self._clear_pending=None
        self.Refresh()
        return True

    def IsLive(self):return bool(self._model and getattr(self._model,'IsLive',False))

    def ConfigureMenus(self,preferred=None):
        if not self.IsLive():return
        self._configuring=True
        try:
            desired=tuple(preferred or self.Key())
            key=list(desired)
            for i,n in enumerate(('Layout','Track','Device')):
                choices=self._model.Choices(n,tuple(key))
                names=[name for name,label in choices];labels=[label for name,label in choices]
                p=self.ownerComp.par[n]
                if list(p.menuNames)!=names:p.menuNames=names
                if list(p.menuLabels)!=labels:p.menuLabels=labels
                value=desired[i] if desired[i] in names else names[0]
                p.val=value;key[i]=value
        finally:self._configuring=False

    def HideOtherViews(self):
        if not self.IsLive():return
        for other in self.ownerComp.parent().ops('inspector_below','inspector_popup'):
            if other==self.ownerComp:continue
            popup=other.op('window_editor');main=other.op('window_main')
            close=getattr(other,'CloseContextMenu',None)
            if close:close()
            if popup and popup.isOpen:popup.par.winclose.pulse()
            if main and main.isOpen:main.par.winclose.pulse()

    def Show(self):
        self.HideOtherViews();self.CloseContextMenu();self.CloseEditor()
        if not self._main.isOpen:self._main.par.winopen.pulse()
        self.Refresh()

    def Disconnect(self):
        self.CloseContextMenu()
        self.ClosePicker()
        if getattr(self,'_popup_extra',0):self._sync_popup_expansion(0)
        self._cancel_popup_geometry()
        if self._model:self._model.Unsubscribe(self._identity,self.OnModelChange)
        self._model=None

    def OpenContextMenu(self,name):
        if name not in ('Layout','Track','Device'):return False
        if self.IsLive():self.ConfigureMenus(self.Key())
        p=self.ownerComp.par[name];names=list(p.menuNames);labels=list(p.menuLabels)
        counts=Counter(labels)
        items=[label if counts[label]==1 else label+' ('+str(i+1)+')' for i,label in enumerate(labels)]
        self._menu_generation+=1
        details=dict(generation=self._menu_generation,context=self.Key(),model_generation=self._model.Stats()['generation'],name=name,choices=dict(zip(items,names)))
        checked=[items[names.index(p.eval())]] if p.eval() in names else []
        # Header choices stay inside the existing Inspector window. Native
        # popMenu Window capture dropped first-item releases on this macOS TD.
        return self.OpenInlineMenu(items,self.SelectContextMenu,details,checked,self.ownerComp,self.ownerComp.op('context_'+name))

    def OpenInlineMenu(self,items,callback,details,checked,host,anchor):
        self.CloseContextMenu()
        panel=host.op('container_context_menu')
        if not panel or not items:return False
        # Native y includes anchors. Editor menus always open down; add only
        # the missing space, keeping the controls at the same distance from top.
        node=anchor;parts=[]
        while node!=host:
            parts.insert(0,node.name);node=node.parent()
        terms=['parent().op(%r).y'%('/'.join(parts[:i+1])) for i in range(len(parts))]
        bottom=0;node=anchor
        while node!=host:bottom+=node.y;node=node.parent()
        if host!=self.ownerComp:
            # A manually taller Popup can show every pooled option without
            # growing its Window. Compact windows retain four-row paging.
            viewport=self._popup_host if self.style=='popup' else self._viewport
            geometry=getattr(self,'_popup_geometry',None)
            viewport_height=geometry['height'] if self.style=='popup' and geometry else viewport.height
            available=bottom+max(0,viewport_height-host.height)
            direction='below';self._menu_extra,capacity=editor_space_for(bottom,len(items),available)
            self._menu_window_extra=max(0,host.height+self._menu_extra-viewport_height) if self.style=='popup' else 0
            if self._menu_extra:self._editor_layout()
        else:direction,capacity=placement_for(bottom,bottom+anchor.height,host.height,len(items))
        self._menu_panel=panel;self._menu_callback=callback
        self._menu_root=self.ownerComp if host==self.ownerComp or host==self._editors[0] else self._popup_host
        self._context_menu=Dropdown(items,details,checked,capacity)
        position='+'.join(terms)
        panel.par.y.expr=('max(2,('+position+')-me.height-2)' if direction=='below' else
                          'min(parent().height-me.height-2,('+position+')+parent().op(%r).height+2)'%'/'.join(parts))
        panel.par.display=True;self._render_context_menu()
        return True

    def OpenEditorMenu(self,items,callback,details,checked,anchor_path):
        editor=self._editors[0 if self.style=='below' else 1]
        return self.OpenInlineMenu(items,callback,details,checked,editor,editor.op(anchor_path))

    def CloseContextMenu(self):
        self._context_menu=None
        panel=getattr(self,'_menu_panel',None) or self.ownerComp.op('container_context_menu')
        self._menu_panel=None;self._menu_callback=None
        self._menu_root=None
        if panel:
            panel.par.display=False
            for i in range(8):
                panel.op('row'+str(i)+'/text_label').par.text=''
                panel.op('row'+str(i)+'/text_check').par.display=False
            panel.op('base_footer/text_count').par.text=''
        if getattr(self,'_menu_extra',0):
            self._menu_extra=0;self._menu_window_extra=0;self._editor_layout()

    def ContextMenuOpen(self):return self._context_menu is not None

    def ContextMenuOutsideClick(self,host=None):
        panel=getattr(self,'_menu_panel',None)
        if self._context_menu and panel and (host is None or host==self._menu_root) and not panel.panel.inside:self.CloseContextMenu()

    def ContextMenuFocusLost(self,host):
        panel=getattr(self,'_menu_panel',None)
        if self._context_menu and panel and host==self._menu_root:self.CloseContextMenu()

    def MenuFocus(self):return bool(self._context_menu and self._menu_root.panel.focusselect)

    def ContextMenuEscape(self):
        panel=getattr(self,'_menu_panel',None)
        if panel and self.MenuFocus():self.CloseContextMenu()

    def ScrollContextMenu(self,delta):
        if self._context_menu and delta:
            if self._context_menu.move(-1 if delta>0 else 1):self._render_context_menu()

    def PageContextMenu(self,direction):
        if self._context_menu and self._context_menu.move(direction*self._context_menu.capacity):self._render_context_menu()

    def SelectContextItem(self,slot):
        state=self._context_menu
        if state is None:return False
        try:item=state.item(slot)
        except ValueError:return False
        callback=getattr(self,'_menu_callback',None) or self.SelectContextMenu
        self.CloseContextMenu()
        return callback(dict(item=item,details=state.details))

    def _render_context_menu(self):
        state=self._context_menu;panel=self._menu_panel
        rows=state.rows();paged=len(state.items)>state.capacity
        footer=24 if paged else 0
        panel.par.h=4+24*len(rows)+footer
        for i in range(8):
            row=panel.op('row'+str(i));row.par.display=i<len(rows)
            if i<len(rows):
                row.par.y=panel.par.h.eval()-2-(i+1)*24
                row.op('text_label').par.text=rows[i]
                row.op('text_check').par.display=rows[i] in state.checked
        panel.op('base_footer').par.display=paged
        panel.op('base_footer/text_count').par.text=state.count_label() if paged else ''
        panel.op('base_footer/previous').par.enable=state.first>0
        panel.op('base_footer/next').par.enable=state.first+state.capacity<len(state.items)

    def SelectContextMenu(self,info):
        details=info.get('details',{});value=details.get('choices',{}).get(info.get('item'))
        self.CloseContextMenu()
        if not self._model or details.get('generation')!=self._menu_generation or details.get('context')!=self.Key() or details.get('model_generation')!=self._model.Stats()['generation']:return False
        name=details['name']
        try:choices=self._model.Choices(name,self.Key())
        except (ValueError,RuntimeError):return False
        if value is None or value not in [key for key,label in choices]:return False
        self._menu_generation+=1;self._follow_routing=False
        self.ownerComp.par[name].val=value;self.OnContext();return True

    def _mapping_values(self):
        return dict(minimum=self._draft.par.Mapminimum.eval(),maximum=self._draft.par.Mapmaximum.eval(),mode=self._draft.par.Mapmode.eval(),button_type=self._draft.par.Mapinput.eval() or None)

    def _update_typed_value(self,caps,stale):
        if self.selected is None or not self.IsLive():return
        schema=self._model.ValueSchema(self._context,self.selected)
        value=self._model.GetCatalog(self._context)[self.selected]['Value']
        enabled=bool(caps and caps['value']['enabled'] and not stale)
        for e in self._editors:
            if not e.op('value_menu'):continue
            field=e.op('field_Value');kind=schema['kind']
            input_type=getattr(self,'_value_type',None) or ('int' if kind=='integer' else 'float')
            field.par.type='integer' if input_type=='int' else 'float'
            numeric=kind in ('float','integer')
            choice=e.op('value_type')
            if choice:
                choice.par.display=numeric;choice.par.enable=numeric and not stale
                choice.op('text_label').par.text=('Int' if input_type=='int' else 'Float')+' ↔'
                field.par.rightoffset=-66 if numeric else -12
            field.par.display=kind not in ('menu','toggle')
            field.par.editmode='editablecontinuous' if enabled else 'selectonly'
            for name in ('menu','toggle'):
                widget=e.op('value_'+name);widget.par.display=kind==name;widget.par.enable=enabled
                label=(schema['labels'][int(value)] if 0<=int(value)<len(schema['labels']) else 'Unavailable') if name=='menu' else ('ON' if value else 'OFF')
                widget.op('text_label').par.text=label+(' ▾' if name=='menu' else '')
            e.op('field_Destination').par.enable=bool(caps['assign']['enabled'] and not stale)

    def TypedValue(self,value):
        if self.selected is None or not self.IsLive() or self.Key()!=self._context:return False
        values=dict(self._model.GetCatalog(self._context)[self.selected]);values['Value']=value
        try:
            changed=self._model.Commit(self._context,self.selected,values,self._token)
            self._draft.par.Value=self._model.GetCatalog(self._context)[self.selected]['Value']
            self._disarm_clear();self._error='';self._update_editor(force=True)
            return changed
        except (ValueError,RuntimeError) as error:self._set_error(str(error));return False

    def CycleValueType(self):
        if self.selected is None or not self.IsLive():return False
        schema=self._model.ValueSchema(self._context,self.selected)
        if schema['kind'] not in ('float','integer'):return False
        current=getattr(self,'_value_type',None) or ('int' if schema['kind']=='integer' else 'float')
        details=dict(context=self._context,slot=self.selected,token=self._token,generation=self._menu_generation)
        return self.SelectValueType(dict(item='Float' if current=='int' else 'Int',details=details))

    def SelectValueType(self,info):
        d=info.get('details',{});choice=str(info.get('item','')).lower()
        if choice not in ('float','int') or not self._model:return False
        if (d.get('context'),d.get('slot'),d.get('token'),d.get('generation'))!=(self._context,self.selected,self._token,self._menu_generation):return False
        self._model.Inspect(self._context,self.selected)
        if self._token!=self._model.GetToken(self._context,self.selected) or self._model.ValueSchema(self._context,self.selected)['kind'] not in ('float','integer'):return False
        # Presentation/input preference only. Never coerce or write the target
        # just because a different numeric editor was chosen.
        self._menu_generation+=1;self._value_scope=None;self._value_type=choice
        self._draft.par.Value=self._model.GetCatalog(self._context)[self.selected]['Value']
        self._disarm_clear();self._error='';self._update_editor(force=True)
        return True

    def OpenValueMenu(self):
        if self.selected is None or not self.IsLive():return False
        self._model.Inspect(self._context,self.selected)
        schema=self._model.ValueSchema(self._context,self.selected)
        if schema['kind']!='menu' or schema['reason'] or self._token!=self._model.GetToken(self._context,self.selected):return False
        labels=list(schema['labels']);items=[label+' ['+str(i)+']' for i,label in enumerate(labels)]
        self._menu_generation+=1
        details=dict(name='Value',context=self._context,slot=self.selected,token=self._token,generation=self._menu_generation,signature=(schema['names'],schema['labels']),choices=dict(zip(items,range(len(items)))))
        value=int(self._model.GetCatalog(self._context)[self.selected]['Value'])
        return self.OpenEditorMenu(items,self.SelectValueMenu,details,[items[value]] if 0<=value<len(items) else [],'value_menu')

    def SelectValueMenu(self,info):
        d=info.get('details',{})
        if not self._model or (d.get('context'),d.get('slot'),d.get('token'),d.get('generation'))!=(self._context,self.selected,self._token,self._menu_generation):return False
        self._model.Inspect(self._context,self.selected)
        schema=self._model.ValueSchema(self._context,self.selected)
        if d.get('signature')!=(schema['names'],schema['labels']):return False
        value=d.get('choices',{}).get(info.get('item'))
        if value is None:return False
        self._menu_generation+=1
        return self.TypedValue(value)

    def ClosePicker(self):
        if getattr(self,'_picker',None) and self._model:self._model.TargetCancel(self._identity)
        self._picker=None
        self._picker_generation=getattr(self,'_picker_generation',0)+1
        for editor in getattr(self,'_editors',()):
            section=editor.op('container_picker')
            if not section:continue
            section.par.display=False
            for name in ('text_count','text_status'):section.op(name).par.text=''
            section.op('assign').par.enable=False
            for i in range(6):
                section.op('row'+str(i)).par.display=False
                section.op('row'+str(i)+'/text_label').par.text=''

    def OpenPicker(self):
        if self.selected is None or not self.IsLive():return False
        capability=self._model.Capabilities(self._context,self.selected)['assign']
        if not capability['enabled']:self._set_error(capability['reason']);return False
        if self._token!=self._model.GetToken(self._context,self.selected):self._set_error('Mapping changed; reopen this control');return False
        if self._picker:
            self.ClosePicker();self._editor_layout();return True
        self._mapping.Close();self._details_open=False;self._disarm_clear();self._value_scope=None
        self._draft.par.Pickscope=self._model.TargetScope();self._draft.par.Pickquery=''
        self._picker=dict(rows=(),filtered=(),visible=(),page=0,chosen=None,message='Searching…',truncated=False)
        self._editor_layout()
        return self.SearchTargets()

    def SearchTargets(self,refresh=False):
        if not self._picker:return False
        self._picker_generation+=1
        scope=(self._context,self.selected,self._token,self._picker_generation)
        self._picker.update(rows=(),filtered=(),visible=(),page=0,chosen=None,message='Searching…')
        self._update_picker()
        def complete(rows,truncated,error):
            if not self._picker or scope!=(self._context,self.selected,self._token,self._picker_generation):return
            self._picker.update(rows=rows,truncated=truncated,message=error)
            self.PickerQuery(self._draft.par.Pickquery.eval())
        try:
            self._model.TargetStart(self._identity,self._draft.par.Pickscope.eval(),'knob' if self.selected<8 else 'button',complete,refresh)
            return True
        except (ValueError,RuntimeError) as error:
            self._picker['message']=str(error);self._update_picker();return False

    def PickerQuery(self,text):
        if not getattr(self,'_picker',None):return False
        query=str(text).strip().casefold()[:256]
        self._picker['filtered']=tuple(row for row in self._picker['rows'] if query in (row['label']+' '+row['path']+'.'+row['name']).casefold())
        self._picker['page']=0;self._picker['chosen']=None
        self._update_picker();return True

    def _update_picker(self):
        picker=getattr(self,'_picker',None)
        if not picker or self.selected is None:return
        rows=picker['filtered'];pages=max(1,(len(rows)+5)//6)
        picker['page']=min(picker['page'],pages-1)
        visible=rows[picker['page']*6:picker['page']*6+6];picker['visible']=visible
        enabled=self._model.Capabilities(self._context,self.selected)['assign']['enabled'] and self._token==self._model.GetToken(self._context,self.selected)
        for editor in self._editors:
            section=editor.op('container_picker')
            if not section:continue
            section.op('text_count').par.text=str(len(rows))+' targets · '+str(picker['page']+1)+'/'+str(pages)+(' · narrow Scope' if picker['truncated'] else '')
            section.op('text_status').par.text=picker['message'] or ('Select a target, then Assign' if rows else 'No targets · change Scope / search')
            section.op('assign').par.enable=enabled and picker['chosen'] is not None
            section.op('prev').par.enable=picker['page']>0;section.op('next').par.enable=picker['page']+1<pages
            for i in range(6):
                button=section.op('row'+str(i));button.par.display=i<len(visible)
                if i>=len(visible):continue
                row=visible[i];label=row['path'].rsplit('/',1)[-1]+'.'+row['name']+' · '+row['style']
                button.op('text_label').par.text=label
                paint(button,(.23,.23,.23) if picker['chosen']==row else (.15,.15,.15))
                ink(button.op('text_label'),MUTED if row['reason'] else TEXT)

    def AssignTarget(self):
        if not self._picker or not self._picker['chosen']:return False
        try:
            result=self._model.Assign(self._context,self.selected,self._picker['chosen']['handle'],self._token)
            self.ClosePicker();self._mapping.Close();self._value_scope=None
            self._token=self._model.GetToken(self._context,self.selected)
            self._original=dict(self._model.GetCatalog(self._context)[self.selected])
            for name,value in self._original.items():self._draft.par[name]=value
            self._value_type=None
            self._error=result['message'];self._editor_layout();self._theme();return True
        except (ValueError,RuntimeError) as error:self._picker['message']=str(error);self._update_picker();return False

    def _set_mapping_values(self,values):
        for field,name in [('minimum','Mapminimum'),('maximum','Mapmaximum'),('mode','Mapmode'),('button_type','Mapinput')]:self._draft.par[name]=values[field] or ('' if field=='button_type' else values[field])

    def OpenMappingChoice(self,field):
        if self.selected is None or not self._mapping.open:return False
        schema=self._model.MappingSchema(self._context,self.selected)
        choices=schema['modes' if field=='mode' else 'inputs']
        if len(choices)<2 or schema['reason'] or self._mapping.IsStale(self._model,self._context,self.selected):return False
        self._menu_generation+=1
        details=dict(name='Mode' if field=='mode' else 'HW Type',generation=self._menu_generation,context=self._context,slot=self.selected,token=self._mapping.token,field=field)
        labels=[choice.upper() for choice in choices]
        current=self._mapping_values()[field]
        return self.OpenEditorMenu(labels,self.SelectMappingChoice,details,[current.upper()] if current else [],'container_mapping/choice_'+('mode' if field=='mode' else 'input'))

    def SelectMappingChoice(self,info):
        details=info.get('details',{});value=str(info.get('item','')).lower()
        if not self._mapping.open or details.get('context')!=self._context or details.get('slot')!=self.selected or details.get('token')!=self._mapping.token:return False
        if details.get('generation')!=self._menu_generation:return False
        if self._mapping.IsStale(self._model,self._context,self.selected):return False
        field=details['field'];schema=self._model.MappingSchema(self._context,self.selected)
        if value not in schema['modes' if field=='mode' else 'inputs'] or schema['reason']:return False
        self._draft.par['Mapmode' if field=='mode' else 'Mapinput']=value;return True

    def onInitTD(self):
        if not self._model:self.Connect()

    def onDestroyTD(self):self.Disconnect()

    def _visible(self):return self._main.isOpen or self._popup.isOpen

    def _write(self,op,value):
        op.par.text=value;self._writes+=1

    def _refresh_rows(self,slots,metadata):
        if not self._model:return
        catalog=self._model.GetCatalog(self._context)
        health_changed=False
        for i,refs in enumerate(self._row_refs):
            if not slots&(1<<i):continue
            record=catalog[i]
            label=record['Label'];mapped=bool(record['Destination'])
            value=self._model.ValueText(self._context,i) if self.IsLive() else (format(record['Value'],'.3g') if mapped else '—')
            previous=self._display.get(i)
            if previous is None or previous[0]!=label:self._write(refs['name'],label)
            if previous is None or previous[1]!=mapped:ink(refs['name'],TEXT if mapped else MUTED)
            if previous is None or previous[2]!=value:self._write(refs['value'],value)
            health=self._model.Health(self._context,i) if self.IsLive() else None
            health_code=health['code'] if health else ''
            slot=('K' if i<8 else 'B')+str(i%8+1)+(health['marker'] if health else '')
            if previous is None or previous[3]!=health_code:
                self._write(refs['slot'],slot);health_changed=True
            self._display[i]=(label,mapped,value,health_code)
        self._dirty&=~slots;self._metadata_dirty&=~metadata
        if metadata:self._normalize_filter()
        return health_changed

    def OnModelChange(self,context,slots,metadata,learn_changed,generation):
        if self.IsLive() and (learn_changed or metadata or not self._model.HasContext(self._context)):
            self.ConfigureMenus(self._model.ActiveContext() if self._follow_routing else self.Key())
            if self.Key()!=self._context:
                self.Refresh();return
        if context!=self._context:return
        self._notifications+=1;self._dirty|=slots;self._metadata_dirty|=metadata
        if self._visible():
            if self._refresh_rows(self._dirty,self._metadata_dirty):self._update_main_status()
        if learn_changed:self._theme()
        if learn_changed and self._clear_pending:
            self._disarm_clear();self._set_error('Clear cancelled · controller state changed')
        if self.selected is not None and self._model.GetToken(self._context,self.selected)!=self._token:
            self._disarm_clear()
            self._set_error('Mapping changed; reopen this control')
            if getattr(self,'_picker',None):self.ClosePicker();self._editor_layout()
        elif self.selected is not None and self._error=='Ping sent · awaiting hardware ACK':
            # A Range/Mode commit already recorded the unacknowledged state.
            # Its matching ACK updates health without changing target metadata.
            if self._mapping.message=='Mapping saved · needs re-LEARN' and not self._mapping.IsStale(self._model,self._context,self.selected):
                info=self._model.Info(self._context,self.selected)
                if info.get('mapped') and not info.get('requires_relearn'):self._error=''
        if self.selected is not None and slots&(1<<self.selected) and not self._value_scope:
            self._draft.par.Value=self._model.GetCatalog(self._context)[self.selected]['Value']
        if self._visible() and self.selected is not None and (slots&(1<<self.selected) or learn_changed):self._update_editor()

    def _disarm_clear(self):
        self._clear_pending=None
        for e in self._editors:
            if e.op('clear'):e.op('clear/text_label').par.text=ICONS['clear']

    def _set_error(self,message):
        self._error=message
        self._editor_display=None
        for e in self._editors:e.op('text_status').par.text=message

    def Hint(self,name,hover):
        if self.selected is None or self._clear_pending:return
        hints=dict(ping='Ping · resend mapping in HW LEARN',clear='Clear · remove this mapping',cancel='Cancel · discard Value draft',apply='Apply · write Value to target')
        if name not in hints:return
        reason=self._model.Capabilities(self._context,self.selected)['value' if name=='apply' else name]['reason'] if self.IsLive() and name!='cancel' else ''
        text=(reason or hints[name]) if hover else (self._error or self._editor_status())
        for e in self._editors:e.op('text_status').par.text=text

    def _editor_status(self):
        if self.selected is None:return ''
        if not self.IsLive():return 'Draft · live values update in list'
        value=self._model.Capabilities(self._context,self.selected)['value']
        if not value['enabled']:return value['reason']
        schema=self._model.ValueSchema(self._context,self.selected)
        if getattr(self,'_value_type',None)=='float' and schema['kind']=='integer':return 'Value edits live target · Int target: whole numbers only'
        if getattr(self,'_value_type',None)=='int' and schema['kind']=='float':
            live=self._model.GetCatalog(self._context)[self.selected]['Value']
            return 'Live '+format(live,'.4g')+' · Int input' if not float(live).is_integer() else 'Value edits live target · Int input'
        return 'Value edits live target'

    def _update_main_status(self):
        self._update_filter()
        if self._model and self._model.Learn:message='●  LEARN MODE ON'
        elif self.IsLive():
            info=[self._model.Info(self._context,i) for i in range(16)]
            registered=sum(bool(r.get('id')) for r in info)
            if self.Key()!=self._model.ActiveContext():message=str(registered)+' saved · browse'
            elif not self._model.Status.get('Connected'):message='Disconnected · '+str(registered)+' saved'
            else:
                mapped=sum(self._model.Health(self._context,i)['code']=='mapped' for i in range(16))
                message='Connected · '+str(mapped)+'/'+str(registered)+' mapped'
        else:message='16 controls · click to edit'
        if getattr(self,'_device_message','') and not self._model.Learn:message=self._device_message
        if message!=self._main_message:
            self._main_message=message;self._write(self.ownerComp.op('text_status'),message)

    def _update_editor(self,force=False):
        heading=(('KNOB ' if self.selected<8 else 'BUTTON ')+str(self.selected%8+1)) if self.selected is not None else 'MAPPING EDITOR'
        caps=None;stale=False
        if self.IsLive() and self.selected is not None:
            health=self._model.Health(self._context,self.selected);heading+=' · '+health['label']
            caps=self._model.Capabilities(self._context,self.selected)
            stale=self._model.GetToken(self._context,self.selected)!=self._token
        status=self._error or self._editor_status()
        signature=(heading,status,stale,tuple((name,c['enabled'],c['reason']) for name,c in caps.items()) if caps else None)
        self._update_typed_value(caps,stale)
        self._update_details()
        if not force and signature==self._editor_display:return
        self._editor_display=signature
        for e in self._editors:
            e.op('text_heading').par.text=heading;e.op('text_status').par.text=status
            if self.IsLive():
                for n in FIELDS:e.op('field_'+n).par.editmode='editablecontinuous' if n=='Value' and caps and caps['value']['enabled'] and not stale else 'selectonly'
                for name,cap in [('apply','value'),('ping','ping'),('clear','clear')]:
                    if e.op(name):e.op(name).par.enable=bool(caps and caps[cap]['enabled'] and not stale)
        self._update_mapping()
        self._update_picker()

    def _update_mapping(self):
        if self.selected is None or not self.IsLive():return
        schema=self._model.MappingSchema(self._context,self.selected)
        enabled=not schema['reason'] and self._mapping.open and not self._mapping.IsStale(self._model,self._context,self.selected)
        row=self._model.GetCatalog(self._context)[self.selected]
        caption='MAPPING  '+format(row['Minimum'],'.4g')+'–'+format(row['Maximum'],'.4g')+'  '+('▾' if self._mapping.open else '▸')
        message=self._mapping.Status(self._model,self._context,self.selected) or schema['reason'] or ('Mapping changed · reopen section' if self._mapping.open and not enabled else 'Range / Mode changes need re-LEARN')
        for e in self._editors:
            toggle=e.op('mapping_toggle')
            if not toggle:continue
            toggle.op('text_label').par.text=caption
            section=e.op('container_mapping');section.par.display=self._mapping.open
            section.op('text_status').par.text=message
            section.op('mapping_apply').par.enable=enabled
            for field in ('minimum','maximum'):section.op('field_'+field).par.editmode='editable' if enabled and schema['range_editable'] else 'selectonly'
            section.op('choice_mode').par.enable=enabled and len(schema['modes'])>1
            section.op('choice_input').par.enable=enabled and len(schema['inputs'])>1

    def _theme(self):
        learn=bool(self._model and self._model.Learn)
        c=self.ownerComp
        paint(c,(.14,.135,.125) if learn else BASE)
        paint(self._viewport,(.14,.135,.125) if learn else BASE)
        self._update_main_status()
        ink(c.op('text_status'),(.80,.78,.72) if learn else MUTED)
        c.op('learn/text_label').par.text=('LEARN ON' if learn else 'HW Learn') if self.IsLive() else ('Exit Learn' if learn else 'Learn')
        paint(c.op('learn'),(.25,.24,.215) if learn else SURFACE)
        for i,refs in enumerate(self._row_refs):
            paint(refs['row'],(.20,.20,.20) if self.selected==i else ((.17,.165,.15) if learn else BASE))
            ink(refs['slot'],ACCENT if self.selected==i else MUTED)
        c.op('text_brand').par.text=('LIVE' if self._follow_routing else 'BROWSE') if self.IsLive() else 'DEMO'
        if not c.op('clear_device'):c.op('text_footer').par.text='● MAPPED  ○ PENDING  ◇ SAVED  ! ISSUE' if self.IsLive() else 'SCROLL TO BROWSE'
        for e in self._editors:paint(e,(.18,.175,.16) if learn else SURFACE)

    def _editor_layout(self):
        expanded=DETAILS if getattr(self,'_details_open',False) else PICKER if getattr(self,'_picker',None) else MAPPING if getattr(self,'_mapping',None) and self._mapping.open else 0
        menu_extra=getattr(self,'_menu_extra',0);offset=expanded+menu_extra
        height=EDITOR+offset
        extra=height+8 if self.selected is not None and self.style=='below' else 0
        visible=self._visible_slots()
        count=len(visible)
        self._rows.par.h=max(1,count*ROW+extra)
        if self._rows.par.vmode.eval()=='anchors':self._rows.par.bottomoffset=-max(1,count*ROW+extra)
        for i,refs in enumerate(self._row_refs):
            refs['row'].par.display=i in visible
            if i in visible:
                index=visible.index(i);selected_index=visible.index(self.selected) if self.selected in visible else -1
                refs['row'].par.y=count*ROW+extra-index*ROW-(extra if index>selected_index else 0)-24
            refs['arrow'].par.text='−' if self.selected==i else '+'
        below=self._editors[0];below.par.display=bool(extra)
        if extra:below.par.y=count*ROW+extra-(visible.index(self.selected)+1)*ROW-height-4
        for e in self._editors:
            e.par.h=height
            if e==self._editors[1] and e.par.vmode.eval()=='anchors':e.par.bottomoffset=-height
            for name,y in [('text_heading',151),('text_empty',64),('label_Label',120),('field_Label',120),('label_Destination',92),('field_Destination',92),('label_Range',64),('field_Minimum',64),('field_Maximum',64),('label_Value',36),('field_Value',36),('text_status',6),('cancel',6),('apply',6),('ping',148),('clear',148),('mapping_toggle',64)]:
                if e.op(name):e.op(name).par.y=y+offset
            for name in ('container_mapping','container_picker','container_details'):
                if e.op(name):e.op(name).par.y=menu_extra
            for n in ['label_Label','label_Destination','label_Range','label_Value','field_Label','field_Destination','field_Minimum','field_Maximum','field_Value','apply','cancel','ping','clear']:
                if not e.op(n):continue
                e.op(n).par.display=self.selected is not None
            e.op('text_empty').par.display=self.selected is None
            if e.op('mapping_toggle'):
                e.op('mapping_toggle').par.display=self.selected is not None
                for n in ('label_Range','field_Minimum','field_Maximum'):e.op(n).par.display=False
                e.op('container_mapping').par.display=self.selected is not None and self._mapping.open
            if e.op('container_picker'):
                e.op('container_picker').par.display=self.selected is not None and bool(getattr(self,'_picker',None))
                for name in ('value_menu','value_toggle','value_type'):
                    e.op(name).par.y=36+offset
                    if self.selected is None:
                        e.op(name).par.display=False;e.op(name+'/text_label').par.text=''
            if e.op('details_toggle'):
                e.op('details_toggle').par.y=148+offset;e.op('details_toggle').par.display=self.selected is not None
                e.op('container_details').par.display=self.selected is not None and getattr(self,'_details_open',False)
            for name in ('cancel','apply'):
                if e.op(name):e.op(name).par.display=False
        self._update_editor(force=True)
        self._sync_popup_expansion(expanded+getattr(self,'_menu_window_extra',0) if self.style=='popup' else 0)

    def _cancel_popup_geometry(self):
        pending=getattr(self,'_popup_geometry_settle',None)
        if pending:pending.kill()
        self._popup_geometry_settle=None;self._popup_geometry=None

    def SettlePopupGeometry(self,generation):
        if generation!=getattr(self,'_popup_geometry_generation',0):return False
        self._popup_geometry_settle=None;self._popup_geometry=None
        popup=self._popup;host=getattr(self,'_popup_host',None)
        if getattr(popup,'valid',True) and not popup.isOpen:
            if host and hasattr(host,'par'):host.par.h=popup.par.winh.eval()
            self._popup_size_pending=True
        return True

    def _sync_popup_expansion(self,extra):
        previous=getattr(self,'_popup_extra',0)
        if extra==previous:return
        popup=self._popup
        if not getattr(popup,'valid',True):self._popup_extra=0;self._cancel_popup_geometry();return
        # Apply only the section's height delta. Manual width/height changes
        # become the new base size; keep the native top-left corner stationary.
        pending=getattr(self,'_popup_size_pending',False) and not popup.isOpen
        host=getattr(self,'_popup_host',None)
        width=popup.par.winw.eval() if pending else (host.width if host and not popup.isOpen else popup.contentWidth) or popup.par.winw.eval()
        height=popup.par.winh.eval() if pending else (host.height if host and not popup.isOpen else popup.contentHeight) or popup.par.winh.eval()
        corner=(popup.x,popup.y+popup.height);border=popup.height-popup.contentHeight
        geometry=getattr(self,'_popup_geometry',None)
        if geometry:
            if popup.isOpen and height==geometry['height'] and corner==geometry['corner']:
                self._cancel_popup_geometry()
            else:
                # Native geometry is asynchronous. Until it settles, resize
                # from our latest requested size, never from the old cache.
                height=geometry['height'];corner=geometry['corner'];border=geometry['border']
        target_height=max(1,height+extra-previous)
        if popup.isOpen:
            # Manual native resizing leaves Opening Width stale. Any offset
            # change can apply that old width, so synchronize it first while
            # retaining the original native position captured above.
            if popup.par.winw.eval()!=width:popup.par.winw=width
            popup.par.justifyoffsetto='primarydisplay';popup.par.justifyh='left';popup.par.justifyv='bottom'
            popup.par.winoffsetx=corner[0];popup.par.winoffsety=corner[1]-border-target_height
        else:popup.par.winw=width
        popup.par.winh=target_height
        self._popup_extra=extra;self._popup_size_pending=not popup.isOpen
        self._cancel_popup_geometry()
        try:schedule=run
        except NameError:schedule=None
        if popup.isOpen and (schedule or popup.contentHeight!=target_height or (popup.x,popup.y+popup.height)!=corner or host and host.height!=target_height):
            self._popup_geometry=dict(height=target_height,corner=corner,border=border)
            self._popup_geometry_generation=getattr(self,'_popup_geometry_generation',0)+1
            if schedule:
                self._popup_geometry_settle=schedule('args[0].SettlePopupGeometry(args[1])',self,self._popup_geometry_generation,delayFrames=3,delayRef=op.TDResources)
        elif not popup.isOpen and host and hasattr(host,'par'):
            host.par.h=target_height
        # Opening-size/offset parameters already update an open native window.
        # Re-pulsing winopen here recreates/reopens it and flashes the surface.

    def Refresh(self):
        if not self._model:return False
        if self.IsLive():self.ConfigureMenus(self._model.ActiveContext() if self._follow_routing else self.Key())
        context=self.Key()
        if context!=self._context:
            self.CloseContextMenu()
            self._context=context;self._model.Subscribe(self._identity,context,self.OnModelChange)
            self.selected=None;self._token=None;self._original=None;self._error='';self._display={};self._value_type=None
            self._mapping.Close();self._menu_generation+=1
            self._clear_device_request=None;self._device_message='';self._details_open=False
            self.ClosePicker()
            self._disarm_clear()
        for n in ('Layout','Track','Device'):
            p=self.ownerComp.par[n]
            self.ownerComp.op('context_'+n+'/text_value').par.text=p.menuLabels[p.menuIndex]
        self.ownerComp.op('text_style').par.text=('FOLD' if self.style=='below' else 'POPUP')+'  ↔'
        self._refresh_rows(65535,65535)
        self._editor_layout();self._theme()
        return True

    def OnContext(self):
        if self._configuring:return
        if self.Key()!=self._context:
            if self.IsLive():self._follow_routing=False
            self.Refresh()

    def OnWindowOpen(self):
        self.HideOtherViews()
        if self._model:self.Refresh()

    def OpenPopup(self):
        if not self._main.isOpen:return
        self.HideOtherViews()
        # Selection and Inspector resizing must not resize/reposition an open editor.
        if self._popup.isOpen:return
        pending=getattr(self,'_popup_size_pending',False)
        # Closed native-window caches can include the title bar after reload.
        # Size from Window retains the actual content size in the viewport.
        host=getattr(self,'_popup_host',None)
        width=self._popup.par.winw.eval() if pending else (host.width if host else self._popup.contentWidth) or self._popup.par.winw.eval()
        x=self._main.x+self._main.width+8
        border=self._main.height-self._main.contentHeight
        height=self._popup.par.winh.eval() if pending else (host.height if host else self._popup.contentHeight) or self._popup.par.winh.eval()
        geometry=getattr(self,'_popup_geometry',None)
        if geometry:height=geometry['height']
        y=self._main.y+self._main.height-height-border
        self._popup.par.justifyoffsetto='primarydisplay';self._popup.par.justifyh='left';self._popup.par.justifyv='bottom'
        self._popup.par.winw=width;self._popup.par.winh=height;self._popup.par.winoffsetx=x;self._popup.par.winoffsety=y
        self._popup.par.winopen.pulse();self._window_opens+=1
        self._popup_size_pending=False
        # Reopening before the previous resize settled must retain its latest
        # intended size, rather than the closed Window's expanded cache.
        if geometry:
            popup_border=getattr(self._popup,'height',height+border)-self._popup.contentHeight
            if popup_border<=0:popup_border=border
            self._cancel_popup_geometry()
            self._popup_geometry=dict(height=height,corner=(x,y+height+popup_border),border=popup_border)
            self._popup_geometry_generation=getattr(self,'_popup_geometry_generation',0)+1
            try:schedule=run
            except NameError:schedule=None
            if schedule:self._popup_geometry_settle=schedule('args[0].SettlePopupGeometry(args[1])',self,self._popup_geometry_generation,delayFrames=3,delayRef=op.TDResources)

    def CloseEditor(self):
        if getattr(self,'_context_menu',None):self.CloseContextMenu()
        self._value_scope=None
        self._value_type=None
        self._details_open=False;self._diagnostics=None;self._details_display=None
        for editor in getattr(self,'_editors',()):
            section=editor.op('container_details')
            if section:
                section.op('text_details').par.text=''
                content=section.op('container_readout/container_info')
                if content:
                    for group in content.children:
                        if group.OPType=='containerCOMP':
                            for field in group.children:
                                if field.OPType=='textCOMP' and field.name.startswith('value'):field.par.text=''
        self.ClosePicker()
        self._menu_generation=getattr(self,'_menu_generation',0)+1
        self._disarm_clear()
        if getattr(self,'_mapping',None):self._mapping.Close()
        self.selected=None;self._token=None;self._original=None;self._error=''
        self._editor_layout();self._theme()

    def BeginValueEdit(self):
        if self.selected is None or not self.IsLive():return False
        self._disarm_clear();self._value_scope=(self._context,self.selected,self._token)
        return True

    def LiveValue(self,text):
        if not self._value_scope or self._value_scope!=(self._context,self.selected,self._token):return False
        # Incomplete numeric text is a local editing state, never a target write.
        if str(text).strip() in ('','-','+','.','-.','+.'):return False
        values=dict(self._model.GetCatalog(self._context)[self.selected])
        try:
            values['Value']=float(text)
            if getattr(self,'_value_type',None)=='int' and not values['Value'].is_integer():raise ValueError('Int input needs a whole number')
            changed=self._model.Commit(self._context,self.selected,values,self._token)
            self._error='';self._update_editor();return changed
        except (ValueError,RuntimeError) as error:self._set_error(str(error));return False

    def EndValueEdit(self):
        self._value_scope=None
        if self.selected is not None:self._draft.par.Value=self._model.GetCatalog(self._context)[self.selected]['Value']

    def DismissPopup(self):
        self.CloseEditor();self._popup.par.winclose.pulse()

    def Action(self,name):
        if not self._model and not self.Connect():return False
        if not isinstance(name,str):return False
        if not name.startswith('context_'):self.CloseContextMenu()
        if name.startswith('context_'):
            n=name.split('_',1)[1]
            if n not in ('Layout','Track','Device'):return False
            return self.OpenContextMenu(n)
        elif name=='filter':return self.OpenFilter()
        elif name=='clear_device':return self.RequestClearDevice()
        elif name=='details_toggle':
            if self.selected is None or not self.IsLive():return False
            opened=getattr(self,'_details_open',False)
            self._mapping.Close();self.ClosePicker();self._details_open=not opened
            if self._details_open:self._diagnostics=self._model.Diagnostics()
            self._editor_layout()
            if self._details_open:
                for editor in self._editors:
                    viewport=editor.op('container_details/container_readout')
                    if viewport:viewport.panel.scrollv=0
        elif name=='details_refresh':
            if self.selected is None or not self.IsLive():return False
            self._diagnostics=self._model.Diagnostics();self._model.Inspect(self._context,self.selected);self._update_details()
        elif name=='details_repair':return self.OpenPicker()
        elif name=='details_reveal':
            if self.selected is None or not self.IsLive():return False
            try:
                path=self._model.Reveal(self._context,self.selected,self._token);self._set_error('Revealed '+path)
            except (ValueError,RuntimeError) as error:self._set_error(str(error));return False
        elif name=='target_picker':return self.OpenPicker()
        elif name=='picker_cancel':
            self.ClosePicker();self._editor_layout()
        elif name=='picker_refresh':return self.SearchTargets(True)
        elif name in ('picker_prev','picker_next'):
            if not self._picker:return False
            self._picker['page']=max(0,self._picker['page']+(-1 if name=='picker_prev' else 1));self._update_picker()
        elif name=='picker_assign':return self.AssignTarget()
        elif name.startswith('picker_row'):
            if not self._picker:return False
            suffix=name[10:]
            if not suffix.isdecimal() or not 0<=int(suffix)<len(self._picker.get('visible',())):return False
            row=self._picker['visible'][int(suffix)]
            self._picker['chosen']=row if not row['reason'] else None
            self._picker['message']=row['reason'] or row['path']+'.'+row['name'];self._update_picker()
        elif name=='value_type':return self.CycleValueType()
        elif name=='value_menu':return self.OpenValueMenu()
        elif name=='value_toggle':
            if self.selected is None:return False
            return self.TypedValue(0 if self._model.GetCatalog(self._context)[self.selected]['Value'] else 1)
        elif name=='mapping_toggle':
            if self.selected is None or not self.IsLive():return False
            self._disarm_clear();self.ClosePicker();self._details_open=False
            if self._mapping.open:self._mapping.Close()
            else:self._set_mapping_values(self._mapping.Open(self._model,self._context,self.selected))
            self._editor_layout()
            if self.style=='popup':self._popup_host.panel.scrollv=0
        elif name in ('mapping_mode','mapping_input'):return self.OpenMappingChoice('mode' if name=='mapping_mode' else 'button_type')
        elif name=='mapping_cancel':
            self._mapping.Close();self._editor_layout()
        elif name=='mapping_apply':
            if self.selected is None or not self._mapping.open:return False
            if self.Key()!=self._context:self.Refresh();return False
            self._disarm_clear()
            try:
                changed,fresh=self._mapping.Apply(self._model,self._context,self.selected,self._mapping_values())
                self._set_mapping_values(fresh)
                if changed:
                    self._original=dict(self._model.GetCatalog(self._context)[self.selected]);self._token=self._model.GetToken(self._context,self.selected)
                    for n,value in self._original.items():self._draft.par[n]=value
                    self._error=''
                self._editor_layout();self._theme()
            except (ValueError,RuntimeError) as error:self._mapping.message=str(error);self._update_mapping();return False
        elif name=='show':self.Show()
        elif name=='follow':
            self._follow_routing=True;self.Refresh()
        elif name=='presentation':
            self.CloseEditor();self._popup.par.winclose.pulse()
            self.style='popup' if self.style=='below' else 'below';self.ownerComp.par.Presentation=self.style
            self._main.par.title='Inspector / '+('Fold' if self.style=='below' else 'Popup');self.Refresh()
        elif name=='learn':
            if self.IsLive():
                self.ownerComp.op('text_status').par.text='Press LEARN on controller';return False
            self._model.SetLearn(not self._model.Learn)
        elif name=='cancel':self.CloseEditor()
        elif name=='dismiss':self.DismissPopup()
        elif name in ('ping','clear'):
            if not self.IsLive() or self.selected is None:return False
            if self.Key()!=self._context:self.Refresh();return False
            try:
                if name=='ping':
                    self._disarm_clear()
                    self._model.Ping(self._context,self.selected,self._token)
                    self._set_error('Ping sent · awaiting hardware ACK')
                else:
                    self._model.CheckClear(self._context,self.selected,self._token)
                    pending=(self._context,self.selected,self._token)
                    if not self._clear_pending or self._clear_pending[0]!=pending or monotonic()>self._clear_pending[1]:
                        self._clear_pending=(pending,monotonic()+8)
                        for e in self._editors:e.op('clear/text_label').par.text=ICONS['confirm']
                        slot=('K' if self.selected<8 else 'B')+str(self.selected%8+1)
                        self._set_error('Clear '+slot+' mapping? Click ? to confirm.')
                        return True
                    self._model.Clear(self._context,self.selected,self._token)
                    self.CloseEditor()
                    self.ownerComp.op('text_status').par.text='Mapping cleared · target Value kept'
            except (ValueError,RuntimeError) as error:
                self._disarm_clear();self._set_error(str(error));return False
        elif name=='apply':
            self._disarm_clear()
            if self.selected is None:return False
            if self.Key()!=self._context:self.Refresh();return False
            values={n:self._draft.par[n].eval() for n in FIELDS}
            # Applying unchanged snapshot text must not rewind a newer live value.
            if values['Value']==self._original['Value']:
                values['Value']=self._model.GetCatalog(self._context)[self.selected]['Value']
            try:self._model.Commit(self._context,self.selected,values,self._token)
            except (ValueError,RuntimeError) as error:self._set_error(str(error));return False
            self.CloseEditor()
        elif name.startswith('slot'):
            suffix=name[4:]
            if not suffix.isdecimal() or not 0<=int(suffix)<16:return False
            slot=int(suffix)
            if self.Key()!=self._context:self.Refresh()
            if self.selected==slot:
                if self.style=='popup' and not self._popup.isOpen:
                    self.OpenPopup();return True
                self.CloseEditor();return True
            if self.IsLive():self._model.Inspect(self._context,slot)
            self._mapping.Close();self.ClosePicker();self._details_open=False;self._value_scope=None;self._value_type=None;self._menu_generation+=1
            self.selected=slot;self._token=self._model.GetToken(self._context,slot)
            self._disarm_clear()
            self._original=dict(self._model.GetCatalog(self._context)[slot]);self._error=''
            for n,v in self._original.items():self._draft.par[n]=v
            self._editor_layout();self._theme()
            if self.style=='popup':self.OpenPopup()
        else:return False
        return True

    def ScrollWheel(self,delta):
        travel=max(0,self._rows.height-self._viewport.height)
        if delta and travel:self._viewport.panel.scrollv=max(0.,min(1.,self._viewport.panel.scrollv.val-float(delta)*32./travel))

    def PopupScrollWheel(self,delta):
        travel=max(0,self._editors[1].height-self._popup_host.height)
        if delta and travel:self._popup_host.panel.scrollv=max(0.,min(1.,self._popup_host.panel.scrollv.val-float(delta)*32./travel))

    def DetailsScrollWheel(self,delta):
        editor=self._editors[1 if self.style=='popup' else 0]
        viewport=editor.op('container_details/container_readout')
        if not viewport:return
        travel=max(0,viewport.op('container_info').height-viewport.height)
        if delta and travel:viewport.panel.scrollv=max(0.,min(1.,viewport.panel.scrollv.val-float(delta)*32./travel))

    def Stats(self):
        return dict(context=self._context,selected=self.selected,dirty_slots=self._dirty.bit_count(),notifications=self._notifications,text_writes=self._writes,window_opens=self._window_opens,model_connected=self._model is not None)

# Small compatibility wrappers for the builder and existing panel callback DATs.
def owner():return op(__name__).parent()
def state():return owner().ext.InspectorView
def action(name):return state().Action(name)
def render():return state().Refresh()
def context():return state().OnContext()
def scroll_wheel(delta):return state().ScrollWheel(delta)
def editors():return state()._editors
