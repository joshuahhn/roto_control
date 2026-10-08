"""Synchronous native outputs keep channel identity through Value bursts."""
from types import SimpleNamespace
import unittest
import test_api

class Channel(list):
    def __init__(self,name):super().__init__([0]);self.name=name;self.writes=0
    def __setitem__(self,index,value):self.writes+=1;super().__setitem__(index,value)

class Output:
    def __init__(self,id=1):self.id=id;self.channels={};self.numSamples=1;self.clears=0;self.appends=0
    @property
    def numChans(self):return len(self.channels)
    def __getitem__(self,name):return self.channels.get(name)
    def clear(self):self.clears+=1;self.channels.clear()
    def appendChan(self,name):
        self.appends+=1;channel=Channel(name);self.channels[name]=channel;return channel

class Pars:
    def __init__(self):self.__dict__['_items']={}
    def __getattr__(self,name):return self._items.setdefault(name,SimpleNamespace(val=None))
    def __setattr__(self,name,value):self.__getattr__(name).val=value

class ControlPublicationTests(unittest.TestCase):
    def setUp(self):
        self.ext=test_api.ApiTests().collection();self.ext._restore_pending=False
        self.output=Output();self.table=SimpleNamespace(text='');self.pars=Pars()
        self.marked=[]
        self.nodes={'base_targets/controls_values':self.output,
            'base_targets/state':self.table,'base_state':SimpleNamespace(par=self.pars),
            'base_targets/mapping_marks':SimpleNamespace(module=SimpleNamespace(update=lambda owner,states:self.marked.append(states)))}
        self.ext.ownerComp.op=lambda name:self.nodes.get(name)
        self.ext._value_parameter=lambda:SimpleNamespace(eval=lambda:0)

    def test_value_burst_updates_only_changed_channel_without_rebuilding_schema(self):
        e=self.ext;e._publish_controls()
        speed=self.output['knob2'];reset=self.output['button8'];reset_writes=reset.writes
        for value in range(10):
            e._collection.bindings['knob',2].write(value,'software');e._publish_controls()
            self.assertIs(self.output['knob2'],speed);self.assertIs(self.output['button8'],reset)
            self.assertEqual(speed[0],value)
            rows=[row.split('\t') for row in self.table.text.splitlines()]
            self.assertEqual(float(rows[1][4]),value)
        self.assertEqual(self.output.clears,1);self.assertEqual(self.output.appends,2)
        self.assertEqual(reset.writes,reset_writes)
        writes=speed.writes;e._publish_controls();self.assertEqual(speed.writes,writes)

    def test_schema_change_replacement_and_missing_channel_rebuild_safely(self):
        e=self.ext;e._publish_controls()
        del e._collection.bindings['button',8];e._publish_controls()
        self.assertEqual(set(self.output.channels),{'knob2'});self.assertEqual(self.output.clears,2)
        replacement=Output(2);self.nodes['base_targets/controls_values']=replacement
        e._publish_controls();self.assertEqual(replacement['knob2'][0],e.GetValue('speed'))
        self.assertEqual(replacement.clears,1)
        replacement.channels={'foreign':Channel('foreign')}
        e._collection.bindings['knob',2].write(8,'software');e._publish_controls()
        self.assertEqual(set(replacement.channels),{'knob2'});self.assertEqual(replacement['knob2'][0],8)

    def test_one_publish_uses_one_detached_snapshot_for_catalog_ack_and_marks(self):
        e=self.ext;del e._publish
        e._publish_inspector=lambda:None
        e.ownerComp.store('needs_relearn',('speed',))
        e._host.controls['knob',2].mapped=True
        original=e.GetControlStates;calls=[]
        def states():
            snapshot=original();calls.append(snapshot);return snapshot
        e.GetControlStates=states
        e._publish()
        self.assertEqual(len(calls),1)
        self.assertIs(self.marked[0],calls[0])
        self.assertEqual(e.ownerComp.fetch('needs_relearn'),())
        self.assertEqual(e.GetControlCatalog()[0]['value'],e.GetValue('speed'))
        self.assertEqual(self.output['knob2'][0],e.GetValue('speed'))
        calls[0][0]['value']=-1
        self.assertEqual(e.GetControlCatalog()[0]['value'],e.GetValue('speed'))
