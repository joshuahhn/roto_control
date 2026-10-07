"""External builder for the native inspector design study."""
from pathlib import Path
prototype_name=globals().get('prototype_name','inspector_below')
prototype_style=globals().get('prototype_style','below')
c=op('/'+prototype_name)
if c:
    if c.extensions[0] is not None:c.ext.InspectorView.Disconnect()
    popup=c.op('window_editor')
    if popup: popup.par.winclose.pulse()
    for name in [o.name for o in c.children]:
        o=c.op(name)
        if o and name!='window_main': o.destroy()
else:
    c=op('/').create(containerCOMP,prototype_name); c.nodeX=400; c.nodeY=0
    c.par.w=240; c.par.h=390
c.par.ext0object=''
c.nodeX=400 if prototype_style=='below' else 750;c.nodeY=0
c.viewer=True; c.par.parentshortcut='InspectorDemo'; c.par.opshortcut=''
c.par.sizefromwindow=True; c.par.fit='off'; c.par.bgalpha=1
if not c.customPages:
    page=c.appendCustomPage('Browse')
    for name,choices,labels in [('Layout',['main','live'],['Main','Live set']),('Track',['track1','track2'],['Track 1','Track 2']),('Device',['pixelsort','fractal'],['pixelSortV3','fractal_pop'])]:
        p=page.appendMenu(name)[0]; p.menuNames=choices; p.menuLabels=labels; p.val=choices[0]
else:
    c.par.Device.menuLabels=['pixelSortV3','fractal_pop']
if not hasattr(c.par,'Model'):
    viewpage=c.appendCustomPage('View')
    viewpage.appendOP('Model',label='Shared model')
    presentation=viewpage.appendMenu('Presentation')[0];presentation.menuNames=['below','popup'];presentation.menuLabels=['Fold','Popup']
c.par.Model.expr="getattr(op, 'InspectorModel', None)"
c.par.Presentation=prototype_style
d=c.create(baseCOMP,'base_draft'); d.viewer=True
p=d.appendCustomPage('Mapping')
for n in ('Label','Destination'): p.appendStr(n)
for n in ('Minimum','Maximum','Value'): p.appendFloat(n)
d.par.Maximum=1
ui=c.create(textDAT,'ui'); ui.par.language='python'; ui.viewer=True
ui.text=Path(project.folder+'/prototypes/inspector/ui.py').read_text()
u=ui.module

def panel(parent,typ,name,x,y,w,h,bg=None):
    o=parent.create(typ,name); o.name=name; o.viewer=True
    o.par.x=x; o.par.y=y; o.par.w=w; o.par.h=h
    o.par.fit='off'; o.par.bgalpha=1 if bg else 0
    for edge in ('leftborder','rightborder','topborder','bottomborder','leftborderi','rightborderi','topborderi','bottomborderi'): o.par[edge]='off'
    if bg: u.paint(o,bg)
    return o

def text(parent,name,value,x,y,w,h,size=12,color=None):
    o=panel(parent,textCOMP,name,x,y,w,h)
    o.par.text=value; o.par.fontsize=size; o.par.fontsizeunits='panelunits'
    o.par.alignx='left'; o.par.aligny='center'; o.par.textpaddingl=0; o.par.textpaddingr=0; o.par.clickthrough=True
    u.ink(o,color or u.TEXT)
    return o

def button(parent,name,label,x,y,w,h,bg=None):
    o=panel(parent,containerCOMP,name,x,y,w,h,bg or u.SURFACE)
    t=text(o,'text_label',label,0,0,w,h); t.par.alignx='center'; t.par.w.expr='parent().width'
    cb=parent.create(panelexecuteDAT,'click_'+name); cb.viewer=True
    cb.par.panels=name; cb.par.panelvalue='lselect'; cb.par.offtoon=True
    cb.text="def onOffToOn(panelValue):\n    parent.InspectorDemo.op('ui').module.action(%r)\n" % name
    return o

def top(o,t): o.par.y.expr='parent().height - %d - me.height' % t

