"""Read-only snapshots around a full saved-project load (run inside TD)."""
from pathlib import Path
import hashlib
import json
import os
import time

c = op('/roto_control_python/roto_python')
folder = Path(project.folder)
artifact = folder / 'prototypes/inspector/project_restart_verification.json'
phase = globals().get('phase', 'before')

def window(p):
    return dict(open=p.isOpen, width=p.contentWidth, height=p.contentHeight,
                x=p.x, y=p.y, opening_width=p.par.winw.eval(),
                opening_height=p.par.winh.eval())

views = {}
for name in ('inspector_below', 'inspector_popup'):
    v = op('/' + name)
    u = v.ext.InspectorView
    views[name] = dict(context=u.Key(), presentation=u.style, selected=u.selected,
        follow=u._follow_routing, filter=u._filter, mapping_open=u._mapping.open,
        details_open=u._details_open, picker_open=u._picker is not None,
        popup_extra=u._popup_extra, popup_geometry=u._popup_geometry,
        settlement_pending=u._popup_geometry_settle is not None,
        main=window(u._main), popup=window(u._popup), error=u._error,
        stats=u.Stats())
sources = {}
for root in (c, op('/inspector_model'), op('/inspector_below'), op('/inspector_popup')):
    for dat in root.findChildren(type=textDAT):
        if dat.par.language.eval() == 'python':
            sources[dat.path] = hashlib.sha256(dat.text.encode()).hexdigest()

snapshot = dict(time=time.time(), pid=os.getpid(), project=project.name,
    state=c.State, catalog=c.GetControlCatalog(), context=c.GetLayoutContext(),
    registry=c.fetch('layout_registry'), views=views, sources=sources,
    model=op('/inspector_model').ext.InspectorModel.Stats(),
    projection_pending=c.ext.RotoPythonExt._inspector_refresh_run is not None,
    probe_exists=bool(op('/base_inspector_acceptance')),
    errors={root.path:root.errors(recurse=True) for root in
            (c, op('/inspector_model'), op('/inspector_below'), op('/inspector_popup'))})
# Match the on-disk JSON representation (TD context APIs return tuples).
snapshot = json.loads(json.dumps(snapshot, default=str))
record = json.loads(artifact.read_text()) if artifact.exists() else {}
record[phase] = snapshot
baseline_phase = globals().get('baseline_phase', 'before')
if phase != baseline_phase:
    before = record[baseline_phase]
    fields = ('id','kind','slot','mode','label','minimum','maximum','button_type',
              'binding_type','comp','parameter')
    project_rows = lambda rows: [{k:r.get(k) for k in fields} for r in rows]
    values = lambda rows: {r['id']:r['value'] for r in rows}
    # Registry runtime snapshots get rebuilt on restore. Its persistent target
    # definitions, identities, pages and context structure must remain exact.
    def definitions(registry):
        data = json.loads(json.dumps(registry))
        for layout in data['records']:
            for track in layout['tracks']:
                for plugin in track['plugins']:
                    state = plugin.get('state', {})
                    state.pop('control_catalog', None)
                    for target in state.get('parameter_assignments', []):
                        for key in ('identity', 'menu_names', 'menu_labels'):
                            target.pop(key, None)
        return data
    snapshot['checks'] = dict(
        binding_metadata=project_rows(snapshot['catalog']) == project_rows(before['catalog']),
        exact_values=values(snapshot['catalog']) == values(before['catalog']),
        registry_exact=snapshot['registry'] == before['registry'],
        registry_definitions=definitions(snapshot['registry']) == definitions(before['registry']),
        active_context=snapshot['context']['key'] == before['context']['key'],
        embedded_sources=snapshot['sources'] == before['sources'],
        two_subscribers=snapshot['model']['subscribers'] == 2,
        no_subscriber_errors=not snapshot['model']['subscriber_errors'],
        no_operator_errors=not any(snapshot['errors'].values()),
        no_probe=not snapshot['probe_exists'])
    old_values=values(before['catalog'])
    snapshot['value_deltas']={r['id']:r['value']-old_values[r['id']]
        for r in snapshot['catalog'] if r['id'] in old_values and r['value'] != old_values[r['id']]}
artifact.write_text(json.dumps(record, indent=2, default=str) + '\n')
print(json.dumps(dict(phase=phase, pid=snapshot['pid'], project=project.name,
    state=snapshot['state'], catalog_size=len(snapshot['catalog']),
    model=snapshot['model'], views=views, checks=snapshot.get('checks')), default=str))
