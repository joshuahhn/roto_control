def on_change(event):
    demo = parent.CallbackDemo
    demo.par.Received = event['value']
    demo.par.Events = demo.par.Events.eval() + 1
    demo.par.Origin = event['origin']


def onPulse(par):
    demo = parent.CallbackDemo
    controller = demo.parent().op('roto_python')
    if par.name == 'Usebinding':
        controller.BindCallback(id='demo.callback.speed', label='Callback', minimum=0,
                                maximum=10, value=demo.par.Speed.eval(), on_change=on_change)
    elif par.name == 'Setvalue':
        if controller.State['Targetid'] != 'demo.callback.speed':
            raise ValueError('Select this callback binding first')
        controller.SetValue(demo.par.Speed.eval())
