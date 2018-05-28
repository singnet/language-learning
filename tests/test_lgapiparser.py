import unittest
import sys
import types

try:
    from link_grammar.lgapiparser import *
    from link_grammar.parsemetrics import ParseMetrics, ParseQuality
    from link_grammar.optconst import *

except ImportError:
    from lgapiparser import *
    from parsemetrics import ParseMetrics, ParseQuality
    from optconst import *


class LGAPITestCase(unittest.TestCase):

    def test_parse_file_with_api(self):
        # Testing over poc-turtle corpus... 100% success is expected.

        # print(type(parse_file_with_api))
        #
        # print(isinstance(parse_file_with_api, types.FunctionType))
        # print(callable(parse_file_with_api))


        options = 0 | BIT_STRIP | BIT_NO_LWALL

        api_metrics = parse_file_with_api("test-data/dict/poc-turtle", "test-data/corpora/poc-turtle/poc-turtle.txt",
                                      None, 1, options)

        print(ParseMetrics.text(api_metrics), sys.stderr)

        self.assertEqual(1.0, api_metrics.completely_parsed_ratio)
        self.assertEqual(0.0, api_metrics.completely_unparsed_ratio)
        self.assertEqual(1.0, api_metrics.average_parsed_ratio)


if __name__ == '__main__':
    unittest.main()
