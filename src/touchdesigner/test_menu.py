"""Menu choice identity, shared API, Learn selection and button event routing."""
import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent / "code/py/roto_python"))
from binding import parameter_value
from controls import Controls
from collection_protocol import CollectionHost
from protocol import digest, sysex
import test_assignment
import test_free_learn


def menu():
    p=test_assignment.AssignmentTests().parameter()
    p.owner.name='master';p.style='Menu';p.menuNames=['alpha','beta','gamma'];p.menuLabels=['Alpha','Beta','Gamma'];p.val='beta'
    return p


class MenuTests(unittest.TestCase):
    def test_knob_index_rounding_names_and_label_metadata(self):
        p=menu();c=Controls([dict(kind='knob',slot=2,id='menu',parameter=p)])
        b=c.bindings['knob',2]
        self.assertEqual((b.minimum,b.maximum,b.value),(0,2,1))
        b.write(b.from_normalized(1),'hardware')
        self.assertEqual(p.eval(),'gamma');self.assertEqual(parameter_value(p),2)
        spec=next(c.specs());self.assertEqual(spec['formatter'](.5),'Beta')
        sent=[];h=CollectionHost(sent.append,lambda *a:None,[spec],'menu')
        h.controls['knob',2]._parameter_details()
        self.assertEqual(sent[-1][17],3)
        self.assertTrue(b.external_changed('alpha'))
        self.assertEqual(b.value,0)

    def test_button_collection_infers_cycle(self):
        c=Controls([dict(kind='button',slot=1,id='menu',parameter=menu())])
        self.assertEqual(c.modes['button',1],'cycle')

    def test_options_change_invalidates_old_identity(self):
        p=menu();c=Controls([dict(kind='knob',slot=1,id='menu',parameter=p)]);b=c.bindings['knob',1]
        p.menuNames.reverse()
        with self.assertRaisesRegex(ValueError,'options changed'): b.write(0,'hardware')
        new=Controls([dict(kind='knob',slot=1,id='menu',parameter=p)]).bindings['knob',1]
        self.assertNotEqual(b.wire_identity,new.wire_identity)

    def test_invalid_menu_shape_and_ranges_rejected(self):
        for names in (['one'],['same','same'],list(map(str,range(25)))):
            p=menu();p.menuNames=names;p.menuLabels=names;p.val=names[0]
            with self.assertRaises(ValueError): Controls([dict(kind='knob',slot=1,id='menu',parameter=p)])
        with self.assertRaises(ValueError): Controls([dict(kind='knob',slot=1,id='menu',parameter=menu(),minimum=1)])

    def ready(self,adapter):
        e=test_assignment.AssignmentTests().fixture();e._host.learning=False
        state=e.AssignParameter('button',3,menu(),button_type=adapter)
        h=e._host;h.connected=h.plugin=True;t=h.controls['button',3]
        h.receive(sysex(11,11,(t.index>>7,t.index&127,*digest(t.target_id,6),1,2,0)))
        return e,state

    def test_push_cycles_wraps_and_ignores_release_or_held_duplicates(self):
        e,s=self.ready('push');p=e._collection.bindings['button',3].parameter
        for value in (127,127,0,0): e._host.receive((191,22,value))
        self.assertEqual(p.eval(),'gamma')
        e._host.receive((191,22,127));e._host.receive((191,22,0))
        self.assertEqual(p.eval(),'alpha')
        e.SetValue(1,id=s['id']);self.assertEqual(p.eval(),'beta')
        self.assertEqual(e.GetControlState(s['id'])['value_label'],'Beta')

    def test_toggle_zero_is_an_action(self):
        e,s=self.ready('toggle');now=[1.0];e._host.clock=lambda:now[0]
        for value in (127,0,127):
            e._host.receive((191,22,value));now[0]+=1
        self.assertEqual(e.GetControlState(s['id'])['value'],1)

    def test_free_learn_selects_button_or_knob(self):
        for kind,cc in (('knob',53),('button',21)):
            e,learner,sent=test_free_learn.FreeLearnTests().fixture();p=menu()
            learner.receive((191,cc,127));self.assertTrue(learner.offer(p))
            self.assertEqual(learner.pending['template'].key[0],kind)
            msg=test_free_learn.FreeLearnTests().ack(learner,int(kind=='button'),3)
            self.assertFalse(learner.receive(msg));e._host.receive(msg)
            self.assertTrue(e._host.controls[kind,3].mapped)
            e._host.learning=False
            e.SetValue(2,id=e._collection.bindings[kind,3].id)
            self.assertEqual(p.eval(),'gamma')
