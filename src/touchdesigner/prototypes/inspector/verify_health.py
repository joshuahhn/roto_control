"""Milestone 1 native fixtures: health, capabilities and unchanged live session."""
from pathlib import Path
import copy
import json
import time

def verify():
    model=op('/inspector_model');production=model.par.Controller.eval()
    before=production.GetControlCatalog();registry=copy.deepcopy(production.fetch('layout_registry'))
    session=model.ext.InspectorModel.adapter.Session()
    holder=production.parent().create(baseCOMP,'base_inspector_health_verification')
    holder.viewer=True;holder.nodeX=700;holder.nodeY=-500
    page=holder.appendCustomPage('Fixture');page.appendFloat('Amount');holder.par.Amount=.37
    clone=None;view=op('/inspector_below');original_style=view.ext.InspectorView.style
    try:
        clone=holder.copy(production,name='controller');clone.Disconnect();clone.par.Followcomp=False;clone.Applybinding()
        layout=clone.CreateLayout('Inspector health fixture');clone.SelectLayout(layout)
        state=clone.AssignParameter('knob',2,holder.par.Amount);id=state['id']
        ext=clone.ext.RotoPythonExt;host=ext._host;packets=[];host.send=lambda p:packets.append(tuple(p))
        host.connected=host.plugin=True;clone.store('needs_relearn',());host._sync();ext._publish()
        assert ext._process is None
        model.par.Controller=clone;model.Sync();model.Flush();key=model.ActiveContext()
        commands=model.op('base_commands');ui=view.ext.InspectorView;ui.style='below'
        view.Action('slot1');editor=view.op('container_scroll/container_content/editor_below')
        assert commands.Health(key,1)['code']=='pending',dict(commands.Health(key,1))
        assert 'Pending' in editor.op('text_heading').par.text.eval()
        assert not editor.op('ping').par.enable.eval()
        target=host.controls[('knob',2)];target.mapped=True;host._sync();ext._publish();model.Sync();model.Flush()
        assert commands.Health(key,1)['code']=='mapped'
        assert view.op('container_scroll/container_content/slot1/text_slot').par.text.eval()=='K2●'
        token=model.GetToken(key,1);target.touched=True;host._sync();ext._publish();model.Sync();model.Flush()
        assert model.GetToken(key,1)==token
        assert not editor.op('apply').par.enable.eval() and not editor.op('clear').par.enable.eval()
        draft=dict(model.GetCatalog(key)[1]);draft['Value']=.6
        try:commands.Commit(key,1,draft,token)
        except ValueError:pass
        else:raise AssertionError('Touched Value write accepted')
        assert holder.par.Amount.eval()==.37
        target.touched=False;host.connected=False;host._sync();ext._publish();model.Sync();model.Flush()
        assert commands.Health(key,1)['code']=='saved'  # Deliberately stale mapped=True.
        assert 'saved' in view.op('text_status').par.text.eval()
        target.mapped=False;host.connected=True;host._sync();clone.store('needs_relearn',(id,));ext._publish();model.Sync();model.Flush()
        assert commands.Health(key,1)['code']=='relearn',dict(commands.Health(key,1))
        clone.store('needs_relearn',());ext._publish();model.Sync();model.Flush()
        holder.par.Amount.readOnly=True;model.Inspect(key,1);model.Flush()
        assert commands.Health(key,1)['code']=='invalid'
        assert not commands.Capabilities(key,1)['value']['enabled']
        assert commands.Capabilities(key,1)['clear']['enabled']
        holder.par.Amount.readOnly=False;holder.par.Amount.expr='0.37';model.Inspect(key,1);model.Flush()
        assert 'CONSTANT or BIND' in commands.Capabilities(key,1)['value']['reason']
        assert not packets and holder.par.Amount.eval()==.37
        result=dict(native_build=str(app.build),pending_vs_ack=True,mapped_marker=True,
                    touch_capability_ui_refresh=True,touch_keeps_draft_token=True,
                    disconnected_stale_ack_shows_saved=True,relearn_visible=True,
                    readonly_and_expression_targets_blocked=True,invalid_target_clear_allowed=True,
                    promoted_commands=True,fixture_value_preserved=True,no_fixture_midi_packets=True)
        for i in range(6):
            clone.SelectLayout(clone.CreateLayout('Cache fixture '+str(i)))
            model.Sync();model.GetCatalog(model.ActiveContext())
            if i==0:
                assert model.Health(key,1)['code']=='invalid'
                assert not model.Capabilities(key,1)['value']['enabled']
        live=model.ext.InspectorModel
        assert len(live._source)<=4 and len(live._info)<=4 and len(live._revisions)<=4
        assert len(live.adapter._definitions_cache)<=4
        result['six_contexts_bounded_at_four']=True
        result['invalid_inactive_target_browse_survives']=True
    finally:
        view.ext.InspectorView.style=original_style;view.CloseEditor()
        model.par.Controller=production;model.Sync();model.Flush()
        if clone:clone.Disconnect()
        holder.destroy()
    assert production.GetControlCatalog()==before and production.fetch('layout_registry')==registry
    assert model.ext.InspectorModel.adapter.Session()==session
    # Browse an existing inactive Device without pretending its saved mapping is acknowledged.
    manager=production.ext.RotoPythonExt._layout_manager()
    active=tuple(model.ActiveContext());inactive=next(((*active[:2],p['id']) for p in manager.track()['plugins'] if p['id']!=active[2]),None)
    if inactive:
        rows=model.GetCatalog(inactive)
        for slot,row in enumerate(rows):
            if row['Destination']:
                assert model.Health(inactive,slot)['code'] in ('saved','invalid')
                assert not model.Capabilities(inactive,slot)['value']['enabled']
        result['inactive_browse_no_ack']=True
    assert tuple(model.ActiveContext())==active
    snapshots=[op('/inspector_below').Stats()['text_writes'],op('/inspector_popup').Stats()['text_writes']]
    samples=[]
    for i in range(120):
        start=time.perf_counter();model.Sync();model.Flush()
        if i>=20:samples.append((time.perf_counter()-start)*1000)
    assert snapshots==[op('/inspector_below').Stats()['text_writes'],op('/inspector_popup').Stats()['text_writes']]
    for _ in range(1000):model.RequestSync()
    assert model.ext.InspectorModel._sync_run is not None
    model.ext.InspectorModel._sync_run.kill();model.ext.InspectorModel._sync_run=None
    assert model.Stats()['subscribers']==2 and not model.Stats()['subscriber_errors']
    assert not any(c.errors(recurse=True) for c in [model,op('/inspector_below'),op('/inspector_popup')])
    result.update(production_catalog_registry_session_preserved=True,idle_text_write_delta=0,
                  sync_p95_ms=sorted(samples)[94],burst_requests=1000,pending_sync_runs=1,
                  cache_contexts=model.Stats()['cache_contexts'],definition_cache_contexts=len(model.ext.InspectorModel.adapter._definitions_cache),errors='')
    Path(project.folder+'/prototypes/inspector/health_verification.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result))

verify()
