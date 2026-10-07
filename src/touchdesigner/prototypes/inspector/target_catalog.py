"""On-demand, cancellable target discovery; caches contain scalar records only."""
from collections import OrderedDict
from time import perf_counter


class TargetService:
    def __init__(self, source, schedule, capacity=32, limit=4096, budget=.002):
        self.source = source
        self.schedule = schedule
        self.capacity, self.limit, self.budget = capacity, limit, budget
        self.cache = OrderedDict()
        self.jobs = {}
        self.epoch = 0
        self.serial = 0
        self.errors = []

    def Start(self, identity, scope, kind, callback, refresh=False):
        if kind not in ('knob', 'button'):
            raise ValueError('Invalid control kind')
        self.Cancel(identity)
        scope = self.source.Scope(scope)
        key = (self.source.Session(), scope, kind)
        if not refresh and key in self.cache:
            self.cache.move_to_end(key)
            rows, truncated = self.cache[key]
            try:callback(rows, truncated, '')
            except Exception as error:self.errors=(self.errors+[str(error)])[-8:]
            return
        if len(self.jobs) >= 2:
            raise ValueError('Target discovery busy; retry after the other picker finishes')
        self.serial += 1
        job = dict(serial=self.serial, key=key, units=iter(self.source.Units(scope, kind)),
                   rows=[], callback=callback, pending=None, steps=0, truncated=False)
        self.jobs[identity] = job
        self._step(identity, job['serial'])

    def _step(self, identity, serial):
        job = self.jobs.get(identity)
        if not job or job['serial'] != serial:
            return
        job['pending'] = None
        started = perf_counter()
        try:
            if job['key'][0] != self.source.Session():
                self._finish(identity, job, 'Controller session changed; reopen picker')
                return
            # Time budget and unit bound both apply, even with a coarse clock.
            for _ in range(128):
                if job['steps'] >= self.limit * 4 or len(job['rows']) >= self.limit:
                    job['truncated'] = True
                    self._finish(identity, job)
                    return
                unit = next(job['units'])
                job['steps'] += 1
                if unit is False:
                    job['truncated'] = True
                elif unit is not None:
                    row = dict(unit)
                    row['handle'] = (self.epoch, job['key'][0], job['key'][2],
                                     row['owner_id'], row['path'], row['name'], row['fingerprint'])
                    job['rows'].append(row)
                if perf_counter() - started >= self.budget:
                    break
        except StopIteration:
            self._finish(identity, job)
            return
        except Exception as error:
            self._finish(identity, job, str(error))
            return
        job['pending'] = self.schedule(lambda: self._step(identity, serial))

    def _finish(self, identity, job, error=''):
        if self.jobs.get(identity) is not job:
            return
        self.jobs.pop(identity)
        if hasattr(job['units'],'close'):job['units'].close()
        rows = () if error else tuple(job['rows'])
        if not error:
            self.cache[job['key']] = (rows, job['truncated'])
            self.cache.move_to_end(job['key'])
            while len(self.cache) > self.capacity or sum(len(v[0]) for v in self.cache.values()) > self.limit:
                self.cache.popitem(last=False)
        try:
            job['callback'](rows, job['truncated'], error)
        except Exception as failure:
            self.errors = (self.errors + [str(failure)])[-8:]

    def Cancel(self, identity):
        job = self.jobs.pop(identity, None)
        if job:
            if job['pending'] is not None:
                job['pending'].kill()
            job['units'].close() if hasattr(job['units'], 'close') else None

    def Reset(self):
        for identity in list(self.jobs):
            self.Cancel(identity)
        self.cache.clear()
        self.errors.clear()
        self.epoch += 1

    def Resolve(self, handle, kind):
        if not isinstance(handle, tuple) or len(handle) != 7:
            raise ValueError('Choose a target from the picker')
        epoch, session, offered_kind, owner_id, path, name, fingerprint = handle
        if epoch != self.epoch or session != self.source.Session() or kind != offered_kind:
            raise ValueError('Target picker expired; refresh it')
        parameter, record = self.source.Resolve(path, name, kind)
        if record['reason']:
            raise ValueError(record['reason'])
        if record['owner_id'] != owner_id or record['fingerprint'] != fingerprint:
            raise ValueError('Target definition changed; refresh picker')
        return parameter

    def Stats(self):
        return dict(pages=len(self.cache), entries=sum(len(v[0]) for v in self.cache.values()),
                    jobs=len(self.jobs), pending=sum(j['pending'] is not None for j in self.jobs.values()),
                    errors=tuple(self.errors))


