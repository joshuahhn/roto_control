"""Temporary physical FUNC/SEL + Inspector click recorder; never sends MIDI.

Execute this file in TD in a separate namespace, then Start(controller, path).
Mark(controller, 'FUNC shown') associates a human observation with captured wire
events. Save(controller) writes a snapshot. Stop(controller) restores all hooks
and writes the final report. Screen state is never guessed from a packet alone.
No nodes, timers, new MIDI ports, synthetic packets or registration writes.
"""
from collections import deque
from pathlib import Path
from time import monotonic
import json

HEADER=(240,0,34,3,2)
COMMANDS={
    10:{1:'DAW_STARTED',2:'PING_DAW',3:'DAW_PING_RESP',4:'NUM_TRACKS',5:'FIRST_TRACK',6:'SET_FIRST_TRACK',7:'TRACK_DETAILS',8:'TRACK_DETAILS_END',9:'SELECT_TRACK',12:'ROTO_DAW_CONNECTED',20:'PAGE_LEFT',21:'PAGE_RIGHT',22:'DISPLAY_NAME'},
    11:{1:'SET_PLUGIN_MODE',2:'NUM_DEVICES',3:'FIRST_DEVICE',4:'SET_FIRST_DEVICE',5:'DEVICE_DETAILS',6:'DEVICE_DETAILS_END',7:'SELECT_DEVICE',8:'DAW_SELECT_DEVICE',9:'SET_DEVICE_LEARN',10:'LEARN_PARAM',11:'CONTROL_MAPPED',12:'SET_PLUGIN_ENABLE',13:'SET_PLUGIN_LOCK',14:'UNMAP_CONTROL'},
    12:{1:'SET_MIXER_ALL_MODE',2:'SET_MIXER_SELECTED_MODE',4:'DAW_SELECT_TRACK',5:'SET_MIXER_CHANNEL_MODE'}
}

def Decode(message):
    raw=tuple(message)
    if len(raw)<8 or raw[:5]!=HEADER or raw[-1]!=247 or any(type(n)is not int or not 0<=n<128 for n in raw[1:-1]):return None
    group,command=raw[5:7]
    # Continuous display feedback is unrelated to tabs and would drown the trace.
    if group==10 and command in (11,24) or group==11 and command in (15,):return None
    return dict(group=group,command=command,name=COMMANDS.get(group,{}).get(command,'UNKNOWN'),data=list(raw[7:-1]),raw=list(raw),family={10:'GENERAL / Track',11:'PLUGIN / Device',12:'MIX'}.get(group,'UNKNOWN'))

class Recorder:
    def __init__(self,snapshot,capacity=512,clock=monotonic):
        self.snapshot=snapshot;self.clock=clock;self.started=clock();self.sequence=0;self.events=deque(maxlen=capacity)
        self.dropped=0;self.errors=0
    def Event(self,kind,data):
        try:
            self.sequence+=1
            if len(self.events)==self.events.maxlen:self.dropped+=1
            self.events.append(dict(sequence=self.sequence,seconds=round(self.clock()-self.started,6),kind=kind,data=data,context=self.snapshot()))
        except Exception:self.errors+=1  # A probe failure must never break dispatch.
    def Packet(self,kind,message,**extra):
        decoded=Decode(message)
        if decoded is not None:self.Event(kind,dict(decoded,**extra))
    def Report(self):
        return dict(schema=1,temporary_readonly_probe=True,screen_state_requires_human_markers=True,
                    queued_tx_is_not_wire_delivery=True,capacity=self.events.maxlen,dropped=self.dropped,
                    logging_errors=self.errors,events=list(self.events))

def Snapshot(controller,views=()):
    routing=dict(controller.GetLayoutContext());state=controller.State
    layout=routing.get('layout_id')
    tracks=controller.GetTracks(layout) if layout else []
    track=routing.get('track_id')
    devices=controller.GetPlugins(layout,track) if layout and track else []
    return dict(routing=routing,tracks=[dict(id=t['id'],name=t['name']) for t in tracks[:64]],track_count=len(tracks),
                devices=[dict(id=d['id'],name=d['name']) for d in devices[:64]],device_count=len(devices),
                connected=state['Connected'],plugin=state['Plugin'],learning=state['Learning'],
                views=[dict(path=v.ownerComp.path,key=v.Key(),follows_routing=v._follow_routing,
                            dropdown=(dict(name=v._context_menu.details['name'],first=v._context_menu.first) if getattr(v,'_context_menu',None) else None)) for v in views],
                controls=[dict(id=r['id'],kind=r['kind'],slot=r['slot'],comp=r['comp'],parameter=r['parameter']) for r in controller.GetControlCatalog()])

