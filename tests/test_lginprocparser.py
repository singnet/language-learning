import os
import unittest

from src.common.optconst import *
from src.common.textprogress import TextProgress
from src.grammar_tester.lginprocparser import LGInprocParser
from src.grammar_tester import load_parses
from src.grammar_tester.lgmisc import LGParseError, get_dir_name
from src.common.tokencount import update_token_counts

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

lg_post_explosion = \
"""
conclusions : icp-sf-ms is a reliable method of blood analysis for cd , mn and pb even for the evaluation on an individual basis.
by comparing eyebrow shape and position in both young and mature women , this study provides objective data with which to plan forehead rejuvenating procedures.
the odds of being overweight in adulthood was @number@ times greater ( @percent@ ci : @date@ @number@ ) in overweight compared with healthy weight youth.
holocaust survivors did not differ in the level of resilience from comparisons ( mean : @number@ ± @number@ vs. @number@ ± @number@ respectively ) .
[(LEFT-WALL)(holocaust.n)(survivors.n)(did.v-d)(not.e)(differ.v)(in.r)(the)(level.n)(of)
(resilience.n-u)(from)(comparisons.n)(()(mean.a)([:])(@number@[?].n)(±[?].n)(@number@[?].n)(vs.)
(@number@[?].n)(±[?].n)(@number@[?].n)([respectively])())(.)]
[[0 25 4 (Xp)][0 5 2 (WV)][0 2 1 (Wd)][1 2 0 (AN)][2 3 0 (Sp)][3 5 1 (I*d)][3 4 0 (N)]
[4 5 0 (En)][5 11 2 (MVp)][5 6 0 (MVp)][6 8 1 (Js)][7 8 0 (Ds**c)][8 9 0 (Mf)][9 10 0 (Jp)]
[10 11 0 (Mp)][11 12 0 (Jp)][12 18 3 (MXp)][13 18 2 (Xd)][14 18 1 (A)][17 18 0 (AN)][16 17 0 (AN)]
[18 24 3 (Xc)][18 19 0 (Mp)][19 22 2 (Jp)][20 22 1 (AN)][21 22 0 (AN)]]
[0]
"""

sharp_sign_linkage = \
"""
postscript set to 1
graphics set to 0
echo set to 1
verbosity set to 1
link-grammar: Info: Dictionary found at /home/aglushchenko/anaconda3/envs/ull-lg551/share/link-grammar/en/4.0.dict
link-grammar: Info: Dictionary version 5.5.1, locale en_US.UTF-8
link-grammar: Info: Library version link-grammar-5.5.1. Enter "!help" for help.
But there still remained all the damage that had been done that day , and the king had nothing with which to pay for this.
No complete linkages found.
Found 8706604 linkages (4 of 1000 random linkages had no P.P. violations) at null count 3
	Linkage 1, cost vector = (UNUSED=3 DIS= 7.85 LEN=84)
[(LEFT-WALL)(but.ij)(there.#their)(still.n)(remained.v-d)(all.a)(the)(damage.n-u)(that.j-p)(had.v-d)
(been.v)([done])(that.j-r)(day.r)(,)(and.ij)(the)(king.n)(had.v-d)(nothing)
([with])([which])(to.r)(pay.v)(for.p)(this.p)(.)]
[[0 26 6 (Xp)][0 23 5 (WV)][0 15 4 (Xx)][0 10 3 (WV)][0 1 0 (Wc)][1 4 2 (WV)][1 3 1 (Wdc)]
[3 4 0 (Ss*s)][2 3 0 (Ds**c)][4 5 0 (O)][5 7 1 (Ju)][7 10 1 (Bs*t)][5 6 0 (ALx)][6 7 0 (Dmu)]
[7 8 0 (Rn)][8 9 0 (Ss*b)][9 10 0 (PPf)][10 13 1 (MVpn)][12 13 0 (DTn)][14 15 0 (Xd)][15 18 2 (WV)]
[15 17 1 (Wdc)][17 18 0 (Ss*s)][16 17 0 (Ds**c)][18 22 1 (MVi)][22 23 0 (I)][18 19 0 (Os)][23 24 0 (MVp)]
[24 25 0 (Js)]]
[0]
"""

