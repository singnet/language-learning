from .optconst import *

__all__ = ['get_output_suffix', 'print_output', 'LGParseError']


LINK_1ST_TOKEN_INDEX = 0
LINK_2ND_TOKEN_INDEX = 1


class LGParseError(Exception):
    pass

def get_output_suffix(options: int) -> str:
    """ Return output file name suffix depending on set options """

    out_format = options & BIT_OUTPUT

    suff = "2" if (options & BIT_LG_EXE) else ""

    if (out_format & BIT_OUTPUT_CONST_TREE) == BIT_OUTPUT_CONST_TREE:
        return ".tree" + suff
    elif (out_format & BIT_OUTPUT_DIAGRAM) == BIT_OUTPUT_DIAGRAM:
        return ".diag" + suff
    elif (out_format & BIT_OUTPUT_POSTSCRIPT) == BIT_OUTPUT_POSTSCRIPT:
        return ".post" + suff
    else:
        return ".ull" + suff


def print_output(tokens: list, raw_links: list, options: int, ofl):
    """
    Print links in ULL format to the output specified by 'ofl' variable.

    :param tokens: List of tokens.
    :param links: List of links.
    :param ofl: Output file handle.
    :return:
    """
    rwall_index = -1

    i = 0

    for token in tokens:
        if not token.startswith("###"):
            ofl.write(token + ' ')
        else:
            if token.find("RIGHT-WALL") >= 0:
                rwall_index = i
        i += 1

    ofl.write('\n')

    links = sorted(raw_links, key=lambda x: (x[0], x[1]))

    for link in links:
        # Filter out all links with LEFT-WALL if 'BIT_NO_LWALL' is set
        # if (options & BIT_NO_LWALL) and (link[LINK_1ST_TOKEN_INDEX] == 0 or link[LINK_2ND_TOKEN_INDEX] == 0):
        if (options & BIT_ULL_NO_LWALL) and (link[LINK_1ST_TOKEN_INDEX] == 0 or link[LINK_2ND_TOKEN_INDEX] == 0):
            continue

        # Filter out all links with RIGHT-WALL if 'BIT_RWALL' is not set
        if (options & BIT_RWALL) != BIT_RWALL and rwall_index >= 0 \
                and (link[LINK_1ST_TOKEN_INDEX] == rwall_index or link[LINK_2ND_TOKEN_INDEX] == rwall_index):
            continue

        token_count = len(tokens)
        index1, index2 = link[LINK_1ST_TOKEN_INDEX], link[LINK_2ND_TOKEN_INDEX]

        if index1 < token_count and index2 < token_count:
            print(index1, tokens[index1], index2, tokens[index2], file=ofl)
        else:
            print(tokens)
            print(token_count, (index1, index2))

    print('', file=ofl)
