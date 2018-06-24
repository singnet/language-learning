import unittest
from grammar_test.grammartester import GrammarTester, test_grammar
from grammar_test.lginprocparser import LGInprocParser
from grammar_test.optconst import *

import cProfile

from common.fileconfman import JsonFileConfigManager
from common.cliutils import handle_path_string
from grammar_test.textfiledashb import TextFileDashboard

# dict = "/usr/local/share/link-grammar/en"
# dict = "en"
# dict = "poc-turtle"

# corp = "/home/alex/data/corpora"
# corp = "/home/alex/data/poc-english/poc_english_noamb.txt"
# corp = "/home/alex/data/corpora/Children_Gutenberg_cleaned/pg24878.txt_split_default"
# corp = "/var/tmp/lang-learn/pg24878.txt_split_default"
# corp = "/home/alex/data/corpora/cleaned_Gutenberg_Children/pg24878.txt_headless_split_e"
# corp = "/home/alex/data/corpora/cleaned_Gutenberg_Children"
# corp = "/home/alex/data/corpora/poc-english-multi"
# corp = "/home/alex/data/corpora/poc-english/poc_english.txt"

# dest = "/home/alex/data2/parses/AGI-2018-paper-data-2018-04-22"
# dest = "/home/alex/data2/parses/cleaned_Gutenberg_Children"
# dest = "/home/alex/data2/parses"
# dest = "/var/tmp/lang-learn"

tmpl = "/home/alex/data/dict/poc-turtle"
grmr = "/home/alex/data/dict"
limit = 100
opts = BIT_SEP_STAT | BIT_LG_EXE | BIT_NO_LWALL | BIT_NO_PERIOD | BIT_STRIP | BIT_RM_DIR #| BIT_DPATH_CREATE | BIT_LOC_LANG | BIT_PARSE_QUALITY #| BIT_ULL_IN #| BIT_OUTPUT_DIAGRAM #| BIT_SEP_STAT

# # Gutenberg Children Parses
# dict = "en"
# corp = "/home/alex/data/corpora/cleaned_Gutenberg_Children"
# dest = "/home/alex/data2/parses/cleaned_Gutenberg_Children_ref"
# ref = None


# # Gutenberg Children Parses
# dict = "/home/alex/data2/parses/Gutenberg-Children-2018-05-30"
# corp = "/home/alex/data/corpora/cleaned_Gutenberg_Children"
# dest = "/home/alex/data2/parses/Gutenberg-Children-2018-05-30"
# ref = "/home/alex/data2/parses/cleaned_Gutenberg_Children_ref"
# # ref = None


# ref = "/home/alex/data/corpora"
# ref = "/home/alex/data/poc-english/poc_english_noamb_parse_ideal.txt"
# ref = None

# # Parseability test
# dict = "poc-turtle"
# # dict = "en"
# # corp = "/home/alex/data/corpora/poc-english-multi"
# corp = "/home/alex/data/corpora/poc-english-one"
# # corp = "/home/alex/data/corpora/poc-english/poc_english.txt"
# dest = "/home/alex/data2/parses"
# # ref = "/home/alex/data2/parses"
# # ref = "/home/alex/data2/parses/poc_english.txt.ref"
# ref = None

# # AGI-2018 Test
# dict = "/home/alex/data2/parses/AGI-2018-paper-data-2018-04-22/POC-English-NoAmb-LEFT-WALL+period"
# corp = "/home/alex/data/poc-english/poc_english_noamb.txt"
# dest = "/home/alex/data2/parses/AGI-2018-paper-data-2018-04-22/POC-English-NoAmb-LEFT-WALL+period"
# ref = "/home/alex/data/poc-english/poc_english_noamb_parse_ideal.txt"

# # Gutenberg-Alice-2018-06-01 parse for ULL reference
# dict = "en"
# corp = "/home/alex/data2/parses/Gutenberg-Alice-2018-06-01/alice_11-0_txt_split_default.txt"
# dest = "/home/alex/data2/parses/Gutenberg-Alice-2018-06-01/parses"
# ref = None

# # Gutenberg-Alice-2018-06-01 parse and validation with multiple dictionaries
# dict = "/home/alex/data2/parses/Gutenberg-Alice-2018-06-01"
# corp = "/home/alex/data2/parses/Gutenberg-Alice-2018-06-01/alice_11-0_txt_split_default.txt"
# dest = "/home/alex/data2/parses/Gutenberg-Alice-2018-06-01"
# ref = "/home/alex/data2/parses/Gutenberg-Alice-2018-06-01/parses/alice_11-0_txt_split_default.txt.ull"
# # ref = None

# # Child Directed Speech
# dict = "en"
# # dict = "/home/alex/data2/parses/Gutenberg-Alice-2018-06-01"
# corp = "/home/alex/data/corpora/ChildDirectedSpeech"
# dest = "/home/alex/data2/parses/ChildDirectedSpeech"
# # ref = "/home/alex/data2/parses/Gutenberg-Alice-2018-06-01/parses/alice_11-0_txt_split_default.txt.ull"
# ref = None



# # PubMed-2018-06-01 parse for ULL reference
# dict = "en"
# corp = "/home/alex/data2/parses/PubMed-2018-06-01/data"
# dest = "/home/alex/data2/parses/PubMed-2018-06-01/ref"
# ref = None

CONF_DICT_PATH = "input_grammar"
CONF_CORP_PATH = "input_corpus"
CONF_DEST_PATH = "output_path"
CONF_REFR_PATH = "ref_path"
CONF_GRMR_PATH = "grammar_root"
CONF_TMPL_PATH = "template_path"
CONF_LNK_LIMIT = "linkage_limit"


class GrammarTesterTestCase(unittest.TestCase):

    # @unittest.skip
    def test_test_with_conf(self):
        conf_path = "test-data/config/AGI-2018.json"

        try:
            cfgman = JsonFileConfigManager(conf_path)
            dboard = TextFileDashboard(cfgman)
            parser = LGInprocParser()

            # Get configuration parameters
            config = cfgman.get_config("", "grammar-tester")

            # Create GrammarTester instance
            tester = GrammarTester(handle_path_string(config[0][CONF_GRMR_PATH]),
                                   handle_path_string(config[0][CONF_TMPL_PATH]),
                                   config[0][CONF_LNK_LIMIT], opts, parser, dboard)

            cfg = config[0]
            # for cfg in config:

            # Run grammar test
            pm, pq = tester.test(handle_path_string(cfg[CONF_DICT_PATH]), handle_path_string(cfg[CONF_CORP_PATH]),
                                 handle_path_string(cfg[CONF_DEST_PATH]), handle_path_string(cfg[CONF_REFR_PATH]))

            dboard.update_dashboard()

            print(pm.text(pm))

        except Exception as err:
            print(str(err))

        # self.assertEqual(25, gt._total_dicts)
        # self.assertEqual(88, pm.sentences)

    @unittest.skip
    def test_test(self):
        pr = LGInprocParser()

        gt = GrammarTester(grmr, tmpl, limit, opts, pr)
        pm, pq = gt.test(dict, corp, dest, ref)

        print(pm.text(pm))

        # self.assertEqual(25, gt._total_dicts)
        self.assertEqual(88, pm.sentences)

    @unittest.skip
    def test_test_grammar(self):
        file_name = "/var/tmp/test-grammar-stats"

        def run_test():
            test_grammar(corp, dest, dict, grmr, tmpl, limit, opts, ref)
            return ""

        cProfile.run(run_test())

        # cProfile.run(print("!!!!!!"))
        # p = pstats.Stats(file_name)
        # p.strip_dirs().sort_stats(-1).print_stats()
        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()
