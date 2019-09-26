# language-learning/src/grammar_learner/generalization.py               # 81231
import logging
from copy import copy, deepcopy
from operator import itemgetter
from .clustering import cluster_id
from .utl import kwa


def aggregate(categories, threshold, similarity_function, verbose = 'none'):
    logger = logging.getLogger(__name__ + ".aggregate")
    cats = deepcopy(categories)
    cats.pop('dj_counts', None)
    similar_clusters = []
    similarities = []
    ncats = len(cats['words'])

    for i, x in enumerate(cats['djs']):
        if i == 0:
            continue
        if cats['parent'][i] > 0:
            continue
        for j in range(i + 1, ncats):
            if cats['parent'][j] > 0:
                continue
            similarity = similarity_function(x, cats['djs'][j])
            if similarity > threshold:
                similar_clusters.append([i, j, similarity])
            #? if similarity > aggregate and similarity < merge:
            similarities.append(round(similarity, 2))

    merges = [{x[0], x[1]} for x in similar_clusters if x[2] > threshold]
    merged = []
    for m, mset in enumerate(merges):
        if m in merged:
            continue
        for k in range(m + 1, len(merges)):
            if k in merged:
                continue
            if len(mset & merges[k]) > 0:
                if mset | merges[k] not in merges:
                    merges.append(mset | merges[k])
                merged.extend([m, k])
    merges = [x for i, x in enumerate(merges) if i not in merged]

    for mset in merges:
        new_cluster_id = len(cats['parent'])
        cats['cluster'].append(cluster_id(new_cluster_id, new_cluster_id))
        # TODO: check new_cluster_id > 25**n ⇒ change n_letters in _id's ?
        cats['parent'].append(0)
        cats['children'].append(mset)
        cats['words'].append(set())
        cats['disjuncts'].append(set())
        cats['djs'].append(set())
        cats['counts'].append(0)
        cats['quality'].append(threshold)
        for cluster in mset:
            cats['parent'][cluster] = new_cluster_id
            cats['words'][new_cluster_id].update(cats['words'][cluster])
            cats['disjuncts'][new_cluster_id].update(cats['disjuncts'][cluster])
            cats['djs'][new_cluster_id].update(cats['djs'][cluster])
            cats['counts'][new_cluster_id] += cats['counts'][cluster]
            # cats['similarities'][new_cluster_id]... TODO?
        cats['similarities'].append(
            [0 for word in cats['words'][new_cluster_id]])

        d = {x: (i + 1) for i, x in
             enumerate(sorted(set([x for y in cats['disjuncts'] for x in y])))}
        cats['djs'] = [set([d[x] for x in y]) for y in cats['disjuncts']]
        # TODO? sort by frequency?

    return cats, sorted(set(similarities), reverse = True)

import sys

def reorder(cats):
    # logger = logging.getLogger(__name__ + ".reorder")
    # logger.debug("cats" + str(cats))

    # Parents: top clusters
    top_clusters = [(i, len(cats['words'][i])) for i, x in
                    enumerate(cats['parent']) if x == 0 and i > 0]

    top = [0] + [x[0] for x in
                 sorted(top_clusters, key = itemgetter(1), reverse = True)]
    ordnung = copy(top)  # deepcopy(top)? - copy list objects as well

    # Children branches
    def branch(i, children):
        if children[i] == 0:
            return []
        else:
            x = []
            # TODO? define order of children?
            for j in children[i]:
                x.append(j)
                y = branch(j, children)
                if len(y) > 0:
                    x.extend(y)
            return x

    for j, k in enumerate(top):  # top, not ordnung - only top level clusters
        branchi = branch(k, cats['children'])
        if len(branchi) > 0:
            ordnung.extend(branchi)

    new_cats = {}
    new_cats['parent'] = [ordnung.index(cats['parent'][i]) for i in ordnung]

    n = sum(1 for i in new_cats['parent'] if i == 0)
    new_cats['cluster'] = [cluster_id(i, n) if x == 0 else None
                           for i, x in enumerate(new_cats['parent'])]

    for key in cats.keys():
        if key not in ['cluster', 'parent', 'word_counts']:
            new_cats[key] = [cats[key][i] if i < len(cats[key]) else None
                             for i in ordnung]

    for i, item in enumerate(new_cats['children']):
        if type(item) is set and len(item) > 0:
            new_cats['children'][i] = set([ordnung.index(x) for x in item])

    rules = [i for i, x in enumerate(new_cats['parent'])
             if (x == 0 and i > 0)]

    sign = lambda x: (1, -1)[x < 0]

    for rule in rules:
        if len(new_cats['disjuncts'][rule]) > 0:
            new_rule = []
            for disjunct in new_cats['disjuncts'][rule]:
                new_dj = []
                for index in disjunct:
                    new_dj.append(ordnung.index(abs(index)) * sign(index))
                new_rule.append(tuple(new_dj))
            new_cats['disjuncts'][rule] = set(new_rule)
        else:  # 81130: prune clusters with empty dj sets  # TODO: update
            print(('rule', rule, '- 0 djs in new_cats[disjuncts][rule]:',
                   new_cats['disjuncts'][rule]))

    return new_cats


