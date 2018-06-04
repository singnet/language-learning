import sys
import re

from .optconst import *

"""
    Utilities for parsing postscript notated tokens and links, returned by Link Grammar API method Linkage.postscript()
     
"""

__all__ = ['strip_token', 'parse_tokens', 'parse_links', 'parse_postscript', 'skip_lines', 'trim_garbage']

__version__ = "1.0.0"


def strip_token(token) -> str:
    """
    Strip off suffix substring
    :param token: token string
    :return: stripped token if a suffix found, the same token otherwise
    """
    if token.startswith(".") or token.startswith("["):
        return token

    pos = token.find("[")

    # If "." is not found
    if pos < 0:
        pos = token.find(".")

        # If "[" is not found or token starts with "[" return token as is.
        if pos <= 0:
            return token

    return token[:pos:]


def parse_tokens(txt, opt) -> list:
    """
    Parse string of tokens
    :param txt: string token line extracted from postfix notation output string returned by Linkage.postfix()
            method.
    :param opt: bit mask option value (see parse_test() description for more details)
    :return: list of tokes
    """
    toks = []
    start_pos = 1
    end_pos = txt.find(")")
    token_count = 0

    while end_pos - start_pos > 0:
        token = txt[start_pos:end_pos:]

        if opt & BIT_STRIP == BIT_STRIP:
            token = strip_token(token)

        if token.find("-WALL") > 0:

            if (token == "RIGHT-WALL" and (opt & BIT_RWALL) == BIT_RWALL) or \
                (token == "LEFT-WALL" and not (opt & BIT_NO_LWALL)):

                token = "###" + token + "###"
                toks.append(token)
        else:
            if token_count == 0:
                toks.append(r"###LEFT-WALL###")
                token_count += 1

            if opt & BIT_CAPS == 0:
                token = token.lower()

            toks.append(token)

        start_pos = end_pos + 2
        end_pos = txt.find(")", start_pos)
        token_count += 1

    # print(toks)
    return toks


def parse_links(txt, toks) -> list:
    """
    Parse links represented in postfix notation and prints them in OpenCog notation.

    :param txt: link list in postfix notation
    :param toks: list of tokens previously extracted from postfix notated output
    :return: List of links in ULL format
    """
    links = []
    inc = 0

    # # Add LEFT-WALL token if not already presented
    # if not toks[0].startswith(r"###"):
    #     toks.insert(0, r"###LEFT-WALL###")
    #     inc = 1         # index increment to make sure the links are stay correct

    token_count = len(toks)

    start_pos = 1
    end_pos = txt.find("]")

    q = re.compile('(\d+)\s(\d+)\s\d+\s\(.+\)')

    while end_pos - start_pos > 0:
        mm = q.match(txt[start_pos:end_pos:])

        if mm is not None:
            index1 = int(mm.group(1)) + inc
            index2 = int(mm.group(2)) + inc

            if index2 < token_count:
                links.append((index1, toks[index1], index2, toks[index2]))

        start_pos = end_pos + 2
        end_pos = txt.find("]", start_pos)

    return links


def parse_postscript(text: str, options: int, ofile) -> ([], []):
    """
    Parse postscript notation of the linkage.

    :param text: text string returned by Linkage.postscript() method.
    :param ofile: output file object reference
    :return: Tuple of two lists: (tokens, links).
    """

    p = re.compile('\[(\(.+?\)+?)\]\[(.*?)\]\[0\]', re.S)

    m = p.match(text.replace("\n", ""))

    if m is not None:
        tokens = parse_tokens(m.group(1), options)
        links = parse_links(m.group(2), tokens)
        sorted_links = sorted(links, key=lambda x: (x[0], x[2]))

        return tokens, sorted_links

    else:
        print("parse_postscript(): regex does not match!", file=sys.stderr)
        print(text, file=sys.stderr)

    return [], []

def skip_lines(text: str, lines_to_skip: int) -> int:
    """
     Skip specified number of lines from the beginning of a text string.

    :param text: Text string with zero or many '\n' in.
    :param lines_to_skip: Number of lines to skip.
    :return: Return position of the first character after the specified number of lines is skipped.
    """
    l = len(text)

    pos = 0
    cnt = lines_to_skip

    while l and cnt:
        if text[pos] == "\n":
            cnt -= 1
        pos += 1
    return pos


def trim_garbage(text: str) -> int:
    """
    Strip all characters from the end of string until ']' is reached.

    :param text: Text string.
    :return: Return position of a character following ']' or zero in case of a null string.
    """
    l = len(text)-1

    while l:
        if text[l] == "]":
            return l+1
        l -= 1

    return 0