def stretch(o,inset=0): o.par.w.expr='parent().width - %d' % inset

t=text(c,'text_title','Inspector',12,0,160,24,17); top(t,8)
t=text(c,'text_brand','DEMO',0,0,44,24,8,u.MUTED); top(t,8); t.par.alignx='right'; t.par.x.expr='parent().width-56'
for i,n in enumerate(('Layout','Track')):
    b=button(c,'context_'+n,'',12,0,104,28); top(b,40)
    b.par.w.expr='(parent().width-30)/2'; b.par.x.expr='12+%d*(me.width+6)'%i
    text(b,'text_caption',n.upper(),8,16,80,10,8,u.MUTED)
    text(b,'text_value','',8,2,75,16,11)
    t=text(b,'text_cycle','↔',0,3,14,18,10,u.MUTED); t.par.x.expr='parent().width-18'
b=button(c,'context_Device','',12,0,216,30); top(b,74); stretch(b,24)
text(b,'text_caption','DEVICE',8,0,48,30,8,u.MUTED)
t=text(b,'text_value','',58,0,132,30,11); t.par.w.expr='parent().width-82'
t=text(b,'text_cycle','↔',0,0,14,30,10,u.MUTED); t.par.x.expr='parent().width-18'
t=text(c,'text_style','',12,0,132,24,9,u.ACCENT); top(t,110); stretch(t,108)
b=button(c,'learn','Learn',0,0,72,24); top(b,110); b.par.x.expr='parent().width-84'
t=text(c,'text_status','',12,0,216,18,10,u.MUTED); top(t,138); stretch(t,24)
t=text(c,'text_footer','SCROLL TO BROWSE',12,1,216,16,8,u.MUTED); stretch(t,24)
v=panel(c,containerCOMP,'container_scroll',0,18,240,216)
v.par.w.expr='parent().width'; v.par.h.expr='max(1,parent().height-174)'; v.par.crop='on'; v.par.mousewheel=True; v.par.pvscrollbar='auto'; v.par.scrollbarthickness=6
wheel=c.create(panelexecuteDAT,'scroll_wheel'); wheel.viewer=True
wheel.par.panels='container_scroll'; wheel.par.panelvalue='wheel'; wheel.par.offtoon=False; wheel.par.valuechange=True
wheel.text="def onValueChange(panelValue, prev):\n    parent.InspectorDemo.op('ui').module.scroll_wheel(panelValue.val)\n"
content=panel(v,containerCOMP,'container_content',0,0,234,416)
content.par.w.expr='parent().width-6'; content.par.y.expr='parent().height-me.height'
for i in range(16):
    row=button(content,'slot'+str(i),'',12,0,210,24,u.BASE); stretch(row,24)
    text(row,'text_slot',('K' if i<8 else 'B')+str(i%8+1),4,0,24,24,10,u.MUTED)
    t=text(row,'text_name','',32,0,120,24,11); t.par.w.expr='max(1,parent().width-92)'
    t=text(row,'text_value','',0,0,40,24,10,u.MUTED); t.par.alignx='right'; t.par.x.expr='parent().width-58'
    t=text(row,'text_arrow','+',0,0,12,24,12,u.MUTED); t.par.x.expr='parent().width-12'
    row.op('text_label').destroy()
