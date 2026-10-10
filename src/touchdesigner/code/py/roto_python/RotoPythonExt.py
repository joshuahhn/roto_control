"""TD adapter. All hardware MIDI runs in the owned external Python process."""

import copy
from contextlib import nullcontext
import json
import os
from pathlib import Path
import subprocess
import time
from binding import parameter_value


class RotoPythonExt:
    def __init__(self, ownerComp):
        self.ownerComp = ownerComp
        self._layout_ready = False
        self._layout_dirty = False
        self._layouts = None
        self._process = None
        self._receive = b""
        self._pending = b""
        self._started_at = 0.0
        self._transport_ready = False
        self._target_path = ""
        self._dispatching = False
        self._binding = None
        self._collection = None
        self._actions = None
        self._identities = {}
        self._last_error = ""
        self._restoring = False
        self._restore_pending = True
        self._mirror_expected = None
        self._delete_request = None
        self._follow = None
        self._receive_epoch = None
        self._inspector_refresh_run = None
        learner = ownerComp.op("free_learn")
        self._free_learner = learner.module.FreeLearner(self) if learner is not None else None
        self._host = ownerComp.op("protocol").module.Host(
            self._send, self._assign, self._value_parameter().eval(), **self._display_names())
        helper = ownerComp.op('text_comp_follow')
        if helper is not None:
            self._follow = helper.module.CompFollower(self)
        self._publish()

    def _action_registry(self):
        if getattr(self, '_actions', None) is None:
            self._actions = self.ownerComp.op('controls').module.Actions()
        return self._actions

    def RegisterAction(self, id, label, recall, *, replace=False):
        """Register an explicit consumer recall(event); never execute it here."""
        if self._dispatching:
            raise ValueError('Do not register actions during dispatch')
        return self._action_registry().register(id, label, recall, replace=replace)

    def UnregisterAction(self, id):
        """Remove a runtime entry point; retain saved Button references."""
        if self._dispatching:
            raise ValueError('Do not unregister actions during dispatch')
        registry = self._action_registry()
        removed = registry.entries.pop(id, None) is not None
        self._publish()
        return removed

    def GetActions(self):
        registry = self._action_registry()
        return [registry.state(id) for id in registry.entries]

    def GetActionState(self, id):
        return self._action_registry().state(id)

    def _restore_actions(self):
        registry = self.ownerComp.op('controls').module.Actions()
        self._actions = registry
        hook = self.ownerComp.op('registration')
        try:
            register = getattr(hook.module, 'onRegisterActions', None) if hook is not None else None
            if register is not None:
                register(self.ownerComp)
        except Exception as exc:
            registry.entries.clear()
            registry.error = 'Action registration failed: ' + str(exc)

    def _action_callback(self, action_id):
        def dispatch(event):
            result = self._recall_action(action_id, event)
            if result['status'] != 'succeeded':
                raise ValueError(result['status'] + ': ' + result['error'])
        return dispatch

    def _recall_action(self, id, event):
        result = self._action_registry().recall(id, event)
        # Publish true live parameter values even after partial consumer failure.
        # Deferred TD callbacks then observe the same value and do not repeat it.
        if self._collection is not None:
            for key, binding in list(self._collection.bindings.items()):
                if binding.parameter is not None and self._collection.modes[key] != 'pulse':
                    self.onControlChange(key, binding.parameter)
        return result

    def RecallAction(self, id):
        """Explicit software recall; independent of Button assignment/LEARN."""
        if self._dispatching or self._host.learning or self._restoring or self._restore_pending:
            raise ValueError('Exit LEARN/restore; do not recall recursively')
        follower = getattr(self, '_follow', None)
        manager = getattr(self, '_layouts', None)
        if manager is not None:
            manager.owner_ready(required=True)
            if manager.quarantined and not manager.legacy:
                raise ValueError('Activate the repaired Layout before recall')
        if (follower is not None and (follower.gated or follower.paused or follower.pending or getattr(follower,'backlog',False))) or (manager is not None and manager.mutating):
            raise ValueError('Action recall is fenced during context transition')
        self._dispatching = True
        try:
            result = self._recall_action(id, dict(origin='software', kind='pulse'))
        finally:
            self._dispatching = False
        self._publish()
        return result

    def AssignAction(self, slot, action_id, *, button_type='push', id=None):
        """Assign a stable action reference to one Button; preserve other slots."""
        return self._assign_target('button', slot, None, button_type=button_type,
                                   _id=id, action_id=action_id)

    def SetTrackComp(self, layout_id, track_id, comp):
        """Compatibility: link that Track's active Device."""
        return self._follow.set_link(layout_id, track_id, comp)

    def SetPluginComp(self, layout_id, track_id, plugin_id, comp):
        return self._follow.set_plugin_link(layout_id, track_id, plugin_id, comp)

    def SelectComp(self, comp):
        return self._follow.select(comp)

    def GetCompContext(self):
        return self._follow.context() if self._follow else dict(enabled=False, status='unavailable')

    def _discard_context_output(self):
        kept = []
        for line in self._pending.splitlines(keepends=True):
            try:
                message = json.loads(line)['midi']
            except (ValueError, KeyError):
                kept.append(line)  # preserve a partially transmitted frame
                continue
            if not self._follow.context_output(message):
                kept.append(line)
        self._pending = b''.join(kept)

    def _receive_midi(self, message, token=None):
        follower = getattr(self, '_follow', None)
        manager = getattr(self, '_layouts', None)
        learner = getattr(self, '_free_learner', None)
        if follower is not None and token is not None and token[0] != follower.connection_generation:
            return
        stale = follower is not None and token is not None and token != follower.token
        unavailable = manager is not None and (not manager.owner_ready() or manager.quarantined and not manager.legacy)
        fenced = unavailable or (follower is not None and (follower.gated or stale)) or self._dispatching or bool(manager and manager.mutating)
        consumed = manager.receive(message, control_only=fenced) if manager is not None else False
        if not consumed and not fenced and learner is not None:
            consumed = learner.receive(message)
        if not consumed:
            self._host.receive(message, control_only=fenced)
        if manager is not None and not fenced:
            manager.acknowledge()
        if learner is not None:
            learner.sync()


    @property
    def State(self):
        """Snapshot for callers; diagnostics live inside the network."""
        return {par.name: par.eval() for par in self.ownerComp.op("base_state").customPars
                if par.name != 'Manualvalue'}

    def _value_parameter(self):
        """Legacy outer Value, or its internal backing after the UI upgrade."""
        legacy = getattr(self.ownerComp.par, 'Value', None)
        return legacy if legacy is not None else self.ownerComp.op('base_state').par.Manualvalue

    def _enable_manual_controls(self, enabled):
        self._value_parameter().enable = enabled
        pulse = getattr(self.ownerComp.par, 'Offerparameter', None)
        if pulse is not None:
            pulse.enable = enabled

    def _display_names(self):
        return {"track_name": self.ownerComp.par.Trackname.eval() if hasattr(self.ownerComp.par, "Trackname") else "EFFECT",
                "plugin_name": self.ownerComp.par.Pluginname.eval() if hasattr(self.ownerComp.par, "Pluginname") else "CUSTOM"}

    def SetLayoutNames(self, track_name, plugin_name):
        """Update fixed hardware display names without changing mapping identity."""
        manager=getattr(self,'_layouts',None)
        if manager is not None and not manager.legacy and manager.locked and manager.selected_track not in (None,manager.track()['id']):
            raise ValueError('Unlock before renaming a Track different from hardware selection')
        self._layout_dirty = True
        plugin_name_changed = plugin_name != self._host.plugin_name
        result = self._host.set_display_names(track_name, plugin_name)
        for name, value in (("Trackname", track_name), ("Pluginname", plugin_name)):
            par = getattr(self.ownerComp.par, name, None)
            if par is not None and par.eval() != value:
                par.val = value
        if result:
            self._last_error = ""
        manager=getattr(self,'_layouts',None)
        if manager is not None and not manager.legacy and not manager.mutating:
            if plugin_name_changed:manager.plugin()['name_mode']='manual'
            manager.capture(force=True)
            if result:
                manager.menu()
                if self._host.connected:manager.announce_tracks(select=False)
        self._publish()
        return result

    def _layout_manager(self):
        if self._layouts is None:
            dat = self.ownerComp.op('layouts')
            if dat is None:
                raise ValueError('Install Layout support first')
            self._layouts = dat.module.Layouts(self)
        return self._layouts

    def GetLayouts(self):
        manager = self._layout_manager()
        manager.refresh_owners()
        return [dict(id=r['id'], name=r['name'],category=r.get('category','LEGACY'),owner=copy.deepcopy(r.get('owner')),
                     track_name=manager.track(r['id'])['name'],
                     plugin_name=manager.plugin(r['id'])['plugin_name'],track_count=len(r['tracks']),
                     active=r['id']==manager.data['active']) for r in manager.data['records']]


    def SelectLayout(self, id):
        return self._layout_manager().select(id)

    def CreateLayout(self, name):
        return self._layout_manager().create(name)

    def RenameLayout(self, id, name):
        return self._layout_manager().rename(id, name)

    def RemoveLayout(self, id):
        return self._layout_manager().remove(id)

    def GetTracks(self, layout_id=None):
        manager=self._layout_manager();layout=manager.layout(layout_id)
        return [dict(id=t['id'],name=t['name'],plugin_id=t['active_plugin'],
                     plugin_name=manager.plugin(layout['id'],t['id'])['plugin_name'],
                     plugin_count=len(t['plugins']),
                     active=t['id']==layout['active_track']) for t in layout['tracks']]

    def GetPlugins(self, layout_id=None, track_id=None):
        manager=self._layout_manager()
        follower=getattr(self,'_follow',None)
        if follower:follower.refresh_links()
        track=manager.track(layout_id,track_id)
        return [dict(id=p['id'],name=p['plugin_name'],comp_name=p.get('comp_name'),
                     name_mode=p.get('name_mode','manual'),focus_comp=copy.deepcopy(p.get('focus_comp')),
                     active=p['id']==track['active_plugin']) for p in track['plugins']]

    def CreatePlugin(self, layout_id, track_id, name):
        return self._layout_manager().create_plugin(layout_id,track_id,name)

    def SelectPlugin(self, layout_id, track_id, plugin_id):
        return self._layout_manager().select_plugin(layout_id,track_id,plugin_id)

    def RenamePlugin(self, layout_id, track_id, plugin_id, name):
        return self._layout_manager().rename_plugin(layout_id,track_id,plugin_id,name)

    def RemovePlugin(self, layout_id, track_id, plugin_id):
        return self._layout_manager().remove_plugin(layout_id,track_id,plugin_id)

    def GetLayoutContext(self):
        manager=getattr(self,'_layouts',None)
        if manager is not None:manager.refresh_owners()
        return manager.context() if manager is not None else dict(key=None,label='Initializing',legacy=True)


    def CreateTrack(self, layout_id, name):
        return self._layout_manager().create_track(layout_id,name)

    def SelectTrack(self, layout_id, track_id):
        return self._layout_manager().select_track(layout_id,track_id)

    def RenameTrack(self, layout_id, track_id, name):
        return self._layout_manager().rename_track(layout_id,track_id,name)

    def RemoveTrack(self, layout_id, track_id):
        return self._layout_manager().remove_track(layout_id,track_id)

    def _check_single_id(self, id):
        active_id = self._binding.id if self._binding is not None else "Value"
        if id is not None and id != active_id:
            raise ValueError("Unknown target ID: " + str(id))
        return active_id

    def GetControlState(self, id=None):
        """Detached per-target snapshot in target units; never parses DAT state."""
        if self._collection is not None:
            key = self._collection.key(id)
            binding = self._collection.bindings[key]
            target = self._host.controls[key]
            mode = self._collection.modes[key]
            error = self._collection.errors.get(key, "") or (self._last_error if not self._host.enabled else "")
            active_id = binding.id
        else:
            active_id = self._check_single_id(id)
            key, binding, target, mode = ("knob", 1), self._binding, self._host, "value"
            error = self._last_error
        parameter = binding.parameter if binding is not None else None
        comp_path, parameter_name, parameter_style = "", "", ""
        parameter_ready=True
        value = binding.value if binding is not None else target.value
        value_source='cached'
        manager=getattr(self,'_layouts',None)
        owner_ready=manager is None or manager.owner_ready() and (not manager.quarantined or manager.legacy)
        if parameter is not None:
            value=None;value_source='unavailable';parameter_ready=False
            try:
                if parameter.owner.valid:
                    comp_path,parameter_name=parameter.owner.path,parameter.name
                    parameter_style=getattr(parameter,'style','')
                    if binding.valid and owner_ready:
                        binding.check_parameter()
                        value=0 if mode=='pulse' else parameter_value(parameter)
                        binding.normalized(value)  # reject unreadable/nonfinite observations
                        value_source='pulse' if mode=='pulse' else 'live';parameter_ready=True
            except (ValueError,AttributeError,RuntimeError,TypeError) as exc:
                error=error or str(exc)
            if not parameter_ready:
                value=None;value_source='unavailable';error=error or 'Target unavailable'
        elif binding is None:
            comp_path,parameter_name=self.ownerComp.path,'Value'
            if hasattr(self.ownerComp,'par') and getattr(self.ownerComp.par,'Value',None) is None:
                backing=self._value_parameter()
                comp_path,parameter_name=backing.owner.path,backing.name
        if not owner_ready:value=None;value_source='unavailable'
        normalized=(binding.normalized(value) if binding is not None else value) if value is not None else 0
        action_id = getattr(binding, 'action_id', None)
        action_state = self.GetActionState(action_id) if action_id else None
        if action_id:
            value_source = 'action' if owner_ready else 'unavailable'
            if not owner_ready:error = error or 'Layout owner unavailable or quarantined; explicitly repair and Activate'
            if not action_state['available']:error = error or action_state['error']
        return dict(action_id=action_id, action_result=action_state['result'] if action_state else None,
                    action_available=action_state['available'] if action_state else None,
                    mapping_error=error,
                    id=active_id, kind=key[0], slot=key[1], mode=mode,
                    label=binding.label if binding is not None else target.target_label,
                    value=value,value_source=value_source,normalized=normalized,
                    minimum=binding.minimum if binding is not None else 0,
                    maximum=binding.maximum if binding is not None else 1,
                    mapped=owner_ready and parameter_ready and self._host.enabled and target.mapped, touched=target.touched,
                    valid=owner_ready and parameter_ready and self._host.enabled and target.enabled and (binding is None or binding.valid) and (action_state is None or action_state['available']),
                    connected=target.connected, plugin=target.plugin, error=error or (action_state['error'] if action_state else ''),
                    button_type=getattr(target, "button_type", None),
                    binding_type="action" if action_id else "parameter" if parameter is not None else "callback" if binding is not None else "value",
                    comp=comp_path, parameter=parameter_name,
                    menu_names=list(binding.menu_names) if binding is not None else [],
                    menu_labels=list(binding.menu_labels) if binding is not None else [],
                    value_label=binding.format_value(normalized) if binding is not None and binding.menu_names and value is not None else "",
                    parameter_style=parameter_style,
                    requires_relearn=active_id in self.ownerComp.fetch('needs_relearn', ()) and not target.mapped)


    def GetControlStates(self):
        """Detached snapshots for every registered control, in registration order."""
        ids = list(self._collection.ids) if self._collection is not None else [None]
        manager=getattr(self,'_layouts',None)
        with manager.owner_observation() if manager is not None else nullcontext():
            return [self.GetControlState(id) for id in ids]


    def GetControlCatalog(self):
        """Saved definitions with current registered values; missing slots have no live value."""
        return self._catalog_from_states(self.GetControlStates())

    def _catalog_from_states(self, states):
        live={r['id']:r for r in states}
        records=copy.deepcopy(self.ownerComp.fetch('control_catalog',list(live.values())))
        for record in records:
            state=live.get(record['id'])
            if state is not None:
                for key in ('value','value_source','normalized','value_label','valid','mapped','touched','connected','plugin','error','mapping_error','action_id','action_available','action_result'):
                    record[key]=state.get(key)
            else:record.update(value=None,value_source='unavailable',valid=False,mapped=False)
        return records


    def _update_catalog(self, states=None):
        if self._restore_pending:
            return
        previous={state['id']:state for state in self.ownerComp.fetch('control_catalog', [])}
        records=[]
        for state in self.GetControlStates() if states is None else states:
            old=previous.get(state['id'], {})
            record=dict(state)
            for field in ('comp','parameter'):
                if record['binding_type'] != 'action' and not record[field] and old.get(field):
                    record[field]=old[field]
            record['last_mapped']=state['mapped'] or old.get('last_mapped', False)
            records.append(record)
        manager=getattr(self,'_layouts',None)
        if manager is not None and not manager.legacy:
            target_ids={t['id'] for t in manager.record()['targets']}
            present={state['id'] for state in records}
            removed=set(self.ownerComp.fetch('removed_controls',[]))
            for id, old in previous.items():
                if id in target_ids and id not in present and id not in removed:
                    old=dict(old,valid=False,mapped=False,error='Target unavailable',mapping_error='Target unavailable')
                    records.append(old)
        if records != self.ownerComp.fetch('control_catalog', []):
            self.ownerComp.store('control_catalog', records)

    def GetValue(self, id=None):
        """Current target-unit value; defaults to Knob 1."""
        return self.GetControlState(id)["value"]

    def Applybinding(self):
        follower = getattr(self, '_follow', None)
        if follower is not None:
            follower.repair()
        self._restore_pending = False
        self._restoring = True
        try:
            self._restore_actions()
            has_registry=self.ownerComp.op('layouts') is not None and self.ownerComp.fetch('layout_registry',None) is not None
            if has_registry and self.ownerComp.par.Setupmode.eval()=='callback':
                previous_manager=getattr(self,'_layouts',None)
                suspended=self.ownerComp.fetch('layout_registry_suspended',False)
                manager=self._layout_manager()
                if previous_manager is not None and not previous_manager.legacy and self._layout_ready:
                    manager.capture(force=True)
                if not suspended:
                    # Saved parameter Layouts remain in registry; legacy hook owns
                    # its independent overlays after opting out of Layout mode.
                    for field,value in (('parameter_assignments',[]),('assignment_device_id',None),('control_overrides',{}),('removed_controls',[]),('pending_unmaps',[]),('pending_unmap_identities',[]),('needs_relearn',()),('control_catalog',[]),('page_targets',[])):
                        self.ownerComp.store(field,value)
                manager.legacy=True;manager.attach()
                self.ownerComp.store('layout_registry_suspended',True)
            elif has_registry:
                self._layout_manager().restore()
                return tuple(self._collection.ids)
            result = self.ownerComp.op("setup").module.restore(self.ownerComp)
            if self._collection is None and self.ownerComp.fetch('parameter_assignments', []):
                assigned = self._assignment_specs()
                if not any((spec['kind'],spec['slot']) == ('knob',1) for spec in assigned):
                    binding = self._binding
                    assigned.insert(0, dict(kind='knob',slot=1,id=binding.id if binding else 'Value',
                        parameter=binding.parameter if binding else self._value_parameter(),
                        on_change=binding.on_change if binding else None,
                        minimum=binding.minimum if binding else 0,maximum=binding.maximum if binding else 1,
                        value=binding.value if binding else self._value_parameter().eval(),
                        label=binding.label if binding else 'Value'))
                result = self.BindControls(assigned,group_id=self.ownerComp.par.Groupid.eval())
            self._layout_ready=True
            if self.ownerComp.op('layouts') is not None:
                try:
                    self._layout_manager()
                except ValueError as exc:
                    self._last_error = str(exc)
            self._publish()
            return result
        except Exception as exc:
            self._fault(exc)
            return False
        finally:
            self._restoring = False

    def ClearLearn(self, id=None):
        """Request hardware unmap for one control; retain its TD registration/value."""
        self._layout_dirty = True
        if getattr(self,'_layouts',None) is not None and not self._layouts.confirmed:
            raise ValueError('Await current Layout recall before hardware-only Clear Learn')
        if self._dispatching:
            raise ValueError("Do not clear LEARN inside a hardware callback")
        if self._collection is not None:
            result = self._host.clear_learn(self._collection.key(id))
        else:
            self._check_single_id(id)
            result = self._host.clear_learn()
        self._publish()
        return result

    def RemoveControl(self, id):
        """Delete one registered target and suppress saved-hook recall; retain empty slot."""
        self._layout_dirty = True
        if self._collection is None:
            active_id=self._check_single_id(id)
            if self._dispatching or self._host.learning or self._host.touched:
                raise ValueError("Exit LEARN and release the control before removing")
            if self._host.connected and self._host.plugin:
                self._host.clear_learn()
            removed=set(self.ownerComp.fetch('removed_controls', []));removed.add(active_id)
            self.ownerComp.store('removed_controls',sorted(removed))
            pending={tuple(key) for key in self.ownerComp.fetch('pending_unmaps', [])}
            pending.add(('knob',1));self.ownerComp.store('pending_unmaps',sorted(pending))
            self.BindControls([],group_id='removed.single',_allow_empty=True)
            return active_id
        manager=getattr(self,'_layouts',None)
        if manager is not None and id not in self._collection.ids:
            target=next((t for t in manager.record()['targets'] if t['id']==id),None)
            if target is None:raise ValueError('Unknown target ID: '+str(id))
            manager.guard()
            removed=set(self.ownerComp.fetch('removed_controls',[]));removed.add(id)
            self.ownerComp.store('removed_controls',sorted(removed))
            self.ownerComp.store('parameter_assignments',[r for r in self.ownerComp.fetch('parameter_assignments',[]) if r['id']!=id])
            self.ownerComp.store('control_catalog',[r for r in self.ownerComp.fetch('control_catalog',[]) if r['id']!=id])
            pending={tuple(key) for key in self.ownerComp.fetch('pending_unmaps',[])};pending.add((target['kind'],target['slot']))
            self.ownerComp.store('pending_unmaps',sorted(pending))
            identities=[r for r in self.ownerComp.fetch('pending_unmap_identities',[]) if (r['kind'],r['slot'])!=(target['kind'],target['slot'])]
            if target.get('identity'):identities.append({k:target[k] for k in ('kind','slot','index','identity')})
            self.ownerComp.store('pending_unmap_identities',identities)
            self._publish();return id
        key=self._collection.key(id)
        target=self._host.controls[key]
        if self._dispatching or self._host.learning or target.touched:
            raise ValueError("Exit LEARN and release the control before removing")
        if self._host.connected and self._host.plugin and (getattr(self,"_layouts",None) is None or self._layouts.confirmed):
            self._host.clear_learn(key)
        if manager is not None:
            identities=[r for r in self.ownerComp.fetch('pending_unmap_identities',[]) if (r['kind'],r['slot'])!=key]
            identities.append(dict(kind=key[0],slot=key[1],index=target.index,identity=target.target_id))
            self.ownerComp.store('pending_unmap_identities',identities)
        pending=set(tuple(key) for key in self.ownerComp.fetch('pending_unmaps', []))
        pending.add(key)
        self.ownerComp.store('pending_unmaps', sorted(pending))
        self._host.pending_unmaps=pending
        removed=set(self.ownerComp.fetch('removed_controls', []));removed.add(id)
        self.ownerComp.store('removed_controls', sorted(removed))
        watcher=self.ownerComp.op('base_targets/watch_'+key[0]+str(key[1]))
        watcher.par.active=False
        watcher.par.op.expr='';watcher.par.op.val='';watcher.par.pars=''
        self._collection.ids.pop(id)
        for mapping in (self._collection.bindings,self._collection.modes,self._collection.button_types,self._collection.paths,self._collection.errors,self._collection.indices):
            mapping.pop(key,None)
        self._host.controls.pop(key)
        self._host._sync()
        self._enable_manual_controls(('knob',1) in self._collection.bindings)
        table=self.ownerComp.op('base_targets/targets')
        for row in range(table.numRows-1,0,-1):
            if table[row,'id'].val==id:
                table.deleteRow(row)
        overrides=dict(self.ownerComp.fetch('control_overrides', {}));overrides.pop(id,None)
        self.ownerComp.store('control_overrides',overrides)
        self.ownerComp.store('needs_relearn',tuple(value for value in self.ownerComp.fetch('needs_relearn', ()) if value!=id))
        self.ownerComp.store('parameter_assignments',[record for record in self.ownerComp.fetch('parameter_assignments', []) if record['id']!=id])
        self._publish()
        return id

    def RemoveAllControls(self):
        """Remove every registered target, keeping all 16 empty hardware slots."""
        if self._collection is None:
            return (self.RemoveControl(self._check_single_id(None)),)
        if self._dispatching or self._host.learning or self._host.touched:
            raise ValueError("Exit LEARN and release all controls before removing")
        manager=getattr(self,"_layouts",None)
        saved=[t["id"] for t in manager.record()["targets"]] if manager is not None and not manager.legacy else []
        ids=tuple(dict.fromkeys([*self._collection.ids,*saved]))
        for id in ids:
            self.RemoveControl(id)
        return ids

    def ClearAllLearn(self):
        """Clear every registered hardware slot, retaining TD targets/values."""
        if self._dispatching:
            raise ValueError("Do not clear LEARN inside a hardware callback")
        if not self._host.connected or not self._host.plugin:
            raise ValueError("Connect to PLUGIN before clearing LEARN")
        if self._host.learning or self._host.touched:
            raise ValueError("Exit LEARN and release all controls before clearing")
        ids = [state['id'] for state in self.GetControlStates()]
        # Preflight every slot before sending; transport failures can still be partial.
        for id in ids:
            self.ClearLearn(id)
        return tuple(ids)

    def ConfigureControl(self, id, *, minimum=None, maximum=None, mode=None, button_type=None):
        """Validate configuration; only changed wire semantics require re-LEARN."""
        self._layout_dirty = True
        if self._collection is None:
            raise ValueError("Editable configuration requires a control collection")
        key = self._collection.key(id)
        old = self._collection.bindings[key]
        target = self._host.controls[key]
        if self._dispatching or self._host.learning or target.touched:
            raise ValueError("Exit LEARN and release the control before editing")
        spec = dict(kind=key[0], slot=key[1], id=id, label=old.label,
                    minimum=old.minimum if minimum is None else minimum,
                    maximum=old.maximum if maximum is None else maximum,
                    mode=self._collection.modes[key] if mode is None else mode,
                    button_type=self._collection.button_types[key] if button_type is None else button_type,
                    value=old.value, parameter=old.parameter, on_change=old.on_change, action_id=getattr(old, 'action_id', None))
        candidate = self.ownerComp.op('controls').module.Controls([spec])
        binding = candidate.bindings[key]
        if binding.value != old.value and candidate.modes[key] != 'pulse':
            raise ValueError("Range must include the current value; change Value first")
        if (binding.signature == old.signature and candidate.modes[key] == self._collection.modes[key]
                and candidate.button_types[key] == self._collection.button_types[key]):
            return self.GetControlState(id)
        # Input TYPE is a local RX adapter; target metadata/hash are unchanged.
        if binding.signature == old.signature and candidate.modes[key] == self._collection.modes[key]:
            target.button_type = candidate.button_types[key]
            self._collection.button_types[key] = candidate.button_types[key]
            overrides = dict(self.ownerComp.fetch('control_overrides', {}))
            overrides[id] = dict(minimum=old.minimum, maximum=old.maximum,
                                 mode=self._collection.modes[key], button_type=target.button_type)
            self.ownerComp.store('control_overrides', overrides)
            self._publish()
            return self.GetControlState(id)
        wire = list(candidate.specs())[0]
        replacement = self.ownerComp.op('collection_protocol').module.Control(
            target.send, key, target.index, wire['identity'], wire['label'], wire['value'],
            wire['formatter'], wire['mode'], wire['button_type'])
        # Do not leave old hardware semantics driving a newly configured target.
        if target.mapped:
            self._host.clear_learn(key)
        self._collection.bindings[key] = binding
        self._collection.modes[key] = candidate.modes[key]
        self._collection.button_types[key] = candidate.button_types[key]
        self._collection.errors.pop(key, None)
        self._host.controls[key] = replacement
        self._host._sync()
        overrides = dict(self.ownerComp.fetch('control_overrides', {}))
        overrides[id] = dict(minimum=binding.minimum, maximum=binding.maximum,
                             mode=candidate.modes[key], button_type=candidate.button_types[key])
        self.ownerComp.store('control_overrides', overrides)
        self.ownerComp.store('needs_relearn', tuple(set(self.ownerComp.fetch('needs_relearn', ())) | {id}))
        self._publish()
        return self.GetControlState(id)

    def _assignment_specs(self):
        """Resolve persisted Inspector assignments independently of demo setup."""
        result = []
        for record in self.ownerComp.fetch('parameter_assignments', []):
            if record.get('action_id'):
                result.append(dict({k:v for k,v in record.items() if k not in ('identity','comp','parameter','menu_names','menu_labels')},
                                   on_change=self._action_callback(record['action_id'])))
                continue
            target = self.ownerComp.op(record['comp'])
            parameter = getattr(target.par, record['parameter'], None) if target is not None else None
            if parameter is None:
                raise ValueError('Assigned parameter missing: '+record['comp']+'.'+record['parameter'])
            result.append(dict(kind=record['kind'], slot=record['slot'], id=record['id'],
                               parameter=parameter, mode=record['mode'], label=record['label'],
                               minimum=record['minimum'], maximum=record['maximum'],
                               button_type=record['button_type'], index=record.get('index',record['slot']-1+(8 if record['kind']=='button' else 0))))
        return result

    def AssignParameter(self, kind, slot, parameter, *, button_type=None, _id=None, _wire_index=None, _hardware_mapped=False, _saved_spec=None):
        """Assign one parameter slot, preserving other controls."""
        return self._assign_target(kind, slot, parameter, button_type=button_type, _id=_id,
                                   _wire_index=_wire_index, _hardware_mapped=_hardware_mapped, _saved_spec=_saved_spec)

    def _assign_target(self, kind, slot, parameter, *, button_type=None, _id=None, _wire_index=None,
                       _hardware_mapped=False, _saved_spec=None, action_id=None):
        """Shared one-slot installation for parameter and named action adapters."""
        self._layout_dirty = True
        if kind not in ('knob', 'button') or type(slot) is not int or not 1 <= slot <= 8:
            raise ValueError('Control must be knob/button, slot 1..8')
        key = kind, slot
        if action_id is not None:
            state = self.GetActionState(action_id)
            if not state['available'] and not _hardware_mapped:
                raise ValueError(state['error'])
        follower = getattr(self, '_follow', None)
        if follower is not None and (follower.gated or follower.paused or follower.pending):
            raise ValueError('Assignment is fenced during context transition')
        if self._dispatching:
            raise ValueError('Do not assign inside a hardware callback')
        target = self._host.controls.get(key) if self._collection is not None else self._host if key == ('knob', 1) else None
        if target is not None and target.touched and not self._host.learning:
            raise ValueError('Release the control before assigning')
        manager=getattr(self,'_layouts',None)
        if manager is not None:manager.owner_ready(required=True)
        if manager is not None and manager.quarantined and not manager.legacy:raise ValueError('Activate the repaired Layout before assigning')
        if _hardware_mapped and manager is not None and not manager.legacy:
            manager.capture(force=True)
            self._layout_dirty=True
        old = self._collection.bindings.get(key) if self._collection is not None else self._binding if key == ('knob', 1) else None
        if old is not None and (_id is None or old.id==_id) and old.parameter == parameter and getattr(old, 'action_id', None) == action_id and old.valid and (not old.menu_names or tuple(parameter.menuNames) == old.menu_names and tuple(parameter.menuLabels) == old.menu_labels):
            return self.GetControlState(old.id)
        style = getattr(parameter, 'style', '')
        mode = 'pulse' if action_id else 'value' if kind == 'knob' else 'cycle' if style == 'Menu' else 'pulse' if style == 'Pulse' else 'toggle'
        adapter = None if kind == 'knob' else button_type or (
            getattr(target, 'button_type', None) or ('push' if mode == 'pulse' else 'toggle'))
        import uuid
        id = _id or ('action.' if action_id else 'parameter.')+uuid.uuid4().hex
        spec = dict(kind=kind, slot=slot, id=id, parameter=parameter, mode=mode, button_type=adapter)
        if action_id:
            spec.update(action_id=action_id, label=state['label'], on_change=self._action_callback(action_id))
        if _saved_spec is not None:
            spec.update({k:v for k,v in _saved_spec.items() if k not in ('kind','slot','id','parameter','identity')})
            mode=spec['mode'];adapter=spec['button_type']
        if _wire_index is not None:
            spec['index'] = _wire_index
        # Validate the candidate and duplicate Par/bind-master ownership first.
        specs = []
        if self._collection is not None:
            for other_key, binding in self._collection.bindings.items():
                if other_key != key:
                    specs.append(dict(kind=other_key[0], slot=other_key[1], id=binding.id,
                                      parameter=binding.parameter, on_change=binding.on_change, action_id=getattr(binding, 'action_id', None),
                                      minimum=binding.minimum, maximum=binding.maximum,
                                      label=binding.label, value=binding.value,
                                      mode=self._collection.modes[other_key],
                                      button_type=self._collection.button_types[other_key], index=self._collection.indices[other_key]))
        elif key != ('knob', 1):
            binding = self._binding
            specs.append(dict(kind='knob', slot=1, id=binding.id if binding else 'Value',
                              parameter=binding.parameter if binding else self._value_parameter(),
                              on_change=binding.on_change if binding else None,
                              label=binding.label if binding else 'Value',
                              minimum=binding.minimum if binding else 0,
                              maximum=binding.maximum if binding else 1,
                              value=binding.value if binding else self._value_parameter().eval()))
        candidate = self.ownerComp.op('controls').module.Controls([*specs, spec])
        binding = candidate.bindings[key]
        watcher = self.ownerComp.op('base_targets/watch_'+kind+str(slot))
        if watcher is None:
            raise ValueError('Missing control watcher')
        if self._collection is None:
            # Transition once from single-target mode, before hardware LEARN.
            if _hardware_mapped:
                self.ownerComp.store('assignment_device_id',dict(device_id=self._host.device_id,group_id=self.ownerComp.par.Groupid.eval()))
            self.BindControls([*specs, spec], group_id=self.ownerComp.par.Groupid.eval(), _allow_learning=True)
        else:
            wire = next(wire for wire in candidate.specs() if (wire['kind'],wire['slot']) == key)
            replacement = self.ownerComp.op('collection_protocol').module.Control(
                self._host._send, key, wire['index'],
                wire['identity'], wire['label'], wire['value'], wire['formatter'], mode, adapter)
            if target is not None and target.mapped and not self._host.learning and not _hardware_mapped:
                self._host.clear_learn(key)
            watcher.par.active = False
            if old is not None:
                self._collection.ids.pop(old.id, None)
            self._collection.ids[id] = key
            self._collection.bindings[key] = binding
            self._collection.modes[key] = mode
            self._collection.button_types[key] = adapter
            self._collection.indices[key] = candidate.indices[key]
            self._collection.paths[key] = parameter.owner.path if parameter is not None else ''
            self._collection.errors.pop(key, None)
            self._host.controls[key] = replacement
            self._host._sync()
        watcher.par.op.expr = ''
        watcher.par.op.expr = "str(parent.RotoPython.ext.RotoPythonExt.Controlowner("+repr(kind)+","+str(slot)+"))"
        watcher.par.pars = parameter.name if parameter is not None else ''
        watcher.par.active = parameter is not None
        records = [record for record in self.ownerComp.fetch('parameter_assignments', [])
                   if (record['kind'],record['slot']) != key]
        records.append(dict(kind=kind, slot=slot, id=id, comp=os.path.relpath(parameter.owner.path,self.ownerComp.path) if parameter is not None else '',
                            parameter=parameter.name if parameter is not None else '', mode=mode, label=binding.label,
                            minimum=binding.minimum, maximum=binding.maximum, button_type=adapter, index=self._host.controls[key].index))
        if action_id:
            records[-1]['action_id'] = action_id
        self.ownerComp.store('parameter_assignments', records)
        # The overlay is the registration source; remove the superseded table row.
        table = self.ownerComp.op('base_targets/targets')
        for row in range(table.numRows-1,0,-1):
            if table[row,'kind'].val == kind and int(table[row,'slot'].val) == slot:
                table.deleteRow(row)
        removed = set(self.ownerComp.fetch('removed_controls', []))
        if old is not None and not _hardware_mapped and old.id != id:
            removed.add(old.id)
        removed.discard(id)
        self.ownerComp.store('removed_controls', sorted(removed))
        overrides = dict(self.ownerComp.fetch('control_overrides', {}))
        overrides.pop(id, None)  # this installation's validated spec is authoritative
        self.ownerComp.store('control_overrides', overrides)
        pending = {tuple(value) for value in self.ownerComp.fetch('pending_unmaps', [])};pending.discard(key)
        self.ownerComp.store('pending_unmaps', sorted(pending));self._host.pending_unmaps = pending
        self.ownerComp.store('pending_unmap_identities',[r for r in self.ownerComp.fetch('pending_unmap_identities',[]) if (r['kind'],r['slot'])!=key])
        self.ownerComp.store('needs_relearn', tuple(set(self.ownerComp.fetch('needs_relearn', ())) | {id}))
        self._enable_manual_controls(('knob',1) in self._collection.bindings)
        self._output_values = None
        self._publish()
        return self.GetControlState(id)


    def Hello(self):
        return "RotoPythonExt: single target / 8 knobs / 8 buttons"

    def _fault(self, exc):
        self._last_error = str(exc)
        if self._binding is not None:
            self._binding.valid = False
        self._host.mapped = False
        self._host.enabled = False
        self._host.last_event = "Binding suspended: " + self._last_error
        self._publish()

    def _mirror(self, normalized):
        if self._value_parameter().eval() != normalized:
            self._mirror_expected = normalized
            self._value_parameter().val = normalized

    def _assign(self, value):
        # Acknowledge physical input before the deferred TD callbacks.
        self._host.parameter_changed(value)
        try:
            self._dispatching = True
            if self._binding is not None:
                actual = self._binding.write(self._binding.from_normalized(value), "hardware")
                value = self._binding.normalized(actual)
                self._host.value = value
            self._mirror(value)
        except Exception as exc:
            self._fault(exc)
        finally:
            self._dispatching = False

    @property
    def Targetowner(self):
        binding = self._binding
        if binding is not None and binding.parameter is not None and binding.valid:
            try:
                if binding.parameter.owner.valid:
                    return binding.parameter.owner
            except Exception:
                pass
        return ""

    def _install_binding(self, candidate):
        removed=set(self.ownerComp.fetch('removed_controls', []))
        if getattr(self,'_restoring',False) and candidate.id in removed:
            self.BindControls([],group_id='removed.single',_allow_empty=True)
            return candidate.id
        if self._dispatching:
            raise ValueError("Do not replace binding inside on_change")
        if self._host.learning or self._host.touched:
            raise ValueError("Cannot bind while learning or touched")
        previous = self._identities.get(candidate.id)
        if previous is not None and previous != candidate.signature:
            raise ValueError("Target id already registered with different value semantics")
        watcher = self.ownerComp.op("target_callbacks")
        if watcher is None:
            raise RuntimeError("Install target_callbacks before binding")
        # All validation precedes changes to the existing binding.
        candidate.check_parameter()
        removed.discard(candidate.id)
        self.ownerComp.store('removed_controls',sorted(removed))
        pending={tuple(key) for key in self.ownerComp.fetch('pending_unmaps', [])}
        pending.discard(('knob',1));self.ownerComp.store('pending_unmaps',sorted(pending))
        self._leave_collection()
        self._host.configure_target(candidate.wire_identity, candidate.label,
                                    candidate.normalized(candidate.value),
                                    candidate.format_value)
        watcher.par.active = False
        watcher.par.op.expr = "str(parent.RotoPython.ext.RotoPythonExt.Targetowner)"
        watcher.par.pars = candidate.parameter.name if candidate.parameter is not None else ""
        self._target_path = candidate.parameter.owner.path if candidate.parameter is not None else ""
        self._restore_pending = False
        self._binding = candidate
        self._identities[candidate.id] = candidate.signature
        self._last_error = ""
        watcher.par.active = candidate.parameter is not None
        self._mirror(candidate.normalized(candidate.value))
        self._publish()
        return candidate.id

    def BindParameter(self, parameter, *, id, minimum=None, maximum=None, label=None):
        self._layout_dirty = True
        if (not parameter.owner.valid or not parameter.isCustom
                or parameter.style not in ("Float", "Int", "Menu") or parameter.readOnly
                or parameter.mode.name not in ("CONSTANT", "BIND")):
            raise ValueError("Bind a writable CONSTANT/BIND custom Float, Int or Menu parameter")
        minimum = (0 if parameter.style == "Menu" else parameter.normMin) if minimum is None else minimum
        maximum = (len(parameter.menuNames)-1 if parameter.style == "Menu" else parameter.normMax) if maximum is None else maximum
        # Explicit limits must not request values the target would silently clamp.
        if parameter.style != "Menu" and ((parameter.clampMin and float(minimum) < parameter.min)
                or (parameter.clampMax and float(maximum) > parameter.max)):
            raise ValueError("Binding range exceeds target clamp limits")
        candidate = self.ownerComp.op("binding").module.Binding(
            id, label or parameter.label, minimum, maximum, parameter_value(parameter),
            integer=parameter.style == "Int", parameter=parameter)
        return self._install_binding(candidate)

    def BindCallback(self, *, id, label, minimum, maximum, value, on_change):
        if getattr(self,'_layouts',None) is not None and not self._layouts.legacy:
            raise ValueError('Callback Layouts require a reconstruction factory; use existing registration-hook mode outside Layout conversion')
        self._layout_dirty = True
        if not callable(on_change):
            raise TypeError("on_change must be callable")
        candidate = self.ownerComp.op("binding").module.Binding(
            id, label, minimum, maximum, value, on_change=on_change)
        return self._install_binding(candidate)

    def SetValue(self, value, id=None):
        manager=getattr(self,'_layouts',None)
        if manager is not None:manager.owner_ready(required=True)
        if manager is not None and manager.quarantined and not manager.legacy:raise ValueError('Activate the repaired Layout before writing')
        if self._collection is not None:
            if self._dispatching:
                raise ValueError("Do not call SetValue inside on_change")
            key = self._collection.key(id)
            binding = self._collection.bindings[key]
            if self._collection.modes[key] == "pulse":
                raise ValueError("Pulse targets use Offerparameter for LEARN")
            try:
                learner = getattr(self,"_free_learner",None)
                if learner is not None and self._host.learning:
                    learner.ignore(binding.parameter,binding.clamp(value))
                actual = binding.write(value, "software")
                if learner is not None and self._host.learning:
                    self._host.controls[key].value = binding.normalized(actual)
                else:
                    self._host.parameter_changed(binding.normalized(actual), key)
                if key == ("knob", 1):
                    self._mirror(binding.normalized(actual))
                self._publish()
                return actual
            except Exception as exc:
                self._control_fault(key, exc)
                raise
        self._check_single_id(id)
        if self._dispatching:
            raise ValueError("Do not call SetValue recursively inside on_change")
        try:
            if self._binding is None:
                normalized = self.ownerComp.op("protocol").module.raw_value(value) / 16383
                actual = normalized
            else:
                learner = getattr(self,"_free_learner",None)
                if learner is not None and self._host.learning:
                    learner.ignore(self._binding.parameter,self._binding.clamp(value))
                actual = self._binding.write(value, "software")
                normalized = self._binding.normalized(actual)
            if self._host.learning and getattr(self,"_free_learner",None):
                self._host.value = normalized
            else:
                self._host.parameter_changed(normalized)
            self._mirror(normalized)
            self._publish()
            return actual
        except Exception as exc:
            self._fault(exc)
            raise


    def Unbind(self):
        self._layout_dirty = True
        removed=set(self.ownerComp.fetch('removed_controls', []))
        if getattr(self,'_restoring',False) and 'Value' in removed:
            self.BindControls([],group_id='removed.single',_allow_empty=True)
            return
        if self._dispatching:
            raise ValueError("Do not unbind inside on_change")
        if self._host.learning or self._host.touched:
            raise ValueError("Cannot unbind while learning or touched")
        watcher = self.ownerComp.op("target_callbacks")
        if watcher is not None:
            watcher.par.active = False
            watcher.par.op.expr = "str(parent.RotoPython.ext.RotoPythonExt.Targetowner)"
            watcher.par.pars = ""
        removed.discard('Value');self.ownerComp.store('removed_controls',sorted(removed))
        pending={tuple(key) for key in self.ownerComp.fetch('pending_unmaps', [])}
        pending.discard(('knob',1));self.ownerComp.store('pending_unmaps',sorted(pending))
        self._restore_pending = False
        self._binding = None
        self._last_error = ""
        self._leave_collection()
        self._host.configure_target("Value", "Value", self._value_parameter().eval(),
                                    self.ownerComp.op("protocol").module.format_number, default=True)
        self._publish()

    def onTargetValueChange(self, par, prev):
        binding = self._binding
        if binding is None or par != binding.parameter or not binding.valid:
            return
        try:
            if binding.external_changed(par.eval()):
                self.SetValue(binding.value)
        except Exception as exc:
            self._fault(exc)

    def _send(self, message):
        follower = getattr(self, '_follow', None)
        if follower is not None and follower.gated and follower.context_output(message):
            return False
        self._pending += (json.dumps({"midi": message}) + "\n").encode()
        if len(self._pending) > 262144:
            self.Disconnect()
            raise RuntimeError("MIDI output queue exceeded limit")

    def _publish(self):
        manager=getattr(self,'_layouts',None)
        with manager.owner_observation() if manager is not None else nullcontext():
            return self._publish_state()


    def _publish_inspector(self, force=False, states=None):
        manager=getattr(self,'_layouts',None)
        with manager.owner_observation() if manager is not None else nullcontext():
            return self._publish_inspector_state(force,states)

    def _publish_inspector_state(self, force=False, states=None):
        if not force and getattr(self,'_inspector_refresh_run',None) is not None:return
        inspector = self.ownerComp.op("inspector")
        if inspector is None:
            return
        try:
            data=inspector.op("inspector_data").module
            states=self.GetControlCatalog() if states is None else self._catalog_from_states(states)
            signature=getattr(data,'projection_signature',None)
            key=(getattr(inspector,'id',id(inspector)),data.refresh,signature(inspector,states)) if signature else None
            if not force and key is not None and key==getattr(self,'_inspector_projection',None) and not inspector.fetch('refresh_error',''):
                return
            if not force and key is not None:
                try:
                    self._inspector_refresh_run=run('args[0]._flush_inspector()',self,endFrame=True)
                    return
                except NameError:
                    pass  # Pure Python callers have no TD event scheduler.
            if force:self._cancel_inspector_refresh()
            data.refresh(inspector,states)
            self._inspector_projection=key
            inspector.store("refresh_error", "")
        except Exception as exc:
            # An optional UI observer must not break transport or target dispatch.
            inspector.store("refresh_error", str(exc))
            if inspector.op('owned_runtime') is not None:
                try:
                    import json
                    metadata=inspector.op('context_state')
                    snapshot=json.loads(metadata.text) if metadata.text.strip() else {}
                    snapshot['projection_error']=str(exc)
                    metadata.text=json.dumps(snapshot,sort_keys=True)+'\n'
                except Exception:
                    pass  # The original optional observer error remains in storage.
            title = inspector.op("title")
            if title is not None:
                title.par.text = "Inspector unavailable: " + str(exc)

    def _cancel_inspector_refresh(self):
        pending=getattr(self,'_inspector_refresh_run',None)
        if pending is not None:pending.kill()
        self._inspector_refresh_run=None

    def _flush_inspector(self):
        self._inspector_refresh_run=None
        if not getattr(self.ownerComp,'valid',True):return
        current=getattr(getattr(self.ownerComp,'ext',None),'RotoPythonExt',self)
        if current is not self:return
        # Read the latest catalog and UI scope after the full callback burst.
        self._publish_inspector(force=True)

    def _leave_collection(self):
        if self._collection is None:
            return
        for watcher in self.ownerComp.ops("base_targets/watch_*"):
            watcher.par.active = False
        old = self._host
        self._host = self.ownerComp.op("protocol").module.Host(self._send, self._assign, self._value_parameter().eval(), **self._display_names())
        self._host.connected, self._host.plugin = old.connected, old.plugin
        self._collection = None
        self._enable_manual_controls(True)
        self.ownerComp.op("base_targets/state").clear()
        self.ownerComp.op("base_targets/controls_values").clear()
        self._output_values = None

    def BindControls(self, specs, *, group_id, _allow_empty=False, _allow_learning=False, _automatic_follow=False):
        self._layout_dirty = True
        manager=getattr(self,'_layouts',None);follower=getattr(self,'_follow',None)
        routing_install=bool(_automatic_follow and manager is not None and manager.mutating
                             and follower is not None and follower.committing)
        if self._dispatching or ((self._host.learning or self._host.touched and not routing_install)
                                 and not (_allow_learning and self._host.learning)):
            raise ValueError("Cannot replace controls inside a callback, during LEARN or touch")
        specs=list(specs)
        if getattr(self,'_layouts',None) is not None and not self._layouts.legacy and any(spec.get('parameter') is None and not spec.get('action_id') for spec in specs):
            raise ValueError('Callback Layouts require a reconstruction factory; collection was not changed')
        specs=[dict(spec, on_change=self._action_callback(spec['action_id'])) if spec.get('action_id') else spec for spec in specs]
        original=bool(specs)
        removed=set(self.ownerComp.fetch('removed_controls', []))
        if getattr(self,'_restoring',False):
            assigned=self._assignment_specs()
            assigned_slots={(spec['kind'],spec['slot']) for spec in assigned}
            specs=[spec for spec in specs if spec['id'] not in removed and (spec['kind'],spec['slot']) not in assigned_slots]+assigned
        else:
            removed.difference_update(spec['id'] for spec in specs)
        overrides = self.ownerComp.fetch('control_overrides', {})
        specs = [dict(spec, **overrides.get(spec['id'], {})) for spec in specs]
        collection = self.ownerComp.op("controls").module.Controls(specs,allow_empty=_allow_empty or original or bool(removed))
        host = self.ownerComp.op("collection_protocol").module.CollectionHost(
            self._send, self._assign_control, list(collection.specs()), group_id,
            allow_empty=_allow_empty or original or bool(removed))
        host.track_name, host.plugin_name = self._host.track_name, self._host.plugin_name
        device = self.ownerComp.fetch('assignment_device_id',None)
        if device and device['group_id'] == group_id:
            host.device_id = device['device_id']
        pending={tuple(key) for key in self.ownerComp.fetch('pending_unmaps', [])} - set(collection.bindings)
        host.pending_unmaps=pending
        watchers = {}
        for key in collection.bindings:
            watcher = self.ownerComp.op("base_targets/watch_" + key[0] + str(key[1]))
            if watcher is None:
                raise ValueError("Install collection watchers before binding")
            watchers[key] = watcher
        for watcher in self.ownerComp.ops("base_targets/watch_*"):
            watcher.par.active = False
        self.ownerComp.op("target_callbacks").par.active = False
        host.connected, host.plugin, host.learning = self._host.connected, self._host.plugin, self._host.learning
        host._sync()
        self.ownerComp.store("removed_controls",sorted(removed))
        self.ownerComp.store("pending_unmaps",sorted(pending))
        self._host, self._collection, self._binding = host, collection, None
        self._enable_manual_controls(("knob", 1) in collection.bindings)
        self._output_values = None
        self._restore_pending, self._last_error = False, ""
        for key, watcher in watchers.items():
            binding = collection.bindings[key]
            # Reassigning the same expression can retain a pre-restore None cache.
            watcher.par.op.expr = ""
            watcher.par.op.expr = "str(parent.RotoPython.ext.RotoPythonExt.Controlowner(" + repr(key[0]) + "," + str(key[1]) + "))"
            watcher.par.pars = binding.parameter.name if binding.parameter is not None else ""
            watcher.par.active = binding.parameter is not None
        if host.connected and host.plugin:
            host._devices()
        self._mirror(host.value)
        self._publish()
        return tuple(collection.ids)

    def FreeLearnChanges(self, changes):
        if self._free_learner is not None:
            self._free_learner.changes(changes)

    def FreeLearnPulse(self, parameter):
        if self._free_learner is not None:
            self._free_learner.pulse(parameter)

    def Controlowner(self, kind, slot):
        if self._collection is None:
            return ""
        binding = self._collection.bindings.get((kind, slot))
        if binding is not None and binding.valid and binding.parameter is not None and binding.parameter.owner.valid:
            return binding.parameter.owner
        return ""

    def _control_fault(self, key, exc):
        self._collection.suspend(key, exc)
        self._host.controls[key].enabled = False
        self._host.controls[key].mapped = False
        self._last_error = str(exc)
        self._host._sync()
        self._publish()

    def _assign_control(self, key, value):
        if self._dispatching:
            return
        binding = self._collection.bindings[key]
        target = self._host.controls[key]
        try:
            manager=getattr(self,'_layouts',None)
            if manager is not None:manager.owner_ready(required=True)
            if manager is not None and manager.quarantined and not manager.legacy:raise ValueError('Activate the repaired Layout before dispatch')
            self._dispatching = True
            if self._collection.modes[key] == "pulse":
                self._collection.pulse(key)
            else:
                if self._collection.modes[key] == 'cycle':
                    current=parameter_value(binding.parameter) if binding.parameter is not None else binding.value
                    value = binding.normalized((int(current)+1) % len(binding.menu_names))
                target.parameter_changed(value)
                actual = binding.write(binding.from_normalized(value), "hardware")
                target.value = binding.normalized(actual)
                if key == ("knob", 1):
                    self._mirror(target.value)
        except Exception as exc:
            self._control_fault(key, exc)
        finally:
            self._dispatching = False


    def onControlChange(self, key, par, pulse=False):
        if self._collection is None:
            return
        binding = self._collection.bindings.get(key)
        if (binding is None or not binding.valid or binding.parameter is None
                or par.owner != binding.parameter.owner or par.name != binding.parameter.name):
            return
        try:
            if pulse:
                # Hardware dispatch already executes the business Pulse. Its
                # deferred callback must never offer or execute it again.
                expected = getattr(binding, "pulse_expected", 0)
                if expected:
                    binding.pulse_expected = expected - 1
                elif self._host.learning and not getattr(self,"_free_learner",None):
                    self._host.offer_parameter(key)
            elif binding.external_changed(par.eval()):
                if self._host.learning and getattr(self,"_free_learner",None):
                    target = self._host.controls[key]
                    target.value = binding.normalized(binding.value)
                else:
                    self._host.parameter_changed(binding.normalized(binding.value), key)
                if key == ("knob", 1):
                    self._mirror(binding.normalized(binding.value))
            self._publish()
        except Exception as exc:
            self._control_fault(key, exc)

    def _trace_control_midi(self, message):
        if self._collection is None:
            return
        is_button = len(message) == 3 and message[0] == 191 and 20 <= message[1] <= 27
        is_mapping = len(message) >= 8 and tuple(message[:7]) == (240, 0, 34, 3, 2, 11, 11)
        if is_button or is_mapping:
            table = self.ownerComp.op("base_targets/rx_events")
            table.appendRow([f"{time.monotonic():.3f}", "button" if is_button else "mapping", " ".join(str(x) for x in message)])
            while table.numRows > 33:
                table.deleteRow(1)

    def _check_controls(self):
        for key, binding in self._collection.bindings.items():
            if not binding.valid:
                continue
            try:
                binding.check_parameter()
                if binding.parameter is not None and binding.parameter.owner.path != self._collection.paths[key]:
                    self._collection.paths[key] = binding.parameter.owner.path
                    records = [dict(record) for record in self.ownerComp.fetch('parameter_assignments', [])]
                    for record in records:
                        if record['id'] == binding.id:
                            record['comp'] = os.path.relpath(binding.parameter.owner.path,self.ownerComp.path)
                            record['parameter'] = binding.parameter.name
                    self.ownerComp.store('parameter_assignments',records)
                    if self._collection.modes[key] != "pulse":
                        self.onControlChange(key, binding.parameter)
            except Exception as exc:
                self._control_fault(key, exc)

    def _publish_controls(self, states=None):
        states = [self.GetControlState(b.id) for b in self._collection.bindings.values()] if states is None else states
        observed = {state['id']:state for state in states}
        table = self.ownerComp.op("base_targets/state")
        rows = [["kind", "slot", "id", "mode", "value", "mapped", "valid", "error"]]
        for key, binding in self._collection.bindings.items():
            target = self._host.controls[key]
            state = observed[binding.id]
            rows.append([key[0], str(key[1]), binding.id, self._collection.modes[key], str(binding.value),
                         str(int(target.mapped)), str(int(state['valid'])), state['error']])
        content = "\n".join("\t".join(row) for row in rows) + "\n"
        if table.text.replace("\r\n", "\n") != content:
            table.text = content
        output = self.ownerComp.op("base_targets/controls_values")
        values = {key[0] + str(key[1]): binding.value for key, binding in self._collection.bindings.items()}
        previous=getattr(self, "_output_values", None)
        rebuild=(previous is None or previous.keys()!=values.keys()
                 or getattr(self,"_output_op_id",None)!=output.id
                 or output.numSamples!=1 or output.numChans!=len(values))
        changed=[(name,value) for name,value in values.items()
                 if previous is None or previous.get(name)!=value]
        channels=[] if rebuild else [(output[name],value) for name,value in changed]
        if rebuild or any(channel is None for channel,value in channels):
            output.clear()
            output.numSamples = 1
            for name, value in values.items():
                output.appendChan(name)[0] = value
        else:
            for channel,value in channels:channel[0]=value
        self._output_values=values;self._output_op_id=output.id
        first = self._collection.bindings.get(("knob", 1))
        self.ownerComp.op("base_state").par.Targetvalue = first.value if first is not None else 0
        self.ownerComp.op("base_state").par.Targetid = self._host.device_id
        self.ownerComp.op("base_state").par.Bindingvalid = self._host.enabled and all(observed[b.id]['valid'] for b in self._collection.bindings.values())

    def Connect(self):
        if self._restore_pending:
            self.Applybinding()
        if not self._host.enabled:
            raise ValueError("Apply a valid binding before connecting")
        self.Disconnect()
        folder = Path(project.folder)
        # Keep the venv entry-point symlink: resolving it loses venv discovery.
        python = (folder / self.ownerComp.par.Python.eval()).absolute()
        if not python.is_file():
            raise FileNotFoundError("Configure a Python interpreter with mido and python-rtmidi")
        embedded = self.ownerComp.op("midi_process")
        if embedded is not None and embedded.text.strip():
            command = [str(python), "-u", "-c", embedded.text,
                       "--device", self.ownerComp.par.Device.eval()]
        else:
            helper = (folder / self.ownerComp.par.Helper.eval()).resolve()
            if not helper.is_file():
                raise FileNotFoundError("Configure Helper or embed the midi_process DAT")
            command = [str(python), str(helper), "--device", self.ownerComp.par.Device.eval()]
        self._process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            bufsize=0)
        os.set_blocking(self._process.stdin.fileno(), False)
        os.set_blocking(self._process.stdout.fileno(), False)
        self._started_at = time.monotonic()
        self._host.last_event = "Opening MIDI ports"
        self._publish()

    def Disconnect(self):
        self._cancel_inspector_refresh()
        follower = getattr(self, '_follow', None)
        if follower is not None:
            follower.session_boundary()
        self._receive_epoch = None
        manager=getattr(self,"_layouts",None)
        if manager is not None and not manager.mutating:
            try: manager.capture(force=True)
            except ValueError: pass
        if self._process is not None:
            if self._process.poll() is None:
                self._process.terminate()
            self._process.stdin.close()
            self._process.stdout.close()
            # Reap the child; dropping Popen alone can leave a zombie until a
            # later subprocess launch. Bounded shutdown only, never in Tick.
            try:
                self._process.wait(timeout=0.05)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait(timeout=0.05)
            self._process = None
        self._receive = self._pending = b""
        self._transport_ready = False
        self._host.stop()
        learner = getattr(self,'_free_learner',None)
        if learner is not None:
            learner.pending = None
            learner.sync()
        self._publish()
        if getattr(self,'_inspector_refresh_run',None) is not None:
            self._publish_inspector(force=True)

    def Offerparameter(self, id=None):
        if self._collection is None:
            self._check_single_id(id)
        key = self._collection.key(id) if self._collection is not None else None
        if key is not None and getattr(self._collection.bindings[key], 'action_id', None):
            follower = getattr(self, '_follow', None)
            manager = getattr(self, '_layouts', None)
            if (not self.GetControlState(id)['valid'] or self._dispatching or
                    (follower is not None and (follower.gated or follower.paused or follower.pending)) or
                    (manager is not None and manager.mutating)):
                return False
        result = self._host.offer_parameter(key) if key is not None else self._host.offer_parameter()
        self._publish()
        return result

    def onParValueChange(self, par, prev):
        follower = getattr(self, '_follow', None)
        if follower is not None and par.name in ('Followcomp', 'Focuscomp'):
            try:
                if par.name == 'Followcomp':
                    follower.observe(force=True, explicit=bool(par.eval()))
                    follower.flush()
                elif not follower.manager.mutating and not follower.syncing_ui:
                    current = follower.handles.get(follower.manager.plugin()['id'])
                    current = current if follower.eligible(current) else None
                    desired = par.eval()
                    if desired is None and str(par.val).strip():
                        # TD leaves the old OP string unresolved on rename.
                        # An unresolved reference is not an explicit unlink.
                        follower.sync_ui()
                    elif desired != current:
                        follower.set_plugin_link(follower.manager.data['active'], follower.manager.track()['id'], follower.manager.plugin()['id'], desired)
            except ValueError as exc:
                self._last_error = str(exc); follower.sync_ui()
            self._publish(); return
        if par.name == 'Layout':
            manager=self._layout_manager()
            if manager.mutating or par.eval()==manager.data['active']:return
            try:
                manager.select(par.eval())
            except ValueError as exc:
                par.val=manager.data['active'];self._last_error=str(exc);self._publish()
        elif par.name == 'Track':
            manager=self._layout_manager()
            if manager.mutating or par.eval()==manager.layout()['active_track']:return
            try:self.SelectTrack(manager.data['active'],par.eval())
            except ValueError as exc:
                par.val=manager.layout()['active_track'];self._last_error=str(exc);self._publish()
        elif par.name == 'Plugin':
            manager=self._layout_manager()
            if manager.mutating or par.eval()==manager.plugin()['id']:return
            try:self.SelectPlugin(manager.data['active'],manager.track()['id'],par.eval())
            except ValueError as exc:
                par.val=manager.plugin()['id'];self._last_error=str(exc);self._publish()
        elif par.name in ("Trackname", "Pluginname"):
            manager=getattr(self,'_layouts',None)
            if manager is not None and manager.mutating:return
            if self._display_names()==dict(track_name=self._host.track_name,plugin_name=self._host.plugin_name):return
            try:
                if par.name=='Pluginname' and manager is not None and not manager.legacy:
                    self.RenamePlugin(manager.data['active'],manager.track()['id'],manager.plugin()['id'],par.eval())
                else:self.SetLayoutNames(**self._display_names())
            except ValueError as exc:
                par.val = self._host.track_name if par.name == "Trackname" else self._host.plugin_name
                self._last_error = str(exc)
            self._publish()
        elif par.name == 'Manualvalue' or par.name == 'Value' and getattr(par, 'owner', self.ownerComp) == self.ownerComp:
            value = par.eval()
            expected, self._mirror_expected = self._mirror_expected, None
            if value == expected:
                return
            if self._collection is not None:
                key = self._collection.key()
                self.SetValue(self._collection.bindings[key].from_normalized(value))
            elif self._binding is None:
                self.SetValue(value)
            elif self._binding.valid:
                self.SetValue(self._binding.from_normalized(value))

    def _request_delete(self, kind):
        manager = self._layout_manager()
        if kind == 'layout' and len(manager.data['records']) == 1:
            raise ValueError('Cannot delete the last Layout')
        if kind == 'track' and len(manager.layout()['tracks']) == 1:
            raise ValueError('Cannot delete the last Track')
        if kind == 'device' and len(manager.track()['plugins']) == 1:
            raise ValueError('Cannot delete the last Device')
        manager.guard()
        label = manager.layout()['name'] if kind == 'layout' else manager.plugin()['plugin_name'] if kind == 'device' else manager.track()['name']
        details = dict(kind=kind, manager=manager, layout_id=manager.data['active'],
                       plugin_id=manager.plugin()['id'],
                       track_id=manager.track()['id'], item='Delete ' + kind.capitalize() + ': ' + label)
        self._delete_request = details
        self._open_delete_menu(details)

    def _open_delete_menu(self, details):
        op.TDResources.op('popMenu').Open(items=['Cancel', details['item']],
            callback=self._on_delete_choice, callbackDetails=details, autoClose=1,
            title='Delete ' + details['kind'].capitalize() + '?')

    def _on_delete_choice(self, info):
        details = info.get('details')
        if (details is not self._delete_request or not self.ownerComp.valid
                or self.ownerComp.ext.RotoPythonExt is not self):
            return
        self._delete_request = None
        if info.get('item') != details['item']:
            return
        manager = details['manager']
        try:
            if (manager is not self._layouts or manager.data['active'] != details['layout_id']
                    or manager.track()['id'] != details['track_id'] or manager.plugin()['id'] != details['plugin_id']):
                raise ValueError('Delete confirmation expired')
            if details['kind'] == 'layout':
                self.RemoveLayout(details['layout_id'])
            elif details['kind'] == 'device':
                self.RemovePlugin(details['layout_id'],details['track_id'],details['plugin_id'])
            else:
                self.RemoveTrack(details['layout_id'], details['track_id'])
        except ValueError as exc:
            self._last_error = str(exc)
        self._publish()

    def Openinspector(self):
        """Open only this controller's owned Inspector; no routing/business call."""
        return self.ownerComp.op('inspector/owned_runtime').module.open_inspector(self.ownerComp)

    def onParPulse(self, par):
        if par.name in ('Newplugin','Deleteplugin'):
            manager=self._layout_manager();layout_id=manager.data['active'];track_id=manager.track()['id']
            try:
                if par.name=='Newplugin':
                    self.SelectPlugin(layout_id,track_id,self.CreatePlugin(layout_id,track_id,self.ownerComp.par.Newpluginname.eval()))
                else:self._request_delete('device')
            except ValueError as exc:self._last_error=str(exc)
            self._publish();return
        if par.name in ('Newtrack','Deletetrack'):
            manager=self._layout_manager();layout_id=manager.data['active']
            try:
                if par.name=='Newtrack':
                    self.SelectTrack(layout_id,self.CreateTrack(layout_id,self.ownerComp.par.Newtrackname.eval()))
                else:self._request_delete('track')
            except ValueError as exc:self._last_error=str(exc)
            self._publish();return
        if par.name in ('Newlayout','Renamelayout','Deletelayout'):
            manager=self._layout_manager()
            try:
                if par.name=='Newlayout':
                    self.SelectLayout(self.CreateLayout(self.ownerComp.par.Layoutname.eval()))
                elif par.name=='Renamelayout':
                    self.RenameLayout(manager.data['active'],self.ownerComp.par.Layoutname.eval())
                else:self._request_delete('layout')
            except ValueError as exc:
                self._last_error=str(exc)
            self._publish();return
        {"Connect": self.Connect, "Disconnect": self.Disconnect, "Openinspector": self.Openinspector,
         "Offerparameter": self.Offerparameter, "Applybinding": self.Applybinding}[par.name]()

    def Tick(self):
        if self._restore_pending:
            self.Applybinding()
        manager=getattr(self,'_layouts',None)
        with manager.owner_observation() if manager is not None else nullcontext():
            return self._tick()


    def onDestroyTD(self):
        follower = getattr(self, '_follow', None)
        if follower is not None:
            follower.refresh_links()
        self.Disconnect()


    def RegisterComp(self, comp, *, new_identity=False):
        return self._layout_manager().register_comp(comp,new_identity)


    def LookupCompLayout(self, comp):
        manager=self._layout_manager();manager.refresh_owners((comp,))
        return next((r['id'] for r in manager.data['records'] if r.get('owner')
                     and manager.owner_handles.get(r['owner']['id']) is comp and r['owner']['state']=='bound'),None)


    def GetLayoutRegistry(self):
        return self._layout_manager().registry_snapshot()


    def CheckLayoutRevision(self, revision):
        return self._layout_manager().check_revision(revision)


    def ValidateLayoutRegistry(self, snapshot):
        self._layout_manager().validate(snapshot)
        return True


    def PlanCompLayoutMigration(self, migration_id, classifications, *, entries=None, active_variants=None):
        """Explicit offline dry-run; unclassified/CUSTOM records remain in place."""
        dat = self.ownerComp.op('layout_migration')
        if dat is None:
            raise ValueError('Install migration source support first')
        return dat.module.plan(self._layout_manager(), migration_id, classifications, entries, active_variants)


    def ApplyCompLayoutMigration(self, plan, *, recovery_path):
        """Review a plan before this offline commit; never writes target Pars."""
        dat = self.ownerComp.op('layout_migration')
        if dat is None:
            raise ValueError('Install migration source support first')
        return dat.module.apply(self._layout_manager(), plan, recovery_path)


    def RelinkLayoutOwner(self, layout_id, comp):
        return self._layout_manager().relink_owner(layout_id,comp)


    def UnregisterLayoutOwner(self, layout_id):
        return self._layout_manager().unregister_owner(layout_id)


    def GetPluginTargets(self, layout_id=None, track_id=None, plugin_id=None):
        return self._layout_manager().plugin_targets(layout_id,track_id,plugin_id)


    def _publish_state(self):
        manager=getattr(self,'_layouts',None)
        if manager is not None and manager.mutating:
            return
        states=self.GetControlStates()
        self._update_catalog(states)
        pending = self.ownerComp.fetch('needs_relearn', ())
        if pending:
            mapped = {state['id']:state['mapped'] for state in states}
            remaining = tuple(id for id in pending if not mapped.get(id, False))
            if remaining != pending:
                self.ownerComp.store('needs_relearn', remaining)
        if manager is not None:
            try:
                manager.attach()
                manager.capture()
                if not manager.legacy:self.ownerComp.store('layout_registry_suspended',False)
            except ValueError as exc:
                self.ownerComp.store('layout_registry_suspended',True)
                self._last_error = str(exc)
        par = self.ownerComp.op("base_state").par
        par.Value.val = self._value_parameter().eval()
        par.Connected.val = self._host.connected
        par.Plugin.val = self._host.plugin
        par.Mapped.val = self._host.mapped
        par.Touched.val = self._host.touched
        par.Rx.val = self._host.rx
        par.Tx.val = self._host.tx
        par.Rejected.val = self._host.rejected
        par.Echoblocked.val = self._host.echo_blocked
        par.Status.val = self._host.last_event
        par.Learning.val = self._host.learning
        par.Bindingvalid.val = self._host.enabled and (self._binding is None or self._binding.valid)
        par.Lasterror.val = self._last_error
        par.Targetid.val = self._binding.id if self._binding is not None else "Value"
        par.Targetvalue.val = self._binding.value if self._binding is not None else self._host.value
        if self._collection is not None:
            self._publish_controls(states)
        marker = self.ownerComp.op("base_targets/mapping_marks")
        if marker is not None:
            try:
                marker.module.update(self.ownerComp, states)
                self.ownerComp.store("mapping_mark_error", "")
            except Exception as exc:
                self.ownerComp.store("mapping_mark_error", str(exc))
        self._publish_inspector(states=states)


    def _tick(self):
        if self._collection is not None:
            self._check_controls()
        if self._binding is not None and self._binding.valid:
            try:
                self._binding.check_parameter()
                parameter = self._binding.parameter
                if parameter is not None and parameter.owner.path != self._target_path:
                    self._target_path = parameter.owner.path
                    # A changed OP reference resets the watcher's baseline.
                    # Resync only on rename/reparent, not by polling values.
                    self.onTargetValueChange(parameter, None)
            except Exception as exc:
                self._fault(exc)
        learner = getattr(self,"_free_learner",None)
        if learner is not None:
            learner.sync()
        process = self._process
        follower = getattr(self, '_follow', None)
        if follower is not None:
            # Observe the TD selection boundary before dispatching this batch.
            follower.observe()
        if process is None:
            if follower is not None:
                follower.flush(); self._publish()
            return
        if not self._receive and follower is not None:
            self._receive_epoch = follower.token
        try:
            for _ in range(8):
                try:
                    chunk = os.read(process.stdout.fileno(), 65536)
                except BlockingIOError:
                    break
                if not chunk:
                    break
                self._receive += chunk
            if len(self._receive) > 262144:
                raise RuntimeError("MIDI input buffer exceeded limit")
            for _ in range(256):
                if b"\n" not in self._receive:
                    break
                line, self._receive = self._receive.split(b"\n", 1)
                try:
                    event = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise RuntimeError(line.decode(errors="replace")) from exc
                if "error" in event:
                    raise RuntimeError(event["error"])
                if event.get("ready"):
                    self._transport_ready = True
                    self._host.start()
                elif "midi" in event:
                    self._trace_control_midi(event["midi"])
                    self._receive_midi(event['midi'], self._receive_epoch)
                if follower is not None:
                    # Buffered bytes retain their ingress epoch, including a
                    # partial final line completed after context activation.
                    if not self._receive:
                        self._receive_epoch = follower.token
            if process.poll() is not None:
                raise RuntimeError(f"MIDI process exited ({process.returncode})")
            if not self._transport_ready and time.monotonic() - self._started_at > 8:
                raise TimeoutError("MIDI process did not become ready")
        except (OSError, ValueError, RuntimeError) as exc:
            self.Disconnect()
            self._host.last_event = str(exc)
            self._publish()
            raise
        if follower is not None:
            try:
                follower.flush(backlog=b'\n' in self._receive)
            except (OSError, TimeoutError):
                self.Disconnect(); raise
        try:
            self._host.flush_display(time.monotonic())
            if self._pending:
                try:
                    written = os.write(process.stdin.fileno(), self._pending)
                except BlockingIOError:
                    written = 0
                self._pending = self._pending[written:]
            self._publish()
        except (OSError, ValueError, RuntimeError) as exc:
            self.Disconnect()
            self._host.last_event = str(exc)
            self._publish()
            raise
