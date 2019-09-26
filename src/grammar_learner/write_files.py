# language-learning/src/grammar_learner/write_files.py                  # 90119
import logging
import os, linkgrammar
from collections import OrderedDict
from copy import deepcopy
from .utl import UTC
from typing import Tuple, Union, List


def list2file(lst, out_file):
    string = ''
    for i, line in enumerate(lst):
        if i > 0: string += '\n'
        for j, x in enumerate(line):
            if isinstance(x, (list, set, tuple)):
                z = ' '.join(str(y) for y in x)
            else:
                try:
                    z = str(x)
                except TypeError:
                    z = 'ERROR'
            if j > 0: string += '\t'
            string += z
    with open(out_file, 'w') as f:
        f.write(string)
    return string


def rules2list(rules_dict, grammar_rules = 2, verbose = 'none'):
    """
    Convert rules from dictionary structure to list structure

    :param rules_dict:          {'cluster': [], 'words': [], } ⇒ return rules []
    :param grammar_rules:       kwargs['grammar_rules']: 1 - connectors, 2 - disjuncts
    :param verbose:             Verbosity argument
    :param cost_func:
    :return:                    Rule list: [[<cluster>, [<word list>], '', '', [(<disjunct>, <cost>)...]]...]
    """
    logger = logging.getLogger(__name__ + ".rules2list")
    # logger.debug("rules_dict: " + str(rules_dict))

    # sign = lambda x: ('+', '-')[x < 0]

    def disjunct(x, cluster_list, cluster):
        """
        That's where a connector turns from numeric into character representation

        :param x:               Other cluster ID (integer)
        :param cluster_list:    Cluster name list (letters)
        :param cluster:         Cluster name (letter corresponding to current cluster name)
        :return:                Connector (two cluster names stitched together followed by direction sign)
        """
        if x < 0:
            return cluster_list[abs(x)] + cluster + '-'
        else:
            return cluster + cluster_list[abs(x)] + '+'

    DJ_VECTOR, DJ_COST = 0, 1

    # Using different dictionary data entry when disjuncts are followed by costs
    add_cost = True if rules_dict.get("cl_dj_cst", None) is not None else False
    dj_tuples = rules_dict['cl_dj_cst'] if add_cost else rules_dict['disjuncts']

    rules = []
    for i, cluster in enumerate(rules_dict['cluster']):
        if i == 0 or cluster is None:
            continue

        rule = [cluster]
        rule.append(sorted(rules_dict['words'][i]))

        if grammar_rules in [1,-1]:  # interconnected connector-based rules
            lefts = set()
            rights = set()
            for djtuple in rules_dict['disjuncts'][i]:
                for x in djtuple:
                    if x < 0:
                        lefts.add(disjunct(x, rules_dict['cluster'], cluster))
                    else:
                        rights.add(disjunct(x, rules_dict['cluster'], cluster))
            rule.append(sorted(lefts))
            rule.append(sorted(rights))
            rule.append('')
        else:  # rules: disjuncts
            rule.append('')  # lefts
            rule.append('')  # rights

            disjuncts = []

            # for djtuple in rules_dict['disjuncts'][i]:
            for djtuple in dj_tuples[i]:
                try:
                    vector, cost = (djtuple[DJ_VECTOR], djtuple[DJ_COST]) if add_cost else (djtuple, 1.0)

                    dj = ' & '.join(
                        [disjunct(x, rules_dict['cluster'], cluster) for x in vector])

                    disjuncts.append((dj, cost))

                except TypeError:
                    logger.critical(f'- wrong djtuple? - {djtuple}')

            rule.append(sorted(disjuncts, key=lambda x: x[0]))
            # rule.append(sorted(disjuncts))
        rules.append(rule)

    return rules


