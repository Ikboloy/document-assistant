import unittest
from evaluate import evaluate, score_ranking


class EvaluationTests(unittest.TestCase):
    def test_known_ranking_and_duplicate_pages(self):
        score = score_ranking([9, 2, 2, 3], [2, 4])
        self.assertEqual(score['recall'], 0.5)
        self.assertAlmostEqual(score['precision'], 1 / 3)
        self.assertEqual(score['reciprocal_rank'], 0.5)

    def test_empty_and_unanswerable(self):
        self.assertEqual(score_ranking([], [1])['reciprocal_rank'], 0)
        self.assertFalse(score_ranking([], [])['false_positive'])
        self.assertTrue(score_ranking([1], [])['false_positive'])

    def test_benchmark_reports_all_queries_without_api(self):
        result = evaluate()
        self.assertEqual(len(result['queries']), 8)
        self.assertEqual(result['answerable_queries'], 6)
        self.assertEqual(result['unanswerable_queries'], 2)
        for key in ['mean_page_recall', 'mean_page_precision', 'mean_reciprocal_rank', 'unanswerable_retrieval_rate']:
            self.assertTrue(0 <= result[key] <= 1)
        with self.assertRaises(ValueError):
            evaluate(0)
