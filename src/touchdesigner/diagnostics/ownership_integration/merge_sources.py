"""Apply exact reviewed hunks, reconcile only RotoPythonExt methods against base."""
from pathlib import Path
import ast,hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[4]
ISSUE=Path('/Users/huihongnin/.t3/worktrees/roto_control/t3-issue-9-comp-custom-layouts')
RUN=Path(RUN_PATH)
patch=Path('/var/folders/5q/krg7wb4d4lsgpmlmgqvywj_w0000gn/T/roto-issue9-reviewed-emhbnibb/review.patch')
assert hashlib.sha256(patch.read_bytes()).hexdigest()=='277f734d9697292066551278c4805d90e74612059180f002bf10b2837b109a7f'
include=['src/touchdesigner/'+x for x in ('code/py/roto_python/free_learn.py','code/py/roto_python/layouts.py','code/py/roto_python/text_comp_follow.py','export_component.py','test_tag_devices.py','test_layout_owners.py','diagnostics/issue_9/*','docs/plans/issue-9-owner-layouts.md')]
args=['git','apply']+['--include='+x for x in include]+[str(patch)]
subprocess.run(args[:2]+['--check']+args[2:],cwd=ROOT,check=True)
subprocess.run(args,cwd=ROOT,check=True)
rel='src/touchdesigner/code/py/roto_python/RotoPythonExt.py';f=ROOT/rel
base=subprocess.check_output(['git','show','1cb09d9:'+rel],cwd=ROOT,text=True)
ours=f.read_text();theirs=(ISSUE/rel).read_text()
def methods(source):
    lines=source.splitlines(keepends=True);cls=next(n for n in ast.parse(source).body if isinstance(n,ast.ClassDef) and n.name=='RotoPythonExt')
    return lines,{n.name:(min([n.lineno]+[d.lineno for d in n.decorator_list])-1,n.end_lineno) for n in cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
bline,b=methods(base);oline,o=methods(ours);tline,t=methods(theirs)
body=lambda lines,r:''.join(lines[r[0]:r[1]])
changed=[name for name in t if name not in b or body(tline,t[name])!=body(bline,b[name])]
changes=[];insertions=[];log=[]
for name in changed:
    replacement=body(tline,t[name])
    if name=='_publish_state':
        replacement=body(oline,o['_publish']).replace('def _publish(self):','def _publish_state(self):',1)
        log.append(dict(method=name,merge='reviewed owner_observation wrapper + HEAD publication/state reuse implementation'))
    elif name=='GetControlCatalog':log.append(dict(method=name,merge='reviewed live/availability semantics supersede old cached getter; deferred UI/output mechanisms retained'))
    else:log.append(dict(method=name,merge='reviewed source function'))
    if name in o:changes.append((*o[name],replacement))
    else:insertions.append(replacement)
for start,end,replacement in sorted(changes,reverse=True):oline[start:end]=[replacement+'\n']
source=''.join(oline)
# New methods remain inside the same extension class; order does not own behavior.
source+='\n'+''.join('\n'+x+'\n' for x in insertions)
source=source.replace('import copy\n','import copy\nfrom contextlib import nullcontext\n',1)
ast.parse(source);f.write_text(source)
(RUN/'merge_methods.json').write_text(json.dumps(dict(base='1cb09d9',head='55fa9b377a9d326c3786b535678400e877d20671',exact_hunk_includes=include,roto_methods=log,preserved_head_methods=[name for name in o if name in b and body(oline, o[name])!=body(bline,b[name])]),indent=2)+'\n')
print('Reviewed ownership hunks applied; RotoPythonExt function-scoped reconciliation:',len(changed),'methods')
