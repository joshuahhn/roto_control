"""Snapshot composition at owned Inspector boundaries; fake TD, no native proof."""
import copy
import json
import unittest
from types import SimpleNamespace as S

from test_owned_inspector import (SOURCE, Node, builder, execute_isolation_call_sites,
                                  fixture, isolation_boundary, load, runtime)
import test_snapshot_presets as snapshots
from export_component import reset_mapping_storage, reset_registration


class OwnedSnapshotTests(unittest.TestCase):
    def test_snapshot_source_parity_and_required_flags_are_not_optional(self):
        for failure in ('missing', 'stale', 'missing_flag'):
            with self.subTest(failure=failure):
                c, w, required, internal = isolation_boundary()
                dat = c.op('snapshots')
                if failure == 'missing':
                    c.children.remove(dat)
                elif failure == 'stale':
                    dat.text = '# obsolete Snapshot source'
                else:
                    del dat.par.loadonstart
                with self.assertRaisesRegex(ValueError, 'snapshots'):
                    builder._verify_runtime_sources(c, SOURCE)
        c, w, required, internal = isolation_boundary()
        execute_isolation_call_sites(builder, c, w)
        builder._verify_runtime_sources(c, SOURCE)
        self.assertEqual(tuple(getattr(c.op('snapshots').par, n).eval()
                               for n in ('file', 'syncfile', 'loadonstart')), ('', False, False))

    def test_cleanup_classifies_snapshot_source_and_embedded_authoritative_docs(self):
        cleanup = load('owned_snapshot_cleanup', SOURCE/'cleanup_network.py')
        c = Node('controller')
        snapshot = Node('snapshots', c, 'textDAT')
        docs = Node('docs', c)
        doc = Node('fn_snapshots_md', docs, 'textDAT')
        for node in (snapshot, docs, doc):
            node.nodeWidth, node.nodeHeight = 100, 60
        plans = cleanup.plan(c)
        self.assertEqual({p['path']: set(p['positions']) for p in plans},
                         {c.path: {'snapshots', 'docs'}, docs.path: {'fn_snapshots_md'}})
        embed = load('owned_snapshot_docs', SOURCE/'scripts/td_project_docs.py')
        payload = embed.read_project_docs(SOURCE)
        self.assertEqual(dict(payload['functions'])['snapshots'],
                         (SOURCE/'docs/functions/snapshots.md').read_text())

    def test_headless_publication_open_and_local_reinit_do_not_recall_or_change_library(self):
        e, manager, pars = snapshots.SnapshotTests().fixture()
        c, w, model, views = fixture()
        old_owner = e.ownerComp
        tree_op = c.op
        c.fetch, c.store, c.par = old_owner.fetch, old_owner.store, old_owner.par
        c.op = lambda name: tree_op(name) or old_owner.op(name)
        e.ownerComp = c
        manager.owner = c
        for name in ('GetLayoutContext', 'GetLayouts', 'GetCompContext', 'GetActions'):
            setattr(c, name, getattr(e, name))
        c.ext.RotoPythonExt = e
        Node('owned_runtime', w, 'textDAT').module = runtime
        Node('inspector_data', w, 'textDAT').module = load(
            'snapshot_headless_data', SOURCE/'code/py/roto_python/inspector/inspector_data.py')
        for name in ('targets', 'database', 'context_state'):
            Node(name, w, 'textDAT')
        preset = e.SaveSnapshot('Owned Knobs')
        e.AssignAction(1, preset['id'])
        saved = copy.deepcopy(e._snapshot_manager().database())
        definitions = copy.deepcopy(manager.record()['targets'])
        values = [p.eval() for p in pars]
        e._publish_inspector(force=True)
        self.assertEqual(w.fetch('refresh_error'), '')
        self.assertIn(preset['id'], w.op('targets').text)
        self.assertIn(preset['id'], w.op('database').text)
        self.assertIn(preset['id'], str(json.loads(w.op('context_state').text)['actions']))
        e.onParPulse(S(name='Openinspector'))
        views[0].ext.InspectorView.Show.assert_called_once()
        runtime.initialize(c)
        runtime.validate(c)
        # Rebuild saved providers with the accepted shared registration lifecycle.
        e._restore_actions()
        e._publish_inspector(force=True)
        self.assertTrue(e.GetActionState(preset['id'])['available'])
        self.assertEqual(e._snapshot_manager().database(), saved)
        self.assertEqual(manager.record()['targets'], definitions)
        self.assertEqual([p.eval() for p in pars], values)
        self.assertEqual([p.writes for p in pars], [[], [], [], []])
        self.assertIsNone(w.op('lister'))
        self.assertIsNone(w.op('title'))
        # The same composition on a disposable fake clone uses both sanitizers.
        for view in views:
            view.ext.InspectorView._editors = (view.op('editor'),)
        reset_mapping_storage(c)
        reset_registration(c)
        runtime.sanitize(c)
        self.assertEqual(c.fetch('snapshot_presets'), dict(version=2, records=[], deleted=[]))
        self.assertEqual(e.GetActions(), [])
        self.assertEqual([p.writes for p in pars], [[], [], [], []])
        for view in views:
            self.assertEqual(view.op('base_draft').par.Destination, '')


if __name__ == '__main__':
    unittest.main()
