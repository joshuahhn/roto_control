"""Disk-only candidate pin; no TD or MIDI interaction."""
from pathlib import Path
import datetime,hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[4]
RUN=Path(__file__).resolve().parent/('run_'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
RUN.mkdir()
patch=Path('/var/folders/5q/krg7wb4d4lsgpmlmgqvywj_w0000gn/T/roto-issue9-reviewed-emhbnibb/review.patch')
assert hashlib.sha256(patch.read_bytes()).hexdigest()=='277f734d9697292066551278c4805d90e74612059180f002bf10b2837b109a7f'
record=dict(head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip(),dirty=subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True),issue9_patch=str(patch),issue9_sha256=hashlib.sha256(patch.read_bytes()).hexdigest(),files={})
for f in sorted((ROOT/'src/touchdesigner').rglob('*')):
    if not f.is_file() or any(x in f.parts for x in ('.venv','__pycache__')):continue
    if f.suffix not in ('.py','.md','.toe','.tox'):continue
    rel=str(f.relative_to(ROOT));record['files'][rel]=hashlib.sha256(f.read_bytes()).hexdigest()
    if f.suffix in ('.py','.md'):
        dest=RUN/'source_baseline'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(f.read_bytes())
(RUN/'source_pin.json').write_text(json.dumps(record,indent=2)+'\n')
print(RUN)
