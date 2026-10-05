"""Visual claim ownership, shared destinations and preservation of user styling."""
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
sys.path.insert(0,str(Path(__file__).parent/'code/py/roto_python/base_targets'))
from mapping_marks import update, TAG, COLOR, KEY

class Node:
    def __init__(self,id,path):
        self.id,self.path,self.valid,self.isCOMP=id,path,True,True
        self.tags,self.color,self.storage=set(),(.4,.3,.2),{}
        self.active=True
    def fetch(self,key,default=None): return self.storage.get(key,default)
    def store(self,key,value): self.storage[key]=value
    def op(self,name):
        return SimpleNamespace(par=SimpleNamespace(Connected=SimpleNamespace(eval=lambda:self.active),Plugin=SimpleNamespace(eval=lambda:self.active)))

class MappingMarksTests(unittest.TestCase):
    def setUp(self):
        self.a,self.b,self.target=Node(1,'/a'),Node(2,'/b'),Node(3,'/target')
        self.nodes=[self.a,self.b,self.target]
    def resolve(self,key):
        return next((n for n in self.nodes if n.valid and key in (n.id,n.path)),None)
    def state(self,**changes):
        return dict(dict(valid=True,mapped=True,connected=True,plugin=True,binding_type='parameter',comp='/target'),**changes)
    def test_shared_controls_and_controllers_restore_only_last_claim(self):
        original=self.target.color
        update(self.a,[self.state(),self.state()],self.resolve)
        update(self.b,[self.state()],self.resolve)
        self.assertEqual(self.target.color,COLOR);self.assertIn(TAG,self.target.tags)
        update(self.a,[],self.resolve)
        self.assertIn(TAG,self.target.tags)
        update(self.b,[],self.resolve)
        self.assertNotIn(TAG,self.target.tags);self.assertEqual(self.target.color,original)
    def test_preexisting_tag_and_manual_color_are_preserved(self):
        self.target.tags.add(TAG);self.target.tags.add('user')
        update(self.a,[self.state()],self.resolve)
        self.target.color=(.8,.1,.2)
        self.a.path='/renamed_owner'
        update(self.a,[self.state()],self.resolve)
        self.assertEqual(self.target.color,(.8,.1,.2))
        update(self.a,[],self.resolve)
        self.assertEqual(self.target.tags,{TAG,'user'})
        self.assertEqual(self.target.color,(.8,.1,.2))
    def test_rename_and_stale_controller_claim(self):
        update(self.a,[self.state()],self.resolve)
        self.target.path='/renamed';self.a.path='/renamed_owner'
        update(self.a,[self.state(comp='/renamed')],self.resolve)
        self.assertIn(TAG,self.target.tags)
        self.a.valid=False
        update(self.b,[],self.resolve) # no targets owned by b: does not scan unrelated nodes
        update(self.a,[],self.resolve)
        self.assertNotIn(TAG,self.target.tags)
    def test_unmapped_invalid_callback_and_disconnect_do_not_mark(self):
        for state in [self.state(mapped=False),self.state(valid=False),self.state(binding_type='callback'),self.state(connected=False)]:
            update(self.a,[state],self.resolve)
            self.assertNotIn(TAG,self.target.tags)
        update(self.a,[self.state()],self.resolve)
        self.a.active=False;update(self.a,[],self.resolve)
        self.assertNotIn(TAG,self.target.tags)

if __name__=='__main__': unittest.main()
