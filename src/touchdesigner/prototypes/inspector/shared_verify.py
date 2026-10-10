"""Live-TD correctness probes; only mock inspector data is changed/restored."""
import json
from pathlib import Path

def verify():
    model=op('/inspector_model').ext.InspectorModel
    assert not getattr(model,'IsLive',False),'Synthetic verification requires the demo model'
    views=[op('/inspector_below').ext.InspectorView,op('/inspector_popup').ext.InspectorView]
    snapshot=model.Snapshot()
    saved=[dict(context=v.Key(),selected=v.selected,draft={n:v._draft.par[n].eval() for n in ('Label','Destination','Minimum','Maximum','Value')},scroll=v._viewport.panel.scrollv.val) for v in views]
    checks=[]
    def check(name,condition):
        assert condition,name
        checks.append(name)
    def context(view,key):
        for n,x in zip(('Layout','Track','Device'),key):view.ownerComp.par[n]=x
        view.OnContext()
    try:
        a,b=views;key=('main','track1','pixelsort')
        for v in views:
            context(v,key);v.CloseEditor()
            if not v._main.isOpen:v._main.par.winopen.pulse()
        check('single model / shared read-only catalog',a._model is b._model and a._model.GetCatalog(key) is b._model.GetCatalog(key))
        a.Action('slot1');b.Action('slot1');opens=b.Stats()['window_opens']
        a._draft.par.Label='committed in Below';b._draft.par.Label='unfinished in Popup'
        model.UpdateValues(key,{1:.612});model.Flush()
        check('live rows update without clobbering either draft',all(v._row_refs[1]['value'].par.text.eval()=='0.612' for v in views) and b._draft.par.Label.eval()=='unfinished in Popup' and b._draft.par.Value.eval()==snapshot['rows'][key][1]['Value'])
        check('Apply accepted',a.Action('apply'))
        model.Flush()
        check('Apply keeps newer live value',model.GetCatalog(key)[1]['Value']==.612)
        check('Apply propagates across views',b._row_refs[1]['name'].par.text.eval()=='committed in Below')
        check('stale mapping draft rejected without overwrite',not b.Action('apply') and b.selected==1 and model.GetCatalog(key)[1]['Label']=='committed in Below')
        b.Action('cancel');check('Cancel retains Popup native window',b._popup.isOpen)
        for i in range(96):
            b.Action('slot'+str(i%16));b.Action('apply' if i%2 else 'cancel')
        check('96 Apply/Cancel sessions reuse one popup',b._popup.isOpen and b.Stats()['window_opens']==opens)
        a.Action('learn');model.Flush()
        check('shared Learn alert on both surfaces',all(v.ownerComp.op('text_status').par.text.eval()=='●  LEARN MODE ON' for v in views))
        a.Action('learn');model.Flush()
        # Reject a whole malformed batch, including its otherwise-valid first item.
        old=model.GetCatalog(key)[1]['Value']
        try:model.UpdateValues(key,{1:.2,16:.3})
        except ValueError:pass
        else:raise AssertionError('invalid batch accepted')
        check('invalid batch is atomic',model.GetCatalog(key)[1]['Value']==old)
        a.Action('slot1');a._draft.par.Minimum=1;a._draft.par.Maximum=0
        check('invalid range preserves draft and model',not a.Action('apply') and a.selected==1 and model.GetCatalog(key)[1]['Minimum']==0)
        a.Action('cancel')
        a._viewport.panel.wheel=0;a._viewport.panel.scrollv=.5;a._viewport.panel.wheel=-1
        check('native wheel callback scrolls Below',a._viewport.panel.scrollv.val>.5)
        # All 8 contexts / 16 controls: writes belong only to their selected key.
        cases=0
        for key in model._source:
            for v in views:context(v,key)
            for slot in range(16):
                a.Action('slot'+str(slot));a._draft.par.Label='check-'+str(cases)
                check_name=a._draft.par.Label.eval()
                assert a.Action('apply');model.Flush()
                assert b._row_refs[slot]['name'].par.text.eval()==check_name
                b.Action('slot'+str(slot));b._draft.par.Label='discard';b.Action('cancel')
                assert model.GetCatalog(key)[slot]['Label']==check_name
                cases+=1
        check('128 cross-view commits and 128 cancels / isolated contexts',cases==128)
        check('LRU cache bounded at four contexts',model.Stats()['cache_contexts']<=4)
        for v in views:
            for _ in range(10):v.Connect()
        check('reconnect has exactly two subscribers',model.Stats()['subscribers']==2)
        context(a,('main','track1','pixelsort'));context(b,('main','track1','pixelsort'))
        generation=model.Generation;model.Invalidate()
        try:model.UpdateValues(a.Key(),{1:.5},generation=generation)
        except ValueError:pass
        else:raise AssertionError('stale generation accepted')
        model.Flush();check('stale producer generation rejected',model.GetCatalog(a.Key())[1]['Value']==old)
        check('invalid slot rejected',not a.Action('slot16') and not a.Action('slot-1'))
        check('no subscriber errors',not model.Stats()['subscriber_errors'])
        return dict(checks=checks,passed=len(checks),cross_view_commits=cases,cancels=cases)
    finally:
        model.Restore(snapshot);model.Flush()
        for v,s in zip(views,saved):
            v.CloseEditor();context(v,s['context']);v.Refresh()
            if s['selected'] is not None:
                v.Action('slot'+str(s['selected']))
                for n,x in s['draft'].items():v._draft.par[n]=x
            v._viewport.panel.scrollv=s['scroll']

result=verify()
Path(project.folder+'/prototypes/inspector/shared_correctness.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result))