def Start(controller,path,views=(),menu=None):
    ext=controller.ext.RotoPythonExt
    if getattr(ext,'_tab_layout_probe',None):raise ValueError('Tab probe already running; Stop first')
    views=tuple(views);rec=Recorder(lambda:Snapshot(controller,views));hooks=[]
    rec.Event('start',dict(controller=controller.path,source='physical messages only'))
    Path(path).write_text(json.dumps(rec.Report(),indent=2))  # Validate output before installing hooks.
    def install(target,name,wrapper):
        original=getattr(target,name);had_override=name in vars(target);previous=vars(target).get(name)
        replacement=wrapper(original);setattr(target,name,replacement)
        hooks.append((target,name,replacement,had_override,previous))
    def receive(original):
        def wrapped(message,*args,**kwargs):
            rec.Packet('rx_before',message)
            try:return original(message,*args,**kwargs)
            finally:rec.Packet('rx_after',message)
        return wrapped
    def send(original):
        def wrapped(message,*args,**kwargs):
            result=original(message,*args,**kwargs)
            rec.Packet('queued_tx',message,accepted=result is not False)
            return result
        return wrapped
    def call(kind):
        def wrapper(original):
            def wrapped(*args,**kwargs):
                rec.Event(kind,dict(args=[str(n) for n in args]))
                return original(*args,**kwargs)
            return wrapped
        return wrapper
    def item_selection(original):
        def wrapped(info,*args,**kwargs):
            details=info.get('details',{})
            rec.Event('item_callback_before',dict(item=info.get('item'),name=details.get('name'),
                      menu_generation=details.get('generation'),model_generation=details.get('model_generation')))
            result=original(info,*args,**kwargs)
            rec.Event('item_callback_after',dict(item=info.get('item'),accepted=bool(result)))
            return result
        return wrapped
    def list_selection(target):
        def wrapper(original):
            def wrapped(*args,**kwargs):
                # Lister's actual native onSelect signature supplies start/end
                # flags and cells. Record only those scalars, before dispatch.
                rec.Event('native_list_selection',dict(
                    startrow=args[0] if len(args)>0 else None,
                    startcol=args[1] if len(args)>1 else None,
                    endrow=args[3] if len(args)>3 else None,
                    endcol=args[4] if len(args)>4 else None,
                    start=args[6] if len(args)>6 else kwargs.get('start'),
                    end=args[7] if len(args)>7 else kwargs.get('end'),
                    click=target.ownerComp.panel.click.val,
                    inside=target.ownerComp.panel.inside.val,
                    focus=target.ownerComp.panel.focusselect.val,
                    previous_click=target._clickedOnce))
                return original(*args,**kwargs)
            return wrapped
        return wrapper
    try:
        install(ext,'_receive_midi',receive);install(ext._host,'send',send)
        for view in views:
            install(view,'OpenContextMenu',call('selector_click'))
            if hasattr(view,'SelectContextMenu'):install(view,'SelectContextMenu',item_selection)
            if hasattr(view,'SelectContextItem'):install(view,'SelectContextItem',call('selector_item_press'))
        if menu:
            for name in ('winOpen','LostFocus','Close','OnMouseDown','OnMouseUp','OnClick','OnSelect'):
                if hasattr(menu,name):install(menu,name,call('menu_'+name))
            lister=getattr(menu,'Lister',None)
            if lister:
                native=lister.ext.ListerExt
                install(native,'onSelect',list_selection(native))
                install(native,'DoubleClick',call('native_double_click'))
        ext._tab_layout_probe=dict(recorder=rec,hooks=hooks,path=str(path),views=views)
    except Exception:
        for target,name,replacement,had_override,previous in reversed(hooks):
            if had_override:setattr(target,name,previous)
            else:delattr(target,name)
        raise
    Save(controller)
    return rec.Report()

def Mark(controller,label):
    probe=controller.ext.RotoPythonExt._tab_layout_probe
    probe['recorder'].Event('human_marker',dict(label=str(label)));return Save(controller)

def Save(controller):
    probe=getattr(controller.ext.RotoPythonExt,'_tab_layout_probe',None)
    if not probe:raise ValueError('Tab probe is not running')
    report=probe['recorder'].Report();Path(probe['path']).write_text(json.dumps(report,indent=2));return report

def Stop(controller):
    ext=controller.ext.RotoPythonExt;probe=getattr(ext,'_tab_layout_probe',None)
    if not probe:return None
    probe['recorder'].Event('stop',{})
    conflicts=[]
    for target,name,replacement,had_override,previous in reversed(probe['hooks']):
        if getattr(target,name) is not replacement:conflicts.append(name);continue
        if had_override:setattr(target,name,previous)
        else:delattr(target,name)
    report=probe['recorder'].Report();report['restore_conflicts']=conflicts
    try:Path(probe['path']).write_text(json.dumps(report,indent=2))
    finally:delattr(ext,'_tab_layout_probe')
    return report
