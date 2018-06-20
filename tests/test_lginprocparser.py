import unittest
import sys
from link_grammar.inprocparser import parse_batch_ps_output, parse_file_with_lgp, parse_file_with_lgp0
from grammar_test.optconst import *
from grammar_test.lginprocparser import LGInprocParser

lg_post_output = """
echo set to 1
postscript set to 1
graphics set to 0
verbosity set to 0
tuna has fin .
[(LEFT-WALL)(tuna)(has)(fin)(.)]
[[0 1 0 (C05C02)][1 2 0 (C02C01)][2 3 0 (C01C04)][3 4 0 (C04C03)]]
[0]

eagle isa bird .
[(LEFT-WALL)(eagle)(isa)(bird)(.)]
[[0 1 0 (C05C02)][1 2 0 (C02C01)][2 3 0 (C01C06)][3 4 0 (C06C03)]]
[0]

fin isa extremity .
[(LEFT-WALL)(fin)(isa)(extremity)(.)]
[[0 1 0 (C05C04)][1 2 0 (C04C01)][2 3 0 (C01C06)][3 4 0 (C06C03)]]
[0]

tuna isa fish .
[(LEFT-WALL)(tuna)(isa)(fish)(.)]
[[0 1 0 (C05C02)][1 2 0 (C02C01)][2 3 0 (C01C06)][3 4 0 (C06C03)]]
[0]

fin has scale .
[(LEFT-WALL)(fin)([has])(scale)(.)]
[[0 1 0 (C05C04)][1 3 0 (C04C04)][3 4 0 (C04C03)]]
[0]

eagle has wing .
[(LEFT-WALL)(eagle)(has)(wing)(.)]
[[0 1 0 (C05C02)][1 2 0 (C02C01)][2 3 0 (C01C04)][3 4 0 (C04C03)]]
[0]

wing has feather .
[(LEFT-WALL)(wing)([has])(feather)(.)]
[[0 1 0 (C05C04)][1 3 0 (C04C04)][3 4 0 (C04C03)]]
[0]

wing isa extremity .
[(LEFT-WALL)(wing)(isa)(extremity)(.)]
[[0 1 0 (C05C04)][1 2 0 (C04C01)][2 3 0 (C01C06)][3 4 0 (C06C03)]]
[0]

herring isa fish .
[(LEFT-WALL)(herring)(isa)(fish)(.)]
[[0 1 0 (C05C02)][1 2 0 (C02C01)][2 3 0 (C01C06)][3 4 0 (C06C03)]]
[0]

herring has fin .
[(LEFT-WALL)(herring)(has)(fin)(.)]
[[0 1 0 (C05C02)][1 2 0 (C02C01)][2 3 0 (C01C04)][3 4 0 (C04C03)]]
[0]

parrot isa bird .
[(LEFT-WALL)(parrot)(isa)(bird)(.)]
[[0 1 0 (C05C02)][1 2 0 (C02C01)][2 3 0 (C01C06)][3 4 0 (C06C03)]]
[0]

parrot has wing .
[(LEFT-WALL)(parrot)(has)(wing)(.)]
[[0 1 0 (C05C02)][1 2 0 (C02C01)][2 3 0 (C01C04)][3 4 0 (C04C03)]]
[0]

Bye.
"""

class LGInprocParserTestCase(unittest.TestCase):
    # @unittest.skip
    def test_parse_batch_ps_output(self):
        pr = LGInprocParser()
        num_sent = len(pr._parse_batch_ps_output(lg_post_output))
        self.assertEqual(num_sent, 12, "'parse_batch_ps_output()' returns '{}' instead of '{}'".format(num_sent, 12))

    # @unittest.skip
    def test_parse_file_with_lgp(self):
        """ Test 'parse_file_with_lgp' with default dictionary """
        # print(__doc__, sys.stderr)

        # Testing over poc-turtle corpus... 100% success is expected.
        options = 0 | BIT_STRIP

        metrics = parse_file_with_lgp("test-data/dict/poc-turtle", "test-data/corpora/poc-turtle/poc-turtle.txt",
                             None, 1, options)

        self.assertEqual(1.0, metrics.completely_parsed_ratio)
        self.assertEqual(0.0, metrics.completely_unparsed_ratio)
        self.assertEqual(1.0, metrics.average_parsed_ratio)

    # @unittest.skip
    def test_parse_file_with_lgp_cmp(self):
        """ Make sure 'parse_file_with_lgp' and 'parse_file_with_lgp0' produce the same results. """
        # print(__doc__, sys.stderr)

        pr = LGInprocParser()

        # Testing over poc-turtle corpus... 100% success is expected.
        options = 0 | BIT_STRIP

        # Test if two functions return the same results.
        tup_lgp = parse_file_with_lgp0("test-data/dict/poc-turtle", "test-data/corpora/poc-turtle/poc-turtle.txt",
                                      None, 1, options)

        metrics = pr.parse("test-data/dict/poc-turtle", "test-data/corpora/poc-turtle/poc-turtle.txt", None,
                                      None, options)

        print(tup_lgp, sys.stderr)
        print(metrics.text(metrics), sys.stderr)

        self.assertEqual(tup_lgp[0], metrics.completely_parsed_ratio)
        self.assertEqual(tup_lgp[1], metrics.completely_unparsed_ratio)
        self.assertEqual(tup_lgp[2], metrics.average_parsed_ratio)


if __name__ == '__main__':
    unittest.main()
