# language-learning/src/grammar_learner/pparser.py                      # 190417
import logging
import pandas as pd
from collections import Counter
from .corpus_stats import corpus_stats
from .utl import kwa


def mst2words(lines, **kwargs):
    logger = logging.getLogger(__name__ + ".mst2words")
    lw = kwa('', 'left_wall', **kwargs)
    dot = kwa(False, 'period', **kwargs)

    pairs = []
    for line in lines:
        if len(line) > 1:
            if line[0].isdigit():
                x = line.split()
                if len(x) in [4, 5] and x[0].isdigit() and x[2].isdigit():  # 190325
                    if x[1] == '###LEFT-WALL###':
                        if lw in ['', 'none']:
                            continue
                        else:
                            x[1] = lw
                    if not dot and x[3] == '.':
                        continue
                    pairs.append([x[1], x[3]])
    df = pd.DataFrame(pairs, columns=['word','link'])
    df['count'] = 1

    return df


def mst2connectors(lines, **kwargs):
    df = mst2words(lines, **kwargs)
    lefts = df.copy()
    lefts['word'] = lefts['word'] + '-'
    lefts = lefts.rename(columns={'word': 'link', 'link': 'word'})
    df['link'] = df['link'] + '+'
    links = pd.concat([lefts, df], axis=0, ignore_index=True, sort=True)

    return links


def mst2disjuncts(lines, **kwargs):
    """
    Create data frame and fill it out with words and protodisjuncts, obtained from .ull file(s).

    :param lines:       Text lines, obtained from .ull file(s)
    :param kwargs:      Argument dictionary.
    :return:            Pandas data frame filled with words and protodisjuncts.
    """
    logger = logging.getLogger(__name__ + ".mst2disjuncts")

    lw = kwa('', 'left_wall', **kwargs)
    dot = kwa(False, 'period', **kwargs)
    min_word_count = kwa(1, 'min_word_count', **kwargs)                 # 190417
    min_link_count = kwa(1, 'min_link_count', **kwargs)

    if len(lines[-1]) > 0: lines.append([])
    pairs = []

    # Temporary dictionaries for links and words of one sentence. Cleanup is done in save_djs.
    links = dict()
    words = dict()

    # sl: sentences as lists of words                                   # 190417
    sl = [x for x in [l.split() for l in lines] if len(x) > 0 and
          not (len(x) in [4, 5] and x[0].isdigit() and x[2].isdigit())]
    # tokens: words with counts >= min_word_count                       # 190417
    tokens = {w: c for w, c in Counter([w for s in sl for w in s]).items()
              if c >= min_word_count}

    # logger.debug(f"tokens: {tokens}")

    # if lw not in ['', 'none']: tokens['###LEFT-WALL###'] = 1            # 190424
    # if dot: tokens['.'] = 1                                             # 190424

    if lw in ['', 'none']:
        if '###LEFT-WALL###' in tokens:
            tokens.pop('###LEFT-WALL###')
    else:
        if '###LEFT-WALL###' not in tokens:
            tokens['###LEFT-WALL###'] = 1

    if not dot and "." in tokens:
        tokens.pop(".")

    def save_djs(words, links):
        if len(links) > 0:
            for k, v in links.items():
                if k in words:
                    if len(v) == 1:
                        disjunct = words[abs(list(v)[0])] \
                                   + ('+' if list(v)[0] > 0 else '-')
                    else:
                        l = sorted([x for x in v if abs(x) in words and x <= 0],
                                   reverse=True)
                        r = sorted([y for y in v if y in words and y > 0])
                        disjunct = ' & '.join([words[abs(z)]
                                               + ('+' if z > 0 else '-')
                                               for z in (l + r)])
                    pairs.append([words[k], disjunct])
        links = {}
        words = {}
        return words, links

    for line in lines:
        if len(line) > 1:
            if line[0].isdigit():
                x = line.split()

                # Only link lines, obtained from .ull-file, are taken into account
                if len(x) in [4, 5] and x[0].isdigit() and x[2].isdigit() \
                        and x[1] in tokens and x[3] in tokens:          # 190417
                    if x[1] == '###LEFT-WALL###': x[1] = lw             # 190424
                    # try:  # FIXME: overkill? already checked by .isdigit lin3 85
                    i = int(x[0])           # left word index
                    j = int(x[2])           # right word index
                    # except: continue
                    words[i] = x[1]         # left word
                    words[j] = x[3]         # right word

                    # Each word (marked by the index) has a set of linked word indexes
                    #   where left indexes are saved negative while right ones are saved positive.
                    if i in links:
                        links[i].add(j)
                    else: links[i] = set([j])
                    if j in links:
                        links[j].add(-i)
                    else: links[j] = set([-i])
                else:  # sentence starting with digit = same as next else
                    words, links = save_djs(words, links)
            else:  # sentence starting with letter
                words, links = save_djs(words, links)
        else:  # empty line or last LR = same as previous else
            words, links = save_djs(words, links)

    df = pd.DataFrame(pairs, columns=['word','link'])
    df['count'] = 1

    # logger.debug(str(df))
    return df


