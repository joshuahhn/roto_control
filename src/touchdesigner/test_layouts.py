"""Layout isolation, transactional preflight and no parameter presets."""
import copy
import json
from types import SimpleNamespace
import unittest
import test_assignment
from controls import Controls
from collection_protocol import CollectionHost
from layouts import Layouts
from protocol import digest,sysex

class Par:
    def __init__(self,value):self.val=value;self.enable=True
    def eval(self):return self.val
class Pars:
    def __setattr__(self,name,value):
        old=self.__dict__.get(name)
        if isinstance(old,Par) and not isinstance(value,Par):old.val=value
        else:object.__setattr__(self,name,value)
class Table:
    numRows=1
    def row(self,index):return [SimpleNamespace(val='id')]
    def clear(self):pass
    def appendRow(self,row):pass

class LayoutTests(unittest.TestCase):
    def fixture(self):
        ext=test_assignment.AssignmentTests().fixture()
        p=test_assignment.AssignmentTests().parameter()
        ext._collection=Controls([dict(kind='knob',slot=1,id='original',parameter=p)])
        ext._host=CollectionHost(ext._send,ext._assign_control,list(ext._collection.specs()),'test')
        ext._host.connected=ext._host.plugin=True
        ext._restore_pending=ext._restoring=False;ext._layouts=None;ext._layout_dirty=False;ext._free_learner=None
        pars=Pars()
        for name,value in [('Value',.5),('Offerparameter',False),('Groupid','test'),('Setupmode','collection'),('Trackname','EFFECT'),('Pluginname','CUSTOM')]:setattr(pars,name,Par(value))
        ext.ownerComp.par=pars
        oldop=ext.ownerComp.op
        ext.ownerComp.op=lambda name:SimpleNamespace(par=SimpleNamespace(Speed=p),valid=p.owner.valid) if name=='../master' else Table() if name=='base_targets/targets' else oldop(name)
        manager=Layouts(ext);ext._layouts=manager
        return ext,manager,p

    def test_a_b_a_reads_actual_value_without_writes_or_pulse(self):
        ext,m,p=self.fixture();identity=ext._host.controls['knob',1].target_id
        b=m.create('B');m.select(b);self.assertEqual(ext.GetControlStates(),[])
        p.val=8
        m.select('custom')
        self.assertEqual(ext.GetValue('original'),8)
        self.assertEqual(ext._host.controls['knob',1].target_id,identity)
        self.assertFalse(ext._host.controls['knob',1].mapped)
        m.rename('custom','Renamed');self.assertEqual(m.record()['device_id'],'TD controls:test')
        self.assertEqual(p.eval(),8)

    def test_lock_learning_touch_preflight_and_callback_reject_atomic(self):
        ext,m,p=self.fixture();b=m.create('B');before=copy.deepcopy(m.data);host=ext._host
        for guard in ('locked','touched'):
            setattr(m,guard,True if guard=='locked' else {52})
            with self.assertRaises(ValueError):m.select(b)
            self.assertEqual(m.data,before);self.assertIs(ext._host,host)
            setattr(m,guard,False if guard=='locked' else set())
        ext._host.learning=True
        with self.assertRaises(ValueError):m.select(b)
        ext._host.learning=False
        with self.assertRaisesRegex(ValueError,'factory'):ext.BindCallback(id='cb',label='Callback',minimum=0,maximum=1,value=0,on_change=lambda e:None)
        self.assertEqual(m.data,before);self.assertIs(ext._host,host)

    def test_invalid_destination_reject_and_active_delete_uses_id(self):
        ext,m,p=self.fixture();b=m.create('B');original=copy.deepcopy(m.record())
        m.record(b)['targets']=[dict(original['targets'][0],minimum=-100)]
        with self.assertRaises(ValueError):m.select(b)
        self.assertEqual(m.data['active'],'custom')
        m.record(b)['targets']=[]
        ext.SetLayoutNames('NEW','CUSTOM')
        self.assertTrue(m.remove('custom'))
        self.assertEqual(m.data['active'],b);self.assertEqual(len(m.data['records']),1)
        with self.assertRaises(ValueError):m.remove(b)

    def test_missing_target_retained_after_active_deletion_switch_and_restore(self):
        ext,m,p=self.fixture();b=m.create('B');m.capture(force=True)
        p.owner.valid=False
        m.select(b);m.select('custom')
        self.assertEqual(ext.GetControlStates(),[])
        self.assertEqual(m.record()['targets'][0]['id'],'original')
        self.assertEqual(ext.GetControlCatalog()[0]['error'],'Target unavailable')
        m.restore();self.assertEqual(m.record()['targets'][0]['id'],'original')
        ext.RemoveControl('original');m.capture(force=True)
        self.assertEqual(m.record()['targets'],[])

    def test_offline_clear_all_reconciles_empty_from_scoped_removed_ack(self):
        ext,m,p=self.fixture();target=ext._host.controls['knob',1]
        packet=sysex(11,11,(0,target.index,*digest(target.target_id,6),0,0,0))
        ext._host.connected=ext._host.plugin=False
        ext.RemoveAllControls();m.capture(force=True)
        self.assertEqual(m.record()['targets'],[])
        m.restore();ext._host.connected=ext._host.plugin=True
        before=ext._pending
        self.assertTrue(m.receive(packet));self.assertTrue(m.confirmed)
        self.assertNotEqual(ext._pending,before)
        packets=[json.loads(line)['midi'] for line in ext._pending[len(before):].splitlines()]
        self.assertEqual(packets,[list(sysex(11,14,(0,0)))])

    def test_capacity_and_version_validation(self):
        ext,m,p=self.fixture()
        for i in range(7):m.create('Layout '+str(i))
        with self.assertRaisesRegex(ValueError,'8 plugins'):m.create('overflow')
        bad=copy.deepcopy(m.data);bad['version']=2
        with self.assertRaises(ValueError):Layouts.validate(bad)

    def test_reassign_cancels_removed_identity_and_late_ack_cannot_unmap(self):
        ext,m,p=self.fixture();target=ext._host.controls['knob',1]
        packet=sysex(11,11,(0,target.index,*digest(target.target_id,6),0,0,0))
        ext._host.connected=ext._host.plugin=False
        ext.RemoveAllControls();m.capture(force=True)
        ext.AssignParameter('knob',1,p);m.capture(force=True)
        ext._pending=b''
        self.assertFalse(m.receive(packet))
        self.assertEqual(ext._pending,b'')
        self.assertEqual(ext.ownerComp.fetch('pending_unmap_identities'),[])
