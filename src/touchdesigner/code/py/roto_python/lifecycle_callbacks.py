def onFrameStart(frame):
    parent.RotoPython.Tick()


def onExit():
    parent.RotoPython.Disconnect()


def onProjectPreSave():
    # Save must refresh live handles even when the follower is paused.
    extension = parent.RotoPython.ext.RotoPythonExt
    follower = getattr(extension, '_follow', None)
    if follower is not None:
        follower.refresh_links()
    mix = getattr(extension, '_mix', None)
    if mix is not None:
        mix.refresh_scope()
