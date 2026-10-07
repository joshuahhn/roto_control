"""Only user text edits dispatch Value; model-driven text changes never do."""
def onFocus(comp):parent.InspectorDemo.BeginValueEdit()
def onTextEdit(comp):parent.InspectorDemo.LiveValue(comp.editText)
def onFocusEnd(comp,info):parent.InspectorDemo.EndValueEdit()
def onValueChange(comp,value,prevValue):pass
def onTextEditEnd(comp,value,prevValue):parent.InspectorDemo.LiveValue(value)
