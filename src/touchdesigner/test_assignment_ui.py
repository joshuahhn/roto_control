"""Picker discovers new COMPs and auto-offers a newly assigned target in LEARN."""
from types import SimpleNamespace
import unittest
import test_inspector
import test_inspector_events
from test_bound_parameter import BoundParameter
import inspector_data
import controls

class AssignmentUiTests(unittest.TestCase):
    def test_discovers_new_nested_comp_and_filters_wrong_style(self):
        p=BoundParameter();readonly=BoundParameter();readonly.readOnly=True
        pulse=BoundParameter('Pulse');pulse.name='Reset';pulse._value=0
        node=SimpleNamespace(valid=True,isCOMP=True,path='/scene/new_comp',customPars=[p,readonly,pulse],children=[])
        root=SimpleNamespace(valid=True,isCOMP=True,path='/scene',customPars=[],children=[node])
        controller=SimpleNamespace(valid=True,isCOMP=True,parent=lambda:root,op=lambda name:SimpleNamespace(module=controls))
        inspector=SimpleNamespace(parent=lambda:controller)
        self.assertEqual(inspector_data.available_components(inspector,'knob'),[node])
        self.assertEqual(inspector_data.eligible_parameters(inspector,node,'knob'),[p])
        self.assertEqual(inspector_data.eligible_parameters(inspector,node,'button'),[pulse])

    def test_empty_slot_click_opens_picker_once(self):
        i,calls,click,callbacks,states=test_inspector_events.InspectorEventTests().fixture('COMP')
        menu=[];node=SimpleNamespace(path='/scene/new_comp',valid=True,isCOMP=True)
        original=i.op
        picker=SimpleNamespace(available_components=lambda inspector,kind:[node])
        i.op=lambda name:SimpleNamespace(module=picker) if name=='inspector_data' else original(name)
        callbacks.op=SimpleNamespace(TDResources=SimpleNamespace(op=lambda name:SimpleNamespace(Open=lambda **kw:menu.append(kw))))
        callbacks.onClick(dict(row=1,colName='COMP',rowData=dict(ID='',Control='Knob 4')))
        self.assertEqual(menu[0]['items'],['/scene/new_comp'])
        self.assertEqual(menu[0]['callbackDetails']['slot'],4)
        callbacks.onDoubleClick(dict(row=1,colName='COMP',rowData=dict(ID='',Control='Knob 4')))
        self.assertEqual(len(menu),1)

    def test_assign_during_learn_automatically_offers_without_action(self):
        i,table,states,calls=test_inspector.ConfirmationTests().fixture()
        controller=i.parent();state=states[0];state['label']='Speed'
        assigned=[];controller.AssignParameter=lambda kind,slot,parameter:assigned.append((kind,slot,parameter)) or state
        controller.GetControlState=lambda id:state
        controller.State={'Learning':True}
        controller.Offerparameter=lambda id:calls.append(('offer',id)) or True
        self.assertTrue(inspector_data.assign(i,'knob',1,'parameter.handle'))
        self.assertEqual(assigned,[('knob',1,'parameter.handle')])
        self.assertEqual(calls,[('offer','scene.speed')])
        self.assertIn('waiting for hardware acknowledgement',i.fetch('action_status'))

if __name__=='__main__':unittest.main()
