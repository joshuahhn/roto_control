"""Run/remove the mock shared-model benchmark in the matching active TD project."""
import argparse
import json
import time
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=13316)
    args=parser.parse_args()
    def call(name,arguments):
        req=urllib.request.Request(f'http://127.0.0.1:{args.port}/mcp',json.dumps(dict(jsonrpc='2.0',id=1,method='tools/call',params=dict(name=name,arguments=arguments))).encode(),{'Content-Type':'application/json'})
        response=json.load(urllib.request.urlopen(req,timeout=60))
        for item in response.get('result',{}).get('content',[]):
            if item['type']=='text':
                value=json.loads(item['text'])
                if value.get('success') is False:raise RuntimeError(value)
                return value
        raise RuntimeError(response)
    info=call('project_info',{})
    assert Path(info['folder']).resolve()==ROOT,'Active project does not match checkout'
    call('execute_code',{'code':"assert not op('/inspector_shared_stress'), 'Another shared stress test exists'\nassert not getattr(op('/inspector_model').ext.InspectorModel,'IsLive',False), 'Synthetic stress requires the demo model'"})
    setup="""from pathlib import Path
import types
b=op('/').create(baseCOMP,'inspector_shared_stress');b.tags.add('shared_stress_harness');b.nodeX=1000;b.nodeY=-300
p=b.create(performCHOP,'perform_metrics');p.par.cpumemused=True
n=b.create(nullCHOP,'null_performance');n.inputConnectors[0].connect(p)
r=types.ModuleType('shared_stress_runner');r.__dict__.update(op=op,project=project,app=app)
exec(Path(project.folder+'/prototypes/inspector/shared_stress.py').read_text(),r.__dict__)
e=b.create(executeDAT,'execute_frames');e.par.active=False;e.par.framestart=True;e.par.frameend=False
e.text='def onFrameStart(frame):\\n    runner.tick()\\n';e.module.runner=r
r.initialize();e.par.active=True
"""
    try:
        call('execute_code',{'code':setup})
        deadline=time.monotonic()+240
        while time.monotonic()<deadline:
            time.sleep(5)
            state=call('execute_code',{'code':"r=op('/inspector_shared_stress/execute_frames').module.runner\nprint(r.state,r.frame)"})['output'].strip()
            print(state,flush=True)
            if state.startswith('complete'):break
        else:raise TimeoutError('Shared stress timed out')
        result=json.loads((ROOT/'prototypes/inspector/shared_stress_results.json').read_text())
        if result['failures']:raise RuntimeError(result['failures'])
        print('Complete:',ROOT/'prototypes/inspector/shared_stress_results.json')
    finally:
        call('execute_code',{'code':"b=op('/inspector_shared_stress')\nif b and 'shared_stress_harness' in b.tags:\n e=b.op('execute_frames')\n if e:\n  e.par.active=False\n  r=getattr(e.module,'runner',None)\n  if r and not r.done:r.finish()\n b.destroy()"})

if __name__=='__main__':main()
