"""External bounded RSS sampler; never runs subprocesses in TD's frame loop."""
import argparse,json,subprocess,time
from pathlib import Path
parser=argparse.ArgumentParser();parser.add_argument('--pid',type=int,required=True);parser.add_argument('--directory',type=Path,required=True);parser.add_argument('--seconds',type=float,default=1900);args=parser.parse_args()
started=time.monotonic();path=args.directory/'replacement_rss.jsonl'
with path.open('w') as output:
    while time.monotonic()-started<args.seconds:
        try:progress=json.loads((args.directory/'replacement_progress.json').read_text())
        except (OSError,ValueError):progress={}
        if progress.get('done'):break
        result=subprocess.run(['ps','-o','rss=','-p',str(args.pid)],capture_output=True,text=True,check=True)
        rss=int(result.stdout.strip())
        output.write(json.dumps(dict(elapsed_s=time.monotonic()-started,rss_mib=rss/1024,phase=progress.get('phase'),case=progress.get('case'),soak_elapsed_s=progress.get('soak_elapsed_s')))+'\n');output.flush()
        time.sleep(10)
print('RSS samples',sum(1 for _ in path.open()))
