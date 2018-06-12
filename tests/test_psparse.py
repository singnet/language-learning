import unittest
import sys

try:
    from link_grammar.psparse import strip_token, parse_tokens, parse_links, parse_postscript, get_link_set, prepare_tokens
    from link_grammar.optconst import *
    from link_grammar.parsemetrics import ParseMetrics
    from link_grammar.parsestat import parse_metrics

except ImportError:
    from psparse import strip_token, parse_tokens, parse_links, parse_postscript, get_link_set, prepare_tokens
    from optconst import *
    from parsemetrics import ParseMetrics
    from parsestat import parse_metrics


gutenberg_children_bug = \
"""
[(LEFT-WALL)(")(project.v)(gutenberg[?].n)('s.p)(alice[?].n)('s.p)(adventures.n)([in])(wonderland.n)
(,)(by)(lewis[!])(carroll[?].n)(")(()(edited.v-d)())]
[[0 2 1 (Wi)][0 1 0 (ZZZ)][2 9 2 (Os)][6 9 1 (Ds**x)][5 6 0 (YS)][4 5 0 (D*u)][3 4 0 (YS)]
[7 9 0 (AN)][9 11 1 (MXsx)][10 11 0 (Xd)][11 17 2 (Xc)][11 13 1 (Jp)][12 13 0 (AN)][13 16 1 (MXsp)]
[16 17 0 (Xca)][13 14 0 (ZZZ)][15 16 0 (Xd)]]
[0]
"""
gutenberg_children_bug2 = "[ebook # @number@ ][(LEFT-WALL)(release.n)(date.n)(:.j)(@date@[?].n)([)(ebook[?].a)([#])" \
                          "(@number@[?].n)(])][[0 3 2 (Xx)][0 2 1 (Wa)][1 2 0 (AN)][3 4 0 (Jp)][4 8 2 (MXs)]" \
                          "[5 8 1 (Xd)][6 8 0 (A)][8 9 0 (Xc)]][0]"


# cleaned_Gutenberg_Children bug list
cgch_bug_001 = \
"""
[ illustration : " i tell you what , you stay right here ! "[(LEFT-WALL)([[])(illustration.n-u)(:.v)(")([i])(tell.v)(you)(what)(,)(you)(stay.v)(right.a)(here)(!)(")][[0 14 4 (Xp)][0 9 3 (Xx)][0 6 2 (WV)][0 2 0 (Wd)][2 3 0 (Ss)][3 6 1 (I*v)][3 4 0 (ZZZ)][6 8 1 (QI)][6 7 0 (Ox)][9 11 1 (WV)][9 10 0 (Wd)][10 11 0 (Sp)][11 12 0 (Pa)][12 13 0 (MVp)][14 15 0 (ZZZ)]][0]
"""


