import unittest
import sys

try:
    from link_grammar.parsestat import calc_parse_quality, parse_quality, calc_stat, parse_metrics
    from link_grammar.parsemetrics import ParseQuality

except ImportError:
    from parsestat import calc_parse_quality, parse_quality, calc_stat, parse_metrics
    from parsemetrics import ParseQuality


# Token indexes
LWALL = 0; tuna = 1; isa = 2; fish = 3; DOT = 4; RWALL = 5

# Reference set
ref_set =   {(LWALL, DOT), (LWALL, isa), (LWALL, tuna), (tuna, isa), (isa, fish), (fish, DOT)}

# Equal set (0, 0, 1.0)
test_set1 = {(LWALL, DOT), (LWALL, isa), (LWALL, tuna), (tuna, isa), (isa, fish), (fish, DOT)}

# Three link missing set (3, 0, 0.5)
test_set2 = {(LWALL, DOT), (LWALL, isa), (LWALL, tuna)}

# One extra link (0, 1, 1.0)
test_set3 = {(LWALL, DOT), (LWALL, isa), (LWALL, tuna), (tuna, isa), (isa, fish), (fish, DOT), (DOT, RWALL)}

# Three different links (3, 3, 0.5)
test_set4 = {(LWALL, DOT), (LWALL, fish), (LWALL, tuna), (tuna, DOT), (isa, fish), (isa, DOT)}


# Token indexes
a1 = 1; dad = 2; is2 = 3; a2 = 4; human = 5; DOT2 = 6

ref_set5 = {(a1, dad), (dad, is2), (is2, human), (a2, human)}
# ref_set5 = {(LWALL, dad), (LWALL, is2), (LWALL, DOT2), (a1, dad), (dad, is2), (is2, human), (a2, human)}

# Three different links (3, 0, 0.55)
test_set5 = {(dad, is2), (a2, human)}
# test_set5 = {(LWALL, dad), (dad, a2), (a2, human)}


class TestStat(unittest.TestCase):

    def test_calc_parse_quality_equal(self):
        """ Equal set test """
        (m, e, q) = calc_parse_quality(test_set1, ref_set)

        self.assertEqual((0, 0, 1.0), (m, e, q))

    def test_calc_parse_quality_three_missing(self):
        """ Three missing links test """
        (m, e, q) = calc_parse_quality(test_set2, ref_set)

        self.assertEqual((3, 0, 0.5), (m, e, q))

    def test_calc_parse_quality_one_extra(self):
        """ One extra link test """
        (m, e, q) = calc_parse_quality(test_set3, ref_set)

        self.assertEqual((0, 1, 1.0), (m, e, q))

    def test_calc_parse_quality_three_different(self):
        """ Three different links test """
        (m, e, q) = calc_parse_quality(test_set4, ref_set)

        self.assertEqual((3, 3, 0.5), (m, e, q))

    # @unittest.skip
    def test_calc_parse_quality_bug_found(self):
        """ Three different links test """
        (m, e, q) = calc_parse_quality(test_set5, ref_set5)

        self.assertEqual((2, 0, 0.5), (m, e, q))

    def test_parse_quality_cmp(self):
        (m, e, q) = calc_parse_quality(test_set5, ref_set5)
        pq = parse_quality(test_set5, ref_set5)
        self.assertEqual(m, pq.missing)
        self.assertEqual(e, pq.extra)
        self.assertEqual(q, pq.quality)

    @unittest.skip
    def test_calc_stat(self):
        """ test_calc_stat """
        # print(__doc__, sys.stderr)

        f, n, s = calc_stat(['###LEFT-WALL###', 'dad', 'was', 'not', 'a', 'parent', 'before', '.'])
        # print(f, n, s)
        self.assertTrue(f and (not n) and (s > 0.99))

        f, n, s = calc_stat(['[qqq]', '[www]', '[eee]', '[rrr]', '[ttt]', '[yyy]', '[uuu]', '[.]'])
        # print(f, n, s)
        self.assertTrue(n and (not f) and (s < 0.1))

        f, n, s = calc_stat(['###LEFT-WALL###', 'dad', 'was', 'not', '[a]', '[parent]', '[before]'])
        # print(f, n, s)
        self.assertTrue((not f) and (not n) and (s - 0.5 < 0.01))

    def test_calc_stat_4(self):
        f, n, s = calc_stat(["###LEFT-WALL###", "[a]", "dad", "is", "[a]", "human", "[.]"])
        # print(f, n, s, file=sys.stderr)
        self.assertTrue((not f) and (not n) and (s == 0.6))

    def test_parse_stat_cmp(self):
        f, n, s = calc_stat(["###LEFT-WALL###", "[a]", "dad", "is", "[a]", "human", "[.]"])
        pm = parse_metrics(["###LEFT-WALL###", "[a]", "dad", "is", "[a]", "human", "[.]"])
        self.assertEqual(f, pm.completely_parsed_ratio, "'completely_parsed_ratio' mismatch")
        self.assertEqual(n, pm.completely_unparsed_ratio, "'completely_unparsed_ratio' mismatch")
        self.assertEqual(s, pm.average_parsed_ratio, "'average_parsed_ratio' mismatch")


if __name__ == '__main__':
    unittest.main()
