"""Read-only snapshot before integration; no configuration or target setters."""
from pathlib import Path
import copy,hashlib,json
folder=Path(RUN_PATH);c=op('/roto_control_python/roto_python');m=op('/inspector_model');e=c.ext.RotoPythonExt
assert project.name=='inspector_editor_actions.45.toe' and m.par.Controller.eval()==c
fields=('parameter_assignments','assignment_device_id','control_overrides','removed_controls','pending_unmaps','needs_relearn','control_catalog','pending_unmap_identities','page_targets')
record=dict(project=project.name,project_folder=project.folder,controller=c.path,process_pid=getattr(e._process,'pid',None),state=dict(c.State),routing=c.GetLayoutContext(),follow=c.GetCompContext(),catalog=c.GetControlCatalog(),registry=copy.deepcopy(c.fetch('layout_registry')),manager_data=copy.deepcopy(e._layout_manager().data),materialized={k:copy.deepcopy(c.fetch(k,None)) for k in fields},controller_pars={p.name:(p.eval().path if getattr(p.eval(),'isOP',False) else p.eval()) for p in c.customPars},panes=[dict(type=p.type.name,owner=p.owner.path,x=p.x,y=p.y,zoom=p.zoom,selected=[x.path for x in p.owner.selectedChildren]) for p in ui.panes if hasattr(p,'owner') and p.owner],sources=[],views=[],native_targets={})
for x in (c,m,op('/inspector_below'),op('/inspector_popup')):
    for d in x.findChildren(type=DAT):
        if not hasattr(d,'text'):continue
        text=d.text;path=d.path.lstrip('/');dest=folder/'live_sources'/(path+'.txt');dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(text)
        record['sources'].append(dict(path=d.path,sha256=hashlib.sha256(text.encode()).hexdigest(),file=d.par.file.eval() if hasattr(d.par,'file') else None,sync=d.par.syncfile.eval() if hasattr(d.par,'syncfile') else False))
for v in (op('/inspector_below'),op('/inspector_popup')):
    u=v.ext.InspectorView
    record['views'].append(dict(path=v.path,context=u.Key(),follow=u._follow_routing,style=u.style,selected=u.selected,filter=u._filter,details_open=u._details_open,mapping_open=u._mapping.open,main_open=u._main.isOpen,popup_open=u._popup.isOpen,main=dict(x=u._main.x,y=u._main.y,w=u._main.contentWidth,h=u._main.contentHeight),popup=dict(x=u._popup.x,y=u._popup.y,w=u._popup.contentWidth,h=u._popup.contentHeight)))
for layout in record['manager_data']['records']:
    for track in layout['tracks']:
        for plugin in track['plugins']:
            for r in list(plugin['targets'])+list(plugin['state'].get('page_targets',[])):
                owner=c.op(r.get('comp',''));par=getattr(owner.par,r.get('parameter',''),None) if owner else None
                if par is None:continue
                key=owner.path+'.'+par.name
                record['native_targets'][key]=dict(owner=owner.path,name=par.name,style=par.style,value=None if par.style=='Pulse' else par.eval(),mode=str(par.mode),label=par.label,default=par.default,normMin=par.normMin,normMax=par.normMax,min=par.min,max=par.max,clampMin=par.clampMin,clampMax=par.clampMax,menuNames=list(par.menuNames or ()),menuLabels=list(par.menuLabels or ()))
(folder/'live_baseline.json').write_text(json.dumps(record,indent=2,default=str)+'\n')
assert not any(s['sync'] for s in record['sources'] if s['path'].endswith(('/RotoPythonExt','/layouts','/text_comp_follow','/free_learn','/live_model','/ui','/InspectorCommands')))
print(json.dumps(dict(project=record['project'],pid=record['process_pid'],routing=record['routing'],catalog=len(record['catalog']),layouts=[dict(name=l['name'],tracks=[dict(name=t['name'],devices=[dict(name=p['plugin_name'],targets=len(p['targets']),library=len(p['state'].get('page_targets',[]))) for p in t['plugins']]) for t in l['tracks']]) for l in record['manager_data']['records']],native_targets=len(record['native_targets']),sources=len(record['sources'])),default=str))
