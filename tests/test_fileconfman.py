import unittest
import os, sys
from decimal import Decimal

from ull.common.fileconfman import JsonFileConfigManager
from ull.common.parsemetrics import ParseMetrics

conf_path = "test-data/config/config-example-01.json"
# conf_path = "/home/alex/PycharmProjects/language-learning/tests/test-data/config/config-example-01.json"

params = \
      {
        "input_grammar": "./grammar.dict",
        "input_categories": "./cat_tree.txt",
        "parse_format": "ull"
      }

class JsonRWTestCase(unittest.TestCase):

    def test_string_keys(self):
        nodes = ["AFC", "BZ"]
        print(nodes)
        print(tuple(nodes))

        print("{0[0]}{0[1]}".format(nodes))
        print("{1}--{0}".format(*nodes))

        pm = ParseMetrics()
        pm.average_parsed_ratio = Decimal("0.66")
        pm.sentences = 3
        print("{sentences}>>{sentences}>>{parseability}".format(parseability=pm.parseability(pm), sentences=pm.sentences))
        print("{nodes[2]}{nodes[1]}{nodes[0]}".format(nodes=["A", "B", "C"]))
        print("{nodes[1]}>>{sentences}>>{parseability}".format(parseability=pm.parseability(pm), sentences=pm.sentences, nodes=["A", "B", "C"]))

        # print("{0[2:5]}".format("qwertyuio"))

    @unittest.skip
    def test_read_config(self):
        print(os.environ['PWD'], file=sys.stderr)

        cm = JsonFileConfigManager(conf_path)

        cfg = cm.get_config("", "grammar-tester")

        print(cfg)

        self.assertEqual(params, cfg[0])


if __name__ == '__main__':
    unittest.main()