def save_link_grammar(rules, output_grammar, grammar_rules = 2,
                      header = '', footer = '',       # legacy FIXME:DEL?
                      add_cost = False):
    """
    Save grammar rules into properly formated Link Grammar dictionary file

    :param rules:           Rule tree represented by list of lists:
                            [<cluster1_record>, <cluster2_record>,..., <clustern_record>]
                            where <clusterx_record> is:
                            [ <cluster_id>, [<words>], '', '',
                                    [(<disj1>, <cost1>),(<disj2>, <cost2>), ..., (<disjn>, <costn>)] ]
    :param output_grammar:  Path to the output dictionary file.
    :param grammar_rules:   Integer value: 1 ⇒ connectors, 2+ ⇒ disjuncts
    :param header:          Header text string (legacy?)
    :param footer:          Footer test string (legacy?)
    :param cost_func:       Disjunct cost function pointer.
    :return:                Responce dictionary
    """
    CLUSTER, WORDS, LEFTS, RIGHTS, DISJUNCTS = 0, 1, 2, 3, 4

    def wrap_disjunct(disjunct: Union[str, Tuple[str, str]]) -> str:
        """ Wrap disjunct into square brackets if cost is provided in tuple """

        # If there is a tuple such as (DISJUNCT, COST)
        if isinstance(disjunct, tuple):
            return f'[{disjunct[0]}]{disjunct[1]}' if add_cost else f'({str(disjunct[0])})'

        # Otherwise do it in an old fashion style
        else:
            return f'({str(disjunct)})'

    logger = logging.getLogger(__name__ + ".save_link_grammar")
    # logger.debug(f"Rules:\n{rules}")

    if type(rules) is dict:
        rules = rules2list(rules, grammar_rules)

    # logger.debug(f"Rules:\n{rules}")

    line_list = list()
    clusters = set()
    for rule in rules:
        line = ''
        if len(rule[LEFTS]) > 0 and len(rule[RIGHTS]) > 0:
            line += '{' + ' or '.join(
                str(x) for x in rule[LEFTS]) + '} & {' + ' or '.join(
                str(y) for y in rule[RIGHTS]) + '}'
        else:
            if len(rule[LEFTS]) > 0:
                line += ' or '.join('(' + str(x) + ')' for x in rule[LEFTS])
            elif len(rule[RIGHTS]) > 0:
                line += ' or '.join('(' + str(x) + ')' for x in rule[RIGHTS])
        if len(rule[DISJUNCTS]) > 0:
            if line != '': line += ' or '
            line += ' or '.join(wrap_disjunct(x) for x in rule[DISJUNCTS])

        cluster_number = '% ' + str(rule[CLUSTER]) + '\n'  # comment line: cluster
        cluster_and_words = ' '.join(
            '"' + word + '"' for word in rule[WORDS]) + ':\n'
        line_list.append(cluster_number + cluster_and_words + line + ';\n')
        clusters.add(rule[0])

    line_list.sort()  # FIXME: overkill?

    if os.path.isfile(output_grammar):
        out_file = output_grammar
    elif os.path.isdir(output_grammar):
        out_file = output_grammar
        if out_file[-1] != '/': out_file += '/'
        out_file += 'dict_'
        out_file = out_file + str(len(clusters)) + 'C_' + str(UTC())[:10]
        if linkgrammar.__version__ == '5.4.4':  # 190128: restore LG 5.4.4 option
            out_file = out_file + '_0006.4.0.dict'
        else: out_file = out_file + '_0007.4.0.dict'
    else:
        raise FileNotFoundError('File not found', output_grammar)

    if header == '':
        header = '% Grammar Learner v.0.7 ' + str(UTC()) \
                 + '\n<dictionary-version-number>: V0v0v7+;\n'
        if linkgrammar.__version__ == '5.4.4':  # 190128: restore LG 5.4.4 option
            header = '% Grammar Learner v.0.6 ' + str(UTC()) \
            + '\n<dictionary-version-number>: V0v0v6+;\n'
    header = header + '<dictionary-locale>: EN4us+;'

    unknown_word = '<UNKNOWN-WORD>: XXX+;'
    if linkgrammar.__version__ == '5.4.4':  # 190128: restore LG 5.4.4 options
        unknown_word = 'UNKNOWN-WORD: XXX+;'

    if footer == '':
        footer = '% ' + str(len(clusters)) + ' word clusters, ' \
                 + str(len(rules)) + ' Link Grammar rules.\n'  # \
                # + '% Link Grammar file saved to: "' + out_file + '"'
                # 90110: Link Grammar sometimes parses (commented) filename 
    lg = header + '\n\n' + '\n'.join(line_list) + '\n' + unknown_word + '\n\n' + footer
    # lg = lg.replace('@', '.')  # 80706 WSD: word@1 ⇒ word.1  # removed  190804

    with open(out_file, 'w') as f: f.write(lg)

    response = OrderedDict([('grammar_file', out_file),
                            ('grammar_clusters', len(clusters)),
                            ('grammar_rules', len(rules))])
    return response


