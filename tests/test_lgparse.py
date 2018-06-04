import unittest
import sys

# try:
#     from link_grammar.lgapiparser import parse_file_with_api
#     from link_grammar.lgparse import print_output, create_grammar_dir, LGParseError
#     from link_grammar.optconst import *
#     from link_grammar.inprocparser import parse_batch_ps_output, parse_file_with_lgp
#     from link_grammar.parsemetrics import ParseMetrics, ParseQuality
#
# except ImportError:
#     from lgapiparser import parse_file_with_api
#     from lgparse import print_output, create_grammar_dir, LGParseError
#     from optconst import *
#     from inprocparser import parse_batch_ps_output, parse_file_with_lgp
#     from parsemetrics import ParseMetrics, ParseQuality

from grammartest import *
# from grammartest import parse_file_with_api, print_output, LGParseError, parse_file_with_lgp, ParseMetrics, ParseQuality
# from .lgparse import , create_grammar_dir
# from .optconst import *
# from .inprocparser import parse_batch_ps_output

class TestStringMethods(unittest.TestCase):
    """ TestStringMethods """

    @staticmethod
    def cmp_lists(list1, list2) -> bool:
        if list1 is None or list2 is None or len(list1) != len(list2):
            return False

        for i in range(0, len(list1)):
            if list1[i] != list2[i]:
                return False

        return True

    # @unittest.skip
    def test_parse_file_with_api_ordinary(self):
        """ Test parse with default dictionary """
        print(__doc__, sys.stderr)

        # Testing over poc-turtle corpus... 100% success is expected.
        options = 0 | BIT_STRIP
        metrics = parse_file_with_api("test-data/dict/poc-turtle", "test-data/corpora/poc-turtle/poc-turtle.txt",
                             None, 1, options)

        self.assertEqual(1.0, metrics.completely_parsed_ratio)
        self.assertEqual(0.0, metrics.completely_unparsed_ratio)
        self.assertEqual(1.0, metrics.average_parsed_ratio)

    # @unittest.skip
    def test_parse_file_with_api_ull(self):

        # Testing over poc-turtle corpus retreaved from MST-parser links output. 100% success is expected.
        options = 0 | BIT_STRIP | BIT_ULL_IN
        metrics = parse_file_with_api("test-data/dict/poc-turtle",
                             "test-data/parses/poc-turtle-mst/poc-turtle-opencog-mst-parses.txt",
                             None, 1, options)

        self.assertEqual(1.0, metrics.completely_parsed_ratio)
        self.assertEqual(0.0, metrics.completely_unparsed_ratio)
        self.assertEqual(1.0, metrics.average_parsed_ratio)

    # @unittest.skip
    def test_parse_file_with_api_eng(self):

        options = 0 | BIT_STRIP | BIT_ULL_IN

        # Testing over poc-english corpus retreaved from hand coded links
        metrics = parse_file_with_api("en", "test-data/parses/poc-english-mst/poc_english_noamb_parse_ideal.txt",
                                    None, 1, options)

        self.assertEqual(1.0, metrics.completely_parsed_ratio)
        self.assertEqual(0.0, metrics.completely_unparsed_ratio)
        self.assertEqual(1.0, metrics.average_parsed_ratio)

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

    def test_parse_file_with_lgp_vs_api(self):
        """ Test 'parse_file_with_lgp' with default dictionary """
        # print(__doc__, sys.stderr)

        # Testing over poc-turtle corpus... 100% success is expected.
        options = 0 | BIT_STRIP | BIT_NO_LWALL

        api_metrics = parse_file_with_api("test-data/dict/poc-turtle", "test-data/corpora/poc-turtle/poc-turtle.txt",
                                      None, 1, options)

        lgp_metrics = parse_file_with_lgp("test-data/dict/poc-turtle", "test-data/corpora/poc-turtle/poc-turtle.txt",
                                      None, 1, options)

        print(ParseMetrics.text(api_metrics), sys.stderr)
        print(ParseMetrics.text(lgp_metrics), sys.stderr)

        self.assertEqual(api_metrics.completely_parsed_ratio, lgp_metrics.completely_parsed_ratio)
        self.assertEqual(api_metrics.completely_unparsed_ratio, lgp_metrics.completely_unparsed_ratio)
        self.assertEqual(api_metrics.average_parsed_ratio, lgp_metrics.average_parsed_ratio)

    @unittest.skip
    def test_create_grammar_dir(self):
        self.assertTrue("en" == create_grammar_dir("en", "", "", 0))

        with self.assertRaises(LGParseError) as ctx:
            create_grammar_dir("/home/alex/en", "", "", 0)

        self.assertEqual("Dictionary path does not exist.", str(ctx.exception))


if __name__ == '__main__':
    unittest.main()