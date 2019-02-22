import unittest
import sys

from src.grammar_tester.optconst import *
from src.grammar_tester.lginprocparser import LGInprocParser
from src.common.textprogress import TextProgress
from src.grammar_tester import load_ull_file
from src.grammar_tester.lgmisc import ParserError, LGParseError


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

class LGInprocParserTestCase(unittest.TestCase):
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

    # @unittest.skip
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
                 "/var/tmp/parse", None, 0, bar)
        self.assertEqual(12, 12)

    def test_load_ull_file_not_found(self):

        with self.assertRaises(FileNotFoundError) as ctx:
            data = load_ull_file("/var/tmp/something.txt")

        # self.assertEqual("list index out of range", str(ctx.exception))

    def test_load_ull_file_access_denied(self):

        with self.assertRaises(PermissionError) as ctx:
            data = load_ull_file("/root/something.txt")

        # self.assertEqual("list index out of range", str(ctx.exception))

    # @unittest.skip
    def test_parse_file_not_found(self):
        with self.assertRaises(FileNotFoundError) as ctx:
            pr = LGInprocParser()
            pr.parse("tests/test-data/dict/poc-turtle", "tests/test-data/corpora/poc-turtle/poc-turtle.txt",
                     "/var/tmp/parse", "tests/test-data/corpora/poc-turtle/poc-horse.txt", BIT_PARSE_QUALITY)

        # self.assertEqual("list index out of range", str(ctx.exception))

    # @unittest.skip
    def test_parse_invalid_file_format(self):

        # from subprocess import Popen, PIPE
        #
        # with Popen(["conda", "env", "list"], stdout=PIPE, stderr=PIPE) as wh:
        #
        #     raw, err = wh.communicate()
        #     print(raw.decode("utf-8-sig"))

        with self.assertRaises(LGParseError) as ctx:
            pr = LGInprocParser()
            pr.parse("tests/test-data/dict/poc-turtle", "tests/test-data/corpora/poc-turtle/poc-turtle.txt",
                 "/var/tmp/parse", "tests/test-data/corpora/poc-turtle/poc-turtle.txt", BIT_PARSE_QUALITY)

        # self.assertEqual("list index out of range", str(ctx.exception))

    # @unittest.skip
    def test_parse_invalid_ref_file(self):

        # with self.assertRaises(LGParseError) as ctx:
        try:
            pr = LGInprocParser()
            pr.parse("tests/test-data/dict/poc-turtle", "tests/test-data/corpora/poc-english/poc_english.txt",
                     "/var/tmp/parse", "tests/test-data/parses/poc-turtle-mst/poc-turtle-parses-expected.txt",
                     BIT_PARSE_QUALITY)
        except Exception as err:
            print(str(type(err)) + ": " + str(err), file=sys.stderr)


if __name__ == '__main__':
    unittest.main()