class TestPSParse(unittest.TestCase):

    post_all_walls = "[(LEFT-WALL)(Dad[!])(was.v-d)(not.e)(a)(parent.n)(before)(.)(RIGHT-WALL)]" \
                     "[[0 7 2 (Xp)][0 1 0 (Wd)][1 2 0 (Ss*s)][2 5 1 (Osm)][2 3 0 (EBm)]" \
                     "[4 5 0 (Ds**c)][5 6 0 (Mp)][7 8 0 (RW)]][0]"
    post_no_walls = "[(eagle)(has)(wing)(.)][[0 2 1 (C04C01)][1 2 0 (C01C01)][2 3 0 (C01C05)]][0]"
    post_no_links = "[([herring])([isa])([fish])([.])][][0]"

    link_str = "[0 7 2 (Xp)][0 1 0 (Wd)][1 2 0 (Ss*s)][2 5 1 (Osm)][2 3 0 (EBm)][4 5 0 (Ds**c)][5 6 0 (Mp)][7 8 0 (RW)]"

    tokens_all_walls = "(LEFT-WALL)(Dad[!])(was.v-d)(not.e)(a)(parent.n)(before)(.)(RIGHT-WALL)"
    tokens_no_walls = "(eagle)(has)(wing)(.)"
    tokens_no_walls_no_period = "(eagle)(has)(wing)"

    @staticmethod
    def cmp_lists(list1: [], list2: []) -> bool:
        if list1 is None or list2 is None or len(list1) != len(list2):
            return False

        for i in range(0, len(list1)):
            if list1[i] != list2[i]:
                return False

        return True

    def test_strip_token(self):
        """ test_strip_token """
        # print(__doc__, sys.stderr)

        self.assertEqual(strip_token("strange[!]"), "strange")
        self.assertEqual(strip_token("strange.a"), "strange")
        self.assertEqual(strip_token("[strange]"), "[strange]")

    # @unittest.skip
    def test_parse_tokens(self):
        """ test_parse_tokens """
        # print(__doc__, sys.stderr)

        options = 0

        # No RIGHT-WALL, no CAPS
        options |= BIT_STRIP
        # tokens = parse_tokens(self.tokens_all_walls, options)
        # self.assertTrue(self.cmp_lists(tokens, ['###LEFT-WALL###', 'dad', 'was', 'not', 'a',
        #                                         'parent', 'before', '.']))

        # Tokens without walls
        tokens = parse_tokens(self.tokens_no_walls, options)
        self.assertTrue(self.cmp_lists(tokens, ['###LEFT-WALL###', 'eagle', 'has', 'wing', '.']))

        # RIGHT-WALL and CAPS, no STRIP
        options |= (BIT_RWALL | BIT_CAPS)
        options &= ~BIT_STRIP
        tokens = parse_tokens(self.tokens_all_walls, options)
        self.assertTrue(self.cmp_lists(tokens, ['###LEFT-WALL###', 'Dad[!]', 'was.v-d', 'not.e', 'a',
                                                'parent.n', 'before', '.', '###RIGHT-WALL###']))

        # Tokens without walls
        tokens = parse_tokens(self.tokens_no_walls, options)
        # print(tokens, file=sys.stdout)
        self.assertTrue(self.cmp_lists(tokens, ['###LEFT-WALL###', 'eagle', 'has', 'wing', '.']))

    @unittest.skip
    def test_parse_tokens_no_left_wall(self):
        # NO_LWALL and CAPS, no STRIP
        options = 0
        options |= BIT_CAPS | BIT_NO_LWALL
        # options |= (BIT_NO_LWALL | BIT_CAPS)
        # options &= (~(BIT_STRIP | BIT_RWALL))
        tokens = parse_tokens(self.tokens_all_walls, options)

        # print(tokens)

        self.assertTrue(self.cmp_lists(tokens, ['Dad[!]', 'was.v-d', 'not.e', 'a',
                                                'parent.n', 'before', '.']))

    @unittest.skip
    def test_parse_tokens_no_walls_no_period(self):
        options = 0
        options |= BIT_STRIP | BIT_NO_PERIOD | BIT_NO_LWALL
        tokens = parse_tokens(self.tokens_all_walls, options)

        # print(tokens)

        self.assertTrue(self.cmp_lists(tokens, ['dad', 'was', 'not', 'a', 'parent', 'before']))

    @unittest.skip
    def test_parse_tokens_rwall_no_period(self):
        options = 0
        options |= BIT_STRIP | BIT_NO_PERIOD | BIT_RWALL
        tokens = parse_tokens(self.tokens_all_walls, options)

        # print(tokens)

        self.assertTrue(self.cmp_lists(tokens, ['###LEFT-WALL###', 'dad', 'was', 'not', 'a', 'parent', 'before',
                                                '###RIGHT-WALL###']))

    @unittest.skip
    def test_parse_tokens_no_period(self):
        options = 0
        options |= BIT_STRIP | BIT_NO_PERIOD | BIT_RWALL
        tokens = parse_tokens(self.tokens_no_walls, options)

        # print(tokens)

        self.assertTrue(self.cmp_lists(tokens, ['###LEFT-WALL###', 'eagle', 'has', 'wing']))

    @unittest.skip
    def test_parse_no_period_if_no_period(self):
        options = 0
        options |= BIT_STRIP | BIT_NO_PERIOD | BIT_RWALL
        tokens = parse_tokens(self.tokens_no_walls_no_period, options)

        # print(tokens)

        self.assertTrue(self.cmp_lists(tokens, ['###LEFT-WALL###', 'eagle', 'has', 'wing']))

    # @unittest.skip
    def test_parse_links(self):
        """ test_parse_links """
        # print(__doc__, sys.stderr)

        links = parse_links(self.link_str, ['###LEFT-WALL###', 'dad', 'was', 'not', 'a', 'parent', 'before', '.'])

        # [0 7 2 (Xp)][0 1 0 (Wd)][1 2 0 (Ss*s)][2 5 1 (Osm)][2 3 0 (EBm)][4 5 0 (Ds**c)][5 6 0 (Mp)][7 8 0 (RW)]
        self.assertTrue(self.cmp_lists(links, [  (0, 7),
                                                 (0, 1),
                                                 (1, 2),
                                                 (2, 5),
                                                 (2, 3),
                                                 (4, 5),
                                                 (5, 6) ]))

    # @unittest.skip
    def test_parse_postscript_all_walls(self):
        """ test_parse_postscript """
        # print(__doc__, sys.stderr)

        options = 0
        options |= (BIT_RWALL | BIT_CAPS)
        options &= ~BIT_STRIP
        tokens, links = parse_postscript(self.post_all_walls, options, sys.stdout)
        pm = parse_metrics(tokens)
        self.assertEqual(1.0, pm.completely_parsed_ratio)
        self.assertEqual(0.0, pm.completely_unparsed_ratio)
        self.assertEqual(1.0, pm.average_parsed_ratio)

    # @unittest.skip
    def test_parse_postscript_no_walls(self):
        """ test_parse_postscript """
        # print(__doc__, sys.stderr)

        options = 0
        options |= (BIT_RWALL | BIT_CAPS)
        options &= ~BIT_STRIP

        tokens, links = parse_postscript(self.post_no_walls, options, sys.stdout)
        pm = parse_metrics(tokens)
        self.assertEqual(1.0, pm.completely_parsed_ratio)
        self.assertEqual(0.0, pm.completely_unparsed_ratio)
        self.assertEqual(1.0, pm.average_parsed_ratio)

    # @unittest.skip
    def test_parse_postscript_no_links(self):
        """ test_parse_postscript """
        # print(__doc__, sys.stderr)

        options = 0
        options |= (BIT_RWALL | BIT_CAPS)
        options &= ~BIT_STRIP

        tokens, links = parse_postscript(self.post_no_links, options, sys.stdout)
        pm = parse_metrics(tokens)
        self.assertEqual(0.0, pm.completely_parsed_ratio)
        self.assertEqual(1.0, pm.completely_unparsed_ratio)
        self.assertEqual(0.0, pm.average_parsed_ratio)

    # @unittest.skip
    def test_parse_postscript_gutenchildren_bug(self):
        """ test_parse_postscript """
        # print(__doc__, sys.stderr)

        options = 0
        # options |= (BIT_RWALL | BIT_CAPS)
        # options &= ~BIT_STRIP

        tokens, links = parse_postscript(gutenberg_children_bug, options, sys.stdout)

        pm = parse_metrics(tokens)

        self.assertEqual(0.0, pm.completely_parsed_ratio)
        self.assertEqual(0.0, pm.completely_unparsed_ratio)
        self.assertEqual(0.9375, pm.average_parsed_ratio)

    def test_get_link_set(self):
        # post_all_walls = "[(LEFT-WALL)(Dad[!])(was.v-d)(not.e)(a)(parent.n)(before)(.)(RIGHT-WALL)]" \
        #                  "[[0 7 2 (Xp)][0 1 0 (Wd)][1 2 0 (Ss*s)][2 5 1 (Osm)][2 3 0 (EBm)]" \
        #                  "[4 5 0 (Ds**c)][5 6 0 (Mp)][7 8 0 (RW)]][0]"
        expected_set = {(1, 2), (2, 5), (2, 3), (4, 5), (5, 6)}
        options = BIT_NO_LWALL | BIT_NO_PERIOD | BIT_STRIP | BIT_PARSE_QUALITY
        tokens, links = parse_postscript(self.post_all_walls, options, sys.stdout)
        result_set = get_link_set(tokens, links, options)

        print(expected_set)
        print(result_set)

        self.assertTrue(result_set == expected_set)

    def test_prepare_tokens_both_walls_period_no_options(self):
        token_list = ['###LEFT-WALL###', 'dad', 'was', 'not', 'a', 'parent', 'before', '.', '###RIGHT-WALL###']
        token_list_no_walls = ['dad', 'was', 'not', 'a', 'parent', 'before', '.']
        token_list_no_period = ['###LEFT-WALL###', 'dad', 'was', 'not', 'a', 'parent', 'before', '###RIGHT-WALL###']
        token_list_words_only = ['dad', 'was', 'not', 'a', 'parent', 'before']

        # Should take no action
        options = 0 | BIT_RWALL
        result_list = prepare_tokens(token_list, options)
        self.assertEqual(token_list, result_list, "Lists are not the same!!!")

        # Should return a list with no walls only word-tokens and period
        options = 0 | BIT_NO_LWALL
        result_list = prepare_tokens(token_list, options)
        self.assertEqual(token_list_no_walls, result_list, "Lists are not the same!!!")

        # Should return a list with walls, word-tokens and period
        options = 0 | BIT_RWALL | BIT_NO_PERIOD
        result_list = prepare_tokens(token_list, options)
        self.assertEqual(token_list_no_period, result_list, "Lists are not the same!!!")

        # Should return a list with no walls and no period
        options = 0 | BIT_NO_LWALL | BIT_NO_PERIOD
        result_list = prepare_tokens(token_list, options)
        self.assertEqual(token_list_words_only, result_list, "Lists are not the same!!!")

        tokens_period_in_brackets = ["dad", "[has]", "[a]", "[telescope]", "[.]"]
        options = 0 | BIT_NO_LWALL | BIT_NO_PERIOD
        result_list = prepare_tokens(tokens_period_in_brackets, options)
        self.assertEqual(["dad", "[has]", "[a]", "[telescope]"], result_list, "Lists are not the same!!!")

        tokens_only_period_unboxed = ["[dad]", "has", "[binoculars]", "."]
        options = 0 | BIT_NO_LWALL | BIT_NO_PERIOD
        result_list = prepare_tokens(tokens_only_period_unboxed, options)
        self.assertEqual(["[dad]", "has", "[binoculars]"], result_list, "Lists are not the same!!!")


if __name__ == '__main__':
    unittest.main()
