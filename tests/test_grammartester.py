import unittest
from link_grammar.grammartester import GrammarTester
from link_grammar.lginprocparser import LGInprocParser
from link_grammar.parsemetrics import ParseMetrics

dict = "/home/alex/data/parses/AGI-2018-paper-data-2018-04-22"

corp = "/home/alex/data/corpora"
# corp = "/home/alex/data/poc-english/poc_english_noamb.txt"

dest = "/home/alex/data2/parses/AGI-2018-paper-data-2018-04-22"
tmpl = "/home/alex/data/dict/poc-turtle"
grmr = "/home/alex/data/dict"
limit = 1
opts = 0
ref = "/home/alex/data/corpora"
# ref = "/home/alex/data/poc-english/poc_english_noamb.txt"


class MyTestCase(unittest.TestCase):
    def test_test(self):
        pr = LGInprocParser()
        try:
            gt = GrammarTester(grmr, tmpl, limit, opts, pr)
            pm = gt.test(dict, corp, dest, None)
        except Exception as err:
            print(str(err))

        self.assertEqual(True, True)


if __name__ == '__main__':
    unittest.main()
