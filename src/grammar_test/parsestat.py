from decimal import *

from ull.common.parsemetrics import ParseQuality, ParseMetrics

"""
    Statistics estimation set of functions
"""

__all__ = ['calc_stat', 'parse_metrics', 'calc_parse_quality', 'parse_quality']

def calc_stat(tokens: list) -> (int, int, Decimal):
    """
    Calculate percentage of successfully linked tokens. Token in square brackets considered to be unlinked.

    :param tokens: List of tokens.
    :return: Tuple (int, int, Decimal):
                - 1 if all tokens are linked, 0 otherwise;
                - 1 if all tokens are unlinked, 1 otherwise;
                - Percentage of successfully parsed tokens.
    """

    end_token = len(tokens)

    # Nothing to calculate if no tokens found
    if end_token == 0:
        return 0.0

    start_token = 0 if not tokens[0].startswith("###") else 1

    while tokens[end_token-1].startswith("###") or tokens[end_token-1] == "." or tokens[end_token-1] == "[.]":
        end_token -= 1

    total = end_token - start_token

    # Initialize number of unlinked tokens
    unlinked = 0

    for i in range(start_token, end_token, 1):
        if tokens[i].startswith("["):
            unlinked += 1

    return unlinked == 0, total == unlinked, (1.0 if unlinked == 0 else Decimal("1.0") - Decimal(unlinked) / Decimal(total))


def parse_metrics(tokens: list) -> ParseMetrics:
    """
    Calculate percentage of successfully linked tokens. Token in square brackets considered to be unlinked.

    :param tokens: List of tokens.
    :return: ParseMetrics
    """
    pm = ParseMetrics()

    end_token = len(tokens)

    # Nothing to calculate if no tokens found
    if end_token == 0:
        return pm

    start_token = 0 if not tokens[0].startswith("###") else 1

    while tokens[end_token-1].startswith("###") or tokens[end_token-1] == "." or tokens[end_token-1] == "[.]":
        end_token -= 1

    total = end_token - start_token

    if not total:
        return pm

    # Initialize number of unlinked tokens
    unlinked = 0

    for i in range(start_token, end_token, 1):
        if tokens[i].startswith("["):
            unlinked += 1

    if unlinked == 0:
        pm.completely_parsed_ratio = Decimal("1.0")
        pm.average_parsed_ratio = Decimal("1.0")
    else:
        pm.average_parsed_ratio = Decimal("1.0") - Decimal(unlinked) / Decimal(total)

    if total == unlinked:
        pm.completely_unparsed_ratio = Decimal("1.0")

    # print(pm.text(pm))

    return pm


def calc_parse_quality(test_set: set, ref_set: set) -> (int, int, Decimal):
    """
    Estimate parse quality

    :param test_set: Set of links being tested.
    :param ref_set: Reference set of links
    :return: Tuple (m, e, a) where  m - number of links missing in test set, e - number of extra links in test set,
                                    a - match links to total links ratio
    """
    len_ref = len(ref_set)

    if len_ref > 0:
        return len(ref_set - test_set), len(test_set - ref_set), Decimal(len(test_set & ref_set)) / Decimal(len_ref)

    return 0, 0, Decimal("0.0")


def parse_quality(test_set: set, ref_set: set) -> ParseQuality:
    """
    Estimate parse quality

    :param test_set: Set of links being tested.
    :param ref_set: Reference set of links
    :return: ParseQuality instance filled with calculated values.
    """
    pq = ParseQuality()

    len_ref = len(ref_set)

    if len_ref > 0:
        pq.total = len_ref
        pq.missing = len(ref_set - test_set)
        pq.extra = len(test_set - ref_set)
        pq.quality = Decimal(len(test_set & ref_set)) / Decimal(len_ref)

    return pq
