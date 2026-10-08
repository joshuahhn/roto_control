"""Install Reveal sources; TD reloads Inspector extensions, retaining real MIDI.

Reopen the previously selected control after TD's extension reload settles.
"""
from pathlib import Path
directory=Path(project.folder)/'prototypes/inspector'
m=op('/inspector_model')
dat=m.op('live_model');dat.text=(directory/'live_model.py').read_text()
for view in (op('/inspector_below'),op('/inspector_popup')):
    dat=view.op('ui')
    dat.text=(directory/'ui.py').read_text()
print('Reveal sources installed; production controller/MIDI unchanged')