def files2links(**kwargs):  # 2018 legacy, 2019-02: » filter_lines, lines2links
    # kwargs['input_files'] » read files » return links DataFrame
    parse_mode = kwa('lower', 'parse_mode', **kwargs)
    # parse_mode: 'given'~ as parsed, 'lower', 'casefold'
    context = kwa(2, 'context', **kwargs)
    group = True  # always? » kwa(True, 'group', **kwargs) ?
    verbose = kwa('none', 'verbose', **kwargs)

    df = pd.DataFrame(columns=['word', 'link', 'count'])

    files = kwargs['input_files']
    if len(files) == 0:
        return df, {'parsed_links': 0, 'error': 'files2links: files = []'}
    lines = []
    for i, file in enumerate(files):
        with open(file, 'r') as f:
            lines.extend(f.readlines())

    if parse_mode == 'lower':
        lines = [' '.join([y.lower() if y != '###LEFT-WALL###'
                 else y for y in x.split()]) for x in lines]
    elif parse_mode == 'casefold':
        lines = [' '.join([y.casefold() if y != '###LEFT-WALL###'
                 else y for y in x.split()]) for x in lines]

    response = corpus_stats(lines)
    ordnung = ['word', 'link', 'count']
    cdf = mst2connectors(lines, **kwargs)[ordnung]
    ddf = mst2disjuncts(lines, **kwargs)[ordnung]

    unique_connectors = cdf.groupby('link', as_index=False).sum()
    avg_connector_count = round(len(cdf)/len(unique_connectors), 1)
    unique_djs = ddf.groupby('link', as_index=False).sum()
    avg_disjunct_count = round(len(ddf)/len(unique_djs), 1)
    unique_seeds = ddf.groupby(['word', 'link'], as_index=False).sum()
    avg_seed_count = round(len(ddf) / len(unique_seeds), 1)

    ddf['djlen'] = ddf['link'].apply(lambda x: x.count('&') +1)
    avg_disjunct_length = float(round(ddf['djlen'].mean(), 1))
    max_disjunct_length = int(ddf['djlen'].max())

    response['corpus_stats'].extend([
        ['Unique connectors number', len(unique_connectors)],
        ['Total  connectors count ', len(cdf)],
        ['Average connector count ', avg_connector_count],
        ['Unique disjuncts number', len(unique_djs)],
        ['Total  disjuncts count ', len(ddf)],
        ['Average disjunct count ', avg_disjunct_count],
        ['Average disjunct length', avg_disjunct_length],
        ['Maximum disjunct length', max_disjunct_length],
        ['Unique seeds number', len(unique_seeds)],
        ['Total  seeds count ', len(ddf)],
        ['Average seed count ', avg_seed_count]])

    if context > 1:
        df = ddf
        terms = 'disjuncts'
    elif context == 1:
        df = cdf
        terms = 'connectors'
    else:
        df = mst2words(lines, **kwargs)
        terms = 'words'  # legacy, not used  # FIXME:DEL?

    if group:  # Always True?  # FIXME:DEL?
        df = df.groupby(['word','link'], as_index=False).sum() \
            .sort_values(by=['count', 'word', 'link'],
                         ascending=[False, True, True]) \
            .reset_index(drop=True)

    response.update({
        'terms': terms,
        'parsed_links': sum(df['count']),
        'unique_links': len(df),
        'unique_words': len(set(df['word'].tolist())),
        'unique_terms': len(set(df['link'].tolist())),
        'word-term_pairs': len(df.groupby(['word', 'link'],
                                          as_index=False).sum())
    })

    return df, response


