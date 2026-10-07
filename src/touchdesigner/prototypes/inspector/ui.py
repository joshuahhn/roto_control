"""Compact views over a shared demo or real controller catalog."""
from time import monotonic
ROW=26
EDITOR=178
BASE=(.085,.085,.085)
SURFACE=(.12,.12,.12)
ACCENT=(.76,.76,.76)
TEXT=(.86,.86,.86)
MUTED=(.50,.50,.50)
FIELDS=('Label','Destination','Minimum','Maximum','Value')

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
        self._follow_routing=True
        self._configuring=False
        self._rows=ownerComp.op('container_scroll/container_content')
        self._viewport=ownerComp.op('container_scroll')
        self._draft=ownerComp.op('base_draft')
        self._main=ownerComp.op('window_main')
        self._popup=ownerComp.op('window_editor')
        self._editors=(self._rows.op('editor_below'),ownerComp.op('editor_popup'))
        self._row_refs=[dict(row=self._rows.op('slot'+str(i)),name=self._rows.op('slot'+str(i)+'/text_name'),value=self._rows.op('slot'+str(i)+'/text_value'),slot=self._rows.op('slot'+str(i)+'/text_slot'),arrow=self._rows.op('slot'+str(i)+'/text_arrow')) for i in range(16)]
        self.Connect()

    def Key(self):return tuple(self.ownerComp.par[n].eval() for n in ('Layout','Track','Device'))

    def Connect(self):
        self.Disconnect()
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
        if self._model:self._model.Unsubscribe(self._identity,self.OnModelChange)
        self._model=None

    def onInitTD(self):
        if not self._model:self.Connect()

    def onDestroyTD(self):self.Disconnect()

    def _visible(self):return self._main.isOpen

    def _write(self,op,value):
        op.par.text=value;self._writes+=1

    def _refresh_rows(self,slots,metadata):
        if not self._model:return
        catalog=self._model.GetCatalog(self._context)
        for i,refs in enumerate(self._row_refs):
            if not slots&(1<<i):continue
            record=catalog[i]
            label=record['Label'];mapped=bool(record['Destination'])
            value=self._model.ValueText(self._context,i) if self.IsLive() else (format(record['Value'],'.3g') if mapped else '—')
            previous=self._display.get(i)
            if previous is None or previous[0]!=label:self._write(refs['name'],label)
            if previous is None or previous[1]!=mapped:ink(refs['name'],TEXT if mapped else MUTED)
            if previous is None or previous[2]!=value:self._write(refs['value'],value)
            self._display[i]=(label,mapped,value)
        self._dirty&=~slots;self._metadata_dirty&=~metadata

    def OnModelChange(self,context,slots,metadata,learn_changed,generation):
        if self.IsLive() and (learn_changed or metadata or not self._model.HasContext(self._context)):
            self.ConfigureMenus(self._model.ActiveContext() if self._follow_routing else self.Key())
            if self.Key()!=self._context:
                self.Refresh();return
        if context!=self._context:return
        self._notifications+=1;self._dirty|=slots;self._metadata_dirty|=metadata
        if self._visible():self._refresh_rows(self._dirty,self._metadata_dirty)
        if learn_changed:self._theme()
        if learn_changed and self._clear_pending:
            self._disarm_clear();self._set_error('Clear cancelled · controller state changed')
        if self.selected is not None and self._model.GetToken(self._context,self.selected)!=self._token:
            self._disarm_clear()
            self._set_error('Mapping changed; reopen this control')

    def _disarm_clear(self):
        self._clear_pending=None
        for e in self._editors:
            if e.op('clear'):e.op('clear/text_label').par.text='⌫'

    def _set_error(self,message):
        self._error=message
        for e in self._editors:e.op('text_status').par.text=message

    def Hint(self,name,hover):
        if self.selected is None or self._clear_pending:return
        hints=dict(ping='Ping · resend mapping in HW LEARN',clear='Clear · remove this mapping',cancel='Cancel · discard Value draft',apply='Apply · write Value to target')
        if name not in hints:return
        text=hints[name] if hover else (self._error or ('Value edits live target' if self.IsLive() and self.Key()==self._model.ActiveContext() else 'Browse only · mapping read-only'))
        for e in self._editors:e.op('text_status').par.text=text

    def _theme(self):
        learn=bool(self._model and self._model.Learn)
        c=self.ownerComp
        paint(c,(.14,.135,.125) if learn else BASE)
        paint(self._viewport,(.14,.135,.125) if learn else BASE)
        c.op('text_status').par.text='●  LEARN MODE ON' if learn else ((('Connected' if self._model.Status.get('Connected') else 'Disconnected')+' · '+('live' if self.Key()==self._model.ActiveContext() else 'browse')) if self.IsLive() else '16 controls  ·  click to edit')
        ink(c.op('text_status'),(.80,.78,.72) if learn else MUTED)
        c.op('learn/text_label').par.text=('LEARN ON' if learn else 'HW Learn') if self.IsLive() else ('Exit Learn' if learn else 'Learn')
        paint(c.op('learn'),(.25,.24,.215) if learn else SURFACE)
        for i,refs in enumerate(self._row_refs):
            paint(refs['row'],(.20,.20,.20) if self.selected==i else ((.17,.165,.15) if learn else BASE))
            ink(refs['slot'],ACCENT if self.selected==i else MUTED)
        c.op('text_brand').par.text=('LIVE' if self._follow_routing else 'BROWSE') if self.IsLive() else 'DEMO'
        for e in self._editors:paint(e,(.18,.175,.16) if learn else SURFACE)

    def _editor_layout(self):
        extra=EDITOR+8 if self.selected is not None and self.style=='below' else 0
        self._rows.par.h=16*ROW+extra
        for i,refs in enumerate(self._row_refs):
            refs['row'].par.y=16*ROW+extra-i*ROW-(extra if self.selected is not None and i>self.selected else 0)-24
            refs['arrow'].par.text='−' if self.selected==i else '+'
        below=self._editors[0];below.par.display=bool(extra)
        if extra:below.par.y=16*ROW+extra-(self.selected+1)*ROW-EDITOR-4
        for e in self._editors:
            for n in ['label_Label','label_Destination','label_Range','label_Value','field_Label','field_Destination','field_Minimum','field_Maximum','field_Value','apply','cancel','ping','clear']:
                if not e.op(n):continue
                e.op(n).par.display=self.selected is not None
            e.op('text_empty').par.display=self.selected is None
            e.op('text_heading').par.text=(('KNOB ' if self.selected<8 else 'BUTTON ')+str(self.selected%8+1)) if self.selected is not None else 'MAPPING EDITOR'
            editable=True
            if self.IsLive():
                info=self._model.Info(self._context,self.selected) if self.selected is not None else {}
                editable=bool(info.get('valid') and info.get('available') and info.get('mode')!='pulse' and self.Key()==self._model.ActiveContext())
                for n in FIELDS:e.op('field_'+n).par.editmode='editable' if n=='Value' and editable else 'selectonly'
                e.op('apply').par.enable=editable
            assigned=bool(self.IsLive() and self.selected is not None and self._model.Info(self._context,self.selected).get('id') and self.Key()==self._model.ActiveContext())
            for n in ('ping','clear'):
                if e.op(n):e.op(n).par.enable=assigned
            e.op('text_status').par.text=self._error or (('Value edits live target' if editable else 'Browse only · mapping read-only') if self.IsLive() and self.selected is not None else ('Draft · live values update in list' if self.selected is not None else ''))

    def Refresh(self):
        if not self._model:return False
        if self.IsLive():self.ConfigureMenus(self._model.ActiveContext() if self._follow_routing else self.Key())
        context=self.Key()
        if context!=self._context:
            self._context=context;self._model.Subscribe(self._identity,context,self.OnModelChange)
            self.selected=None;self._token=None;self._original=None;self._error='';self._display={}
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
        width=self._main.contentWidth;x=self._main.x+self._main.width+8
        border=self._main.height-self._main.contentHeight
        y=self._main.y+self._main.height-EDITOR-border
        if self._popup.isOpen and self._popup.contentWidth==width and self._popup.contentHeight==EDITOR and self._popup.x==x and self._popup.y==y:return
        self._popup.par.justifyoffsetto='primarydisplay';self._popup.par.justifyh='left';self._popup.par.justifyv='bottom'
        self._popup.par.winw=width;self._popup.par.winh=EDITOR;self._popup.par.winoffsetx=x;self._popup.par.winoffsety=y
        self._popup.par.winopen.pulse();self._window_opens+=1

    def CloseEditor(self):
        self._disarm_clear()
        self.selected=None;self._token=None;self._original=None;self._error=''
        self._editor_layout();self._theme()

    def DismissPopup(self):
        self.CloseEditor();self._popup.par.winclose.pulse()

    def Action(self,name):
        if not self._model and not self.Connect():return False
        if not isinstance(name,str):return False
        if name.startswith('context_'):
            n=name.split('_',1)[1]
            if n not in ('Layout','Track','Device'):return False
            if self.IsLive():
                self._follow_routing=False;self.ConfigureMenus(self.Key())
            p=self.ownerComp.par[n];choices=list(p.menuNames)
            p.val=choices[(choices.index(p.eval())+1)%len(choices)];self.OnContext()
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
                        for e in self._editors:e.op('clear/text_label').par.text='?'
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