for name,parentcomp in [('editor_below',content),('editor_popup',c)]:
    e=panel(parentcomp,containerCOMP,name,12 if name=='editor_below' else 0,0,210,178,u.SURFACE)
    if name=='editor_below': stretch(e,24)
    else:
        e.par.display=False
        e.par.w.expr="parent.InspectorDemo.op('window_editor').contentWidth if parent.InspectorDemo.op('window_editor').isOpen else parent.InspectorDemo.width"
    t=text(e,'text_empty','Select a control in the Inspector',12,64,186,44,11,u.MUTED); stretch(t,24)
    t.par.type='multiline';t.par.wordwrap=True;t.par.alignx='center'
    t=text(e,'text_heading','',12,151,186,18,9,u.ACCENT); stretch(t,24)
    for n,label,y in [('Label','Label',120),('Destination','Target',92),('Value','Value',36)]:
        text(e,'label_'+n,label,12,y,46,22,10,u.MUTED)
        f=text(e,'field_'+n,'',62,y,136,22,11)
        f.par.clickthrough=False; f.par.editmode='editable'; f.par.textpaddingl=6; f.par.textpaddingr=6; f.par.textpaddingunits='panelunits'
        f.par.bgalpha=1; u.paint(f,(.08,.08,.08)); stretch(f,74)
        f.par.text.bindExpr="parent.InspectorDemo.op('base_draft').par.%s"%n
        if n=='Value': f.par.type='float'; f.par.precision=3
    text(e,'label_Range','Range',12,64,46,22,10,u.MUTED)
    for i,n in enumerate(('Minimum','Maximum')):
        f=text(e,'field_'+n,'',62,64,65,22,11)
        f.par.clickthrough=False; f.par.editmode='editable'; f.par.type='float'; f.par.precision=3; f.par.textpaddingl=6; f.par.textpaddingr=6; f.par.textpaddingunits='panelunits'
        f.par.bgalpha=1; u.paint(f,(.08,.08,.08))
        f.par.w.expr='(parent().width-80)/2'; f.par.x.expr='62+%d*(me.width+6)'%i
        f.par.text.bindExpr="parent.InspectorDemo.op('base_draft').par.%s"%n
    t=text(e,'text_status','',12,6,186,24,9,u.MUTED); stretch(t,24)
    for i,n in enumerate(('cancel','apply')):
        b=button(e,n,n.title(),12,6,100,22,(.23,.23,.23) if n=='apply' else (.17,.17,.17))
        b.par.w.expr='(parent().width-30)/2'; b.par.x.expr='12+%d*(me.width+6)'%i
        u.ink(b.op('text_label'),u.ACCENT if n=='apply' else u.TEXT)
if not c.op('window_main'): c.create(windowCOMP,'window_main')
for name,target,title,w,h in [('window_main','', 'Inspector / '+('Fold' if prototype_style=='below' else 'Popup'),240,390),('window_editor','editor_popup','Edit mapping',240,178)]:
    o=c.op(name) or c.create(windowCOMP,name); o.viewer=True
    o.par.winop.expr='parent.InspectorDemo' if not target else "parent.InspectorDemo.op('editor_popup')"
    o.par.title=title; o.par.size='custom'; o.par.winw=w; o.par.winh=h; o.par.borders=True; o.par.bordersinsize=False
cb=c.create(parameterexecuteDAT,'context_changed'); cb.viewer=True; cb.par.op.expr='parent.InspectorDemo'; cb.par.pars='Layout Track Device'; cb.par.builtin=False
cb.text="def onValueChange(par,prev):\n    parent.InspectorDemo.op('ui').module.context()\n"
windowcb=c.create(parameterexecuteDAT,'window_opened');windowcb.viewer=True
windowcb.par.op='window_main';windowcb.par.pars='winopen';windowcb.par.custom=False;windowcb.par.builtin=True
windowcb.text="def onPulse(par):\n    parent.InspectorDemo.OnWindowOpen()\n"
for p in [c,v,content]+[content.op('slot'+str(i)) for i in range(16)]+list([content.op('editor_below'),c.op('editor_popup')]):
    for i,o in enumerate(p.children): o.nodeX=(i%5)*200; o.nodeY=-(i//5)*160
action_namespace=dict(globals(),action_views=[c])
exec(Path(project.folder+'/prototypes/inspector/build_editor_actions.py').read_text(),action_namespace)
exec(Path(project.folder+'/prototypes/inspector/build_mapping.py').read_text(),dict(globals(),action_views=[c]))
c.seq.ext.numBlocks=1;c.par.initextonstart=True
c.par.ext0object="op('./ui').module.InspectorView(me)";c.par.ext0promote=True
c.initializeExtensions(0)
print(c.path,c.Stats())
