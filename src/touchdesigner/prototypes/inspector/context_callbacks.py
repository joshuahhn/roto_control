"""Header callback source: open the in-window dropdown on release inside."""

def header_callback_source(name):
    if name not in ('Device','Layout','Track'):raise ValueError('Unknown context selector')
    return '''def onOnToOff(panelValue):
    owner=parent.InspectorDemo
    if not owner.op(%r).panel.inside:
        return
    if owner.ext.InspectorView._main.isOpen:
        owner.OpenContextMenu(%r)
''' % ('context_'+name,name)
