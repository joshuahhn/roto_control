"""Live TD checks against actual pixelSortV3 / fractal_pop parameters.

Run begin(controller), wait one frame, software(controller), wait one frame,
hardware(controller), then finish(controller) on the next frame. No MIDI ports
are opened. finish restores values, camera state, callback and saved setup.
"""
from pathlib import Path


def setup(controller):
    namespace={}
    path=Path(project.folder)/'real_component_setup.py'
    exec(compile(path.read_text(),str(path),'exec'),namespace)
    return namespace


def begin(controller):
    ext=controller.ext.RotoPythonExt
    if ext._process is not None or controller.State['Connected']:
        raise ValueError('Disconnect before synthetic verification')
    camera=controller.parent().op('fractal_pop/cameraViewport')
    camera_ext=camera.extensions[0]
    original=camera_ext.Reset
    test=dict(snapshot=[(b.parameter,b.parameter.eval(),b.parameter.bindExpr)
                        for b in ext._collection.bindings.values() if b.parameter.style!='Pulse'],
              camera=camera_ext,transform=camera_ext.CameraTransform.copy(),
              pivot=camera_ext.cameraInst.pivot.copy(),reset=original,resets=[],sent=[])
    def observed_reset():
        test['resets'].append('Reset')
        return original()
    camera_ext.Reset=observed_reset
    controller.store('real_verification',test)
    for id,key in ext._collection.ids.items():
        b=ext._collection.bindings[key]
        if key[0]=='knob':
            controller.SetValue(b.from_normalized(.4),id=id)
        elif ext._collection.modes[key]=='toggle':
            controller.SetValue(1-b.value,id=id)
            controller.SetValue(next(value for p,value,_ in test['snapshot'] if p==b.parameter),id=id)
    return 'software writes staged'


def software(controller):
    ext=controller.ext.RotoPythonExt;test=controller.fetch('real_verification')
    for id,key in ext._collection.ids.items():
        b=ext._collection.bindings[key]
        assert controller.GetValue(id)==b.parameter.eval()
        if key[0]=='knob':b.parameter.val=b.from_normalized(.6)
    tumble=controller.parent().op('fractal_pop').par.Tumblemult
    tumble.bindMaster.val=2.7
    return 'external/master edits staged'


def hardware(controller):
    ext=controller.ext.RotoPythonExt;test=controller.fetch('real_verification');host=ext._host
    for id,key in ext._collection.ids.items():
        if ext._collection.modes[key]!='pulse':
            assert controller.GetValue(id)==ext._collection.bindings[key].parameter.eval()
    assert controller.GetValue('fractal.tumble')==2.7
    host.send=test['sent'].append
    protocol=controller.op('protocol').module
    host.start();host.receive(protocol.sysex(10,12));host.receive(protocol.sysex(11,1,(0,)))
    for key,target in host.controls.items():
        host.receive(protocol.sysex(11,11,(0,target.index,*protocol.digest(target.target_id,6),int(key[0]=='button'),key[1]-1,0)))
    ext._publish()
    assert len([s for s in controller.GetControlStates() if s['mapped']])==13
    for slot in range(1,9):
        host.receive((191,11+slot,64));host.receive((191,43+slot,0))
        b=ext._collection.bindings['knob',slot]
        assert b.parameter.eval()==b.from_normalized(8192/16383)
    for slot in (1,2,3):
        for value in (0,127,0):host.receive((191,19+slot,value))
        assert ext._collection.bindings['button',slot].parameter.eval()==0
    for slot in (4,8):
        host.receive((191,19+slot,127))
        if ext._collection.button_types['button',slot]=='push':host.receive((191,19+slot,0))
    ext._publish()
    data=controller.op('inspector/inspector_data').module;i=controller.op('inspector')
    for name in ('pixelSortV3','fractal_pop'):
        data.select_page(i,controller.parent().op(name).path)
        assert i.op('targets').numRows==17
        assert all(i.op('targets')[r,'COMP'].val in ('',controller.parent().op(name).path) for r in range(1,17))
    data.select_page(i,'All COMPs')
    return '13 mappings/input; two native pulses staged'


def finish(controller):
    ext=controller.ext.RotoPythonExt;test=controller.fetch('real_verification')
    try:
        assert test['resets']==['Reset']
        for slot in (4,8):
            assert ext._collection.bindings['button',slot].pulse_expected==0
        assert 'roto_mapped' in controller.parent().op('pixelSortV3').tags
        assert 'roto_mapped' in controller.parent().op('fractal_pop').tags
        controller.Disconnect()
        assert len(controller.GetControlCatalog())==13
        assert not any(s['mapped'] for s in controller.GetControlCatalog())
        assert controller.op('inspector/targets').numRows==17
        assert 'roto_mapped' not in controller.parent().op('pixelSortV3').tags
        assert 'roto_mapped' not in controller.parent().op('fractal_pop').tags
        controller.RemoveControl('pixelsort.low');controller.Applybinding()
        assert len(controller.GetControlCatalog())==12
        assert controller.op('inspector/targets')[1,'Mapped'].val=='Unassigned'
        controller.RemoveAllControls();controller.Applybinding()
        assert controller.GetControlCatalog()==[] and controller.op('inspector/targets').numRows==17
        assert not controller.errors(recurse=True)
        return dict(targets=13,knobs=8,toggles=3,pulses=2,bound_pulse_reset_calls=1,
                    comp_pages=2,clear_restore=True,clear_all=True,errors=[])
    finally:
        controller.Disconnect()
        test['camera'].Reset=test['reset']
        for parameter,value,expression in test['snapshot']:
            parameter.val=value
            assert parameter.bindExpr==expression
        test['camera'].CameraTransform=test['transform']
        test['camera'].cameraInst.pivot=test['pivot'];test['camera'].updatePivot()
        setup(controller)['install'](controller)
        controller.unstore('real_verification')
