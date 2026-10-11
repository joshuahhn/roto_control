"""Runtime BIND ownership is checked at controller write/feedback seams."""
import unittest
from types import SimpleNamespace
import test_bound_parameter
import test_catalog_removal
import test_api


class RuntimeOwnershipTests(unittest.TestCase):
    def fixture(self):
        ext = test_catalog_removal.CatalogRemovalTests().fixture()
        ext._pending = b''
        masters = [test_bound_parameter.BoundParameter() for _ in range(3)]
        aliases = []
        for i, master in enumerate(masters):
            master.owner.path = '/master'+str(i)
            alias = test_bound_parameter.BoundParameter(master=master); alias.owner.path = '/alias'+str(i)
            aliases.append(alias)
        specs = [dict(kind='knob', slot=i+1, id='target'+str(i), parameter=p)
                 for i, p in enumerate(aliases)]
        ext.BindControls(specs, group_id='runtime-bind')
        sent = []; ext._host.send = sent.append
        test_api.ApiTests().ready(ext); sent.clear()
        return ext, masters, aliases, specs, sent

    def test_runtime_rebind_stops_both_conflicting_controls_before_setvalue(self):
        ext, masters, aliases, specs, sent = self.fixture()
        aliases[1].bindMaster = masters[0]
        with self.assertRaisesRegex(ValueError, 'ownership conflict'):
            ext.SetValue(8, id='target1')
        self.assertEqual(masters[0].eval(), 5)
        for id in ('target0', 'target1'):
            state = ext.GetControlState(id)
            self.assertFalse(state['valid']); self.assertFalse(state['mapped'])
            self.assertIn('ownership conflict', state['error'])
        self.assertEqual(sent, [])
        ext.SetValue(8, id='target2')
        self.assertEqual(masters[2].eval(), 8)
        self.assertTrue(ext.GetControlState('target2')['valid'])

    def test_hardware_dispatch_rejects_conflict_without_feedback(self):
        ext, masters, aliases, specs, sent = self.fixture()
        aliases[1].bindMaster = masters[0]
        ext._host.receive((191,13,127)); ext._host.receive((191,45,127))
        self.assertEqual(masters[0].eval(), 5)
        self.assertEqual(sent, [])
        self.assertFalse(ext.GetControlState('target0')['valid'])
        self.assertFalse(ext.GetControlState('target1')['valid'])

    def test_target_feedback_conflict_and_reregistration_recovery(self):
        ext, masters, aliases, specs, sent = self.fixture()
        aliases[1].bindMaster = masters[0]; masters[0].val = 7
        ext.onControlChange(('knob',1), aliases[0])
        self.assertEqual(sent, [])
        self.assertFalse(ext.GetControlState('target1')['valid'])
        aliases[1].bindMaster = masters[1]
        with self.assertRaises(ValueError): ext.SetValue(8, id='target1')
        expressions = [p.bindExpr for p in aliases]
        ext.BindControls(specs, group_id='runtime-bind')
        ext.SetValue(8, id='target1')
        self.assertEqual(masters[1].eval(), 8)
        self.assertEqual([p.bindExpr for p in aliases], expressions)
        self.assertTrue(all(s['valid'] for s in ext.GetControlStates()))

    def test_conflict_discards_queued_feedback_only_for_affected_controls(self):
        import json
        from protocol import sysex
        ext, masters, aliases, specs, sent = self.fixture()
        for message in ((191,12,64), (191,44,0), sysex(10,24,(0,0,65)),
                        (191,14,64), (191,46,0), sysex(10,24,(0,2,67))):
            ext._send(message)
        aliases[1].bindMaster = masters[0]
        with self.assertRaises(ValueError): ext.SetValue(8, id='target1')
        messages = [json.loads(line)['midi'] for line in ext._pending.splitlines()]
        self.assertEqual(messages, [[191,14,64], [191,46,0], list(sysex(10,24,(0,2,67)))])

    def test_semantic_failure_does_not_hide_shared_master_claim(self):
        ext, masters, aliases, specs, sent = self.fixture()
        specs[0]['maximum'] = 5
        ext.BindControls(specs, group_id='runtime-bind')
        masters[0].max = 5
        aliases[1].bindMaster = masters[0]
        with self.assertRaises(ValueError): ext.SetValue(8, id='target1')
        self.assertFalse(ext.GetControlState('target0')['valid'])
        self.assertFalse(ext.GetControlState('target1')['valid'])
        self.assertIn('ownership conflict', ext.GetControlState('target0')['error'])
        self.assertEqual(masters[0].eval(), 5)

    def test_valid_rebind_to_unclaimed_master_remains_writable(self):
        ext, masters, aliases, specs, sent = self.fixture()
        new = test_bound_parameter.BoundParameter(); new.owner.path='/unclaimed'
        aliases[1].bindMaster = new
        ext.SetValue(9, id='target1')
        self.assertEqual(new.eval(), 9)
        self.assertEqual([p.eval() for p in masters], [5,5,5])
        self.assertTrue(ext.GetControlState('target1')['valid'])