def save_category_tree(category_list, tree_file, verbose = 'none'):
    logger = logging.getLogger(__name__ + ".save_category_tree")
    cats = category_list
    clusters = {}
    m = 0
    for i, x in enumerate(cats):
        if x[0] not in clusters: clusters[x[0]] = []
        clusters[x[0]].append(i)
        if x[2] > m: m = x[2]
    tree = []
    for k, v in clusters.items():
        if len(v) == 1:
            tree.append(cats[v[0]])
        elif len(v) > 1:
            words = []
            similarities = []
            for j in v:
                words.extend(cats[j][4])
                similarities.extend(cats[j][5])
            tree.append(
                [cats[v[0]][0], 0, m + 1, cats[v[0]][3], words, similarities])
            for j in v:
                tree.append(
                    ['', m + 1, cats[j][2], cats[j][3], cats[j][4], cats[j][5]])
        else:
            logger.critical(f'WTF? {k} {v}')

    _ = list2file(tree, tree_file)

    return {'tree_file': tree_file}


def save_cat_tree(cats, output_categories, verbose = 'none'):
    # cats: {'cluster':[], 'words':[], ...}
    tree_file = output_categories
    if os.path.isdir(tree_file):  # received directory ⇒ auto file name
        if tree_file[-1] != '/': tree_file += '/'
        n_cats = len([x for i, x in enumerate(cats['cluster'])
                      if i > 0 and x is not None])
        tree_file += (str(n_cats) + '_cat_tree.txt')

    categories = []
    for i, cluster in enumerate(cats['cluster']):
        if i == 0:
            continue
        category = []
        if cats['cluster'][i] is not None:
            category.append(cats['cluster'][i])
        else:
            category.append('')
        category.append(cats['parent'][i])
        category.append(i)
        category.append(round(cats['quality'][i], 2))
        wordz = deepcopy(sorted(cats['words'][i]))
        #-wordz = [x.replace('@', '.') for x in wordz]  # WSD           # 190408
        category.append(wordz)  # 80704+06 tmp hack FIXME
        category.append(cats['similarities'][i])
        # -category.append(cats['children'][i])
        categories.append(category)

    _ = list2file(categories, tree_file)

    return {'cat_tree_file': tree_file}

# Notes:

# 80725 POC 0.1-0.4 deleted, 0.5 restructured, imports updated
# 80827 rules = -1/-2: interconnected clusters, connector/disjunct based rules
# 80929 save_link_grammar ⇒ 0.6
# 81003 save_link_grammar: Link Grammar ⇒ 5.5.1: UNKNOWN-WORD ⇒ <UNKNOWN-WORD>
# 81105 lines 121-123: ready to upgrade Link Grammar 5.4.4 ⇒ 5.5.1
# 81108 lines 116-125: check Link Grammar version and adapt grammar rules
# 81231 cleanup, version = 0.7 (LG 5.5.1), 0.6 (LG 5.4.4)
# 90110 remove filename
# 90119 remove Link Grammar 5.4.4 options (v.0.6)
# 90128 restore Link Grammar 5.4.4 'UNKNOWN-WORD: XXX+;' option
# 190428 WSD ⇒ learner: optional, configurable
