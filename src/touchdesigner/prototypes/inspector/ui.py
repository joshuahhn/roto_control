"""Native inspector design study. Demo state only; no hardware calls."""
import math
selected = None
style = 'below'
learn = False
records = {}
ROW = 26
EDITOR = 194
BASE = (.085, .085, .085)
SURFACE = (.12, .12, .12)
ACCENT = (.76, .76, .76)
TEXT = (.86, .86, .86)
MUTED = (.50, .50, .50)

def owner(): return op(__name__).parent()

def paint(o, rgb):
    o.par.bgcolorr, o.par.bgcolorg, o.par.bgcolorb = rgb

def ink(o, rgb):
    o.par.fontcolorr, o.par.fontcolorg, o.par.fontcolorb = rgb

def content(): return owner().op('container_scroll/container_content')
def key(): return tuple(owner().par[n].eval() for n in ('Layout','Track','Device'))
def editors(): return (content().op('editor_below'), owner().op('editor_popup'))

def fixture(i):
    pixel = owner().par.Device.eval() == 'pixelsort'
    specs = [('Sort criterion','Sortcrit',0,4,4),('Low threshold','Lowthresh',0,1,.45),('High threshold','Highthresh',0,1,.85),('Mix','Mix',0,1,1)] if pixel else [('Power','Power',0,16,8.16)]
    if i >= len(specs): return dict(Label='Unassigned',Destination='',Minimum=0.,Maximum=1.,Value=0.)
    name, target, low, high, value = specs[i]
    return dict(Label=name,Destination=target,Minimum=low,Maximum=high,Value=value)

def open_popup():
    c=owner(); main=c.op('window_main'); popup=c.op('window_editor')
    popup.par.justifyoffsetto='primarydisplay'; popup.par.justifyh='left'; popup.par.justifyv='bottom'
    popup.par.winw=main.contentWidth; popup.par.winh=EDITOR
    popup.par.winoffsetx=main.x+main.width+8
    popup.par.winoffsety=main.y+main.height-EDITOR-32
    popup.par.winopen.pulse()
    popup.par.winoffsety=main.y+main.height-popup.height
    popup.par.winopen.pulse()

def close():
    global selected
    selected=None
    owner().op('window_editor').par.winclose.pulse()
    render()

def context(): close()

def action(name):
    global selected,style,learn
    c=owner()
    if name.startswith('context_'):
        p=c.par[name.split('_',1)[1]]
        choices=list(p.menuNames); p.val=choices[(choices.index(p.eval())+1)%len(choices)]
        close()
    elif name in ('below','popup'):
        style=name; c.op('window_editor').par.winclose.pulse(); render()
        if selected is not None and style=='popup': open_popup()
    elif name=='learn': learn=not learn; render()
    elif name=='cancel': close()
    elif name=='apply':
        if selected is None: return
        d=c.op('base_draft')
        values={n:d.par[n].eval() for n in ('Label','Destination','Minimum','Maximum','Value')}
        if not all(math.isfinite(values[n]) for n in ('Minimum','Maximum','Value')) or values['Minimum']>=values['Maximum']:
            for e in editors(): e.op('text_status').par.text='Enter a valid range: min < max'
            return
        records[(key(),selected)]=values; close()
    elif name.startswith('slot'):
        i=int(name[4:])
        if selected==i: close(); return
        selected=i
        for n,v in records.get((key(),i),fixture(i)).items(): c.op('base_draft').par[n]=v
        render()
        if style=='popup': open_popup()

def render():
    c=owner(); rows=content(); extra=EDITOR+8 if selected is not None and style=='below' else 0
    rows.par.h=16*ROW+extra
    paint(c,(.14,.135,.125) if learn else BASE)
    paint(c.op('container_scroll'),(.14,.135,.125) if learn else BASE)
    c.op('text_status').par.text='●  LEARN MODE ON' if learn else '16 controls  ·  click to edit'
    ink(c.op('text_status'),(.80,.78,.72) if learn else MUTED)
    c.op('learn/text_label').par.text='Exit Learn' if learn else 'Learn'
    paint(c.op('learn'),(.25,.24,.215) if learn else SURFACE)
    for n in ('Layout','Track','Device'):
        c.op('context_'+n+'/text_value').par.text=c.par[n].menuLabels[c.par[n].menuIndex]
    c.op('text_style').par.text='BELOW' if style=='below' else 'POPUP'
    for i in range(16):
        row=rows.op('slot'+str(i)); record=records.get((key(),i),fixture(i)); active=selected==i
        row.par.y=16*ROW+extra-i*ROW-(extra if selected is not None and i>selected else 0)-24
        paint(row,(.20,.20,.20) if active else ((.17,.165,.15) if learn else BASE))
        row.op('text_name').par.text=record['Label']
        ink(row.op('text_name'),TEXT if record['Destination'] else MUTED)
        row.op('text_value').par.text=format(record['Value'],'.3g') if record['Destination'] else '—'
        ink(row.op('text_slot'),ACCENT if active else MUTED)
        row.op('text_arrow').par.text='−' if active else '+'
    below=rows.op('editor_below'); below.par.display=bool(extra)
    if extra: below.par.y=16*ROW+extra-(selected+1)*ROW-EDITOR-4
    for e in editors():
        paint(e,(.18,.175,.16) if learn else SURFACE)
        e.op('text_heading').par.text=('KNOB ' if selected is None or selected<8 else 'BUTTON ')+str((selected or 0)%8+1)+'  /  MAPPING'
        e.op('text_status').par.text='Learn mode is active' if learn else 'Changes stay in this demo'

def scroll_wheel(delta):
    """Translate captured wheel steps into the native scrollbar position."""
    if not delta: return
    viewport = owner().op('container_scroll')
    travel = max(0, content().height - viewport.height)
    if travel:
        viewport.panel.scrollv = max(0., min(1., viewport.panel.scrollv.val - float(delta) * 32. / travel))
