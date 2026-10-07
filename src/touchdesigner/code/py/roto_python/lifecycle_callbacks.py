def onFrameStart(frame):
    parent.RotoPython.Tick()


def onExit():
    parent.RotoPython.Disconnect()


def onProjectPreSave():
    # Save must refresh live handles even when the follower is paused.
    follower = getattr(parent.RotoPython.ext.RotoPythonExt, '_follow', None)
    if follower is not None:
        follower.refresh_links()
