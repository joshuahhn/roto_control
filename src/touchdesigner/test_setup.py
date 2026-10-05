"""Saved setup routes through the binding interface without MIDI/TD."""
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest

sys.path.insert(0,str(Path(__file__).parent/'code/py/roto_python'))
from setup import restore


class Par:
    def __init__(self,value):
        self.value=value
    def eval(self):
        return self.value


class Controller:
    def __init__(self,mode='parameter'):
        self.parameter=object()
        self.target=SimpleNamespace(valid=True,isCOMP=True,par=SimpleNamespace(Speed=self.parameter))
        self.par=SimpleNamespace(**{k:Par(v) for k,v in {
            'Setupmode':mode,'Targetcomp':self.target,'Targetpar':'Speed',
            'Bindingid':'visual.speed','Targetlabel':'','Useparrange':True,
            'Minimum':0,'Maximum':10}.items()})
        self.calls=[]
        self.ext=SimpleNamespace(RotoPythonExt=SimpleNamespace(_binding=None))
        self.hook=SimpleNamespace(module=SimpleNamespace(onRegister=self.register))
    def BindParameter(self,p,**kwargs):
        self.calls.append((p,kwargs))
        return kwargs['id']
    def Unbind(self):
        self.calls.append('unbind')
    def register(self,controller):
        self.ext.RotoPythonExt._binding=SimpleNamespace(id='callback.speed',parameter=None)
    def op(self,name):
        return self.hook


class SetupTests(unittest.TestCase):
    def test_value_restores_default(self):
        c=Controller('value')
        self.assertEqual(restore(c),'Value')
        self.assertEqual(c.calls,['unbind'])
    def test_parameter_uses_saved_handle_and_inferred_range(self):
        c=Controller()
        self.assertEqual(restore(c),'visual.speed')
        self.assertEqual(c.calls,[(c.parameter,{'id':'visual.speed','label':None})])
    def test_explicit_limits(self):
        c=Controller()
        c.par.Useparrange.value=False
        restore(c)
        self.assertEqual(c.calls[0][1]['maximum'],10)
    def test_missing_target_and_parameter_fail(self):
        c=Controller()
        c.par.Targetcomp.value=None
        with self.assertRaisesRegex(ValueError,'Target COMP'):
            restore(c)
        c.par.Targetcomp.value=c.target
        c.par.Targetpar.value='Missing'
        with self.assertRaisesRegex(ValueError,'does not exist'):
            restore(c)
        self.assertEqual(c.calls,[])
    def test_callback_hook_registers_runtime_callback(self):
        self.assertEqual(restore(Controller('callback')),'callback.speed')
    def test_empty_callback_hook_does_not_fall_back_to_value(self):
        c=Controller('callback')
        c.hook.module.onRegister=lambda controller:None
        with self.assertRaisesRegex(ValueError,'BindCallback'):
            restore(c)
    def test_empty_hook_cannot_reuse_previous_callback(self):
        c=Controller('callback')
        c.register(c)
        c.hook.module.onRegister=lambda controller:None
        with self.assertRaisesRegex(ValueError,'BindCallback'):
            restore(c)
    def test_callback_collection_hook_is_restored(self):
        c=Controller('callback')
        def register(controller):
            controller.ext.RotoPythonExt._collection=SimpleNamespace(
                ids={'speed':('knob',1),'reset':('button',2)},
                bindings={('knob',1):SimpleNamespace(parameter=None),('button',2):SimpleNamespace(parameter=None)})
        c.hook.module.onRegister=register
        self.assertEqual(restore(c),('speed','reset'))
        with self.assertRaisesRegex(ValueError,'BindCallback'):
            c.hook.module.onRegister=lambda controller:None
            restore(c)

    def test_mixed_collection_hook_is_restored(self):
        c=Controller('callback')
        def register(controller):
            controller.ext.RotoPythonExt._collection=SimpleNamespace(
                ids={'speed':('knob',1),'reset':('button',2)},
                bindings={('knob',1):SimpleNamespace(parameter=c.parameter),
                          ('button',2):SimpleNamespace(parameter=None)})
        c.hook.module.onRegister=register
        self.assertEqual(restore(c),('speed','reset'))

    def test_parameter_hook_is_restored(self):
        c=Controller('callback')
        c.hook.module.onRegister=lambda controller: setattr(
            controller.ext.RotoPythonExt, '_binding',
            SimpleNamespace(id='parameter.speed',parameter=c.parameter))
        self.assertEqual(restore(c),'parameter.speed')

    def test_unknown_mode_fails(self):
        with self.assertRaisesRegex(ValueError,'Unknown setup'):
            restore(Controller('unknown'))


if __name__=='__main__':
    unittest.main()
