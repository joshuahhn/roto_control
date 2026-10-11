"""Count source-level command scans against a pinned baseline; no TD/MIDI I/O.

Run from any directory with Python 3. Repository history is needed for baseline.
These fake-adapter counts do not measure native frame cost or hardware latency.
"""
import json
from pathlib import Path
import subprocess
import sys
import types

TD = Path(__file__).resolve().parents[2]
REPO = TD.parents[1]
INSPECTOR = TD / 'prototypes/inspector'
BASELINE = 'a035d7386813b3a94bd26f57ab3514c780c6de87'
sys.path.insert(0, str(INSPECTOR))
from live_model import ControllerCatalog
from test_snapshot_commands import SnapshotController
from test_live_model import Adapter, KEY, state
import commands
import ui


def old_module(name, filename):
    source = subprocess.run(['git', 'show', BASELINE + ':src/touchdesigner/prototypes/inspector/' + filename],
                            cwd=REPO, check=True, capture_output=True, text=True).stdout
    module = types.ModuleType(name)
    exec(compile(source, filename, 'exec'), module.__dict__)
    return module


def fixture(service):
    adapter = Adapter()
    adapter.controller = SnapshotController()
    adapter.records[KEY] = [dict(state(), id='knob'+str(i), slot=i+1, binding_type='parameter') for i in range(8)]
    reads = []
    original = adapter.Read
    def read(key):
        reads.append(key)
        return original(key)
    adapter.Read = read
    model = ControllerCatalog(adapter, commands_factory=service)
    model.GetCatalog(KEY)
    for i in range(3):
        key = ('layout', 'track', 'other'+str(i))
        adapter.records[key] = [dict(state(), id='other'+str(i))]
        model.GetCatalog(key)
    reads.clear()
    return adapter, model, reads


def measure(service, view_class):
    result = {}
    for explicit in (False, True):
        adapter, model, reads = fixture(service)
        selections = [(KEY,i,model.GetToken(KEY,i)) for i in range(8)] if explicit else []
        reads.clear();before = model.Stats()['sync_calls']
        intent = model.SnapshotIntent(KEY,selections)
        result['snapshot_'+('explicit' if explicit else 'default')] = dict(
            syncs=model.Stats()['sync_calls']-before, context_reads=len(reads), capture_slots=len(intent['capture_tokens']))
        reads.clear();before = model.Stats()['sync_calls']
        model.SnapshotCommand('save',intent,'Measured')
        result['save_'+('explicit' if explicit else 'default')] = dict(
            syncs=model.Stats()['sync_calls']-before, context_reads=len(reads), dispatches=len(adapter.controller.calls))
    adapter, model, reads = fixture(service)
    view = object.__new__(view_class)
    view._model=model;view._context=KEY;view.selected=1;view._token=model.GetToken(KEY,1)
    view._clear_pending=None;view._editors=[];view.CloseContextMenu=lambda:None
    view.Key=lambda:KEY;view.IsLive=lambda:True;view.CloseEditor=lambda:None
    view._set_error=lambda text:None;view._disarm_clear=lambda:setattr(view,'_clear_pending',None)
    view.ownerComp=types.SimpleNamespace(op=lambda name:types.SimpleNamespace(par=types.SimpleNamespace(text='')))
    view.Action('clear');reads.clear();before=model.Stats()['sync_calls']
    view.Action('clear')
    result['clear_confirm'] = dict(syncs=model.Stats()['sync_calls']-before, context_reads=len(reads), dispatches=len(adapter.clears))
    return result


if __name__ == '__main__':
    baseline_commands = old_module('baseline_commands', 'commands.py')
    baseline_ui = old_module('baseline_ui', 'ui.py')
    print(json.dumps(dict(baseline=BASELINE, scope='synthetic source counts; four cached contexts; eight Knobs',
                         before=measure(baseline_commands.CommandService,baseline_ui.InspectorView),
                         after=measure(commands.CommandService,ui.InspectorView)), indent=2))
