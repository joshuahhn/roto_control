"""DAW-style learning: offer an edited Par, commit only the hardware's slot/hash."""
import time
import uuid
from binding import parameter_chain, parameter_value
from protocol import digest


class FreeLearner:
    def __init__(self, extension):
        self.extension = extension
        self.owner = extension.ownerComp
        self.active = False
        self._offers = {}
        self._pending = None
        self.last_parameter = None
        self.baseline = {}
        self.ignored = {}
        self.next_scan = 0
        self.selected_kind = 'knob'
        self.paths = ''

    @property
    def pending(self):
        return self._pending

    @pending.setter
    def pending(self, offer):
        # Layout/page/fence/transport resets already set pending=None. Keep
        # that contract while retaining every offer until its delayed ACK.
        if offer is None:
            self._offers.clear()
        else:
            template = offer['template']
            key = template.index, digest(template.target_id,6)
            self._offers.pop(key,None)
            self._offers[key] = offer
        self._pending = offer

    def _prune(self):
        now = time.monotonic()
        self._offers = {key:offer for key,offer in self._offers.items() if now-offer['time'] <= 30}
        self._pending = next(reversed(self._offers.values()),None)

    def _consume(self, key):
        self._offers.pop(key,None)
        self._pending = next(reversed(self._offers.values()),None)

    @staticmethod
    def key(parameter):
        return getattr(parameter.owner,'id',parameter.owner.path),parameter.name

    def parameter_in_scope(self, parameter):
        """A linked Device learns only its own COMP/public descendants."""
        manager = getattr(self.extension,'_layouts',None)
        follower = getattr(self.extension,'_follow',None)
        if manager is None or manager.legacy or follower is None:
            return True
        plugin = manager.plugin()
        if not plugin.get('focus_comp'):
            return True  # explicit unlinked Devices retain manual registration
        comp = follower.handles.get(plugin['id'])
        if not follower.eligible(comp):
            return False
        roots = [follower.handles.get(p['id']) for track in manager.layout()['tracks']
                 for p in track['plugins'] if p.get('focus_comp')]
        roots = [root for root in roots if follower.eligible(root) and (
            parameter.owner == root or parameter.owner.path.startswith(root.path+'/'))]
        # Explicit nested Devices own their descendants ahead of a parent
        # Device; public BIND parameters still belong to their public owner.
        return bool(roots and max(roots,key=lambda root:len(root.path)) == comp)

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
                if not self.parameter_in_scope(parameter):
                    continue
                if parameter.style not in ('Float','Int','Menu','Toggle','Pulse'):
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
        active = bool(host.enabled and host.connected and host.plugin and host.learning
                      and not (getattr(self.extension, "_follow", None) and self.extension._follow.gated))
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
                self.ignored[self.key(reference)] = reference.menuNames[int(value)] if reference.style == 'Menu' else value

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
            if parameter.style not in ('Float','Int','Menu','Toggle'):
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
        if not self.parameter_in_scope(parameter):
            self.status('Select the Device for '+parameter.owner.name+' before LEARN')
            return False
        e = self.extension
        try:
            self._prune()
            kind = self.selected_kind if parameter.style == 'Menu' else 'button' if parameter.style in ('Toggle','Pulse') else 'knob'
            mode = 'value' if kind == 'knob' else 'cycle' if parameter.style == 'Menu' else 'pulse' if parameter.style == 'Pulse' else 'toggle'
            collection = e._collection
            existing = next((key for key,binding in collection.bindings.items() if binding.parameter == parameter),None) if collection else None
            if existing is not None:
                binding = collection.bindings[existing]
                wire = next(spec for spec in collection.specs() if (spec['kind'],spec['slot']) == existing)
                index = e._host.controls[existing].index
            else:
                used = {target.index for target in e._host.controls.values()} if collection else {0}
                used.update(t['index'] for t in self.owner.fetch('page_targets',[]))
                used.update(offer['template'].index for offer in self._offers.values())
                prior = next((offer for offer in reversed(self._offers.values())
                              if self.key(offer['parameter']) == self.key(parameter)),None)
                index = prior['template'].index if prior else next(index for index in range(128,16384) if index not in used)
                adapter = None if kind == 'knob' else 'push' if mode == 'pulse' else 'toggle'
                candidate = self.owner.op('controls').module.Controls([dict(kind=kind,slot=1,
                    id=prior['binding'].id if prior else 'parameter.'+uuid.uuid4().hex,
                    parameter=parameter,mode=mode,button_type=adapter,index=index)])
                binding = candidate.bindings[kind,1]
                wire = next(candidate.specs())
            template = self.owner.op('collection_protocol').module.Control(e._host._send,(kind,1),index,
                wire['identity'],wire['label'],binding.normalized(parameter_value(parameter) if mode != 'pulse' else 0),
                wire['formatter'],mode,wire['button_type'])
            template.enabled = template.connected = template.plugin = template.learning = True
            if (template.index,digest(template.target_id,6)) not in self._offers and len(self._offers) >= 128:
                raise ValueError('Too many pending LEARN offers; wait for hardware acknowledgement')
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
                self.selected_kind = 'knob' if 52 <= message[1] <= 59 else 'button'
        self._prune()
        if (len(message) != 19 or message[:7] != (240,0,34,3,2,11,11) or message[-1] != 247
                or any(type(value) is not int or not 0 <= value < 128 for value in message[1:-1])):
            return False
        data = message[7:-1]
        offer_key = (data[0]<<7)|data[1],data[2:8]
        pending = self._offers.get(offer_key)
        if pending is None:
            return False
        template = pending['template']
        kind = 'knob' if data[8] == 0 else 'button' if data[8] == 1 else ''
        if not kind or not 0 <= data[9] < 8 or data[10] != 0:
            return False
        menu = bool(pending['binding'].menu_names)
        if kind != template.key[0] and not menu:
            host = self.extension._host
            target = host.controls.get((kind,data[9]+1)) if self.extension._collection is not None else host
            if target is not None:
                target._clear_mapping_state()
            self._consume(offer_key)
            self.last_parameter = None
            self.status('Cannot learn: use a '+template.key[0]+' for this parameter type')
            return True
        e = self.extension
        try:
            if not self.parameter_in_scope(pending['parameter']):
                raise ValueError('Device Focus COMP changed during LEARN; edit the parameter again')
            pending['binding'].check_parameter()
            state = e.AssignParameter(kind,data[9]+1,pending['parameter'],
                _id=pending['binding'].id,_wire_index=template.index,_hardware_mapped=True)
            replacement = e._host.controls[kind,data[9]+1]
            binding = e._collection.bindings[kind,data[9]+1]
            if replacement.index != template.index or binding.signature != pending['binding'].signature:
                raise ValueError('Parameter semantics changed during LEARN; edit it again')
            if menu:
                # Hardware may report its selected kind only on LEARN exit.
                # Menu supports both value and cycle; keep its offered hash
                # while using the ACK's knob/button adapter. Layout capture
                # persists this identity with the actual mode and options.
                replacement.target_id = template.target_id
            elif replacement.target_id != template.target_id:
                raise ValueError('Parameter semantics changed during LEARN; edit it again')
            self._consume(offer_key)
            self.status('Learned '+kind.capitalize()+' '+str(data[9]+1)+': '+state['label'])
        except Exception as exc:
            target = e._host.controls.get((kind,data[9]+1)) if e._collection is not None else e._host
            if target is not None:
                target._clear_mapping_state()
            self._consume(offer_key)
            self.last_parameter = None
            self.status('Cannot commit hardware mapping: '+str(exc))
            return True
        return False  # the common parser now accepts this exact saved index/hash
