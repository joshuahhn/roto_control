from unittest import TestCase
from parity import filter_choices,visible_slots,ClearRequest
from live_model import ControllerCatalog
from test_live_model import Adapter,KEY,state

class DeviceAdapter(Adapter):
    def __init__(self):super().__init__();self.calls=[];self.partial=False
    def ClearDevice(self,context):
        self.calls.append(context)
        if self.partial:
            self.records[context]=self.records[context][1:]
            raise RuntimeError('Removal interrupted')
        self.records[context]=[]

class ParityTests(TestCase):
    def setUp(self):
        self.adapter=DeviceAdapter();self.model=ControllerCatalog(self.adapter)
    def test_filters_are_scalar_readonly_and_keep_all_empty_slots(self):
        info=[{} for _ in range(16)]
        info[1]=dict(id='a',comp='/one',parameter='Amount',binding_type='parameter')
        info[8]=dict(id='b',comp='',parameter='',binding_type='callback')
        info[3]=dict(id='c',comp='/two',parameter='Power',binding_type='parameter')
        self.assertEqual(visible_slots(info,'all'),tuple(range(16)))
        self.assertEqual(visible_slots(info,'callbacks'),(8,))
        self.assertEqual(visible_slots(info,'comp:/one'),(1,))
        self.assertEqual(dict(filter_choices(info))['comp:/two'],'/two')
        self.assertEqual(visible_slots(info,'comp:/deleted'),())
    def test_confirmation_expires_and_is_single_use(self):
        clock=[0];r=ClearRequest('token',lambda:clock[0]);clock[0]=9
        with self.assertRaisesRegex(ValueError,'expired'):r.Consume()
        r=ClearRequest('new',lambda:clock[0]);self.assertEqual(r.Consume(),'new')
        with self.assertRaises(ValueError):r.Consume()
    def test_clear_device_preserves_other_contexts_and_values(self):
        other=('layout','track','other');self.adapter.records[other]=[state(.8)]
        confirmation=self.model.PrepareClearDevice(KEY)
        self.adapter.records[KEY][0]['value']=.9  # Live traffic does not expire confirmation.
        result=self.model.ClearDevice(KEY,confirmation)
        self.assertEqual(result,dict(removed=('target',),remaining=(),error=''))
        self.assertEqual(self.adapter.records[other],[state(.8)])
        self.assertEqual(self.adapter.writes,[])
    def test_config_registration_and_session_changes_expire_request(self):
        for field,value in [('id','replacement'),('maximum',2),('button_type','push')]:
            token=self.model.PrepareClearDevice(KEY);self.adapter.records[KEY][0][field]=value
            with self.assertRaisesRegex(ValueError,'changed'):self.model.ClearDevice(KEY,token)
        token=self.model.PrepareClearDevice(KEY);self.adapter.session+=1
        with self.assertRaisesRegex(ValueError,'changed'):self.model.ClearDevice(KEY,token)
        self.assertEqual(self.adapter.calls,[])
    def test_learn_touch_browse_empty_guards_do_not_remove(self):
        self.adapter.learning=True
        with self.assertRaisesRegex(ValueError,'LEARN'):self.model.PrepareClearDevice(KEY)
        self.adapter.learning=False;self.adapter.records[KEY][0]['touched']=True
        with self.assertRaisesRegex(ValueError,'Release'):self.model.PrepareClearDevice(KEY)
        other=('layout','track','other');self.adapter.records[other]=[state()]
        with self.assertRaisesRegex(ValueError,'Browse'):self.model.PrepareClearDevice(other)
        self.adapter.records[KEY]=[]
        with self.assertRaisesRegex(ValueError,'no registrations'):self.model.PrepareClearDevice(KEY)
        self.assertEqual(self.adapter.calls,[])
    def test_partial_failure_reports_exact_removed_and_remaining_ids(self):
        second=state();second.update(id='second',slot=3);self.adapter.records[KEY].append(second)
        token=self.model.PrepareClearDevice(KEY);self.adapter.partial=True
        result=self.model.ClearDevice(KEY,token)
        self.assertEqual(result,dict(removed=('target',),remaining=('second',),error='Removal interrupted'))
        self.assertEqual(self.adapter.calls,[KEY]);self.assertEqual(self.adapter.writes,[])
