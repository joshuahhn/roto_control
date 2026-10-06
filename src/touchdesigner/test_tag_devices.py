"""User-tagged COMPs own independent Devices within the active Layout/Track."""
import unittest
from types import SimpleNamespace
import test_assignment
import test_device_context
from free_learn import FreeLearner


class TagDeviceTests(unittest.TestCase):
    def fixture(self):
        e,m,f,a,b,t,pa,pb,s,_=test_device_context.DeviceTests().fixture()
        for p in (a,b):
            p.owner.name=p.owner.path.rsplit('/',1)[-1]
            p.owner.tags=set()
        tagged=[];f.tag_sampler=lambda:tuple(tagged)
        return e,m,f,a,b,t,pa,pb,s,tagged

    def target(self,path='/new'):
        p=test_assignment.AssignmentTests().parameter();p.owner.path=path;p.owner.name=path.rsplit('/',1)[-1]
        p.owner.id=30;p.owner.isCOMP=True;p.owner.tags={'roto_device'};p.owner.par=SimpleNamespace(Speed=p)
        return p

    def test_tag_registers_empty_device_without_switching_or_writing(self):
        e,m,f,a,b,t,pa,pb,s,tagged=self.fixture();p=self.target();tagged.append(p.owner)
        old=e.ownerComp.op;e.ownerComp.op=lambda n:p.owner if n=='../new' else old(n)
        ids=f.sync_tags(force=True)
        self.assertEqual(len(ids),1)
        device=m.track()['plugins'][-1]
        self.assertEqual((device['plugin_name'],device['comp_name'],device['name_mode']),('new','new','comp'))
        self.assertEqual(device['focus_comp'],dict(path='../new',state='bound'))
        self.assertEqual(device['targets'],[])
        self.assertEqual((m.plugin()['id'],p.eval(),a.eval()),(pa,5,5))
        self.assertEqual(f.sync_tags(force=True),[])
        self.assertEqual(len(m.track()['plugins']),3)

    def test_existing_link_reused_across_tracks_and_tag_removal_keeps_mapping(self):
        import test_comp_follow
        e,m,f,a,b,t,tb,s,_=test_comp_follow.FollowTests().fixture()
        b.owner.tags={'roto_device'};f.tag_sampler=lambda:(b.owner,)
        self.assertEqual(f.sync_tags(force=True),[])
        b.owner.tags.clear();f.sync_tags(force=True)
        self.assertEqual(m.plugin('custom',tb)['targets'][0]['parameter'],'Speed')
        self.assertEqual(len(m.track('custom',t)['plugins']),1)

    def test_registration_waits_for_learn_touch_lock_and_cancels_removed_tag(self):
        for guard in ('learning','touched','locked'):
            with self.subTest(guard=guard):
                e,m,f,a,b,t,pa,pb,s,tagged=self.fixture();p=self.target();tagged.append(p.owner)
                setattr(m if guard=='locked' else e._host,guard,True)
                self.assertEqual(f.sync_tags(force=True),[])
                self.assertEqual(len(m.track()['plugins']),2)
                p.owner.tags.clear();setattr(m if guard=='locked' else e._host,guard,False)
                self.assertEqual(f.sync_tags(force=True),[])

    def test_learn_edit_cannot_register_foreign_comp_in_active_device(self):
        e,m,f,a,b,t,pa,pb,s,tagged=self.fixture()
        learner=FreeLearner(e);e._free_learner=learner;learner.active=True;e._host.learning=True
        self.assertFalse(learner.offer(b))
        self.assertIsNone(learner.pending)
        self.assertEqual(m.plugin()['id'],pa)

    def test_tag_added_to_already_selected_comp_rechecks_follow_without_changing_layout(self):
        e,m,f,a,b,t,pa,pb,s,tagged=self.fixture();p=self.target();p.owner.tags.clear()
        old=e.ownerComp.op;e.ownerComp.op=lambda n:p.owner if n=='../new' else old(n)
        s[0]=(s[0][0],(p.owner,));f.observe(force=True)
        self.assertEqual(f.status,'failed')
        p.owner.tags.add('roto_device');tagged.append(p.owner);f.next_tag_scan=0
        f.observe(force=True);self.assertIsNotNone(f.pending);f.flush()
        self.assertEqual(m.data['active'],'custom')
        self.assertEqual(m.track()['id'],t)
        self.assertEqual(m.plugin()['focus_comp']['path'],'../new')
        self.assertEqual((p.eval(),a.eval()),(5,5))

    def test_untagged_deleted_internal_and_over_capacity_never_register(self):
        e,m,f,a,b,t,pa,pb,s,tagged=self.fixture();p=self.target()
        p.owner.tags.clear();tagged.append(p.owner);self.assertEqual(f.sync_tags(force=True),[])
        p.owner.tags.add('roto_device');p.owner.valid=False;self.assertEqual(f.sync_tags(force=True),[])
        p.owner.valid=True;p.owner.path=e.ownerComp.path+'/internal';self.assertEqual(f.sync_tags(force=True),[])
        p.owner.path='/new'
        m.track()['plugins'].extend(m.empty_plugin('Dummy') for _ in range(125))
        self.assertEqual(f.sync_tags(force=True),[])
        self.assertIn('capacity',f.tag_error)
        self.assertEqual(len(m.track()['plugins']),127)

    def test_tag_registration_is_transactional_when_menu_observer_fails(self):
        e,m,f,a,b,t,pa,pb,s,tagged=self.fixture();p=self.target();tagged.append(p.owner)
        old=e.ownerComp.op;e.ownerComp.op=lambda n:p.owner if n=='../new' else old(n)
        original=m.menu;calls=[0]
        def menu():
            calls[0]+=1
            if calls[0]==1:raise ValueError('menu observer failed')
            return original()
        m.menu=menu
        self.assertEqual(f.sync_tags(force=True),[])
        self.assertEqual(len(m.track()['plugins']),2)
        self.assertEqual(m.plugin()['id'],pa)
        self.assertEqual(set(f.handles),{pa,pb})

    def test_foreign_focus_after_offer_cannot_commit_delayed_ack(self):
        import test_free_learn
        e,m,f,a,b,t,pa,pb,s,tagged=self.fixture()
        learner=FreeLearner(e);e._free_learner=learner;learner.active=True;e._host.learning=True
        self.assertTrue(learner.offer(a));ack=test_free_learn.FreeLearnTests().ack(learner,slot=2)
        # Relink while hardware's acknowledgement is delayed.
        m.plugin()['focus_comp']=dict(path='../other',state='bound');f.handles[pa]=b.owner
        self.assertTrue(learner.receive(ack))
        self.assertNotIn(('knob',2),e._collection.bindings)

    def test_nested_device_has_its_own_learn_scope(self):
        e,m,f,a,b,t,pa,pb,s,tagged=self.fixture();b.owner.path=a.owner.path+'/child'
        learner=FreeLearner(e);e._free_learner=learner;learner.active=True;e._host.learning=True
        self.assertFalse(learner.offer(b))
        self.assertTrue(learner.offer(a))

    def test_tag_added_to_existing_selected_link_is_a_follow_event(self):
        e,m,f,a,b,t,pa,pb,s,tagged=self.fixture()
        s[0]=(s[0][0],(b.owner,));f.baseline=None;f.observe(force=True)
        self.assertEqual(m.plugin()['id'],pa)  # reload baseline does not switch
        b.owner.tags.add('roto_device');tagged.append(b.owner);f.next_tag_scan=0
        f.observe(force=True)
        self.assertIsNotNone(f.pending)
        self.assertEqual(f.pending['plugin_id'],pb)
        f.flush();self.assertEqual(m.plugin()['id'],pb)


if __name__=='__main__':unittest.main()