explosion_no_linkages = \
"""
echo set to 1
postscript set to 1
graphics set to 0
verbosity set to 1
timeout set to 1
limit set to 100
But there still remained all the damage that had been done that day , and the king had nothing with which to pay for this.
No complete linkages found.
Timer is expired!
Entering "panic" mode...
link-grammar: Warning: Combinatorial explosion! nulls=5 cnt=27061933
Consider retrying the parse with the max allowed disjunct cost set lower.
At the command line, use !cost-max
Found 27061933 linkages (0 of 100 random linkages had no P.P. violations) at null count 5
Bye.
"""


merged_ps_parses = \
"""
There the train was coming mother was holding Jem's hand Dog Monday was licking it everybody was saying good-bye the train was in !
No complete linkages found.
Found 38230999 linkages (0 of 1000 random linkages had no P.P. violations) at null count 2
They had gone.
Found 2 linkages (2 had no P.P. violations)
        Linkage 1, cost vector = (UNUSED=0 DIS= 0.00 LEN=5)
[(LEFT-WALL)(they)(had.v-d)(gone.v)(.)]
[[0 4 2 (Xp)][0 3 1 (WV)][0 1 0 (Wd)][1 2 0 (Sp)][2 3 0 (PP)]]
[0]
"""


class LGInprocParserTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = "/var/tmp/parse"

        if not os.path.isdir(self.tmp_dir):
            os.mkdir(self.tmp_dir)

    # @unittest.skip
    def test_parse_batch_ps_output_explosion_merged_sentences(self):
        # """ Test postscript parsing for total number of parsed sentences """
        pr = LGInprocParser()

        print(merged_ps_parses)

        sentences = pr._parse_batch_ps_output(merged_ps_parses, 0)

        self.assertEqual(2, len(sentences))
        self.assertEqual("There the train was coming mother was holding Jem's hand Dog Monday was licking it everybody "
                         "was saying good-bye the train was in !",
                         sentences[0].text)
        self.assertEqual("[([There])([the])([train])([was])([coming])([mother])([was])([holding])([Jem's])([hand])"
                         "([Dog])([Monday])([was])([licking])([it])([everybody])([was])([saying])([good-bye])([the])"
                         "([train])([was])([in])([!])][][0]",
                         sentences[0].linkages[0])
        self.assertEqual("They had gone.", sentences[1].text)
        self.assertEqual(1, len(sentences[0].linkages))
        self.assertEqual(1, len(sentences[1].linkages))

    # @unittest.skip
    def test_parse_batch_ps_output_explosion(self):
        # """ Test postscript parsing for total number of parsed sentences """
        pr = LGInprocParser()

        print(explosion_no_linkages)

        sentences = pr._parse_batch_ps_output(explosion_no_linkages, 0)

        self.assertEqual(1, len(sentences))
        self.assertEqual("But there still remained all the damage that had been done that day , and the king "
                         "had nothing with which to pay for this.",
                         sentences[0].text)
        self.assertEqual(1, len(sentences[0].linkages))

    @unittest.skip
    def test_parse_batch_ps_output(self):
        """ Test postscript parsing for total number of parsed sentences """
        pr = LGInprocParser()
        num_sent = len(pr._parse_batch_ps_output(lg_post_output, 0))
        self.assertEqual(num_sent, 12, "'parse_batch_ps_output()' returns '{}' instead of '{}'".format(num_sent, 12))

    # # @unittest.skip
    # def test_parse_batch_ps_output_explosion(self):
    #     """ Test for 'combinatorial explosion' """
    #     pr = LGInprocParser(verbosity=0)
    #     num_sent = len(pr._parse_batch_ps_output(lg_post_explosion, 0))
    #     self.assertEqual(num_sent, 4, "'parse_batch_ps_output()' returns '{}' instead of '{}'".format(num_sent, 4))

    # @unittest.skip
    def test_parse_batch_ps_output_sharp(self):
        """ Test for 'sharp sign token suffix' """
        pr = LGInprocParser(verbosity=1)
        sentences = pr._parse_batch_ps_output(sharp_sign_linkage, 0)
        num_sent = len(sentences)
        self.assertEqual(num_sent, 1, "'parse_batch_ps_output()' returns '{}' instead of '{}'".format(num_sent, 1))

        print(sentences[0].text)
        print(sentences[0].linkages)


    def test_parse_sent_count(self):
        pr = LGInprocParser()
        bar = TextProgress(total=12, desc="Overal progress")
        pr.parse("tests/test-data/dict/poc-turtle", "tests/test-data/corpora/poc-turtle/poc-turtle.txt",
                 f"{self.tmp_dir}/poc-turtle.txt.ull", None, 0, bar)
        self.assertEqual(12, 12)

    def test_load_ull_file_not_found(self):

        with self.assertRaises(FileNotFoundError) as ctx:
            data = load_parses("/var/tmp/something.txt")

        # self.assertEqual("list index out of range", str(ctx.exception))

    def test_load_ull_file_access_denied(self):

        with self.assertRaises(PermissionError) as ctx:
            data = load_parses("/root/something.txt")

        # self.assertEqual("list index out of range", str(ctx.exception))

    # @unittest.skip
    def test_parse_file_not_found(self):
        with self.assertRaises(FileNotFoundError) as ctx:
            pr = LGInprocParser()
            pr.parse("tests/test-data/dict/poc-turtle", "tests/test-data/corpora/poc-turtle/poc-turtle.txt",
                     f"{self.tmp_dir}/poc-turtle.txt.ull", "tests/test-data/corpora/poc-turtle/poc-horse.txt", BIT_PARSE_QUALITY)

    @unittest.skip # Remove skipping when LG version >= 5.6.2
    def test_parse__sql_dictionary(self):
        """
        Test that LG parser can take a dictionary in sql format (looks for file dict.db)
        """
        with self.assertRaises(LGParseError):
            pr = LGInprocParser()
            pr.parse("tests/test-data/dict/sql", "tests/test-data/corpora/poc-turtle/poc-turtle.txt",
                     f"{self.tmp_dir}/poc-turtle.txt.ull", None, 0, bar)

    # @unittest.skip
    def test_parse_invalid_file_format(self):

        with self.assertRaises(LGParseError) as ctx:
            pr = LGInprocParser()
            pr.parse("tests/test-data/dict/poc-turtle", "tests/test-data/corpora/poc-turtle/poc-turtle.txt",
                 f"{self.tmp_dir}/poc-turtle-01.txt.ull", "tests/test-data/corpora/poc-turtle/poc-turtle.txt", BIT_PARSE_QUALITY)

        # self.assertEqual("list index out of range", str(ctx.exception))

    # @unittest.skip
    def test_parse_invalid_ref_file(self):

        with self.assertRaises(LGParseError) as ctx:
            pr = LGInprocParser()
            pr.parse("tests/test-data/dict/poc-turtle", "tests/test-data/corpora/poc-english/poc_english.txt",
                     f"{self.tmp_dir}/poc_english.txt.ull", "tests/test-data/parses/poc-turtle-mst/poc-turtle-parses-expected.txt",
                     BIT_PARSE_QUALITY)

    # @unittest.skip
    def test_stop_tokens(self):
        pr = LGInprocParser()
        pm, pq = pr.parse("tests/test-data/dict/poc-turtle", "tests/test-data/corpora/poc-turtle/poc-turtle.txt",
                 f"{self.tmp_dir}/poc-turtle-02.txt.ull", "tests/test-data/parses/poc-turtle-mst/poc-turtle-parses-expected.txt",
                 BIT_PARSE_QUALITY | BIT_EXISTING_DICT | BIT_NO_LWALL | BIT_NO_PERIOD | BIT_STRIP)

        self.assertEqual(12, pm.sentences)
        self.assertEqual(0, pm.skipped_sentences)

        pm, pq = pr.parse("tests/test-data/dict/poc-turtle", "tests/test-data/corpora/poc-turtle/poc-turtle.txt",
                 f"{self.tmp_dir}/poc-turtle-03.txt.ull", "tests/test-data/parses/poc-turtle-mst/poc-turtle-parses-expected.txt",
                 BIT_PARSE_QUALITY | BIT_EXISTING_DICT | BIT_NO_LWALL | BIT_NO_PERIOD | BIT_STRIP, stop_tokens="isa")

        self.assertEqual(6, pm.sentences)
        self.assertEqual(6, pm.skipped_sentences)

        pm, pq = pr.parse("tests/test-data/dict/poc-turtle", "tests/test-data/corpora/poc-turtle/poc-turtle.txt",
                 f"{self.tmp_dir}/poc-turtle-04.txt.ull", "tests/test-data/parses/poc-turtle-mst/poc-turtle-parses-expected.txt",
                 BIT_PARSE_QUALITY | BIT_EXISTING_DICT | BIT_NO_LWALL | BIT_NO_PERIOD | BIT_STRIP, stop_tokens="tuna herring")

        self.assertEqual(8, pm.sentences)
        self.assertEqual(4, pm.skipped_sentences)

    # @unittest.skip
    def test_max_sentence_len(self):
        pr = LGInprocParser()
        pm, pq = pr.parse("en", "tests/test-data/sentence-skip-test/issue-184.txt", f"{self.tmp_dir}/issue-184.ull", None,
                          BIT_EXISTING_DICT | BIT_NO_LWALL | BIT_NO_PERIOD | BIT_STRIP, max_sentence_len=3)

        self.assertEqual(2, pm.sentences)
        self.assertEqual(19, pm.skipped_sentences)

    # @unittest.skip
    def test_min_word_count(self):
        token_counts, total_count = {}, 0
        corpus_file_path = "tests/test-data/corpora/poc-turtle/poc-turtle-dot-separated.txt"

        options = BIT_EXISTING_DICT | BIT_NO_LWALL | BIT_NO_PERIOD | BIT_STRIP

        total_count = update_token_counts(corpus_file_path, token_counts, options)

        self.assertEqual(48, total_count)
        self.assertEqual(6, token_counts.get("isa", 0))
        self.assertEqual(6, token_counts.get("has", 0))
        self.assertEqual(2, token_counts.get("tuna", 0))

        pr = LGInprocParser()
        pm, pq = pr.parse("tests/test-data/dict/poc-turtle", corpus_file_path,
                          f"{self.tmp_dir}/{os.path.split(corpus_file_path)[1]}", None, options,
                          min_word_count=1, token_counts=token_counts)

        self.assertEqual(12, pm.sentences)
        self.assertEqual(0, pm.skipped_sentences)

        pm, pq = pr.parse("tests/test-data/dict/poc-turtle", corpus_file_path,
                          f"{self.tmp_dir}/{os.path.split(corpus_file_path)[1]}", None, options,
                          min_word_count=2, token_counts=token_counts)

        self.assertEqual(10, pm.sentences)
        self.assertEqual(2, pm.skipped_sentences)

    def test_second_linkage_issue(self):
        with open("tests/test-data/second-linkage-test/GCB-NQ.txt.raw") as file:
            raw = file.read()

        options = BIT_EXISTING_DICT | BIT_NO_LWALL | BIT_NO_PERIOD | BIT_STRIP

        lg_parser = LGInprocParser()
        sentenses = lg_parser._parse_batch_ps_output(raw, options)

        self.assertEqual(229, len(sentenses))

    def test_get_dir_name(self):
        file_path = "/home/user/data/tests/GCB-FULL-GLGT-MWC[2..5]-2019-06-11/grammar/ALE500/MWC:2/abs/dict_500C_2019-06-11_0007.4.0.dict"
        # file_path = "/home/user/data/tests/GCB-FULL-GLGT-MWC-2019-06-11/grammar/ALE500/MWC2/abs/dict_500C_2019-06-11_0007.4.0.dict"

        path, name = get_dir_name(file_path)

        # self.assertEqual("/home/user/data/tests/GCB-FULL-GLGT-MWC[2..5]-2019-06-11/grammar/ALE500/MWC:2/abs", path)
        self.assertEqual("dict_500C_2019-06-11_0007", name)


if __name__ == '__main__':
    unittest.main()
