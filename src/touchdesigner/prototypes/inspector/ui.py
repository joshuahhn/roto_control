"""Compact views over a shared demo or real controller catalog."""
from time import monotonic
from editor_state import MappingDraft
ROW=26
EDITOR=178
MAPPING=134
BASE=(.085,.085,.085)
SURFACE=(.12,.12,.12)
ACCENT=(.76,.76,.76)
TEXT=(.86,.86,.86)
MUTED=(.50,.50,.50)
FIELDS=('Label','Destination','Minimum','Maximum','Value')
ICON_FONT='Material Design Icons'
# Codepoints from TD's bundled MaterialDesignIconsMeta.json.
ICONS=dict(ping='\U000f0450',clear='\U000f0b5c',cancel='\U000f0156',apply='\U000f012c',confirm='\U000f0625')

def action_icon(label,name):
    label.par.font=ICON_FONT
    label.par.text=ICONS[name]
    label.par.fontsize=15
    label.par.fontsizeunits='panelunits'
    label.par.alignx=label.par.aligny='center'

def paint(o,rgb):o.par.bgcolorr,o.par.bgcolorg,o.par.bgcolorb=rgb

def ink(o,rgb):o.par.fontcolorr,o.par.fontcolorg,o.par.fontcolorb=rgb

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
        self._menu_generation=0
        self._value_scope=None
        self._popup_extra=0
        self._popup_size_pending=False
        self._follow_routing=True
        self._configuring=False
        self._rows=ownerComp.op('container_scroll/container_content')
        self._viewport=ownerComp.op('container_scroll')
        self._draft=ownerComp.op('base_draft')
        self._main=ownerComp.op('window_main')
        self._popup=ownerComp.op('window_editor')
        popup=ownerComp.op('editor_popup')
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

    def Connect(self):
        self.Disconnect()
        self._value_scope=None
        self._mapping.Close();self._menu_generation+=1
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
            if popup and popup.isOpen:popup.par.winclose.pulse()
            if main and main.isOpen:main.par.winclose.pulse()

    def Show(self):
        self.HideOtherViews();self.CloseEditor()
        if not self._main.isOpen:self._main.par.winopen.pulse()
        self.Refresh()

    def Disconnect(self):
        if getattr(self,'_popup_extra',0):self._sync_popup_expansion(0)
        if self._model:self._model.Unsubscribe(self._identity,self.OnModelChange)
        self._model=None

    def OpenContextMenu(self,name):
        if name not in ('Layout','Track','Device'):return False
        if self.IsLive():self.ConfigureMenus(self.Key())
        p=self.ownerComp.par[name];names=list(p.menuNames);labels=list(p.menuLabels)
        items=[label if labels.count(label)==1 else label+' ('+str(i+1)+')' for i,label in enumerate(labels)]
        self._menu_generation+=1
        details=dict(generation=self._menu_generation,context=self.Key(),model_generation=self._model.Stats()['generation'],name=name,choices=dict(zip(items,names)))
        checked=[items[names.index(p.eval())]] if p.eval() in names else []
        op.TDResources.op('popMenu').Open(items=items,callback=self.SelectContextMenu,callbackDetails=details,checkedItems=checked,autoClose=1)
        return True

    def SelectContextMenu(self,info):
        details=info.get('details',{});value=details.get('choices',{}).get(info.get('item'))
        if not self._model or details.get('generation')!=self._menu_generation or details.get('context')!=self.Key() or details.get('model_generation')!=self._model.Stats()['generation']:return False
        name=details['name']
        try:choices=self._model.Choices(name,self.Key())
        except (ValueError,RuntimeError):return False
        if value is None or value not in [key for key,label in choices]:return False
        self._menu_generation+=1;self._follow_routing=False
        self.ownerComp.par[name].val=value;self.OnContext();return True

    def _mapping_values(self):
        return dict(minimum=self._draft.par.Mapminimum.eval(),maximum=self._draft.par.Mapmaximum.eval(),mode=self._draft.par.Mapmode.eval(),button_type=self._draft.par.Mapinput.eval() or None)

    def _set_mapping_values(self,values):
        for field,name in [('minimum','Mapminimum'),('maximum','Mapmaximum'),('mode','Mapmode'),('button_type','Mapinput')]:self._draft.par[name]=values[field] or ('' if field=='button_type' else values[field])

    def OpenMappingChoice(self,field):
        if self.selected is None or not self._mapping.open:return False
        schema=self._model.MappingSchema(self._context,self.selected)
        choices=schema['modes' if field=='mode' else 'inputs']
        if len(choices)<2 or schema['reason'] or self._mapping.IsStale(self._model,self._context,self.selected):return False
        details=dict(context=self._context,slot=self.selected,token=self._mapping.token,field=field)
        labels=[choice.upper() for choice in choices]
        current=self._mapping_values()[field]
        op.TDResources.op('popMenu').Open(items=labels,callback=self.SelectMappingChoice,callbackDetails=details,checkedItems=[current.upper()] if current else [],autoClose=1)
        return True

    def SelectMappingChoice(self,info):
        details=info.get('details',{});value=str(info.get('item','')).lower()
        if not self._mapping.open or details.get('context')!=self._context or details.get('slot')!=self.selected or details.get('token')!=self._mapping.token:return False
        if self._mapping.IsStale(self._model,self._context,self.selected):return False
        field=details['field'];schema=self._model.MappingSchema(self._context,self.selected)
        if value not in schema['modes' if field=='mode' else 'inputs'] or schema['reason']:return False
        self._draft.par['Mapmode' if field=='mode' else 'Mapinput']=value;return True

    def onInitTD(self):
        if not self._model:self.Connect()

    def onDestroyTD(self):self.Disconnect()

    def _visible(self):return self._main.isOpen

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
        return 'Value edits live target' if value['enabled'] else value['reason']

    def _update_main_status(self):
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
        if not force and signature==self._editor_display:return
        self._editor_display=signature
        for e in self._editors:
            e.op('text_heading').par.text=heading;e.op('text_status').par.text=status
            if self.IsLive():
                for n in FIELDS:e.op('field_'+n).par.editmode='editablecontinuous' if n=='Value' and caps and caps['value']['enabled'] and not stale else 'selectonly'
                for name,cap in [('apply','value'),('ping','ping'),('clear','clear')]:
                    if e.op(name):e.op(name).par.enable=bool(caps and caps[cap]['enabled'] and not stale)
        self._update_mapping()

    def _update_mapping(self):
        if self.selected is None or not self.IsLive():return
        schema=self._model.MappingSchema(self._context,self.selected)
        enabled=not schema['reason'] and self._mapping.open and not self._mapping.IsStale(self._model,self._context,self.selected)
        row=self._model.GetCatalog(self._context)[self.selected]
        caption='MAPPING  '+format(row['Minimum'],'.4g')+'–'+format(row['Maximum'],'.4g')+'  '+('▾' if self._mapping.open else '▸')
        message=self._mapping.message or schema['reason'] or ('Mapping changed · reopen section' if self._mapping.open and not enabled else 'Range / Mode changes need re-LEARN')
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
        c.op('text_footer').par.text='● MAPPED  ○ PENDING  ◇ SAVED  ! ISSUE' if self.IsLive() else 'SCROLL TO BROWSE'
        for e in self._editors:paint(e,(.18,.175,.16) if learn else SURFACE)

    def _editor_layout(self):
        expanded=MAPPING if getattr(self,'_mapping',None) and self._mapping.open else 0
        height=EDITOR+expanded
        extra=height+8 if self.selected is not None and self.style=='below' else 0
        self._rows.par.h=16*ROW+extra
        for i,refs in enumerate(self._row_refs):
            refs['row'].par.y=16*ROW+extra-i*ROW-(extra if self.selected is not None and i>self.selected else 0)-24
            refs['arrow'].par.text='−' if self.selected==i else '+'
        below=self._editors[0];below.par.display=bool(extra)
        if extra:below.par.y=16*ROW+extra-(self.selected+1)*ROW-height-4
        for e in self._editors:
            e.par.h=height
            for name,y in [('text_heading',151),('text_empty',64),('label_Label',120),('field_Label',120),('label_Destination',92),('field_Destination',92),('label_Range',64),('field_Minimum',64),('field_Maximum',64),('label_Value',36),('field_Value',36),('text_status',6),('cancel',6),('apply',6),('ping',148),('clear',148),('mapping_toggle',64)]:
                if e.op(name):e.op(name).par.y=y+expanded
            for n in ['label_Label','label_Destination','label_Range','label_Value','field_Label','field_Destination','field_Minimum','field_Maximum','field_Value','apply','cancel','ping','clear']:
                if not e.op(n):continue
                e.op(n).par.display=self.selected is not None
            e.op('text_empty').par.display=self.selected is None
            if e.op('mapping_toggle'):
                e.op('mapping_toggle').par.display=self.selected is not None
                for n in ('label_Range','field_Minimum','field_Maximum'):e.op(n).par.display=False
                e.op('container_mapping').par.display=self.selected is not None and bool(expanded)
            for name in ('cancel','apply'):
                if e.op(name):e.op(name).par.display=False
        self._update_editor(force=True)
        self._sync_popup_expansion(expanded if self.style=='popup' else 0)

    def _sync_popup_expansion(self,extra):
        previous=getattr(self,'_popup_extra',0)
        if extra==previous:return
        popup=self._popup
        if not getattr(popup,'valid',True):self._popup_extra=0;return
        # Apply only the section's height delta. Manual width/height changes
        # become the new base size; keep the native top-left corner stationary.
        pending=getattr(self,'_popup_size_pending',False) and not popup.isOpen
        host=getattr(self,'_popup_host',None)
        width=popup.par.winw.eval() if pending else (host.width if host and not popup.isOpen else popup.contentWidth) or popup.par.winw.eval()
        height=popup.par.winh.eval() if pending else (host.height if host and not popup.isOpen else popup.contentHeight) or popup.par.winh.eval()
        target_height=max(1,height+extra-previous)
        delta=target_height-height
        if popup.isOpen:
            x,y=popup.x,popup.y
            popup.par.justifyoffsetto='primarydisplay';popup.par.justifyh='left';popup.par.justifyv='bottom'
            popup.par.winoffsetx=x;popup.par.winoffsety=y-delta
        popup.par.winw=width;popup.par.winh=target_height
        self._popup_extra=extra;self._popup_size_pending=not popup.isOpen
        if popup.isOpen:popup.par.winopen.pulse()

    def Refresh(self):
        if not self._model:return False
        if self.IsLive():self.ConfigureMenus(self._model.ActiveContext() if self._follow_routing else self.Key())
        context=self.Key()
        if context!=self._context:
            self._context=context;self._model.Subscribe(self._identity,context,self.OnModelChange)
            self.selected=None;self._token=None;self._original=None;self._error='';self._display={}
            self._mapping.Close();self._menu_generation+=1
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
        y=self._main.y+self._main.height-height-border
        self._popup.par.justifyoffsetto='primarydisplay';self._popup.par.justifyh='left';self._popup.par.justifyv='bottom'
        self._popup.par.winw=width;self._popup.par.winh=height;self._popup.par.winoffsetx=x;self._popup.par.winoffsety=y
        self._popup.par.winopen.pulse();self._window_opens+=1
        self._popup_size_pending=False

    def CloseEditor(self):
        self._value_scope=None
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
        if name.startswith('context_'):
            n=name.split('_',1)[1]
            if n not in ('Layout','Track','Device'):return False
            return self.OpenContextMenu(n)
        elif name=='mapping_toggle':
            if self.selected is None or not self.IsLive():return False
            self._disarm_clear()
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
            self._mapping.Close()
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