def jaccard(x, y):
    try:
        xx = set(x)
        yy = set(y)
    except:
        return 0
    if len(xx) == 0 or len(yy) == 0:
        return 0
    elif len(xx.union(yy)):
        return len(xx.intersection(yy)) / len(xx.union(y))
    else:
        return 0


def squared(x, y):
    try:
        xx = set(x)
        yy = set(y)
    except:
        return 0
    if len(xx) == 0 or len(yy) == 0:
        return 0
    elif len(xx.union(yy)):
        return len(xx.intersection(yy)) ** 2 / len(xx) / len(yy)
    else:
        return 0


def generalize_categories(categories, **kwargs):  # 80717 [F] FIXME:DEL?
    # categories: {'cluster':[], 'words': [], 'disjuncts':[], ...}
    logger = logging.getLogger(__name__ + ".generalize_categories")
    aggregation = kwa('off', 'categories_generalization', **kwargs)
    merge_threshold = kwa(0.8, 'categories_merge', **kwargs)
    aggr_threshold = kwa(0.2, 'categories_aggregation', **kwargs)
    verbose = kwa('none', 'verbose', **kwargs)

    if aggregation == 'jaccard':
        threshold = merge_threshold
        cats, similarities = aggregate(categories, threshold, jaccard, verbose)
        # TODO: list of merged clusters - to delete
        # TODO: delete merged clusters
        z = len(similarities)
        sims = similarities
        while z > 1 and threshold > aggr_threshold:
            cats, similarities = aggregate(cats, threshold, jaccard, verbose)
            sims = [x for x in similarities if x < threshold]
            threshold = max(sims) - 0.01  # 0.001 ?
            z = len(sims)

        return reorder(cats), {'similarity_thresholds': sims}
        # !!! 81217 reorder [F] for (gen) cats (tests - Turtle) ⇒ [x]
    else:
        return categories, {'categories_generalization': 'none'}


def generalize_rules(categories, **kwargs):  # 80622
    # categories: {'cluster':[], 'words': [], 'disjuncts':[], ...}
    logger = logging.getLogger(__name__ + ".generalize_rules")
    merge_threshold = kwa(0.8, 'rules_merge', **kwargs)
    aggr_threshold = kwa(0.2, 'rules_aggregation', **kwargs)
    verbose = kwa('none', 'verbose', **kwargs)

    threshold = merge_threshold  # 0.8
    cats, similarities = aggregate(categories, threshold, jaccard, verbose)
    sims = [x for x in similarities]  # if x < threshold]
    threshold = max(sims) - 0.01
    # TODO: delete merged clusters?

    z = len(similarities)
    while z > 1 and threshold > aggr_threshold:
        cats, similarities = aggregate(cats, threshold, jaccard, verbose)
        sims = [x for x in similarities if x < threshold]
        threshold = max(sims) - 0.01
        z = len(sims)

    # Renumber connectors in disjuncts # TODO: for all clusters?
    clusters = [i for i, x in enumerate(cats['cluster'])
                if i > 0 and x is not None]

    sign = lambda x: (1, -1)[x < 0]
    counter = 0

    def ancestor(connector, parents):
        if parents[abs(connector)] == 0:
            return connector
        else:
            return ancestor(parents[abs(connector)], parents)

    for cluster in clusters:
        new_rule = []
        for disjunct in cats['disjuncts'][cluster]:
            new_dj = []
            for x in disjunct:
                new_dj.append(sign(x) * ancestor(abs(x), cats['parent']))
            new_rule.append(tuple(new_dj))
        cats['disjuncts'][cluster] = set(new_rule)

    return reorder(cats), \
           {'similarity_thresholds': sims, 'updated_disjuncts': counter}


