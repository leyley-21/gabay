import unittest
from evaluate_weights import evaluate
from app.recommendation.engine import RankingWeights

class EvaluationTests(unittest.TestCase):
    def sample(self):
        jobs=[{'code':str(i)} for i in range(5)]
        return [({'profile_id':split,'participant_code':split,'split':split,
                  'ratings':{str(i):3 if i<4 else 0 for i in range(5)}},
                 {'current':jobs,'interests_only':list(reversed(jobs))}) for split in ('development','test')]
    def test_metrics_and_no_automatic_deployment(self):
        result=evaluate(self.sample())
        self.assertEqual(result['splits']['test']['current']['mean_precision_at_5'],.8)
        self.assertGreater(result['splits']['test']['current']['mean_ndcg_at_5'],result['splits']['test']['interests_only']['mean_ndcg_at_5'])
        self.assertEqual(result['status'],'comparison_only_not_automatic_validation')
    def test_missing_reviews_rejected(self):
        sample=self.sample();del sample[0][0]['ratings']['0']
        with self.assertRaises(ValueError):evaluate(sample)
    def test_test_split_required(self):
        with self.assertRaises(ValueError):evaluate(self.sample()[:1])
    def test_weights_reject_nonfinite_and_negative(self):
        for value in (-1,float('nan'),float('inf'),True):
            with self.assertRaises(ValueError): RankingWeights(interest=value)
