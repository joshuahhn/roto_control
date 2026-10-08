"""COMP focus links and one fenced, session-scoped routing decision per Tick."""
import copy
import os
import time

DEVICE_TAG = 'roto_device'


class CompFollower:
    def __init__(self, extension, sampler=None):
        self.e = extension
        self.owner = extension.ownerComp
        self.sampler = sampler or self._sample
        self.handles = {}
        self.pending = None
        self.sequence = self.connection_generation = self.routing_epoch = 0
        self.gated = self.committing = self.paused = False
        self.baseline = self.scope = None
        self.next_sample = 0
        self.error = ''
        self.status = 'waiting_for_selection'
        self.enabled_before = False
        self.observed_comp = ''
        self.backlog = False
        self.syncing_ui = False
        self.tag_sampler = self._tagged
        self.next_tag_scan = 0
        self.tag_error = ''

    @property
    def token(self):
        return self.connection_generation, self.routing_epoch

    @property
    def manager(self):
        return self.e._layout_manager()

    @property
    def enabled(self):
        par = getattr(self.owner.par, 'Followcomp', None)
        return bool(par is not None and par.eval())

    def eligible(self, comp):
        return bool(comp is not None and comp.valid and comp.isCOMP
                    and not getattr(comp, 'utility', False)
                    and getattr(comp, 'type', '') != 'annotate'
                    and not comp.path.startswith(('/sys/', '/local/'))
                    and comp.path != self.owner.path
                    and not comp.path.startswith(self.owner.path + '/'))

    def _sample(self):
        try:
            pane = ui.panes.current
            if pane is None or not pane.open or str(pane.type).split('.')[-1] != 'NETWORKEDITOR':
                return None, ()
            owner = pane.owner
            if owner is None or not owner.valid:
                return None, ()
            return (pane.id, owner.id, owner.path), tuple(owner.selectedChildren)
        except (NameError, AttributeError, RuntimeError):
            return None, ()

    def _components(self):
        """Inventory external COMPs, including untagged copies of owner tokens."""
        parent = getattr(self.owner,'parent',None)
        stack = [parent()] if callable(parent) else []
        result = []
        while stack:
            comp = stack.pop()
            if not self.eligible(comp):
                continue
            lookup = getattr(comp,'op',None)
            if callable(lookup) and lookup('RotoPythonExt') is not None and lookup('protocol') is not None:
                continue  # other controllers and their implementation details
            result.append(comp)
            stack.extend(child for child in getattr(comp,'children',()) if child.isCOMP)
        return sorted(result,key=lambda comp:comp.path)

    def _tagged(self):
        return [comp for comp in self._components() if DEVICE_TAG in getattr(comp,'tags',())]

    def owner_candidates(self):
        components=self._components()
        # The default tag sampler is derived from this same inventory.
        tagged=list(self.tag_sampler()) if self.tag_sampler!=self._tagged else []
        return components+tagged+list(self.handles.values())

    def sync_tags(self, force=False):
        """Allocate owner Layouts while idle; never select or move legacy mappings."""
        now=time.monotonic()
        if not force and now<self.next_tag_scan:return []
        self.next_tag_scan=now+1
        m=self.manager;h=self.e._host
        if (m.legacy or self.paused or self.gated or self.pending or self.backlog
                or m.locked or m.mutating or m.touched or h.touched or h.learning or self.e._dispatching
                or getattr(self.e,'_process',None) is not None and not (h.connected and h.plugin)):
            return []
        try:
            self.refresh_links()
            candidates=list({comp.path:comp for comp in self.tag_sampler() if self.eligible(comp)
                             and DEVICE_TAG in getattr(comp,'tags',())}.values())
            m.guard();m.capture(force=True)
            previous=copy.deepcopy(m.data);handles=dict(self.handles);owners=dict(m.owner_handles)
            tokens=[];created=[]
            try:
                for comp in candidates:
                    if not callable(getattr(comp,'fetch',None)):
                        raise ValueError('COMP must support persistent storage')
                    token=m.owner_token(comp)
                    known=next((r for r in m.data['records'] if token and r.get('owner',{}).get('id')==token),None)
                    if known and known['owner']['state']=='unregistered':continue
                    tokens.append((comp,token))
                    layout_id=m.register_comp(comp)
                    if not any(r['id']==layout_id for r in previous['records']):created.append(getattr(comp,'id',comp.path))
            except Exception as original:
                m._owner_rollback(previous,owners,handles,tokens,{},original)
                raise
            self.tag_error='';return created
        except (ValueError,RuntimeError,AttributeError) as exc:
            self.tag_error=str(exc);return []

    def refresh_links(self):
        m = getattr(self.e, '_layouts', None)
        if m is None:
            return
        m.refresh_owners()
        changed = False
        present = set()
        for layout in m.data['records']:
            for track in layout['tracks']:
                for plugin in track['plugins']:
                    link = plugin.get('focus_comp')
                    if not link:
                        continue
                    tid = plugin['id']; present.add(tid)
                    if (layout.get('owner',{}).get('entry_plugin_id')==tid or link.get('owner_id')) and layout['owner']['state']!='bound':
                        if link['state']!='missing':link['state']='missing';changed=True
                        self.handles.pop(tid,None)
                        continue
                    if link['state'] == 'missing':
                        self.handles.pop(tid, None)
                        continue
                    if tid not in self.handles:
                        self.handles[tid] = self.owner.op(link['path'])
                    comp = self.handles[tid]
                    if not self.eligible(comp):
                        link['state'] = 'missing'; changed = True
                        if self.pending and self.pending['plugin_id'] == tid:
                            self.pending = None
                        continue
                    path = os.path.relpath(comp.path, self.owner.path)
                    if path != link['path']:
                        self._rebase_targets(plugin, link['path'], path)
                        link['path'] = path; changed = True
                    if plugin.get('name_mode') == 'comp' and not self.e._host.learning:
                        name = getattr(comp, 'name', comp.path.rsplit('/', 1)[-1])
                        hardware_name = ''.join(c if 32 <= ord(c) <= 126 else '?' for c in name)[:12]
                        if plugin['plugin_name'] != hardware_name or plugin.get('comp_name') != name:
                            plugin.update(plugin_name=hardware_name, comp_name=name); changed = True
                            if not m.legacy and plugin is m.plugin():
                                self.e._host.plugin_name = hardware_name
                                old_mutating = m.mutating; m.mutating = True
                                try:self.owner.par.Pluginname.val = hardware_name
                                finally:m.mutating = old_mutating
                                if self.e._host.connected and self.e._host.plugin and not self.gated:
                                    m.announce(select=False)
        for tid in set(self.handles) - present:
            self.handles.pop(tid)
        if self.pending:
            try:
                m.plugin(self.pending['layout_id'], self.pending['track_id'], self.pending['plugin_id'])
            except ValueError:
                self.pending = None
        if changed:
            m.save()
            m.menu()

    def _rebase_targets(self, plugin, old_path, new_path, layout_id=None):
        """Rebase only destinations inside this linked live COMP, keeping hashes."""
        old_absolute = os.path.normpath(self.owner.path + '/' + old_path)
        new_absolute = os.path.normpath(self.owner.path + '/' + new_path)
        def rebase(value):
            if isinstance(value, dict):
                path = value.get('comp')
                if isinstance(path, str):
                    normalized = os.path.normpath(path)
                    for old, new in ((old_path, new_path), (old_absolute, new_absolute)):
                        if normalized == old or normalized.startswith(old + '/'):
                            value['comp'] = new + normalized[len(old):]
                            break
                for child in value.values():rebase(child)
            elif isinstance(value, (list, tuple)):
                for child in value:rebase(child)
        m = self.manager
        # A live rename moves the same target everywhere. Explicit owner relink
        # changes only that owner's configuration, preserving Custom references.
        records=m.all_plugins() if layout_id is None else (p for t in m.layout(layout_id)['tracks'] for p in t['plugins'])
        for record in records:
            rebase(record['targets']);rebase(record['state'])
        if not m.legacy and (layout_id is None or layout_id==m.data['active']):
            for field in ('parameter_assignments', 'page_targets', 'control_catalog'):
                value = copy.deepcopy(self.owner.fetch(field, []));rebase(value)
                self.owner.store(field, value)
            self.e._layout_dirty = True

    def sync_ui(self):
        par = getattr(self.owner.par, 'Focuscomp', None)
        if par is None or getattr(self.e, '_layouts', None) is None or self.syncing_ui:
            return
        self.refresh_links()
        comp = self.handles.get(self.manager.plugin()['id'])
        desired = comp if self.eligible(comp) else None
        if par.eval() != desired:
            self.syncing_ui = True
            try:par.val = desired.path if desired else ''
            finally:self.syncing_ui = False

    def set_link(self, layout_id, track_id, comp):
        return self.set_plugin_link(layout_id, track_id, self.manager.plugin(layout_id, track_id)['id'], comp)

    def set_plugin_link(self, layout_id, track_id, plugin_id, comp):
        m = self.manager
        if m.legacy:
            raise ValueError('Focus links require Parameter mapping')
        plugin = m.plugin(layout_id, track_id, plugin_id)
        if m.layout(layout_id).get('owner',{}).get('entry_plugin_id')==plugin_id:
            raise ValueError('Use RelinkLayoutOwner to change the owner Device link')
        self.refresh_links()
        if comp is not None:
            if not self.eligible(comp):
                raise ValueError('Choose a valid external COMP')
            for other in m.layout(layout_id)['tracks']:
                for other_plugin in other['plugins']:
                    if other_plugin['id'] != plugin_id and self.handles.get(other_plugin['id']) == comp:
                        owner=m.layout(layout_id).get('owner')
                        if not owner or m.owner_handles.get(owner['id']) is not comp:
                            raise ValueError('COMP already has a Follow link in this Layout')
        link=dict(path=os.path.relpath(comp.path,self.owner.path),state='bound') if comp else None
        owner=m.layout(layout_id).get('owner')
        if link and owner and m.owner_handles.get(owner['id']) is comp:link['owner_id']=owner['id']
        plugin['focus_comp'] = link
        plugin['name_mode'] = 'comp' if comp else 'manual'
        self.handles.pop(plugin_id, None)
        if comp is not None:
            self.handles[plugin_id] = comp
        self.invalidate()
        self.refresh_links(); m.save(); m.menu()
        return copy.deepcopy(plugin['focus_comp'])

    def resolve(self, comp):
        if self.manager.legacy:
            raise ValueError('COMP Follow is unavailable in Python registration')
        self.refresh_links()
        if not self.eligible(comp):
            raise ValueError('Choose a valid external COMP')
        matches = [(t['id'], p['id']) for t in self.manager.layout()['tracks'] for p in t['plugins']
                   if p.get('focus_comp') and p['focus_comp']['state'] == 'bound'
                   and self.handles.get(p['id']) == comp]
        if len(matches) != 1:
            raise ValueError('COMP has no unique Follow link in Active Layout')
        return self.manager.data['active'], *matches[0]

    def invalidate(self):
        self.pending = None
        self.baseline = None
        self.error = ''
        self.next_sample = 0
        self.status = 'waiting_for_selection'
        self.observed_comp = ''

    def session_boundary(self):
        self.connection_generation += 1
        self.routing_epoch += 1
        self.invalidate()
        self.gated = False
        m = getattr(self.e, '_layouts', None)
        if m is not None:
            m.locked = False; m.touched.clear(); m.confirmed = False
            m.selected_track = m.track()['id']
            m.selected_plugin = m.plugin()['id']
        self.clear_controls()
        self.e._host.learning = self.e._host.touched = False
        for target in getattr(self.e._host, 'controls', {}).values():
            target.touched = False

    def clear_controls(self):
        host = self.e._host
        m = getattr(self.e, '_layouts', None)
        if m is not None:
            m.confirmed = False
        for target in getattr(host, 'controls', {}).values() or (host,):
            target.mapped = False
            target._parts.clear()
            target._deferred_value = target._display_dirty = False
            target._input_value = None
            if hasattr(target, '_pulse_state'):
                target._pulse_state = 0; target.last_pulse = float('-inf')
        if hasattr(host, '_sync'):
            host._sync()
        else:
            host.mapped = False
        self.e._mirror_expected = None
        learner = getattr(self.e, '_free_learner', None)
        if learner:
            learner.pending = learner.last_parameter = None
            learner.ignored = {}; learner.baseline = {}

    @staticmethod
    def context_output(message):
        message = tuple(message)
        if len(message) == 3 and message[0] == 191:
            return True
        if len(message) >= 8 and message[0] == 240:
            return message[5] != 10 or message[6] not in (1, 3, 4, 5, 7, 8)
        return False

    def fence(self):
        if not self.gated:
            self.routing_epoch += 1
            self.gated = True
            self.clear_controls()
            self.e._discard_context_output()
        self.status = 'pending'

    def request(self, layout_id, track_id, source, comp=None, plugin_id=None):
        m = self.manager
        if self.scope is None:
            self.scope = m.data['active'], m.legacy
        plugin_id = m.plugin(layout_id, track_id, plugin_id)['id']
        if source.startswith('hardware') and not (self.e._host.connected and self.e._host.plugin):
            return
        self.sequence += 1
        self.pending = dict(layout_id=layout_id, track_id=track_id, plugin_id=plugin_id, source=source,
                            sequence=self.sequence, generation=self.connection_generation, comp=comp)
        self.error = ''
        if (not m.locked or source == 'hardware_plugin') and (layout_id, track_id, plugin_id) != m.context()['key']:
            self.fence()

    def unlocked(self):
        m = self.manager
        if self.pending is None and m.selected_track and m.selected_track != m.track()['id']:
            self.request(m.data['active'], m.selected_track, 'hardware')
        if self.pending or m.selected_track != m.track()['id']:
            self.fence()

    def before_manual(self, layout_id, track_id, plugin_id=None):
        if self.committing:
            return
        self.pending = None
        plugin_id = self.manager.plugin(layout_id, track_id, plugin_id)['id']
        if (layout_id, track_id, plugin_id) != self.manager.context().get('key'):
            self.fence()

    def after_manual(self):
        if self.committing:
            return
        self.pending = None
        self.sync_ui()
        if self.gated:
            self.recover()

    def observe(self, force=False, explicit=False):
        if self.paused:
            return
        try:
            self._observe(force, explicit)
        except (OSError, TimeoutError):
            raise
        except Exception as exc:
            self.pending = None
            self.paused = True
            self.fence()
            self.error = self.e._last_error = str(exc)
            self.status = 'paused'

    def repair(self):
        self.paused = False
        self.invalidate()

    def _observe(self, force=False, explicit=False):
        m = self.manager
        scope = m.data['active'], m.legacy
        if self.scope != scope:
            self.invalidate(); self.scope = scope
        now = time.monotonic()
        if not force and now < self.next_sample:
            return
        self.next_sample = now + .1
        self.refresh_links()
        registered = self.sync_tags()
        enabled = self.enabled
        if m.legacy or not enabled:
            if self.pending and self.pending['source'] == 'td':
                self.pending = None
            self.baseline = None
            self.enabled_before = enabled
            self.status = 'unavailable' if m.legacy else 'disabled'
            return
        pane, selected = self.sampler()
        self.observed_comp = selected[0].path if pane is not None and len(selected) == 1 and self.eligible(selected[0]) else ''
        signature = pane, tuple((getattr(x, 'id', id(x)), getattr(x, 'path', ''),
                                 DEVICE_TAG in getattr(x, 'tags', ())) for x in selected)
        old = self.baseline
        self.baseline = signature
        activating = explicit or (enabled and not self.enabled_before and old is not None) or (
            old is not None and old[0]==pane and len(selected)==1
            and getattr(selected[0],'id',selected[0].path) in registered)
        self.enabled_before = enabled
        if old is None or old[0] != pane:
            if self.pending and self.pending['source'] == 'td':
                self.pending = None
            if not activating:
                self.status = 'waiting_for_editor' if pane is None else 'waiting_for_selection'
                return
        if signature == old and not activating:
            return
        if self.pending and self.pending['source'] == 'td':
            self.pending = None
        if pane is None or len(selected) != 1:
            self.status = 'waiting_for_selection'; return
        try:
            layout_id, track_id, plugin_id = self.resolve(selected[0])
            self.request(layout_id, track_id, 'td', selected[0], plugin_id)
        except ValueError as exc:
            self.error = str(exc); self.status = 'failed'

    def recover(self):
        m = self.manager
        self.clear_controls()
        if not m.locked:m.selected_track = m.track()['id']
        m.selected_plugin = m.plugin()['id']
        self.gated = False
        if self.e._host.connected and self.e._host.plugin:
            m.announce_tracks(); m.announce()
        self.sync_ui()
        self.status = 'failed' if self.error else 'ready'

    def flush(self, backlog=False):
        self.backlog = backlog
        self.observe(force=bool(self.pending and self.pending['source'] == 'td'))
        if backlog or self.paused:
            return
        m = self.manager; h = self.e._host
        explicit_device = bool(self.pending and self.pending['source'] == 'hardware_plugin')
        if m.legacy or (m.locked and not explicit_device) or m.touched or h.touched or h.learning or m.mutating or self.e._dispatching:
            return
        if getattr(self.e, '_process', None) is not None and not (h.connected and h.plugin):
            self.status = 'waiting_for_transport'; return
        request = self.pending
        if request is None:
            if self.gated:
                self.recover()
            return
        self.pending = None
        if request['generation'] != self.connection_generation:
            return
        try:
            if request['layout_id'] != m.data['active']:
                raise ValueError('Follow context expired')
            if request['source'] == 'td' and self.resolve(request['comp']) != (request['layout_id'], request['track_id'], request['plugin_id']):
                raise ValueError('Follow link expired')
            m.resolve(m.record(request['layout_id'], request['track_id'], request['plugin_id']))
            self.committing = True
            m.select_plugin(request['layout_id'], request['track_id'], request['plugin_id'], hardware=explicit_device)
            if self.gated:
                self.recover()
            self.status = 'ready'; self.error = ''
        except (OSError, TimeoutError):
            raise
        except Exception as exc:
            self.error = str(exc); self.e._last_error = self.error; self.status = 'failed'
            if getattr(exc, 'rollback_failed', False):
                self.paused = True; self.fence(); self.status = 'paused'
            elif self.gated:
                self.recover()
        finally:
            self.committing = False

    def select(self, comp):
        layout_id, track_id, plugin_id = self.resolve(comp)
        self.manager.guard()
        self.manager.select_plugin(layout_id, track_id, plugin_id)
        return self.manager.context()

    def context(self):
        self.refresh_links()
        pending = self.pending
        m = self.manager; h = self.e._host
        reasons = [name for name, active in (('paused',self.paused), ('backlog',self.backlog),
                    ('LOCK',m.locked), ('LEARN',h.learning), ('touch',bool(m.touched or h.touched)),
                    ('activation',m.mutating or self.e._dispatching),
                    ('transport',getattr(self.e,'_process',None) is not None and not (h.connected and h.plugin))) if active]
        routing = self.handles.get(m.plugin()['id'])
        return dict(enabled=self.enabled, status=self.status, error=self.error,
                    device_tag=DEVICE_TAG, tag_error=self.tag_error,
                    observed_comp=self.observed_comp, routing_comp=routing.path if self.eligible(routing) else '',
                    pending_reason=', '.join(reasons) if pending or self.gated else '',
                    connection_generation=self.connection_generation, routing_epoch=self.routing_epoch,
                    gated=self.gated, source=pending['source'] if pending else None,
                    sequence=pending['sequence'] if pending else None,
                    requested_comp=pending['comp'].path if pending and self.eligible(pending['comp']) else '',
                    pending_track_id=pending['track_id'] if pending else None,
                    pending_plugin_id=pending['plugin_id'] if pending else None,
                    focus_comp=copy.deepcopy(self.manager.plugin().get('focus_comp')),
                    **self.manager.context())
