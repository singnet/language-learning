import sys
import re

from .optconst import *

"""
    Utilities for parsing postscript notated tokens and links, returned by Link Grammar API method Linkage.postscript()
     
"""

__all__ = ['strip_token', 'parse_tokens', 'parse_links', 'parse_postscript', 'skip_lines', 'trim_garbage',
           'get_link_set', 'prepare_tokens']

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


def parse_tokens(txt, opt) -> (list, int):
    """
    Parse string of tokens, taken from postscript notated LG parse output.
    After several iterations it became obvious that all tokens should be kept in the original list in order to
    avoid issues with links. All filtering necessary for ULL output is now done in print_output(). All filtering
    necessary for parseability statistics estimation is done in prepare_tokens().
    :param txt: string token line extracted from postfix notation output string returned by Linkage.postfix()
            method.
    :param opt: bit mask option value (see parse_test() description for more details)
    :return: list of tokens
    """
    tokens = []
    offset = 0
    start_pos = 1
    end_pos = txt.find(")")


    while end_pos - start_pos > 0:
        token = txt[start_pos:end_pos:]

        # Strip LG suffixes if the option is set.
        if opt & BIT_STRIP == BIT_STRIP:
            token = strip_token(token)

        # All walls are supplied with leading and trailing hashes as agreed for the project.
        if token.find("-WALL") > 0:

            if token in ["RIGHT-WALL", "LEFT-WALL"]:
                tokens.append(r"###" + token + r"###")

            elif token in ["[RIGHT-WALL]", "[LEFT-WALL]"]:
                tokens.append(r"###" + token[1:-1] + r"###")

        else:
            # Even if LEFT-WALL is not defined in .dict file it is still added into the token list
            #   in order for token numbering to be started from one as agreed for ULL project.
            if start_pos == 1:
                tokens.append(r"###LEFT-WALL###")
                offset = 1

            # By default all tokens are kept lower case.
            if opt & BIT_CAPS == 0:
                token = token.lower()

            tokens.append(token)

        start_pos = end_pos + 2
        end_pos = txt.find(")", start_pos + 1)

    return tokens, offset


def prepare_tokens(tokens: list, options: int) -> list:
    """
    Prepare (filter) list of tokens according to the options flags for statistics calculation.

    :param tokens: Initial list of tokens obtained from parse_tokens().
    :param options: Bit flags.
    :return: Filtered list of tokens.
    """
    token_count = len(tokens)
    first_token = 0
    last_token = token_count - 1

    if not token_count:
        return tokens

    if options & BIT_NO_LWALL:
        if tokens[0].startswith(r"###") or tokens[0].startswith(r"[##"):
            first_token += 1

        # RIGHT-WALL is not needed if LEFT-WALL is stripped off
        if tokens[last_token].startswith(r"###") or tokens[last_token].startswith(r"[##"):
            last_token -= 1

    if not (options & BIT_RWALL) and (tokens[last_token].startswith(r"###") or tokens[last_token].startswith(r"[##")):
        last_token -= 1

    if options & BIT_NO_PERIOD:
        rw = tokens[last_token] if tokens[last_token].startswith(r"###") or tokens[last_token].startswith(r"[##") \
                                else None

        # Skip RIGHT-WALL and period or period in brackets if any
        while last_token and tokens[last_token] in [r"[.]", r".", r"###RIGHT-WALL###", r"[###RIGHT-WALL###]"]:
            last_token -= 1

        # If both period and RIGHT-WALL were found
        if rw is not None:
            # RIGHT-WALL is added to the new list
            return tokens[first_token:last_token+1] + [rw]

    return tokens[first_token:last_token+1]


def parse_links(txt: str, tokens: list, offset: int) -> list:
    """
    Parse links represented in postfix notation and prints them in OpenCog notation.

    :param txt:         Link list in postfix notation, obtained either from LG API or from link-parser postfix output.
    :param tokens:      List of tokens previously extracted from postfix notated output.
    :param offset:      Token index offset. Equals to 1 if tested grammar has no LEFT-WALL and the former was added
                        during postscript parsing. Offset is necessary for the links to have their indexes properly
                        updated.
    :return:            List of links in ULL format.
    """
    links = []

    token_count = len(tokens)

    start_pos = 1
    end_pos = txt.find("]")

    q = re.compile('(\d+)\s(\d+)\s\d+\s\(.+\)')

    while end_pos - start_pos > 0:
        mm = q.match(txt[start_pos:end_pos:])

        if mm is not None:
            index1, index2 = int(mm.group(1))+offset, int(mm.group(2))+offset

            if index2 < token_count:
                links.append((index1, index2))

        start_pos = end_pos + 2
        end_pos = txt.find("]", start_pos)

    return links


def parse_postscript(text: str, options: int, ofile) -> ([], []):
    """
    Parse postscript notation of the linkage.

    :param text:        Text string returned by Linkage.postscript() method.
    :param options      Bit mask, representing different parsing options. See `optconst.py` for details.
    :param ofile:       Output file object reference.
    :return:            Tuple of two lists: (tokens, links).
    """
    p = re.compile('\[(\(.+?\)+?)\]\[(.*?)\]\[0\]', re.S)

    m = p.match(text.replace("\n", ""))

    if m is not None:
        tokens, offset = parse_tokens(m.group(1), options)
        links = parse_links(m.group(2), tokens, offset)

        return tokens, links

    else:
        print("parse_postscript(): regex does not match!", file=sys.stderr)
        print(text, file=sys.stderr)

    return [], []


def get_link_set(tokens: list, links: list, options: int) -> set:
    """
    Create link set from link list filtering out unnecessary links according to options bit flags.

    :param tokens:      Token list.
    :param links:       Link list.
    :param options:     Integer bit mask variable.
    :return:            Filtered set of links.
    """
    all_link_set = set(links)
    exc_link_set = set()

    token_count = len(tokens)

    if token_count:
        last_token = token_count - 1

        if options & BIT_NO_LWALL and tokens[0].find("WALL") > -1:
            exc_link_set |= set({(0, i) for i in range(1, token_count)})

            if tokens[last_token].startswith(r"###"):
                exc_link_set |= set({(i, last_token) for i in range(token_count)})

        if options & BIT_NO_PERIOD:
            if tokens[last_token].startswith(r"###"):
                last_token -= 1

            if tokens[last_token] == ".":
                exc_link_set |= set({(i, last_token) for i in range(token_count)})

        if len(exc_link_set):
            return all_link_set - exc_link_set

    return all_link_set


def skip_lines(text: str, lines_to_skip: int) -> int:
    """
     Skip specified number of lines from the beginning of a text string.

    :param text:            Text string with zero or many '\n' in.
    :param lines_to_skip:   Number of lines to skip.
    :return:                Return position of the first character after the specified number of lines is skipped.
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

    :param text:    Text string.
    :return:        Return position of a character following ']' or zero in case of a null string.
    """
    l = len(text)-1

    while l:
        if text[l] == "]":
            return l+1
        l -= 1

    return 0
