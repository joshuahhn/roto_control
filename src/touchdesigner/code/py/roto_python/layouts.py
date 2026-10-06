"""Versioned parameter-layout database and serialized host activation.

Callbacks remain supported by the legacy API, but cannot be converted without a
reconstruction factory. No target value or callable is persisted as a preset.
"""
import copy
import os
import uuid
from protocol import digest, display_name, sysex, text13
from binding import parameter_value

VERSION=1
FIELDS=('parameter_assignments','assignment_device_id','control_overrides','removed_controls','pending_unmaps','needs_relearn','control_catalog','pending_unmap_identities')
DEFAULTS=([],None,{},[],[],(),[],[])

class Layouts:
    def __init__(self, extension):
        self.ext=extension;self.owner=extension.ownerComp
        self.mutating=False;self.locked=False;self.touched=set();self.confirmed=False
        self.delete_pending=None
        self.legacy=False
        data=self.owner.fetch('layout_registry',None)
        if data is None:
            record=self.snapshot('custom','Custom')
            data=dict(version=VERSION,active='custom',records=[record])
        self.validate(data)
        self.data=copy.deepcopy(data)
        self.save();self.attach();self.menu()

    @staticmethod
    def validate(data):
        if not isinstance(data,dict) or data.get('version')!=VERSION:
            raise ValueError('Unsupported Layout database version')
        records=data.get('records')
        if not isinstance(records,list) or not 1<=len(records)<=8:
            raise ValueError('Layout database needs 1..8 Layouts')
        ids=set();groups=set()
        for record in records:
            if not isinstance(record,dict) or not isinstance(record.get('id'),str) or not record['id'] or record['id'] in ids:
                raise ValueError('Invalid or duplicate Layout ID')
            ids.add(record['id'])
            if not isinstance(record.get('name'),str) or not record['name'].strip(): raise ValueError('Layout name is required')
            if not isinstance(record.get('group_id'),str) or not record['group_id'] or record['group_id'] in groups: raise ValueError('Invalid or duplicate Layout group identity')
            groups.add(record['group_id'])
            display_name(record['track_name']);display_name(record['plugin_name'])
            if not isinstance(record.get('targets'),list) or not isinstance(record.get('state'),dict): raise ValueError('Invalid Layout target/state records')
            slots=set();target_ids=set()
            for target in record['targets']:
                key=(target['kind'],target['slot'])
                if key[0] not in ('knob','button') or type(key[1]) is not int or not 1<=key[1]<=8 or key in slots or target['id'] in target_ids: raise ValueError('Invalid or duplicate Layout target slot/ID')
                slots.add(key);target_ids.add(target['id'])
        if data.get('active') not in ids: raise ValueError('Active Layout is missing')

    def save(self):
        self.validate(self.data)
        if self.owner.fetch('layout_registry',None)!=self.data: self.owner.store('layout_registry',copy.deepcopy(self.data))

    def record(self,id=None):
        id=self.data['active'] if id is None else id
        for record in self.data['records']:
            if record['id']==id:return record
        raise ValueError('Unknown Layout ID: '+str(id))

    def snapshot(self,id,name):
        ext=self.ext;targets=[]
        old=self.record(id) if hasattr(self,"data") and any(r["id"]==id for r in self.data["records"]) else None
        bindings=ext._collection.bindings.items() if ext._collection is not None else [(('knob',1),ext._binding)]
        for key,binding in bindings:
            if binding is None:
                # Built-in Value remains a real target, never a saved numeric preset.
                parameter=self.owner.par.Value
                target=dict(kind='knob',slot=1,id='Value',label='Value',minimum=0,maximum=1,mode='value',button_type=None,index=0)
            else:
                parameter=binding.parameter
                if parameter is None: raise ValueError('Callback Layouts need a reconstruction factory; existing callback API is unchanged')
                target=dict(kind=key[0],slot=key[1],id=binding.id,label=binding.label,minimum=binding.minimum,maximum=binding.maximum,
                            mode=ext._collection.modes[key] if ext._collection is not None else 'value',
                            button_type=ext._collection.button_types[key] if ext._collection is not None else None,
                            index=ext._collection.indices[key] if ext._collection is not None else 0)
            target['identity']=ext._host.controls[key].target_id if ext._collection is not None else ext._host.target_id
            target['menu_names']=list(binding.menu_names) if binding is not None else []
            target['menu_labels']=list(binding.menu_labels) if binding is not None else []
            if not getattr(parameter.owner,'valid',True):
                previous=next((t for t in old['targets'] if t['id']==target['id']),None) if old else None
                if previous is None:raise ValueError('Unavailable target needs a saved Layout record')
                targets.append(copy.deepcopy(previous));continue
            target.update(comp=os.path.relpath(parameter.owner.path,self.owner.path),parameter=parameter.name)
            targets.append(target)
        old=self.record(id) if hasattr(self,'data') and any(r['id']==id for r in self.data['records']) else None
        # Preserve unavailable registrations until an explicit Clear removes them.
        removed=set(self.owner.fetch('removed_controls',[]))
        if old:
            present={t['id'] for t in targets}
            slots={(t['kind'],t['slot']) for t in targets}
            targets.extend(copy.deepcopy(t) for t in old['targets'] if t['id'] not in present and t['id'] not in removed and (t['kind'],t['slot']) not in slots)
        group=self.owner.par.Groupid.eval() if ext._collection is not None else 'legacy:'+ext._host.device_id
        return dict(id=id,name=name,group_id=group,device_id=ext._host.device_id,
                    track_name=ext._host.track_name,plugin_name=ext._host.plugin_name,targets=targets,
                    state={field:copy.deepcopy(self.owner.fetch(field,default)) for field,default in zip(FIELDS,DEFAULTS)})

    def capture(self,force=False):
        if self.legacy or self.mutating or self.ext._restore_pending or not getattr(self.ext,"_layout_ready",True) or not (force or getattr(self.ext,"_layout_dirty",False)):return
        old=self.record()
        record=self.snapshot(old['id'],old['name'])
        self.data['records'][self.data['records'].index(old)]=record
        self.save()
        self.ext._layout_dirty=False

    def menu(self):
        par=getattr(self.owner.par,'Layout',None)
        if par is not None:
            par.menuNames=[r['id'] for r in self.data['records']]
            par.menuLabels=[r['name'] for r in self.data['records']]
            par.val=self.data['active']
        name=getattr(self.owner.par,'Layoutname',None)
        if name is not None:name.val=self.record()['name']

    def attach(self):
        if self.legacy:
            self.ext._host.devices_callback=None
            self.ext._host.plugin_index=0
            return
        self.ext._host.devices_callback=self.announce
        self.ext._host.plugin_index=self.data['records'].index(self.record())
        # Pending offline clears are replayed only after selected-control evidence.
        if hasattr(self.ext._host,'pending_unmaps'):self.ext._host.pending_unmaps=set()

    def announce(self,select=True):
        host=self.ext._host
        host._command(11,2,(len(self.data['records']),));host._command(11,3,(0,))
        for index,record in enumerate(self.data['records']):
            host._command(11,5,(index,*digest(record['device_id'],8),1,*text13(record['plugin_name']),0,0))
        host._command(11,6)
        if select:host._command(11,8,(self.data['records'].index(self.record()),0,0))

    def guard(self,hardware=False):
        host=self.ext._host
        if self.mutating or self.ext._dispatching or host.learning or host.touched or self.touched:
            raise ValueError('Exit LEARN and release controls before switching Layout')
        if self.locked and not hardware:raise ValueError('Unlock hardware before switching Layout')
        if not self.legacy:self.snapshot(self.record()['id'],self.record()['name'])  # callback preflight

    def resolve(self,record):
        specs=[];unavailable=[]
        for target in record['targets']:
            comp=self.owner.op(target['comp']);par=getattr(comp.par,target['parameter'],None) if comp is not None else None
            if par is None or not getattr(comp,'valid',True):
                unavailable.append(target);continue
            if target['mode']=='pulse':
                value=0
            else:
                value=parameter_value(par)
            spec=dict({k:v for k,v in target.items() if k not in ('comp','parameter','identity','menu_names','menu_labels')},parameter=par,value=value)
            if getattr(par,'style','')=='Menu' and (list(par.menuNames)!=target.get('menu_names',[]) or list(par.menuLabels)!=target.get('menu_labels',[])):
                spec['minimum']=0;spec['maximum']=len(par.menuNames)-1
            specs.append(spec)
        self.owner.op('controls').module.Controls(specs,allow_empty=True)
        return specs,unavailable

    def install(self,record,hardware=False):
        specs,unavailable=self.resolve(record)  # all resolvable targets validate before mutation
        ext=self.ext;host=ext._host;session=(host.connected,host.plugin,host.learning)
        self.mutating=True
        try:
            host.connected=host.plugin=False
            learner=getattr(ext,'_free_learner',None)
            if learner:
                learner.pending=learner.last_parameter=None;learner.ignored={};learner.baseline={}
                self.owner.op('learn_parameters').par.active=False
            for field,default in zip(FIELDS,DEFAULTS):self.owner.store(field,copy.deepcopy(record['state'].get(field,default)))
            # Materialized records replace table/hook sources for this Layout.
            self.owner.store('parameter_assignments',copy.deepcopy(record['targets']))
            table=self.owner.op('base_targets/targets');header=[c.val for c in table.row(0)]
            table.clear();table.appendRow(header)
            self.owner.par.Setupmode='collection';self.owner.par.Groupid=record['group_id']
            self.owner.store('assignment_device_id',dict(group_id=record['group_id'],device_id=record['device_id']))
            ext._restoring=False
            ext.BindControls(specs,group_id=record['group_id'],_allow_empty=True)
            for key,binding in ext._collection.bindings.items():
                saved=next(t for t in record['targets'] if t['id']==binding.id)
                semantics_match=(list(binding.menu_names)==saved.get('menu_names',[]) and list(binding.menu_labels)==saved.get('menu_labels',[]))
                if semantics_match and saved.get('identity'):
                    ext._host.controls[key].target_id=saved['identity']
                elif not semantics_match:
                    pending=set(self.owner.fetch('needs_relearn',()));pending.add(binding.id)
                    self.owner.store('needs_relearn',tuple(pending))
            ext._host.device_id=record['device_id'];ext._host.track_name=record['track_name'];ext._host.plugin_name=record['plugin_name']
            self.owner.par.Trackname=record['track_name'];self.owner.par.Pluginname=record['plugin_name']
            ext._host.connected,ext._host.plugin,ext._host.learning=session
            self.data['active']=record['id'];self.confirmed=False;self.attach();self.menu()
            catalog=copy.deepcopy(record['state'].get('control_catalog',[]))
            for missing in unavailable:
                item=next((item for item in catalog if item['id']==missing['id']),None)
                if item is None:
                    item=dict(missing,comp=self.owner.path+'/'+missing['comp'],binding_type='parameter',parameter_style='',value=None,normalized=0,valid=False,mapped=False,connected=session[0],plugin=session[1],touched=False,requires_relearn=True)
                    catalog.append(item)
                item.update(valid=False,mapped=False,error='Target unavailable',last_mapped=False)
            self.owner.store('control_catalog',catalog)
            if ext._host.connected and ext._host.plugin:
                ext._host._command(10,0x16,text13(record['track_name']))
                self.announce(select=not hardware)
            ext._host.last_event='Layout '+record['name']+': awaiting per-control recall' if session[0] else 'Layout '+record['name']+': disconnected'
            ext._last_error=''
            ext._layout_ready=True
        finally:
            self.mutating=False

    def select(self,id,hardware=False):
        destination=self.record(id)
        if id==self.data['active'] and not self.legacy:
            return id
        self.guard(hardware);self.resolve(destination);self.capture(force=True)
        self.legacy=False;self.owner.store("layout_registry_suspended",False)
        previous=copy.deepcopy(self.record())
        try:self.install(destination,hardware)
        except Exception:
            self.install(previous)
            # Recalled controls must reconfirm after rollback; old mapping flags are unsafe.
            raise
        self.save();self.ext._publish();return id

    def restore(self):
        self.legacy=False;self.owner.store("layout_registry_suspended",False)
        self.install(self.record());self.ext._restore_pending=False;self.ext._publish()

    def create(self,name):
        if not isinstance(name,str) or not name.strip():raise ValueError('Layout name is required')
        if len(self.data['records'])>=8:raise ValueError('Layout v1 supports at most 8 plugins (one hardware page)')
        self.guard();self.capture(force=True);id=uuid.uuid4().hex
        record=dict(id=id,name=name.strip(),group_id='layout.'+id,device_id='TD controls:layout.'+id,track_name='EFFECT',plugin_name='CUSTOM',targets=[],state={f:copy.deepcopy(v) for f,v in zip(FIELDS,DEFAULTS)})
        self.data['records'].append(record);self.save();self.menu()
        if self.ext._host.connected and self.ext._host.plugin:self.announce(select=False)
        return id

    def rename(self,id,name):
        if not isinstance(name,str) or not name.strip():raise ValueError('Layout name is required')
        self.record(id)['name']=name.strip();self.save();self.menu();return id

    def remove(self,id):
        record=self.record(id)
        if len(self.data['records'])==1:raise ValueError('Cannot delete the last Layout')
        self.guard()
        if id==self.data['active']:self.select(next(r['id'] for r in self.data['records'] if r['id']!=id))
        self.data['records']=[r for r in self.data['records'] if r['id']!=id];self.save();self.attach();self.menu()
        if self.ext._host.connected and self.ext._host.plugin:self.announce()
        return True

    def receive(self,message):
        message=tuple(message)
        if len(message)==3 and message[0]==191 and 52<=message[1]<=59 and 0<=message[2]<128:
            if message[2]:self.touched.add(message[1])
            else:self.touched.discard(message[1])
        if len(message)<8 or message[:5]!=(240,0,34,3,2) or message[-1]!=247 or any(type(x)is not int or not 0<=x<128 for x in message[1:-1]):return False
        group,command,data=message[5],message[6],message[7:-1]
        if self.legacy:
            if group==11 and command==13 and len(data)==1 and data[0] in (0,1):self.locked=bool(data[0]);return True
            if group==12 or (group==10 and command==2) or (group==11 and command==1):self.locked=False;self.touched.clear()
            return False
        if group==11 and command==11 and len(data)==11:
            pending={tuple(key) for key in self.owner.fetch('pending_unmaps',[])}
            for removed in self.owner.fetch('pending_unmap_identities',[]):
                key=(removed['kind'],removed['slot'])
                if key not in pending or key in self.ext._host.controls:continue
                if data[:2]==(removed['index']>>7,removed['index']&127) and data[2:8]==digest(removed['identity'],6) and data[8:]==(int(removed['kind']=='button'),removed['slot']-1,0):
                    ambiguous=any(t.get('identity')==removed['identity'] and t['index']==removed['index'] for r in self.data['records'] if r['id']!=self.data['active'] for t in r['targets'])
                    if ambiguous:
                        self.ext._last_error='Cannot attribute removed-target acknowledgement uniquely to this Layout'
                        return True
                    self.confirmed=True
                    self.ext._host._command(11,14,(int(removed['kind']=='button'),removed['slot']-1))
                    self.ext._host.last_event='Removed target hardware unmap reconciled'
                    return True
        if group==11 and command==13 and len(data)==1 and data[0] in (0,1):self.locked=bool(data[0]);return True
        if group==11 and command==7 and len(data)==1:
            if data[0]>=len(self.data['records']):return True
            try:self.select(self.data['records'][data[0]]['id'],hardware=True)
            except ValueError as exc:self.ext._last_error=str(exc);self.ext._publish()
            return True
        if group==11 and command==4:
            self.announce(select=False);return True
        if group==12 or (group==10 and command==2) or (group==11 and command==1):
            self.confirmed=False;self.locked=False;self.touched.clear()
        return False

    def acknowledge(self):
        if self.legacy:return
        if not self.confirmed and self.ext._host.mapped:
            self.confirmed=True
            # Selection has current-layout parameter evidence. Scoped offline removals can now be sent.
            for kind,slot in self.owner.fetch('pending_unmaps',[]):
                if (kind,slot) not in self.ext._host.controls:self.ext._host._command(11,14,(int(kind=='button'),slot-1))
            self.ext._host.last_event='Layout '+self.record()['name']+': controls recalled'
