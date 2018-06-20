import unittest

from grammar_test.lgapiparser import *
from grammar_test.optconst import *
from grammar_test.lginprocparser import LGInprocParser


class LGAPITestCase(unittest.TestCase):

    def test_parse_file_with_api(self):
        # Testing over poc-turtle corpus... 100% success is expected.

        options = BIT_NO_LWALL | BIT_NO_PERIOD | BIT_STRIP | BIT_RM_DIR | BIT_LOC_LANG | BIT_PARSE_QUALITY

        lgp = LGInprocParser()
        api = LGApiParser()

        dict = "en"
        corp = "test-data/corpora/poc-english/poc_english.txt"
        reff = "test-data/corpora/poc-english/poc_english_parses_lg.txt"
        outp = "test-data/temp"
        # reff = None

        # dict = "test-data/dict/poc-turtle"
        # corp = "test-data/corpora/poc-turtle/poc-turtle.txt"
        # outp = "test-data/temp"
        # reff = None

        m1, q1 = lgp.parse(dict, corp, outp, reff, options)
        m2, q2 = api.parse(dict, corp, outp, reff, options)


        self.assertTrue(m1 == m2)

        print(q1.text(q1))
        print(q2.text(q2))

        self.assertTrue(q1 == q2)


        # api_metrics = parse_file_with_api("test-data/dict/poc-turtle", "test-data/corpora/poc-turtle/poc-turtle.txt",
        #                               None, 1, options)
        #
        # print(ParseMetrics.text(api_metrics), sys.stderr)
        #
        # self.assertEqual(1.0, api_metrics.completely_parsed_ratio)
        # self.assertEqual(0.0, api_metrics.completely_unparsed_ratio)
        # self.assertEqual(1.0, api_metrics.average_parsed_ratio)


if __name__ == '__main__':
    unittest.main()