def filter_lines(lines, **kwargs):                                      # 90216
    # TODO: logger = logging.getLogger(__name__ + ".filter_lines")
    max_sentence_length = kwa(99, 'max_sentence_length', **kwargs) + 1
    max_unparsed_words = kwa(0, 'max_unparsed_words', **kwargs) + 1
    if lines[-1] != '': lines.append('')
    filtered_lines = []   # list of lines to return
    parsed_sentence = []  # list of lines: sentence + parses
    linked_words = set()  # linked words numbers
    parsed_words = set()  # "parsed" (not [...]) word numbers in the sentence
    for line in lines:
        x = line.split()
        if len(x) in [4, 5] and x[0].isdigit() and x[2].isdigit():
            parsed_sentence.append(line)
            if int(x[0]) > 0 and x[3] != '.':
                linked_words.add(int(x[0]))
                linked_words.add(int(x[2]))
        else:  # empty line or new sentence
            if len(parsed_sentence) > 0:
                if len(parsed_words) < max_sentence_length:
                    if non_parsed_words + len(parsed_words - linked_words) \
                            < max_unparsed_words:
                        filtered_lines.extend(parsed_sentence)
                        filtered_lines.append('')
                parsed_sentence = []
            if len(x) > 0:  # else:  # new sentence:
                parsed_sentence = [line]
                if x[-1] == '.': x = x[:-1]
                parsed_words = set([i+1 for i, w in enumerate(x)
                                    if w[0] != '[' and w[-1] != ']'])
                non_parsed_words = len(x) - len(parsed_words)
                linked_words = set()
            else: continue

    return filtered_lines, corpus_stats(filtered_lines)


def lines2links(lines, **kwargs):                                       # 190410
    logger = logging.getLogger(__name__ + ".lines2links")
    context = kwa(2, 'context', **kwargs)
    group = True  # always? » kwa(True, 'group', **kwargs)? FIXME:DEL?

    lines, re = filter_lines(lines, **kwargs)
    if len(lines) < 1:                                                  # 190410
        df = pd.DataFrame(columns=['word','link'])
        return df, {'filter_lines_error': 'empty_filtered_set'}

    # df = pd.DataFrame(columns=['word', 'link', 'count'])
    if context > 1:  # ddf - disjuncts DataFrame
        df = mst2disjuncts(lines, **kwargs)[['word', 'link', 'count']]

        unique_djs = df.groupby('link', as_index = False).sum()

        avg_disjunct_count = round(len(df) / len(unique_djs), 1)
        df['djlen'] = df['link'].apply(lambda x: x.count('&') + 1)
        avg_disjunct_length = float(round(df['djlen'].mean(), 1))
        max_disjunct_length = int(df['djlen'].max())
        re['corpus_stats'].extend([
            ['Unique disjuncts number', len(unique_djs)],
            ['Total  disjuncts count ', len(df)],         # FIXME!
            ['Average disjunct count ', avg_disjunct_count],
            ['Average disjunct length', avg_disjunct_length],
            ['Maximum disjunct length', max_disjunct_length]])
        # TODO: re-calculate stats on df filtered in mst2words with min_word_count?

    elif context == 1:  # cdf - connectors DataFrame
        df = mst2connectors(lines, **kwargs)[['word', 'link', 'count']]  # cdf
        unique_connectors = df.groupby('link', as_index = False).sum()
        avg_connector_count = round(len(df) / len(unique_connectors), 1)
        re['corpus_stats'].extend([
            ['Unique connectors number', len(unique_connectors)],
            ['Total  connectors count ', len(df)],
            ['Average connector count ', avg_connector_count]])

    else:  # unused legacy: wdf - words DataFrame - word-based word space
        df = mst2words(lines, **kwargs)
        unique_words = df.groupby('word', as_index = False).sum()
        avg_word_count = round(len(df) / len(unique_words), 1)
        re['corpus_stats'].extend([
            ['Unique words number', len(unique_words)],
            ['Total  words count ', len(df)],
            ['Average word count ', avg_word_count]])

    unique_seeds = df.groupby(['word', 'link'], as_index = False).sum()
    avg_seed_count = round(len(df) / len(unique_seeds), 1)
    re['corpus_stats'].extend([
        ['Unique seeds number', len(unique_seeds)],
        ['Average seed count ', avg_seed_count]])

    if group:  # Always True?  # FIXME:DEL?
        df = df.groupby(['word', 'link'], as_index=False).sum() \
            .sort_values(by=['count', 'word', 'link'],
                         ascending=[False, True, True]) \
            .reset_index(drop=True)

    # logger.debug(str(df))
    return df, re

# Notes:

# 180725 POC 0.5 restructured - this module was src/space/poc05.py
# 180802 corpus_stats ⇒ corpus_stats.py
# 180829 files2links: Average, max disjunct lengths
# 181024 line 24: cure case of MST parses file last line not ending with CR
# 181231 cleanup » release 0.7.0
# 190217 filter_lines, lines2links
# 190325 `== 4` » `in [4, 5]` :: allow for parses with added "statistical information"
# 190410 lines2links: check length of filtered dataset > 0
# 190417 mst2disjuncts: prune words with counts < min_word_count
# 190424 Add '###LEFT-WALL###' and '.' to tokens - lines 59, 60