def renumber(cats):  # 81121
    #  Renumber connectors in disjuncts
    clusters = [i for i, x in enumerate(cats['cluster'])
                if i > 0 and x is not None]
    sign = lambda x: (1, -1)[x < 0]

    def ancestor(connector, parents):
        if parents[abs(connector)] == 0:
            return connector
        else:
            return ancestor(parents[abs(connector)], parents)

    for cluster in clusters:
        new_rule = []
        for disjunct in cats['disjuncts'][cluster]:
            new_dj = []
            for x in disjunct:
                new_dj.append(sign(x) * ancestor(abs(x), cats['parent']))
            new_rule.append(tuple(new_dj))
        cats['disjuncts'][cluster] = set(new_rule)

    return cats


def generalise_rules(categories, **kwargs):  # 81121
    # categories: {'cluster':[], 'words': [], 'disjuncts':[], ...}
    generalisation = kwa('jaccard', 'rules_generalization', **kwargs)
    merge_threshold = kwa(0.8, 'rules_merge', **kwargs)
    aggr_threshold = kwa(0.2, 'rules_aggregation', **kwargs)
    verbose = kwa('none', 'verbose', **kwargs)

    if generalisation == 'hierarchical':  # updated 'jaccard' legacy
        threshold = merge_threshold  # 0.8
        cats, similarities = aggregate(categories, threshold, jaccard, verbose)
        sims = [x for x in similarities]  # if x < threshold]
        threshold = max(sims) - 0.01
        # TODO: delete merged clusters?
        z = len(similarities)
        while z > 1 and threshold > aggr_threshold:
            cats, similarities = aggregate(cats, threshold, jaccard, verbose)
            cats = renumber(cats)
            sims = [x for x in similarities if x < threshold]
            threshold = max(sims) - 0.01  # step-by-step hierarchy construction
            z = len(sims)

    else:  # 81120 1-step jaccard-based, iterate after dj connectors update
        threshold = aggr_threshold
        n_clusters = len([x for x in categories['parent'] if x == 0])
        dn = 1
        while dn > 0:
            cats, similarities = aggregate(categories, threshold, jaccard,
                                           verbose)
            cats = renumber(cats)
            n_cats = len([x for x in cats['parent'] if x == 0])
            print(f'n_clusters = {n_clusters}, n_cats = {n_cats}')
            dn = n_clusters - n_cats
            n_clusters = n_cats

    return reorder(cats), {'rules_generalization': 'hierarchical'}


