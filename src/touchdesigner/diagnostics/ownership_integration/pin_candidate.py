"""Pin a reviewable combined candidate without staging or touching TD."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[4]
RUN=Path(__file__).resolve().parent/'run_20261008T071408Z'
import sys
VERSION=sys.argv[1] if len(sys.argv)>1 else 'v3'
OUT=RUN/'candidate'/VERSION
tracked=subprocess.check_output(['git','diff','--name-only','HEAD'],cwd=ROOT,text=True).splitlines()
new=subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines()
# Native snapshots/backups/artifacts are evidence, not source patch hunks.
paths=sorted(p for p in set(tracked+new) if p.endswith(('.py','.md')) and '/run_' not in p)
patch=subprocess.check_output(['git','diff','HEAD','--']+[p for p in paths if p in tracked],cwd=ROOT)
for p in paths:
 if p not in tracked:
  result=subprocess.run(['git','diff','--no-index','--','/dev/null',p],cwd=ROOT,stdout=subprocess.PIPE)
  assert result.returncode==1
  patch+=result.stdout
OUT.mkdir(parents=True,exist_ok=False)
manifest=dict(head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),issue9_patch_sha256='277f734d9697292066551278c4805d90e74612059180f002bf10b2837b109a7f',changed_files={},sources={})
for p in paths:
 content=(ROOT/p).read_bytes();manifest['changed_files'][p]=hashlib.sha256(content).hexdigest()
 dest=OUT/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(content)
# Full source mirror supplies fixture source equality against this combined pin.
for p in sorted((ROOT/'src/touchdesigner').rglob('*')):
 if not p.is_file() or p.suffix not in ('.py','.md'):continue
 if any(n in p.parts for n in ('__pycache__','.venv','ownership_integration')):continue
 rel=p.relative_to(ROOT);dest=OUT/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes());manifest['sources'][str(rel)]=hashlib.sha256(p.read_bytes()).hexdigest()
(OUT/'review.patch').write_bytes(patch);manifest['patch_sha256']=hashlib.sha256(patch).hexdigest()
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(dict(path=str(OUT),patch_sha256=manifest['patch_sha256'],changed=len(paths),sources=len(manifest['sources']))))
