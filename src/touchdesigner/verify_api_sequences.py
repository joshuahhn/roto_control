"""TD integration fixture for the public API. Synthetic MIDI; never opens ports.

Run build_fixture(root, project.folder), wait one TD frame, then exercise(controller).
The fixture's saved Registration hook supports tox reload/reinit checks.
"""
from pathlib import Path
import time


def build_fixture(parent_comp, source_dir):
    if parent_comp.op('base_api_sequence') is not None:
        raise FileExistsError('base_api_sequence already exists')
    source = Path(source_dir)
    fixture = parent_comp.create(baseCOMP, 'base_api_sequence')
    fixture.par.parentshortcut = 'ApiSequence'
    fixture.display = fixture.viewer = True
    controller = fixture.loadTox(str(source/'exports/roto_python.tox'))
    controller.nodeX = 0
    target = fixture.create(baseCOMP, 'base_values')
    target.display = target.viewer = True
    target.nodeX = 350
    page = target.appendCustomPage('Targets')
    speed = page.appendFloat('Speed')[0]
    speed.normMin, speed.normMax, speed.val = 0, 10, 4
    page.appendToggle('Enabled')
    page.appendPulse('Reset')
    watcher = target.create(parameterexecuteDAT, 'pulse_callbacks')
    watcher.viewer = True
    watcher.par.language = 'python'
    watcher.par.op.expr = 'str(parent.ApiSequence.op("base_values"))'
    watcher.par.pars = 'Reset'
    watcher.par.custom, watcher.par.builtin, watcher.par.valuechange, watcher.par.onpulse = True, False, False, True
    watcher.text = 'def onPulse(par):\n    par.owner.store("pulses",par.owner.fetch("pulses",0)+1)\n'
    for name in ('protocol','binding','controls','collection_protocol','setup','RotoPythonExt'):
        controller.op(name).text = (source/'code/py/roto_python'/f'{name}.py').read_text()
    controller.op('registration').text = '''def onRegister(controller):
    target=parent.ApiSequence.op('base_values')
    def changed(event):
        controller.store('api_events',controller.fetch('api_events',[])+[dict(event)])
    controller.BindControls([
        dict(kind='knob',slot=1,id='api.speed',parameter=target.par.Speed),
        dict(kind='knob',slot=2,id='api.callback.speed',label='Callback Speed',minimum=0,maximum=10,value=5,on_change=changed),
        dict(kind='button',slot=1,id='api.enabled',mode='toggle',parameter=target.par.Enabled),
        dict(kind='button',slot=3,id='api.callback.enabled',label='Callback Enabled',mode='toggle',on_change=changed),
        dict(kind='button',slot=2,id='api.reset',mode='pulse',button_type='push',parameter=target.par.Reset),
        dict(kind='button',slot=8,id='api.callback.reset',label='Callback Reset',mode='pulse',button_type='push',on_change=changed)
    ],group_id='api.sequence.v1')
'''
    controller.par.Setupmode = 'callback'
    controller.par.reinitextensions.pulse()
    return controller


def exercise(controller):
    ext = controller.ext.RotoPythonExt
    if ext._process is not None:
        raise ValueError('Synthetic verification must be disconnected')
    assert len(controller.Applybinding()) == 6
    for key, binding in ext._collection.bindings.items():
        if binding.parameter is not None:
            watcher = controller.op('base_targets/watch_'+key[0]+str(key[1]))
            assert watcher.par.op.eval() == binding.parameter.owner
    controller.store('api_events', [])
    target_comp = controller.parent().op('base_values')
    pulse_before = target_comp.fetch('pulses', 0)
    host = ext._host
    protocol = controller.op('protocol').module
    sent = []
    real_send = host.send
    def capture(message):
        sent.append(tuple(message))
        real_send(message)
    host.send = capture
    host.start()
    host.receive(protocol.sysex(10,12)); host.receive(protocol.sysex(11,1,(0,)))
    assert not controller.Offerparameter('api.reset')
    host.receive(protocol.sysex(11,9,(1,)))
    assert controller.Offerparameter('api.reset')
    assert target_comp.fetch('pulses',0) == pulse_before
    host.receive(protocol.sysex(11,9,(0,)))
    for key,target in host.controls.items():
        host.receive(protocol.sysex(11,11,(0,target.index,*protocol.digest(target.target_id,6),
                                         int(key[0]=='button'),key[1]-1,0)))
    assert host.mapped
    controller.SetValue(6.123456789,id='api.speed')
    controller.SetValue(7,id='api.callback.speed')
    controller.SetValue(1,id='api.enabled')
    controller.SetValue(1,id='api.callback.enabled')
    assert controller.GetValue('api.speed') == target_comp.par.Speed.eval()
    assert abs(controller.GetValue('api.speed')-6.123456789)<1e-12
    assert controller.fetch('api_events') == []
    for id in ('api.enabled','api.callback.enabled'):
        slot=controller.GetControlState(id)['slot']
        sent.clear()
        host.receive((191,19+slot,0))
        assert controller.GetValue(id)==0
        assert sent==[(191,19+slot,0),protocol.sysex(10,24,(1,slot-1,*protocol.text13('Off')))]
    sent.clear()
    host.receive((191,12,32)); host.receive((191,44,0))
    host.receive((191,13,64)); host.receive((191,45,0))
    assert not any(message[0]==191 for message in sent)
    host.flush_display(time.monotonic())
    assert abs(controller.GetValue('api.speed')-10*4096/16383)<1e-12
    for slot,id in ((2,'api.reset'),(8,'api.callback.reset')):
        sent.clear()
        for value in (127,127,0,0): host.receive((191,19+slot,value))
        assert [message for message in sent if message[0]==191]==[(191,19+slot,127),(191,19+slot,0)]
        assert controller.GetValue(id)==0
        assert controller.GetControlState(id)['button_type']=='push'
    assert [event['id'] for event in controller.fetch('api_events')]==[
        'api.callback.enabled','api.callback.speed','api.callback.reset']
    try: controller.SetValue(float('nan'),id='api.callback.speed')
    except ValueError: pass
    else: raise AssertionError('Invalid write was accepted')
    assert not controller.GetControlState('api.callback.speed')['valid']
    assert controller.GetControlState('api.enabled')['valid']
    controller.Disconnect()
    assert len(controller.Applybinding())==6
    assert all(controller.GetControlState(id)['valid'] for id in ext._collection.ids)
    assert controller.State['Connected'] is False
    return dict(targets=6,callbacks=3,pulse_before=pulse_before,pulse_expected=pulse_before+1,
                output_channels=controller.op('out_controls').numChans)