def agglomerate(categories, threshold, similarity_function, verbose = 'none'):
    logger = logging.getLogger(__name__ + ".agglomerate")
    cats = deepcopy(categories)
    cats.pop('dj_counts', None)  # 81101 TODO: list ⇒ dict? restructure cats?
    cats.update({'top': deepcopy(cats['parent'])})  # 81123

    similarities = []
    similar_clusters = []
    ncats = len(cats['words'])
    for i, x in enumerate(cats['djs']):
        if i == 0:
            continue
        if cats['parent'][i] > 0:
            continue
        # if cats['top'][i] > 0: continue
        for j in range(i + 1, ncats):
            if cats['parent'][j] > 0:
                continue
            # if cats['top'][j] > 0: continue
            similarity = similarity_function(x, cats['djs'][j])
            if similarity > threshold:
                similar_clusters.append([i, j, similarity])
            # if similarity > aggregate and similarity < merge:
            similarities.append(round(similarity, 2))

    merged = []
    merges = [{x[0], x[1]} for x in similar_clusters if x[2] > threshold]
    for m, mset in enumerate(merges):
        if m in merged:
            continue
        for k in range(m + 1, len(merges)):
            if k in merged:
                continue
            if len(mset & merges[k]) > 0:
                if mset | merges[k] not in merges:
                    merges.append(mset | merges[k])
                merged.extend([m, k])
    merges = [x for i, x in enumerate(merges) if i not in merged]
    for mset in merges:
        new_cluster_id = len(cats['parent'])
        # new_cluster_id = len(cats['top'])  # TODO?
        # cats['cluster'].append(cluster_id(new_cluster_id, new_cluster_id))
        cats['cluster'].append(None)  # 81123
        cats['top'].append(0)  # 81123
        cats['parent'].append(0)  # TODO? append(None) & use top?
        cats['children'].append(mset)
        cats['words'].append(set())
        cats['disjuncts'].append(set())
        cats['djs'].append(set())
        cats['counts'].append(0)
        cats['quality'].append(threshold)

        for cluster in mset:
            cats['top'][cluster] = new_cluster_id  # 81123
            cats['parent'][cluster] = new_cluster_id  # TODO: don't change
            cats['words'][new_cluster_id].update(cats['words'][cluster])
            cats['disjuncts'][new_cluster_id].update(cats['disjuncts'][cluster])
            cats['djs'][new_cluster_id].update(cats['djs'][cluster])
            cats['counts'][new_cluster_id] += cats['counts'][cluster]
            # cats['similarities'][new_cluster_id]... TODO?
        cats['similarities'].append(
            [0 for word in cats['words'][new_cluster_id]])

        d = {x: (i + 1) for i, x in
             enumerate(sorted(set([x for y in cats['disjuncts'] for x in y])))}
        cats['djs'] = [set([d[x] for x in y]) for y in cats['disjuncts']]

    return cats, sorted(set(similarities), reverse = True)


def add_upper_level(categories, **kwargs):
    logger = logging.getLogger(__name__ + ".add_upper_level")
    generalisation = kwa(None, 'rules_generalization', **kwargs)
    merge_threshold = kwa(0.8, 'rules_merge', **kwargs)
    aggr_threshold = kwa(0.2, 'rules_aggregation', **kwargs)
    verbose = kwa('none', 'verbose', **kwargs)
    group_threshold = kwa(0.1, 'top_level', **kwargs)

    if generalisation in ['jaccard', 'hierarchical', 'legacy', 'new']:
        if group_threshold >= aggr_threshold:
            return categories, {'rules_agglomeration': 'no_top_level'}
        threshold = aggr_threshold  # merge_threshold  # 0.8
    else:
        threshold = 0.8

    cats, similarities = agglomerate(categories, threshold, jaccard, verbose)
    sims = [x for x in similarities]  # if x < threshold]

    if len(sims) > 0:
        threshold = max(sims) - 0.01
    else:
        threshold = 0.0
    if threshold <= group_threshold:
        return categories, {'rules_agglomeration': 'no_top_level'}

    z = len(similarities)
    while z > 0 and threshold > group_threshold:
        cats, similarities = agglomerate(cats, threshold, jaccard, verbose)
        sims = [x for x in similarities if x < threshold]
        z = len(sims)
        if z > 0:
            threshold = max(sims) - 0.01
        else:
            threshold = 0.0

    return cats, {'category tree': 'v.2018-12-12'}

# Notes:

# 80725 POC 0.1-0.4 deleted, 0.5 restructured
# 80802 poc05.py restructured, cats2list moved to category_learner.py,
# cats2list copied to poc05.py for tmp compatibility
# TODO: aggregate_cosine?
# 80802 fix compatibility with dj_counts & max_disjuncts, delete ...05.py?
# 81121 generalise_rules
# 81217 FIXME? generalize_categories [F] with new reorder (Turtle tests)
# 81220 refactor, test
# 81231 cleanup
