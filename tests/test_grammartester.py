import unittest
from link_grammar.grammartester import GrammarTester
from link_grammar.lginprocparser import LGInprocParser
from link_grammar.parsemetrics import ParseMetrics
from link_grammar.optconst import *

# dict = "/home/alex/data/parses/AGI-2018-paper-data-2018-04-22/POC-English-NoAmb-LEFT-WALL+period"
# dict = "/usr/local/share/link-grammar/en"
dict = "en"
# dict = "poc-turtle"

# corp = "/home/alex/data/corpora"
# corp = "/home/alex/data/poc-english/poc_english_noamb.txt"
# corp = "/home/alex/data/corpora/Children_Gutenberg_cleaned/pg24878.txt_split_default"
# corp = "/var/tmp/lang-learn/pg24878.txt_split_default"
# corp = "/home/alex/data/corpora/cleaned_Gutenberg_Children/pg24878.txt_headless_split_e"
# corp = "/home/alex/data/corpora/cleaned_Gutenberg_Children/25301-0.txt_headless_split_e"
corp = "/home/alex/data/corpora/cleaned_Gutenberg_Children"
# corp = "/home/alex/data/corpora/poc-english-multi"
# corp = "/home/alex/data/corpora/poc-english/poc_english.txt"

# dest = "/home/alex/data2/parses/AGI-2018-paper-data-2018-04-22/POC-English-NoAmb-LEFT-WALL+period"
# dest = "/home/alex/data2/parses/AGI-2018-paper-data-2018-04-22"
dest = "/home/alex/data2/parses/cleaned_Gutenberg_Children"
# dest = "/home/alex/data2/parses"
# dest = "/var/tmp/lang-learn"

tmpl = "/home/alex/data/dict/poc-turtle"
grmr = "/home/alex/data/dict"
limit = 1
opts = BIT_NO_LWALL | BIT_NO_PERIOD | BIT_STRIP | BIT_RM_DIR | BIT_LOC_LANG | BIT_PARSE_QUALITY #| BIT_ULL_IN | BIT_SEP_STAT

# ref = "/home/alex/data/corpora"
# ref = "/home/alex/data/poc-english/poc_english_noamb_parse_ideal.txt"
ref = None

class GrammarTesterTestCase(unittest.TestCase):
    def test_test(self):
        pr = LGInprocParser()

        gt = GrammarTester(grmr, tmpl, limit, opts, pr)
        pm, pq = gt.test(dict, corp, dest, ref)

        print(pm.text(pm))

        # self.assertEqual(25, gt._total_dicts)
        self.assertEqual(88, pm.sentences)

if __name__ == '__main__':
    unittest.main()
