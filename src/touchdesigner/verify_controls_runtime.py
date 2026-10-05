"""Run disconnected in TD. Synthetic MIDI is explicitly software verification."""
def verify(controller):
    ext = controller.ext.RotoPythonExt
    if ext._process is not None:
        raise ValueError('Disconnect before synthetic verification')
    host = ext._host
    protocol = controller.op('protocol').module
    demo = controller.parent().op('base_controls_demo')
    host.start()
    host.receive(protocol.sysex(10,12))
    host.receive(protocol.sysex(11,1,(0,)))
    for key,target in host.controls.items():
        host.receive(protocol.sysex(11,11,(0,target.index,*protocol.digest(target.target_id,6),int(key[0]=='button'),key[1]-1,0)))
    assert host.mapped
    # Interleave two pairs: neither control may consume the other's half.
    host.receive((191,12,32));host.receive((191,51,10))
    host.receive((191,44,0));host.receive((191,19,96))
    assert abs(demo.par.Knob1.eval()-10*4096/16383)<1e-6
    assert abs(demo.par.Knob8.eval()-10*(96*128+10)/16383)<1e-6
    host.receive((191,20,127))
    assert demo.par.Button1.eval()
    host.receive((191,20,0))
    assert not demo.par.Button1.eval()
    before=int(demo.op('pulse_events')['Button2','count'])
    host.receive((191,21,127));host.receive((191,21,0))
    ext._publish()
    return dict(mapped=sum(t.mapped for t in host.controls.values()),
                pulse_before=before, pulse_expected=before+1,
                channels=[ch.name for ch in controller.op('out_controls').chans()],
                pulse_watch_expected=ext._collection.bindings['button',2].pulse_expected)
