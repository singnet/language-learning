import unittest
import sys
from link_grammar.evaluate import *


parse_no_wall = """tuna isa fish . 
0 tuna 1 isa
1 isa 2 fish
2 fish 3 .
"""

parse_with_wall = """tuna isa fish . 
0 ###LEFT-WALL### 1 tuna
1 tuna 2 isa
2 isa 3 fish
3 fish 4 .
"""

# parse_with_wall = """tuna isa fish .
# 0 ###LEFT-WALL### 1 tuna
# 1 tuna 2 isa
# 2 isa 3 fish
# 3 fish 4 .
# """

class TestEvalMethods(unittest.TestCase):

    def test_get_parses(self):
        ref_data = load_ull_file("test-data/parses/poc-turtle-mst/one-parse-expected.txt")
        test_data = load_ull_file("test-data/parses/poc-turtle-mst/one-parse-expected.txt")
        # test_data = Load_File("test-data/parses/poc-turtle-mst/one-parse-no-wall.txt")
        print("ref_data='", ref_data, "'", file=sys.stderr)
        print("test_data='", test_data, "'", file=sys.stderr)
        ref_parses = get_parses(ref_data, True)
        test_parses = get_parses(test_data, True)
        eval_parses(test_parses, ref_parses, False, sys.stderr)
        self.assertEqual(ref_parses, test_parses)

    def test_get_parses_bug(self):
        test_data = load_ull_file("test-data/corpora/poc-english/poc_english_noamb_parses_1s_2.txt")
        test_parses = get_parses(test_data, True)
        # print(test_parses, file=sys.stderr)
        self.assertEqual(2, len(test_parses[0][1]))

        ref_data = load_ull_file("test-data/corpora/poc-english/poc_english_noamb_parses_ideal_1s_2.txt")
        ref_parses = get_parses(ref_data, True)
        # print(ref_parses, file=sys.stderr)
        self.assertEqual(4, len(ref_parses[0][1]))

    def test_compare_ull_files_with_lw(self):
        pq1 = compare_ull_files("test-data/corpora/poc-english/poc_english_noamb_parses_ideal_1s_2.txt",
                                "test-data/corpora/poc-english/poc_english_noamb_parses_ideal_1s_2.txt",
                                False, False)

        # print(pq1.text(pq1), file=sys.stderr)

        self.assertEqual(1.0, pq1.quality)
        self.assertEqual(7.0, pq1.total)
        self.assertEqual(0.0, pq1.ignored)
        self.assertEqual(0.0, pq1.missing)
        self.assertEqual(0.0, pq1.extra)

    def test_compare_ull_files_no_lw(self):
        pq1 = compare_ull_files("test-data/corpora/poc-english/poc_english_noamb_parses_ideal_1s_2.txt",
                                "test-data/corpora/poc-english/poc_english_noamb_parses_ideal_1s_2.txt",
                                False, True)

        # print(pq1.text(pq1), file=sys.stderr)

        self.assertEqual(1.0, pq1.quality)
        self.assertEqual(4.0, pq1.total)
        self.assertEqual(3.0, pq1.ignored)
        self.assertEqual(0.0, pq1.missing)
        self.assertEqual(0.0, pq1.extra)

if __name__ == '__main__':
    unittest.main()