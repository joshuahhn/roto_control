"""Action release routing remains two clicks despite Lister focus/double-click state."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
import test_inspector
import inspector_data


def module(name):
    path=Path(__file__).parent/'code/py/roto_python/inspector'/f'{name}.py'
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result)
    return result


class InspectorEventTests(unittest.TestCase):
    def fixture(self,column='ClearLearn'):
        i,table,states,calls=test_inspector.ConfirmationTests().fixture()
        callbacks=module('lister_callbacks');events=module('list_events')
        callbacks.parent=events.parent=SimpleNamespace(RotoInspector=i)
        old_op=i.op
        i.op=lambda name:SimpleNamespace(module=callbacks if name=='listerConfig/callbacks' else inspector_data) if name in ('listerConfig/callbacks','inspector_data') else old_op(name)
        data=[{},dict(ID='scene.speed',Control='Knob 1')]
        class Columns:
            def __getitem__(self,key):return SimpleNamespace(val=column)
        lister=SimpleNamespace(ext=SimpleNamespace(ListerExt=SimpleNamespace(Data=data,colDefine=Columns())))
        events.native=lambda: self.fail('Clear must not enter native selection/double-click dispatch')
        def click(u,startrow=1,endrow=1):
            coords=SimpleNamespace(u=u)
            events.onSelect(lister,startrow,2,coords,endrow,2,coords,True,False)
            events.onSelect(lister,startrow,2,coords,endrow,2,coords,False,True)
        return i,calls,click,callbacks,states

    def test_exactly_two_clicks_confirm(self):
        i,calls,click,callbacks,states=self.fixture()
        click(.5);self.assertEqual(calls,[])
        self.assertIsNotNone(i.fetch('pending_clear'))
        click(.2);self.assertEqual(calls,['scene.speed'])
        self.assertIsNone(i.fetch('pending_clear'))

    def test_second_click_no_and_drag_cancel(self):
        i,calls,click,callbacks,states=self.fixture()
        click(.5);click(.8);self.assertEqual(calls,[])
        self.assertIsNone(i.fetch('pending_clear'))
        click(.2,endrow=-1);self.assertEqual(calls,[])
        self.assertIsNone(i.fetch('pending_clear'))

    def test_learn_release_offers_exact_row_once(self):
        i,calls,click,callbacks,states=self.fixture('Learn')
        states[0]['label']='Speed'
        controller=i.parent();controller.GetControlState=lambda id:states[0]
        controller.State={'Learning':True}
        controller.Offerparameter=lambda id:calls.append(('offer',id)) or True
        click(.5)
        self.assertEqual(calls,[('offer','scene.speed')])
        self.assertIsNone(i.fetch('pending_clear'))
        self.assertTrue(states[0]['mapped'])
        self.assertIn('Offered Knob 1',i.fetch('action_status'))
        callbacks.onDoubleClick(dict(row=1,colName='Learn',rowData=dict(ID='scene.speed')))
        self.assertEqual(len(calls),1)

    def test_learn_guards_do_not_write_or_clear(self):
        for condition in ('offline','not_learning','invalid','rejected'):
            i,calls,click,callbacks,states=self.fixture('Learn')
            states[0]['label']='Speed'
            controller=i.parent();controller.GetControlState=lambda id:states[0]
            controller.State={'Learning':condition!='not_learning'}
            if condition=='offline':states[0]['connected']=False
            if condition=='invalid':states[0]['valid']=False
            controller.Offerparameter=lambda id:calls.append(('offer',id)) or False
            click(.5)
            self.assertEqual(calls,[('offer','scene.speed')] if condition=='rejected' else [])
            self.assertIn('Cannot learn:',i.fetch('action_status'))
            self.assertIsNone(i.fetch('pending_clear'))

    def test_learn_on_empty_slot_does_nothing(self):
        i,calls,click,callbacks,states=self.fixture('Learn')
        callbacks.onClick(dict(row=1,colName='Learn',rowData=dict(ID='',Control='Knob 1')))
        self.assertEqual(calls,[])

    def test_mode_popup_and_selection_use_api(self):
        i,calls,click,callbacks,states=self.fixture();i.valid=True
        states[0].update(kind='button',mode='toggle')
        controller=i.parent();controller.GetControlState=lambda id:states[0]
        changes=[];controller.ConfigureControl=lambda id,**fields:changes.append((id,fields))
        menu=[]
        callbacks.op=SimpleNamespace(TDResources=SimpleNamespace(op=lambda name:SimpleNamespace(Open=lambda **kwargs:menu.append(kwargs))))
        callbacks.onClick(dict(row=1,colName='Mode',rowData=dict(ID='scene.speed',Control='Button 1')))
        self.assertEqual(menu[0]['items'],['Toggle','Pulse'])
        self.assertEqual(menu[0]['checkedItems'],['Toggle'])
        i.op=lambda name: SimpleNamespace(module=inspector_data) if name=='inspector_data' else SimpleNamespace(par=SimpleNamespace(Refresh=SimpleNamespace(pulse=lambda:None))) if name=='lister' else SimpleNamespace(text='') if name=='targets' else SimpleNamespace(par=SimpleNamespace(text='')) if name=='title' else None
        menu[0]['callback'](dict(item='Pulse',details=menu[0]['callbackDetails']))
        self.assertEqual(changes,[('scene.speed',dict(mode='pulse'))])

if __name__=='__main__':unittest.main()
