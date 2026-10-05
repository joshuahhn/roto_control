def onPulse(par):
    controller = parent.ParameterDemo.parent().op('roto_python')
    controller.BindParameter(parent.ParameterDemo.par.Speed, id='demo.parameter.speed',
                             minimum=0, maximum=10, label='Speed')
