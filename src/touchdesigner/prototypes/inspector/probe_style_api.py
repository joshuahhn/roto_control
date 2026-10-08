"""Disposable native API scout; no controller or production parameter edits."""
from pathlib import Path
import json
assert not op('/base_style_api_probe')
holder=root.create(baseCOMP,'base_style_api_probe');holder.viewer=True
holder.nodeX=1085;holder.nodeY=0
result={}
try:
    page=holder.appendCustomPage('Test')
    page.appendToggle('Flag');p=page.appendFloat('Amount',label='Amount A',order=1)[0]
    page.appendFloat('Tail',order=2)
    p.default=1;p.val=3;p.normMin=-10;p.normMax=10;p.min=-20;p.max=20
    p.clampMin=p.clampMax=True;p.startSection=True;p.enableExpr='me.par.Flag'
    names=('name','style','index','label','default','val','order','min','max','normMin','normMax','clampMin','clampMax','startSection','enableExpr','readOnly','expr','bindExpr','hidden','styleCloneImmune','help')
    snap=lambda q:{n:getattr(q,n) for n in names}
    old=snap(p);new=page.appendInt('Amount',label='Amount A',order=1,replace=True)[0]
    result.update(before=old,after=snap(new),old_handle_valid=p.valid,old_handle_style=p.style,
                  same_parameter=p.isSamePar(new),old_handle_value=p.eval(),page_order=[q.name for q in holder.customPars])
    # Path/name expression references must keep reading the newly typed target.
    holder.par.Tail.expr='me.par.Amount * 2';holder.par.Amount=4
    result['expression_after_replace']=holder.par.Tail.eval()
    back=page.appendFloat('Amount',label='Amount A',order=1,replace=True)[0]
    result.update(reverse=snap(back),int_handle_valid=new.valid,int_handle_style=new.style)
finally:holder.destroy()
Path(project.folder+'/prototypes/inspector/style_api_probe.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
