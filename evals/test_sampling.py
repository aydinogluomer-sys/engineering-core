import unittest

from evals.sampling import sample_assessment, wilson_interval


class SamplingTests(unittest.TestCase):
    def test_known_interval_and_edges(self):
        low, high = wilson_interval(16, 20)
        self.assertLess(low, 0.8)
        self.assertGreater(high, 0.8)
        self.assertIsNone(wilson_interval(2, 1))
        self.assertIsNone(wilson_interval(True, 2))

    def test_small_samples_are_limited(self):
        self.assertFalse(sample_assessment(3, 3)["sample_adequate"])
        self.assertTrue(sample_assessment(18, 20)["sample_adequate"])


if __name__ == "__main__":
    unittest.main()
