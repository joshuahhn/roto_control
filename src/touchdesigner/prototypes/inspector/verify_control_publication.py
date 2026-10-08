"""Native isolated API/output checks for the synchronous publication change."""
from pathlib import Path
import copy,json

production=op('/roto_control_python/roto_python')
before=production.GetControlCatalog();registry=copy.deepcopy(production.fetch('layout_registry'))
holder=production.parent().create(baseCOMP,'base_control_publication_verification')
holder.viewer=True;holder.nodeX=700;holder.nodeY=-650
clone=None
try:
    page=holder.appendCustomPage('Fixture')
    page.appendFloat('Amount');page.appendInt('Count');page.appendToggle('Enabled');page.appendPulse('Trigger')
    holder.par.Count.normMax=7
    clone=holder.copy(production,name='controller');clone.Disconnect();clone.par.Followcomp=False;clone.Applybinding()
    clone.ext.RotoPythonExt._layouts.capture(force=True)
    clone.op('RotoPythonExt').text=Path(project.folder+'/code/py/roto_python/RotoPythonExt.py').read_text()
    clone.initializeExtensions(0);clone.Applybinding()
    clone.SelectLayout(clone.CreateLayout('Publication fixture'))
    ids={}
    for kind,slot,name in [('knob',1,'Amount'),('knob',2,'Count'),('button',1,'Enabled'),('button',2,'Trigger')]:
        ids[name]=clone.AssignParameter(kind,slot,holder.par[name])['id']
    ext=clone.ext.RotoPythonExt;output=clone.op('base_targets/controls_values')
    original=ext.GetControlStates;calls=[]
    def counted():
        snapshot=original();calls.append(snapshot);return snapshot
    ext.GetControlStates=counted
    names=[c.name for c in output.chans()]
    assert names==['knob1','knob2','button1','button2']
    for n in range(1,7):
        for name,value in [('Amount',n/8),('Count',n),('Enabled',n%2)]:
            previous=len(calls)
            clone.SetValue(value,id=ids[name])
            assert len(calls)==previous+1,'More than one detached state scan per publication'
            assert clone.GetControlState(ids[name])['value']==value,(name,value,clone.GetControlState(ids[name]))
            assert output.numSamples==1 and [c.name for c in output.chans()]==names
            assert [c[0] for c in output.chans()]==[holder.par.Amount.eval(),holder.par.Count.eval(),holder.par.Enabled.eval(),0]
            assert clone.GetControlCatalog()==[dict(s,last_mapped=False) for s in original()]
    assert ext._process is None and not ext._pending
    assert holder.par.Trigger.eval()==0 and getattr(ext._collection.bindings['button',2],'pulse_expected',0)==0
    assert not clone.errors(recurse=True)
    result=dict(native_api_writes=18,synchronous_values_and_channel_shape=True,
        one_state_scan_per_publication=True,no_pulse_dispatch=True,no_midi_process_or_queue=True,errors=[])
finally:
    if clone:clone.Disconnect()
    holder.destroy()
assert production.GetControlCatalog()==before and production.fetch('layout_registry')==registry
result['production_preserved']=True
Path(project.folder+'/prototypes/inspector/control_publication_verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
