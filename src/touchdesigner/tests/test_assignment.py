"""One-slot assignment preserves other live controls and survives saved restore."""
from types import SimpleNamespace
import unittest
import test_api
import test_catalog_removal
from test_bound_parameter import BoundParameter
from protocol import sysex, digest

class AssignmentTests(unittest.TestCase):
    def fixture(self):
        ext=test_catalog_removal.CatalogRemovalTests().fixture()
        ext.ownerComp.par.Groupid=SimpleNamespace(eval=lambda:'test')
        ext._pending=b''
        return ext

    def parameter(self,style='Float',name='Speed'):
        p=BoundParameter(style);p.name=name
        if style in ('Pulse','Toggle'):
            p.normMax=p.max=1;p._value=0
        return p

    def test_add_during_learn_preserves_other_mapping_and_saves(self):
        ext=self.fixture();test_api.ApiTests().ready(ext)
        old=ext._host.controls['knob',2];binding=ext._collection.bindings['knob',2]
        ext._host.receive(sysex(11,9,(1,)))
        parameter=self.parameter()
        state=ext.AssignParameter('knob',3,parameter)
        self.assertTrue(old.mapped);self.assertIs(ext._host.controls['knob',2],old)
        self.assertIs(ext._collection.bindings['knob',2],binding)
        self.assertEqual((state['mode'],state['minimum'],state['maximum']),('value',0,10))
        self.assertFalse(state['mapped']);self.assertTrue(state['requires_relearn'])
        self.assertTrue(ext.Offerparameter(state['id']))
        self.assertEqual(parameter.eval(),5)
        saved=ext.ownerComp.fetch('parameter_assignments')[0]
        self.assertEqual(saved['comp'],'../master');self.assertEqual(saved['parameter'],'Speed')
        # Restore keeps the generated identity and adds it over source registration.
        original_op=ext.ownerComp.op
        ext.ownerComp.op=lambda name:SimpleNamespace(par=SimpleNamespace(Speed=parameter)) if name=='../master' else original_op(name)
        ext._host.learning=False;ext._restoring=True
        ext.BindControls([dict(kind='knob',slot=2,id='speed',minimum=0,maximum=10,value=7,on_change=lambda e:None)],group_id='test')
        self.assertEqual(ext.GetControlState(state['id'])['parameter'],'Speed')

    def test_replacement_rejects_stale_ack_and_only_unmaps_selected_slot(self):
        ext=self.fixture();test_api.ApiTests().ready(ext)
        old=ext._host.controls['knob',2];other=ext._host.controls['button',8]
        sent=[];ext._host.send=sent.append
        state=ext.AssignParameter('knob',2,self.parameter())
        self.assertEqual(sent,[sysex(11,14,(0,1))])
        self.assertTrue(other.mapped)
        ext._host.receive(sysex(11,11,(0,old.index,*digest(old.target_id,6),0,1,0)))
        self.assertFalse(ext.GetControlState(state['id'])['mapped'])
        self.assertNotIn('speed',ext._collection.ids)

    def test_duplicate_or_wrong_style_preserves_all_state(self):
        ext=self.fixture();p=self.parameter();state=ext.AssignParameter('knob',3,p)
        before=list(ext.ownerComp.fetch('parameter_assignments'));host_target=ext._host.controls['knob',3]
        with self.assertRaisesRegex(ValueError,'bound twice'):ext.AssignParameter('knob',4,p)
        with self.assertRaisesRegex(ValueError,'style'):ext.AssignParameter('button',4,p)
        self.assertEqual(ext.ownerComp.fetch('parameter_assignments'),before)
        self.assertIs(ext._host.controls['knob',3],host_target)
        self.assertEqual(ext.AssignParameter('knob',3,p)['id'],state['id'])

    def test_first_assignment_from_builtin_value_works_in_learn(self):
        from protocol import Host
        ext=self.fixture();ext._collection=ext._binding=None
        ext._host=Host(lambda message:None,lambda value:None,.5)
        ext._host.connected=ext._host.plugin=ext._host.learning=True
        state=ext.AssignParameter('knob',1,self.parameter())
        self.assertTrue(ext._host.learning)
        self.assertTrue(ext.Offerparameter(state['id']))
        self.assertFalse(state['mapped'])

    def test_button_inference_and_removal_does_not_resurrect(self):
        ext=self.fixture();state=ext.AssignParameter('button',4,self.parameter('Pulse','Reset'))
        self.assertEqual((state['mode'],state['button_type']),('pulse','push'))
        ext.RemoveControl(state['id'])
        self.assertEqual(ext.ownerComp.fetch('parameter_assignments'),[])
        self.assertIn(state['id'],ext.ownerComp.fetch('removed_controls'))
        toggle=ext.AssignParameter('button',4,self.parameter('Toggle','Enabled'))
        self.assertEqual(toggle['mode'],'toggle')

if __name__=='__main__':unittest.main()
