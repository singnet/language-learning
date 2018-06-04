import unittest
import sys

try:
    from link_grammar.psparse import strip_token, parse_tokens, parse_links, parse_postscript
    from link_grammar.optconst import *
    from link_grammar.parsemetrics import ParseMetrics
    from link_grammar.parsestat import parse_metrics

except ImportError:
    from psparse import strip_token, parse_tokens, parse_links, parse_postscript
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

class TestPSParse(unittest.TestCase):

    post_all_walls = "[(LEFT-WALL)(Dad[!])(was.v-d)(not.e)(a)(parent.n)(before)(.)(RIGHT-WALL)]" \
                     "[[0 7 2 (Xp)][0 1 0 (Wd)][1 2 0 (Ss*s)][2 5 1 (Osm)][2 3 0 (EBm)]" \
                     "[4 5 0 (Ds**c)][5 6 0 (Mp)][7 8 0 (RW)]][0]"
    post_no_walls = "[(eagle)(has)(wing)(.)][[0 2 1 (C04C01)][1 2 0 (C01C01)][2 3 0 (C01C05)]][0]"
    post_no_links = "[([herring])([isa])([fish])([.])][][0]"

    link_str = "[0 7 2 (Xp)][0 1 0 (Wd)][1 2 0 (Ss*s)][2 5 1 (Osm)][2 3 0 (EBm)][4 5 0 (Ds**c)][5 6 0 (Mp)][7 8 0 (RW)]"

    tokens_all_walls = "(LEFT-WALL)(Dad[!])(was.v-d)(not.e)(a)(parent.n)(before)(.)(RIGHT-WALL)"
    tokens_no_walls = "(eagle)(has)(wing)(.)"

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

    def test_parse_tokens(self):
        """ test_parse_tokens """
        # print(__doc__, sys.stderr)

        options = 0

        # No RIGHT-WALL, no CAPS
        options |= BIT_STRIP
        tokens = parse_tokens(self.tokens_all_walls, options)
        self.assertTrue(self.cmp_lists(tokens, ['###LEFT-WALL###', 'dad', 'was', 'not', 'a',
                                                'parent', 'before', '.']))

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

        # NO_LWALL and CAPS, no STRIP
        options |= (BIT_NO_LWALL | BIT_CAPS)
        options &= (~(BIT_STRIP | BIT_RWALL))
        tokens = parse_tokens(self.tokens_all_walls, options)
        self.assertTrue(self.cmp_lists(tokens, ['Dad[!]', 'was.v-d', 'not.e', 'a',
                                                'parent.n', 'before', '.']))

    def test_parse_links(self):
        """ test_parse_links """
        # print(__doc__, sys.stderr)

        links = parse_links(self.link_str, ['###LEFT-WALL###', 'dad', 'was', 'not', 'a', 'parent', 'before', '.'])

        # [0 7 2 (Xp)][0 1 0 (Wd)][1 2 0 (Ss*s)][2 5 1 (Osm)][2 3 0 (EBm)][4 5 0 (Ds**c)][5 6 0 (Mp)][7 8 0 (RW)]
        self.assertTrue(self.cmp_lists(links, [  (0, '###LEFT-WALL###', 7, '.'),
                                                 (0, '###LEFT-WALL###', 1, 'dad'),
                                                 (1, 'dad', 2, 'was'),
                                                 (2, 'was', 5, 'parent'),
                                                 (2, 'was', 3, 'not'),
                                                 (4, 'a', 5, 'parent'),
                                                 (5, 'parent', 6, 'before') ]))

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

if __name__ == '__main__':
    unittest.main()
