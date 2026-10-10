"""Reproduce the native-TD inspector stress test through existing local TDMCP.

python3 prototypes/inspector/run_stress.py --port 13316
Both demo COMPs must already exist. Creates and removes /inspector_stress only.
"""
import argparse
import json
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=13316)
    parser.add_argument('--suite',choices=['main','lifecycle','cooldown','smoke'],default='main')
    parser.add_argument('--output',default='stress_retest.json')
    args=parser.parse_args()
    if Path(args.output).name!=args.output or not args.output.endswith('.json'):
        parser.error('--output must be a JSON basename')
    url=f'http://127.0.0.1:{args.port}/mcp'
    def call(name,arguments):
        body=json.dumps(dict(jsonrpc='2.0',id=1,method='tools/call',params=dict(name=name,arguments=arguments))).encode()
        request=urllib.request.Request(url,body,{'Content-Type':'application/json'})
        data=json.load(urllib.request.urlopen(request,timeout=60))
        for item in data.get('result',{}).get('content',[]):
            if item['type']=='text':
                try:value=json.loads(item['text'])
                except ValueError:value={'text':item['text']}
                if value.get('success') is False:raise RuntimeError(value)
                return value
        raise RuntimeError(data)
    info=call('project_info',{})
    if Path(info['folder']).resolve()!=ROOT:
        raise RuntimeError('Active TD project folder does not match this source checkout')
    setup="""from pathlib import Path
import types
assert not op('/inspector_stress'), 'Another stress test already exists'
assert op('/inspector_below') and op('/inspector_popup')
assert not op('/inspector_model'), 'Legacy benchmark: use run_shared_stress.py for shared-model views'
b=op('/').create(baseCOMP,'inspector_stress');b.tags.add('inspector_stress_harness');b.viewer=True;b.nodeX=1000;b.nodeY=-300
p=b.create(performCHOP,'perform_metrics');p.viewer=True
for name in ['fps','cook','msec','cpumemused','droppedframes']:p.par[name]=True
n=b.create(nullCHOP,'null_performance');n.viewer=True;n.inputConnectors[0].connect(p);n.nodeX=175
r=types.ModuleType('inspector_stress_runner');r.__dict__.update(op=op,project=project,app=app)
exec(Path(project.folder+'/prototypes/inspector/stress.py').read_text(),r.__dict__)
"""
    setup+=f'r.output_name={args.output!r}\n'
    if args.suite=='lifecycle':
        setup+="r.phases=[('below_interactions',[0],'stress',180),('popup_interactions',[1],'stress',180),('popup_row_switch',[1],'rowswitch',240),('popup_interactions_10hz',[1],'stress_10hz',360)]\n"
    elif args.suite=='cooldown':
        setup+="r.phases=[('both_full_60hz_after',[0,1],'full',300),('both_cached_60hz_after',[0,1],'cached',300),('both_idle_30s_cooldown',[0,1],'idle',1800)]\n"
    elif args.suite=='smoke':
        setup+="r.phases=[('both_cached_smoke',[0,1],'cached',180),('idle_smoke',[0,1],'idle',120)]\n"
    setup+="r.initialize()\n"
    setup+="""e=b.create(executeDAT,'execute_frames');e.viewer=True;e.par.active=False;e.par.framestart=True;e.par.frameend=False
e.text="def onFrameStart(frame):\\n    runner.tick()\\n"
e.module.runner=r
"""
    if args.suite=='main':setup+="r.correctness();r.write_result()\n"
    setup+="e.par.active=True\n"
    created=False
    try:
        call('execute_code',{'code':"assert not op('/inspector_stress'), 'Another stress test already exists'"})
        created=True
        call('execute_code',{'code':setup})
        deadline=time.monotonic()+360
        while time.monotonic()<deadline:
            time.sleep(5)
            state=call('execute_code',{'code':"r=op('/inspector_stress/execute_frames').module.runner\nprint(r.state,r.frame)"})['output'].strip()
            print(state,flush=True)
            if state.startswith('complete'):break
        else:raise TimeoutError('Stress test exceeded six minutes')
        result=json.loads((ROOT/'prototypes/inspector'/args.output).read_text())
        if result['failures']:raise RuntimeError(result['failures'])
        print(ROOT/'prototypes/inspector'/args.output)
    finally:
        if created:
            call('execute_code',{'code':"b=op('/inspector_stress')\nif b and 'inspector_stress_harness' in b.tags:\n e=b.op('execute_frames')\n if e:\n  e.par.active=False\n  r=getattr(e.module,'runner',None)\n  if r and not r.done:r.finish()\n b.destroy()"})

if __name__=='__main__':main()
