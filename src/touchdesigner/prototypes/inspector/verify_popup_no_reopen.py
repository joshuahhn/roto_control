"""Staged native section resize: geometry retained, no open/close pulses.

Run phases in separate TD turns with at least two frames between them;
Window COMP size updates are observed after native window processing."""
from pathlib import Path
import json

v=op('/inspector_below');u=v.ext.InspectorView;p=v.op('window_editor')
m=op('/inspector_model');phase=globals().get('phase','start')
if phase=='start':
    assert v.fetch('popup_reopen_fixture',None) is None
    c=m.par.Controller.eval()
    v.CloseEditor();p.par.winclose.pulse()
    v.store('popup_reopen_fixture',dict(style=u.style,controller=c,catalog=c.GetControlCatalog(),
                                      session=m.ext.InspectorModel.adapter.Session(),
                                      opening=(p.par.winw.eval(),p.par.winh.eval())))
    u.style='popup';v.Action('slot0')
    print('Initial Popup opened; staged probe pending')
elif phase=='mapping':
    saved=v.fetch('popup_reopen_fixture');assert saved and p.isOpen
    saved.update(base=(p.contentWidth,p.contentHeight),corner=(p.x,p.y+p.height),main=(v.width,v.height))
    v.store('popup_reopen_pulses',[])
    cb=v.op('probe_section_window') or v.create(parameterexecuteDAT,'probe_section_window')
    cb.viewer=True;cb.par.language='python';cb.nodeX=1660;cb.nodeY=-210
    cb.par.op='window_editor';cb.par.pars='winopen winclose';cb.par.custom=False;cb.par.builtin=True;cb.par.onpulse=True
    cb.text="def onPulse(par):\n    parent.InspectorDemo.fetch('popup_reopen_pulses').append(par.name)\n"
    assert v.Action('mapping_toggle')
elif phase in ('target','back','collapse','finish'):
    saved=v.fetch('popup_reopen_fixture');assert saved
    expected={'target':134,'back':250,'collapse':134,'finish':0}[phase]
    assert p.isOpen and (p.contentWidth,p.contentHeight)==(saved['base'][0],saved['base'][1]+expected)
    assert (p.x,p.y+p.height)==saved['corner']
    assert (v.width,v.height)==saved['main']
    assert not v.fetch('popup_reopen_pulses'),v.fetch('popup_reopen_pulses')
    assert saved['controller'].GetControlCatalog()==saved['catalog']
    assert m.ext.InspectorModel.adapter.Session()==saved['session']
    if phase=='target':assert v.Action('target_picker')
    elif phase=='back':assert v.Action('mapping_toggle')
    elif phase=='collapse':assert v.Action('mapping_toggle')
    else:
        cb=v.op('probe_section_window');cb.destroy()
        v.CloseEditor();p.par.winclose.pulse();u.style=saved['style']
        p.par.winw,p.par.winh=saved['opening']
        v.unstore('popup_reopen_fixture');v.unstore('popup_reopen_pulses')
        result=dict(mapping_target_mapping_collapse_no_open_close_pulses=True,
                    native_height_deltas=[134,250,134,0],width_top_left_main_preserved=True,
                    production_catalog_session_preserved=True,native_visual_flash_verified=False)
        Path(project.folder+'/prototypes/inspector/popup_no_reopen_verification.json').write_text(json.dumps(result,indent=2))
        print(json.dumps(result))
else:raise ValueError('Unknown phase')
print('Popup no-reopen phase:',phase)
