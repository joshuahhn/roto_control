"""Observe custom parameter edits only while hardware LEARN is active."""
def onValuesChanged(changes):
    parent.RotoPython.FreeLearnChanges(changes)


def onPulse(par):
    parent.RotoPython.FreeLearnPulse(par)
