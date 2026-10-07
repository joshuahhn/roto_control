from unittest import TestCase
from acceptance_metrics import Samples,summary,bounded
class AcceptanceMetricsTests(TestCase):
    def test_samples_remain_bounded_and_summarize_recent_window(self):
        samples=Samples(4)
        for i in range(20):samples.add(i)
        self.assertEqual(samples.result()['samples'],4);self.assertEqual(samples.result()['total_samples'],20)
        self.assertEqual(samples.result()['mean'],17.5);self.assertEqual(samples.result()['maximum'],19)
        self.assertEqual(summary([]),dict(samples=0))
    def test_bounds_detect_queues_errors_and_catalog_growth(self):
        s=dict(subscribers=2,cache_contexts=4,source_contexts=4,pending_contexts=4,pending_slots=64,subscriber_errors=[])
        t=dict(pages=32,entries=4096,jobs=2,pending=2,errors=[])
        self.assertTrue(bounded(s,t))
        for field in ('subscribers','cache_contexts','source_contexts','pending_contexts','pending_slots'):
            bad=dict(s);bad[field]+=1;self.assertFalse(bounded(bad,t))
        for field in ('pages','entries','jobs','pending'):
            bad=dict(t);bad[field]+=1;self.assertFalse(bounded(s,bad))
        self.assertFalse(bounded(dict(s,subscriber_errors=['failure']),t))
        self.assertFalse(bounded(s,dict(t,errors=['failure'])))
