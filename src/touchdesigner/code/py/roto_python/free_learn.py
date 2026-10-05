"""DAW-style learning: offer an edited Par, commit only the hardware's slot/hash."""
import time
import uuid
from binding import parameter_chain
from protocol import digest


class FreeLearner:
    def __init__(self, extension):
        self.extension = extension
        self.owner = extension.ownerComp
        self.active = False
        self.pending = None
        self.last_parameter = None
        self.baseline = {}
        self.ignored = {}
        self.next_scan = 0
        self.paths = ''

    @staticmethod
    def key(parameter):
        return getattr(parameter.owner,'id',parameter.owner.path),parameter.name

    def discover(self):
        stack = [self.owner.parent()]
        components, parameters = [], []
        while stack:
            comp = stack.pop()
            if (comp == self.owner or not comp.valid or not comp.isCOMP or getattr(comp,'type','') == 'annotate'
                    or comp.op('RotoPythonExt') is not None and comp.op('protocol') is not None):
                continue
            pars = []
            for parameter in comp.customPars:
                if parameter.style not in ('Float','Int','Toggle','Pulse'):
                    continue
                try:
                    parameter_chain(parameter)
                except (ValueError, AttributeError):
                    continue
                pars.append(parameter)
            if pars:
                components.append(comp)
                parameters.extend(pars)
            stack.extend(child for child in comp.children if child.isCOMP)
        return components,parameters

    def sync(self):
        host = self.extension._host
        active = bool(host.enabled and host.connected and host.plugin and host.learning)
        watcher = self.owner.op('learn_parameters')
        now = time.monotonic()
        if active != self.active:
            self.active = active
            watcher.par.active = active
            self.last_parameter = None
            self.baseline = {}
            self.ignored = {}
            self.next_scan = 0
            if active:
                self.pending = None
        if not active:
            return
        if now >= self.next_scan:
            components,parameters = self.discover()
            paths = ' '.join(comp.path for comp in components)
            if paths != self.paths:
                watcher.par.op.expr = ''
                watcher.par.op.val = paths
                self.paths = paths
            for parameter in parameters:
                self.baseline.setdefault(self.key(parameter),parameter.eval() if parameter.style != 'Pulse' else 0)
            self.next_scan = now+1

    def ignore(self, parameter, value):
        if parameter is not None:
            for reference in parameter_chain(parameter):
                self.ignored[self.key(reference)] = value

    def changes(self, changes):
        if not self.active:
            return
        candidates = []
        for parameter, previous in changes:
            key = self.key(parameter)
            value = parameter.eval()
            old = self.baseline.get(key,previous)
            self.baseline[key] = value
            if value == old or value == self.ignored.pop(key,object()):
                continue
            if parameter.style not in ('Float','Int','Toggle'):
                continue
            candidates.append(parameter)
        # A public BIND Par and its master may both change. Prefer the COMP
        # selected in the TD UI, rather than offering an internal master too.
        candidates.sort(key=lambda parameter:not getattr(parameter.owner,'selected',False))
        if candidates:
            self.offer(candidates[0])

    def pulse(self, parameter):
        if not self.active:
            return
        collection = self.extension._collection
        if collection is not None and any(binding.parameter == parameter and getattr(binding,'pulse_expected',0)
                                          for binding in collection.bindings.values()):
            return
        self.offer(parameter)

    def status(self, text):
        inspector = self.owner.op('inspector')
        if inspector is not None:
            inspector.store('action_status',text)
        self.extension._host.last_event = text
        self.extension._publish()

    def offer(self, parameter):
        if not self.active or self.key(parameter) == self.last_parameter:
            return False
        e = self.extension
        try:
            kind = 'button' if parameter.style in ('Toggle','Pulse') else 'knob'
            mode = 'value' if kind == 'knob' else 'pulse' if parameter.style == 'Pulse' else 'toggle'
            collection = e._collection
            existing = next((key for key,binding in collection.bindings.items() if binding.parameter == parameter),None) if collection else None
            if existing is not None:
                binding = collection.bindings[existing]
                wire = next(spec for spec in collection.specs() if (spec['kind'],spec['slot']) == existing)
                index = e._host.controls[existing].index
            else:
                used = {target.index for target in e._host.controls.values()} if collection else {0}
                index = next(index for index in range(128,16384) if index not in used)
                adapter = None if kind == 'knob' else 'push' if mode == 'pulse' else 'toggle'
                candidate = self.owner.op('controls').module.Controls([dict(kind=kind,slot=1,
                    id='parameter.'+uuid.uuid4().hex,parameter=parameter,mode=mode,button_type=adapter,index=index)])
                binding = candidate.bindings[kind,1]
                wire = next(candidate.specs())
            template = self.owner.op('collection_protocol').module.Control(e._host._send,(kind,1),index,
                wire['identity'],wire['label'],binding.normalized(parameter.eval() if mode != 'pulse' else 0),
                wire['formatter'],mode,wire['button_type'])
            template.enabled = template.connected = template.plugin = template.learning = True
            if not template.offer_parameter():
                return False
            self.pending = dict(parameter=parameter,binding=binding,template=template,time=time.monotonic())
            self.last_parameter = self.key(parameter)
            self.status('Offered '+parameter.owner.name+'.'+parameter.name+'; waiting for hardware slot')
            return True
        except Exception as exc:
            self.status('Cannot learn: '+str(exc))
            return False

    def receive(self, message):
        message = tuple(message)
        if len(message) == 3 and message[0] == 191 and self.active:
            if 52 <= message[1] <= 59 and message[2] > 0 or 20 <= message[1] <= 27:
                self.last_parameter = None
        pending = self.pending
        if pending is None or time.monotonic()-pending['time'] > 30:
            return False
        if (len(message) != 19 or message[:7] != (240,0,34,3,2,11,11) or message[-1] != 247
                or any(type(value) is not int or not 0 <= value < 128 for value in message[1:-1])):
            return False
        data = message[7:-1]
        template = pending['template']
        if ((data[0]<<7)|data[1]) != template.index or data[2:8] != digest(template.target_id,6):
            return False
        kind = 'knob' if data[8] == 0 else 'button' if data[8] == 1 else ''
        if not kind or not 0 <= data[9] < 8 or data[10] != 0:
            return False
        if kind != template.key[0]:
            host = self.extension._host
            target = host.controls.get((kind,data[9]+1)) if self.extension._collection is not None else host
            if target is not None:
                target._clear_mapping_state()
            self.pending = None
            self.last_parameter = None
            self.status('Cannot learn: use a '+template.key[0]+' for this parameter type')
            return True
        e = self.extension
        try:
            state = e.AssignParameter(kind,data[9]+1,pending['parameter'],
                _id=pending['binding'].id,_wire_index=template.index,_hardware_mapped=True)
            replacement = e._host.controls[kind,data[9]+1]
            if replacement.index != template.index or replacement.target_id != template.target_id:
                raise ValueError('Parameter semantics changed during LEARN; edit it again')
            self.pending = None
            self.status('Learned '+kind.capitalize()+' '+str(data[9]+1)+': '+state['label'])
        except Exception as exc:
            target = e._host.controls.get((kind,data[9]+1)) if e._collection is not None else e._host
            if target is not None:
                target._clear_mapping_state()
            self.pending = None
            self.last_parameter = None
            self.status('Cannot commit hardware mapping: '+str(exc))
            return True
        return False  # the common parser now accepts this exact saved index/hash
