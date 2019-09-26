# language-learning/src/learner.py                                      # 190410
import logging
import os, time  # pickle, numpy as np, pandas as pd
from copy import deepcopy
from shutil import copy2 as copy
from collections import OrderedDict, Counter
from .utl import UTC, kwa, sec2string
from .read_files import check_dir, check_mst_files
from .preprocessing import filter_links
from .pparser import files2links, lines2links, filter_lines
from .corpus_stats import corpus_stats
from .category_learner import learn_categories, cats2list
from .grammar_inducer import induce_grammar, add_disjuncts, check_cats
from .generalization import generalize_categories, generalize_rules, \
                            generalise_rules, add_upper_level
from .write_files import list2file, save_link_grammar, save_cat_tree
from ..common.cliutils import handle_path_string

__all__ = ['learn_grammar', 'learn']


def learn(**kwargs):
    def reverse_count(count: int) -> float:
        return 1.0 / float(count) if count else 0.0

    logger = logging.getLogger(__name__ + ".learn")
    verbose = kwa('none', 'verbose', **kwargs)
    start = time.time()
    log = OrderedDict({'start': str(UTC()), 'learn_grammar': 'v.0.7.81231'})
    # input_parses = kwargs['input_parses']
    # output_grammar = kwargs['output_grammar']
    input_parses = handle_path_string(kwargs['input_parses'])
    output_grammar = handle_path_string(kwargs['output_grammar'])

    # WSD: word_sense disambiguation                                    # 190408
    wsd_symbol = kwa('', 'wsd_symbol', **kwargs)
    # prj_dir: project directory
    if os.path.isdir(output_grammar):
        prj_dir = output_grammar
    elif os.path.isfile(output_grammar):
        prj_dir = os.path.dirname(output_grammar)
    else:  # create prj_dir
        if check_dir(output_grammar, True, verbose):
            prj_dir = output_grammar
    log.update({'project_directory': prj_dir})

    output_categories = kwa('', 'output_categories', **kwargs)
    if output_categories == '':
        output_categories = prj_dir
    output_statistics = kwa('', 'output_statistics', **kwargs)
    if output_statistics != '':
        if os.path.isfile(output_statistics):
            corpus_stats_file = output_statistics
        elif os.path.isdir(output_statistics):
            corpus_stats_file = output_statistics + '/corpus_stats.txt'
        else: corpus_stats_file = prj_dir + '/corpus_stats.txt'
    else: corpus_stats_file = prj_dir + '/corpus_stats.txt'

    temp_dir = kwa('', 'temp_dir', **kwargs)  # FIXME: temp_dir/tmpath  # 90221
    tmpath = kwa('', 'tmpath', **kwargs)  # legacy
    if temp_dir != '':
        # if os.path.isdir(temp_dir):
        if check_dir(temp_dir, False, verbose):
            tmpath = temp_dir
        else: tmpath = os.path.abspath(os.path.join('..')) + '/tmp'
    elif tmpath == '':                              # FIXME: stub!      # 90221
        # if check_dir(prj_dir + '/tmp', True, verbose):
        #    tmpath = prj_dir + '/tmp'
        tmpath = os.path.abspath(os.path.join('..')) + '/tmp'           # 90221
    if check_dir(tmpath, True, verbose):
        kwargs['tmpath'] = tmpath
        temp_dir = tmpath

    parse_mode = kwa('lower', 'parse_mode', **kwargs)  # 'casefold' » default?
    context = kwa(2, 'context', **kwargs)
    clustering = kwa('kmeans', 'clustering', **kwargs)  # TODO: update
    cats_gen = kwa('off', 'categories_generalization', **kwargs)
    grammar_rules = kwa(2, 'grammar_rules', **kwargs)
    verbose = kwa('none', 'verbose', **kwargs)

    files, re01 = check_mst_files(input_parses, verbose)
    log.update(re01)
    if 'error' in re01:  # FIXME: assert ?
        print('learner.py » learn » check_mst_files » re01:\n', re01)
        return {'error': 'input_files'}, log
    kwargs['input_files'] = files

    '''Read parses, extract links to DataFrame (2018), + filter sentences'''

    if 'ull_parsing' in kwargs and kwargs['ull_parsing'] == "180829":
        links, re02 = files2links(**kwargs)
        # links: pd.DataFrame(columns=['word', 'link', 'count'])
    else:                                                               # 190417
        links, re02 = filter_links(files, **kwargs)
    log.update(re02)

    if len(links) < 1:  # Requested by @alexei-gl, issue #209           # 190426
        raise ValueError("Empty filtered dataset with max_sentence_length = "
                         + str(kwa(99, 'max_sentence_length', **kwargs))
                         + ", max_unparsed_words = "
                         + str(kwa(0, 'max_unparsed_words', **kwargs)))

    if 'corpus_stats' in log:
        list2file(log['corpus_stats'], corpus_stats_file)
        log.update({'corpus_stats_file': corpus_stats_file})
    else:  # FIXME: raise error / assert ?
        return {'error': 'input_files'}, log

    '''Learn word categories'''

    categories, re03 = learn_categories(links, **kwargs)
    log.update(re03)
    if 'corpus_stats' in log and 'cleaned_words' in re03:
        log['corpus_stats'].extend([
            ['Number of unique words after cleanup', re03['cleaned_words']],
            ['Number of unique features after cleanup', re03['clean_features']]])
        list2file(log['corpus_stats'], corpus_stats_file)

    '''Generalize word categories'''  # FIXME: issues with add_upper_level
    '''
    if cats_gen == 'jaccard' or (cats_gen == 'auto' and clustering == 'group'):
        categories, re04 = generalize_categories(categories, **kwargs)
        log.update(re04)
    elif cats_gen == 'cosine' or (cats_gen == 'auto' and clustering == 'kmeans'):
        log.update({'generalization':
                    'none: vector-similarity based - maybe some day...'})
    else:
        log.update({'generalization': 'none: ' + str(cats_gen)})
    #'''

    '''Learn grammar'''

    if grammar_rules != context:
        context = kwargs['context']
        kwargs['context'] = kwargs['grammar_rules']
        links, re06 = files2links(**kwargs)
        kwargs['context'] = context

    categories = add_disjuncts(categories, links, **kwargs)
    # TODO: check every category has disjuncts?         # 81204,  blocked 81207
    #  ? categories = prune_cats(categories, **kwargs)  # [F] ⇒ induce_grammar?
    #  ? re = check_cats(categories, **kwargs)

    # "Fully connected rules": every cluster connected to all clusters
    if grammar_rules < 0:
        rules = deepcopy(categories)
        clusters = [i for i, x in enumerate(rules['cluster'])
                    if i > 0 and x is not None]
        rule_list = [tuple([-x]) for x in clusters] + \
                    [tuple([x]) for x in clusters]
        for cluster in clusters:
            rules['disjuncts'][cluster] = set(rule_list)
    else:
        rules, re07 = induce_grammar(categories, **kwargs)

    lengths = [len(x) for x in rules['disjuncts']]

    '''Generalize grammar rules'''

    if 'rules_generalization' in kwargs:
        if kwargs['rules_generalization'] in ['jaccard', 'legacy']:
            rules, re08 = generalize_rules(rules, **kwargs)
            log.update(re08)
        elif kwargs['rules_generalization'] in \
                ['hierarchical', 'fast', 'updated', 'new']:
            rules, re08 = generalise_rules(rules, **kwargs)
            log.update(re08)

    if '+' in verbose:
        log['rule_sizes'] = dict(Counter(
            [len(x) for i, x in enumerate(rules['words'])
             if rules['parent'][i] == 0]))

    '''Save word category tree, Link Grammar files: cat_tree.txt, dict...dict'''

    # 81126 3rd hierarchy level over rules:
    if 'top_level' in kwargs and kwargs['top_level'] > -1:
        tree, _ = add_upper_level(rules, **kwargs)
        re09 = save_cat_tree(tree, output_categories, verbose='none')
    else:
        re09 = save_cat_tree(rules, output_categories, verbose='none')
    # TODO: check file save error?
    log.update(re09)

    # # Disjunct cost function dictionary
    # cost_ptr_dict = {"reverse_count": reverse_count}
    #
    # # Select disjunct cost function according to specified parameter if "add_disjunct_costs" is specified
    # cost_function = cost_ptr_dict[kwargs.get("disjunct_cost_formula", "reverse_count")] \
    #     if kwargs.get("add_disjunct_costs", False) == True else None

    # Save 'rules' into proper Link Grammar dictionary file
    re10 = save_link_grammar(rules, output_grammar, grammar_rules, "", "", kwargs.get("add_disjunct_costs", False))

    log.update(re10)
    log.update({'finish': str(UTC())})
    log.update({'grammar_learn_time': sec2string(time.time() - start)})

    return rules, log  # 81126 + rules to count clusters in .ipynb tests  FIXME:DEL?


def learn_grammar(**kwargs):  # Backwards compatibility with legacy calls
    rules, log = learn(**kwargs)
    return log


# Notes:

# 80802: poc05.py/category_learner ⇒ category_learner.py/learn_categories
# 80825: random clusters, interconnected ⇒ cleanup, commit 80828
# 81021 cleanup: Grammar Learner 0.6
# 81102 sparse wordspace agglomerative clustering
# 81126 def learn_grammar ⇒ def learn + decorator
# 81204-07 test and block (snooze) data pruning with max_disjuncts, etc...
# 81231 cleanup
# 190221 tweak temp_dir, tmpath for Grammar Learner tutorial - FIXME line 56...
# 190409 Optional WSD, kwargs['wsd_symbol']
# 190410 resolved empty filtered parses dataset issue
# 190426 raise ValueError in case of empty filtered dataset (requested by pipeline)