class TDTargetSource:
    def __init__(self, owner):
        self.owner = owner

    @property
    def controller(self):
        model = self.owner.par.Model.eval()
        c = model.par.Controller.eval() if model else None
        if not c:
            raise ValueError('Choose a controller')
        return c

    def Session(self):
        c = self.controller
        e = c.ext.RotoPythonExt
        return (c.id, id(e), getattr(getattr(e, '_follow', None), 'connection_generation', None))

    def _excluded(self, component):
        c = self.controller
        # Whole internal subtrees are skipped, not scanned then filtered.
        return (component == c or component.path.startswith(c.path + '/') or
                component.name.startswith(('inspector_', 'TDMCP', 'tdmcp')) or component.OPType == 'annotateCOMP')

    def Scope(self, path):
        c = self.controller
        component = c.op(str(path).strip())
        if not component or component.family != 'COMP' or self._excluded(component):
            raise ValueError('Scope must be a target COMP outside controller/Inspector internals')
        root = c.parent().path
        if component.path != root and not component.path.startswith(root.rstrip('/') + '/'):
            raise ValueError('Scope must be inside the controller project')
        return component.path

    def _record(self, parameter, kind):
        c = self.controller
        reason = ''
        chain = ()
        try:
            chain = c.op('binding').module.parameter_chain(parameter)
            mode = 'value' if kind == 'knob' else 'cycle' if parameter.style == 'Menu' else 'pulse' if parameter.style == 'Pulse' else 'toggle'
            c.op('controls').module.Controls([dict(kind=kind, slot=1, id='inspector.picker.check', parameter=parameter, mode=mode)])
        except (ValueError, AttributeError, TypeError) as error:
            reason = str(error)
        fingerprint = tuple((p.owner.id, p.owner.path, p.name, p.style, p.mode.name, p.readOnly,
                             p.min, p.max, p.normMin, p.normMax, p.clampMin, p.clampMax,
                             tuple(p.menuNames or ()), tuple(p.menuLabels or ())) for p in (chain or (parameter,)))
        return dict(owner_id=parameter.owner.id, path=parameter.owner.path, name=parameter.name,
                    label=parameter.label, style=parameter.style, reason=reason, fingerprint=fingerprint)

    def Units(self, scope, kind):
        stack = [scope]
        visited = 0
        while stack and visited < 4096:
            component = op(stack.pop())
            visited += 1
            yield None
            if not component or not component.valid or self._excluded(component):
                continue
            for parameter in component.customPars:
                if parameter.style in ('Float', 'Int', 'Menu', 'Toggle', 'Pulse'):
                    yield self._record(parameter, kind)
                else:
                    yield None
            children = []
            remaining = 4096 - visited - len(stack)
            for child in component.children:
                yield None
                if child.family != 'COMP' or self._excluded(child):continue
                if len(children) >= remaining:
                    yield False
                    break
                children.append(child.path)
            stack.extend(reversed(children))
        if stack:
            yield False

    def Resolve(self, path, name, kind):
        component = op(self.Scope(path))
        parameter = getattr(component.par, name, None)
        if parameter is None or not parameter.isCustom:
            raise ValueError('Target parameter disappeared; refresh picker')
        return parameter, self._record(parameter, kind)


class InspectorTargets(TargetService):
    def __init__(self, ownerComp):
        self.ownerComp = ownerComp
        super().__init__(TDTargetSource(ownerComp), lambda callback: run('args[0]()', callback, delayFrames=1))

    def onDestroyTD(self):
        self.Reset()
