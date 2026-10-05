"""Writable TD Par bind chains preserve their masters and reject driven roots."""
from types import SimpleNamespace
import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'code/py/roto_python'))
from binding import Binding
from controls import Controls

class BoundParameter:
    def __init__(self,style='Float',master=None):
        self.owner=SimpleNamespace(valid=True,path='/target' if master is not None else '/master')
        self.name='Speed';self.label='Speed';self.isCustom=True;self.readOnly=False
        self.style=style;self.mode=SimpleNamespace(name='BIND' if master is not None else 'CONSTANT')
        self.bindMaster=master;self.bindExpr='master.par.Speed'
        self.normMin=self.min=0;self.normMax=self.max=10
        self.clampMin=self.clampMax=True;self._value=5;self.pulses=0
    def eval(self):return self.bindMaster.eval() if self.mode.name=='BIND' else self._value
    @property
    def val(self):return self.eval()
    @val.setter
    def val(self,value):
        if self.mode.name=='BIND':self.bindMaster.val=value
        else:self._value=value
    def pulse(self):
        if self.mode.name=='BIND':self.bindMaster.pulse()
        else:self.pulses+=1

class BoundParameterTests(unittest.TestCase):
    def test_numeric_write_and_external_master_change_preserve_bind(self):
        master=BoundParameter();p=BoundParameter(master=master)
        b=Binding('speed','Speed',0,10,5,parameter=p);b.write(7,'hardware')
        self.assertEqual(master.eval(),7);self.assertEqual(p.mode.name,'BIND')
        self.assertEqual(p.bindExpr,'master.par.Speed');self.assertFalse(b.external_changed(p.eval()))
        master.val=8;self.assertTrue(b.external_changed(p.eval()));self.assertEqual(b.value,8)
    def test_driven_missing_readonly_or_cyclic_master_rejected(self):
        for state in ('EXPRESSION','EXPORT','readonly','missing','cycle'):
            master=BoundParameter();p=BoundParameter(master=master)
            if state in ('EXPRESSION','EXPORT'):master.mode.name=state
            elif state=='readonly':master.readOnly=True
            elif state=='missing':p.bindMaster=None
            else:master.mode.name='BIND';master.bindMaster=p
            with self.subTest(state=state),self.assertRaises(ValueError):
                Binding('speed','Speed',0,10,5,parameter=p).write(7,'hardware')
            self.assertEqual(master._value,5)
    def test_master_clamp_mismatch_rejected(self):
        master=BoundParameter();master.max=6;p=BoundParameter(master=master)
        with self.assertRaises(ValueError):Binding('speed','Speed',0,10,5,parameter=p).check_parameter()
    def test_bound_toggle_and_pulse_use_same_collection_path(self):
        master=BoundParameter('Toggle');p=BoundParameter('Toggle',master)
        pulse_master=BoundParameter('Pulse');pulse=BoundParameter('Pulse',pulse_master);pulse.name=pulse_master.name='Reset'
        c=Controls([dict(kind='button',slot=1,id='toggle',parameter=p),dict(kind='button',slot=8,id='pulse',mode='pulse',parameter=pulse)])
        c.bindings['button',1].write(1,'hardware');c.pulse(('button',8))
        self.assertEqual(master.eval(),1);self.assertEqual(pulse_master.pulses,1)
        self.assertEqual(p.mode.name,'BIND');self.assertEqual(pulse.mode.name,'BIND')
    def test_two_aliases_of_one_master_rejected(self):
        master=BoundParameter();a=BoundParameter(master=master);b=BoundParameter(master=master);b.name='Other'
        with self.assertRaisesRegex(ValueError,'bound twice'):
            Controls([dict(kind='knob',slot=1,id='a',parameter=a),dict(kind='knob',slot=2,id='b',parameter=b)])
