"""Run start/resized/finish in separate TD turns; restore original UI sizes."""
from pathlib import Path
import json
v=op('/inspector_below');main=v.op('window_main');popup=v.op('window_editor');u=v.ext.InspectorView
phase=globals().get('phase','start')
if phase=='start':
    assert v.fetch('window_size_fixture',None) is None
    popup_size=(popup.contentWidth,popup.contentHeight) if popup.isOpen else (popup.par.winw.eval(),popup.par.winh.eval())
    v.store('window_size_fixture',dict(main=(main.contentWidth,main.contentHeight),popup=popup_size,style=u.style,route=op('/inspector_model').ActiveContext()))
    v.CloseEditor();popup.par.winclose.pulse();u.style='popup'
    popup.par.winw=286;popup.par.winh=214;popup.par.winopen.pulse()
    v.Action('slot1')
elif phase=='resized':
    assert (popup.contentWidth,popup.contentHeight)==(286,214)
    v.store('window_size_corner',(popup.x,popup.y+popup.height))
    main.par.winw=360;main.par.winh=430;main.par.winopen.pulse()
    v.Action('slot2');v.Action('mapping_toggle')
elif phase=='finish':
    saved=v.fetch('window_size_fixture')
    try:
        assert (main.contentWidth,main.contentHeight)==(360,430)
        assert (popup.contentWidth,popup.contentHeight)==(286,348)
        assert (popup.x,popup.y+popup.height)==v.fetch('window_size_corner')
        assert (v.op('editor_popup').width,v.op('editor_popup').height)==(286,348)
        assert u._editors[1].height==312
        assert op('/inspector_model').ActiveContext()==saved['route']
        result=dict(native_popup_resize_independent=True,selection_preserves_popup_size=True,
                    mapping_expansion_adds_134_height=True,mapping_expansion_preserves_width_and_top_left=True,viewport_fits_own_window=True)
    finally:
        v.CloseEditor();popup.par.winclose.pulse();u.style=saved['style']
        main.par.winw,main.par.winh=saved['main'];main.par.winopen.pulse()
        popup.par.winw,popup.par.winh=saved['popup'];v.Refresh();v.unstore('window_size_fixture');v.unstore('window_size_corner')
    path=Path(project.folder+'/prototypes/inspector/window_sizes_verification.json')
    evidence=json.loads(path.read_text()) if path.exists() else {}
    evidence.pop('mapping_expansion_preserves_popup_size',None)
    evidence.update(result);path.write_text(json.dumps(evidence,indent=2));print(json.dumps(evidence))
else:raise ValueError('Unknown phase')
print('Window size phase:',phase)
