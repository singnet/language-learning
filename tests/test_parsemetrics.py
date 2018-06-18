import unittest
import sys

try:
    from link_grammar.parsemetrics import *
except ImportError:
    from parsemetrics import *


class TestMetrics(unittest.TestCase):

    # @unittest.skip
    def test_pm_sum(self):
        pm1 = ParseMetrics()
        pm1.completely_parsed_ratio = 0.5
        pm1.completely_unparsed_ratio = 0.5
        pm1.average_parsed_ratio = 0.5

        pm2 = ParseMetrics()
        pm2.completely_parsed_ratio = 0.2
        pm2.completely_unparsed_ratio = 0.3
        pm2.average_parsed_ratio = 0.5

        pm1 += pm2

        print(ParseMetrics.text(pm1), file=sys.stderr)

        self.assertEqual(0.7, pm1.completely_parsed_ratio)
        self.assertEqual(0.8, pm1.completely_unparsed_ratio)
        self.assertEqual(1.0, pm1.average_parsed_ratio)

    @unittest.skip
    def test_pm_div(self):
        pm1 = ParseMetrics()
        pm1.completely_parsed_ratio = 1.0
        pm1.completely_unparsed_ratio = 0.8
        pm1.average_parsed_ratio = 0.6

        pm1 /= 2

        self.assertEqual(0.5, pm1.completely_parsed_ratio)
        self.assertEqual(0.4, pm1.completely_unparsed_ratio)
        self.assertEqual(0.3, pm1.average_parsed_ratio)

    def test_pq_add(self):
        pq1 = ParseQuality()
        pq1.missing = 0.5
        pq1.extra = 0.4
        pq1.ignored = 0.3
        pq1.total = 0.2
        pq1.quality = 0.1
        
        
        pq2 = ParseQuality()
        pq2.missing = 0.5
        pq2.extra = 0.4
        pq2.ignored = 0.3
        pq2.total = 0.2
        pq2.quality = 0.1

        pq1 += pq2

        print(ParseQuality.text(pq1), file=sys.stderr)

        # Make sure that all the member variables of the first instance have been incremented
        self.assertEqual(1.0, pq1.missing)
        self.assertEqual(0.8, pq1.extra)
        self.assertEqual(0.6, pq1.ignored)
        self.assertEqual(0.4, pq1.total)
        self.assertEqual(0.2, pq1.quality)

        # Make sure that the second instance members have had the same values
        self.assertEqual(0.5, pq2.missing)
        self.assertEqual(0.4, pq2.extra)
        self.assertEqual(0.3, pq2.ignored)
        self.assertEqual(0.2, pq2.total)
        self.assertEqual(0.1, pq2.quality)

    @unittest.skip
    def test_pq_div(self):
        pq1 = ParseQuality()
        pq1.missing = 0.8
        pq1.extra = 0.6
        pq1.ignored = 0.4
        pq1.total = 0.2
        pq1.quality = 0.0

        pq1 /= 2

        self.assertEqual(0.4, pq1.missing)
        self.assertEqual(0.3, pq1.extra)
        self.assertEqual(0.2, pq1.ignored)
        self.assertEqual(0.1, pq1.total)
        self.assertEqual(0.0, pq1.quality)

if __name__ == '__main__':
    unittest.main()