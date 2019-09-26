# language-learning/src/grammar_inducer.py                              # 81207
import logging
from copy import deepcopy
from collections import Counter
from typing import List, Tuple
from .utl import UTC, kwa
from math import log10


def add_disjuncts(cats, links, **kwargs):
    """
    Add disjuncts to {cats} after k-means or agglomerative clustering

    :param cats:        {'cluster': [], 'words': [], }
    :param links:       Pandas data frame with words and protodisjuncts, obtained from .ull file(s).
    :param kwargs:      Argument dictionary.
    :return:            Category tree, packed into Python dictionary (cats extended by disjuncts
                        and their respective occurrencies).
    """
    # TODO?: add top disjuncts only + prune disjuncts  after clusters?
    # OR def prune_cats?

    max_disjuncts = kwa(100000, 'max_disjuncts', **kwargs)
    verbose = kwa('none', 'verbose', **kwargs)

    logger = logging.getLogger(__name__ + ".add_disjuncts")

    # logger.debug(f"cats:\n{str(cats)}")

    fat_cats = deepcopy(cats)

    # Assign numeric ID to each cluster (clusters are marked by letters in cats['cluster'])
    top_clusters = [i for i, x in enumerate(cats['cluster']) if
                    i > 0 and x is not None]

    # Dictionary for holding each word's cluster id
    word_clusters = dict()

    # Assign cluster id to each word
    for i in top_clusters:
        for word in cats['words'][i]:
            word_clusters[word] = i

    # logger.debug("word_clusters:\n" + str(word_clusters))

    df = links.copy()

    # Add column and set cluster ID to a word if the word is clustered, zero otherwise.
    df['cluster'] = df['word'].apply(
        lambda x: word_clusters[x] if x in word_clusters else 0)

    # logger.debug("df:\n" + str(df))

    # Make each cluster subtotal summarizing protodisjunct appearances
    cdf = df.groupby('cluster').sum().reset_index()
    cdf = cdf.loc[cdf['cluster'] > 0]

    # logger.debug("cdf:\n" + str(cdf))

    # Add summarized protodisjuntct appearances to the resulting data frame
    fat_cats['counts'] = [0] + cdf['count'].tolist()

    fat_cats['disjuncts'] = [[]]
    fat_cats['dj_counts'] = [[]]

    # Calculate totals on each protodisjunct appearance of each cluster
    cdf = df.groupby(['cluster', 'link'], as_index = False).sum() \
        .sort_values(by = ['cluster', 'count'], ascending = [True, False])

    # logger.debug("cdf after df.groupby(['cluster', 'link']\n" + str(cdf))

    # TODO?: dj_counts = Counter()
    # ~ ddf = cdf.groupby('link', as_index=False).sum() \
    #             .sort_values(by='count', ascending=[False])
    # ~ dj_counts[tuple(dj)] += categories['dj_counts'][cluster][i]
    # top_djs = set([x[0] for x in dj_counts.most_common(max_disjuncts)])

    # Add protodisjunct list and corresponding appearances to the resulting data frame
    for cluster in top_clusters:
        ccdf = cdf.loc[cdf['cluster'] == cluster]
        fat_cats['disjuncts'].append(ccdf['link'].tolist())
        fat_cats['dj_counts'].append(ccdf['count'].tolist())

    fat_cats['djs'] = [[]]          # cluster's disjunct id list

    # Calculate protodisjunct appearance totals (throughout the whole corpus)
    ldf = df[['link', 'count']].copy().groupby('link').sum().sort_values(
        by = 'count', ascending = False).reset_index()

    # logger.debug("ldf:\n" + str(ldf))

    # Create protodisjunct ID dictionary
    djdict = {x: i for i, x in enumerate(ldf['link'].tolist())}

    # logger.debug(djdict)

    wdf = df[["word", "count"]].groupby(["word"], as_index = False).sum().sort_values(by = ['word'], ascending = [True])

    # logger.debug("wdf:\n" + str(wdf))

    word_counts = { w: c for w, c in dict(zip(wdf["word"].to_list(), wdf["count"].to_list())).items() }

    fat_cats["word_counts"] = word_counts

    # Drop 'word' column
    df.drop(['word'], axis = 1, inplace = True)

    # Add new column with protodisjunct IDs
    df['dj'] = df['link'].apply(lambda x: djdict[x])

    # logger.debug("df:\n" + str(df))

    # Calculate protodisjunct appearance subtotals
    cdf = df.groupby(['cluster', 'dj'], as_index = False).sum().sort_values(
        by = ['cluster', 'dj'], ascending = [True, True])

    # logger.debug("cdf:\n" + str(cdf))

    # # Calculate protodisjunct appearances throughout the corpus
    # adf = df[["dj", "count"]].groupby(['dj'], as_index = False).sum().sort_values(
    #     by = ['dj'], ascending = [True])
    #
    # logger.debug("adf:\n" + str(adf))
    #
    # # Calculate disjunct costs
    # djs_costs = { link: 1.0 / float(count) for link, count in
    #               dict(zip(adf["dj"].to_list(), adf["count"].to_list())).items() }
    #
    # logger.debug("adf dict:\n" + str(djs_costs))

    # Each cluster's protodisjunct list, where each protodisjunct is replaced by its ID,
    #   is appended to the result category tree
    for cluster in top_clusters:
        ccdf = cdf.loc[cdf['cluster'] == cluster]
        fat_cats['djs'].append(ccdf['dj'].tolist())
        # djs = ccdf['dj'].tolist()
        # cst = [ djs_costs.get(djs_id, 1.0) for djs_id in djs]
        # fat_cats['djs'].append(djs)

    # logger.debug("fat_cats:\n" + str(fat_cats))

    return fat_cats


def prune_cats(categories, **kwargs):  # 81204 checked as check_cats ~OK?
    # check each category has associated disjuncts, delete if no disjuncts
    # 81204 ad-hoc:  lost hierarchy, connectors to deleted clusters :(
    cats = {key: [] for key in categories.keys()}
    for i, djs in enumerate(cats['disjuncts']):
        if len(djs) > 0:
            for key in cats.keys():
                cats[key].append(categories[key][i])
        else:
            continue
    return cats, {'prune_cats': 'under construction'}


def check_cats(cats, **kwargs):
    orphans = []
    for i, djs in enumerate(cats['disjuncts']):
        if len(djs) == 0:
            orphans.append([i, cats['cluster'][i], cats['words'][i], djs])
    if len(orphans) > 0:
        print('check_cats » orphans:', orphans)
    return {'orphaned_clusters': orphans}


def induce_grammar(categories, **kwargs):
    """
    Create grammar rule tree

    :param categories:  {'cluster': [], 'words': [], ...}
    :param kwargs:
    :return:            Grammar rule tree represented by dictionary
    """
    def rev_count_cost(disjunct_vector: Tuple[int]):
        """
        Calculate reverse appearance cost value

        :param disjunct_vector:     Disjunct vector pointing to linked clusters
        :return:                    Float cost value
        """
        return 1.0 / float(dj_counts.get(disjunct_vector, 1.0))

    def mi_cd_cost(disjunct_vector: Tuple[int]):
        """
        Calculate mutual information between cluster words and a disjunct

        :param disjunct_vector:     Disjunct vector pointing to linked clusters
        :return:                    Float cost value

        MI(c, d) = log( N(c, d) / (N(c) * N(d)) ), where
        N(c, d)  = sum([N(w1, d), N(w2, d),...N(wn, d)]) - number of times disjunct d appears with the words
                                                              of the cluster c
        N(c) - number of times the cluster words appear with any disjuncts
        N(d) - number of times disjunct d appears with any word

        Because according to LG dictionary rule strategy each word can only be included into only one rule,
        N(c, d) = N(c) so for this particular case MI(c, d) = log( 1 / N(d) )

        The only thing that may make difference is disambiguation. Current GL code adds suffixes to
        disambiguated word instances, if the same word appears in the corpus in different meanings.
        In that case the general formula makes sense.
        """
        return log10(1.0 / float(dj_counts.get(disjunct_vector, 1.0)))

        # return log10(float(rules["dj_counts"][cluster_index][])
        #              / (sum([rules["word_counts"][w] for w in rules["words"][cluster_index]])
        #                 * rules["dj_costs"][disjunct_vector]))

    logger = logging.getLogger(__name__ + ".induce_grammar")
    # logger.debug(f"Categories: {str(categories)}")

    cost_functions = {"reverse_count": rev_count_cost, "mi_simplified": mi_cd_cost}

    max_disjuncts = kwa(100000, 'max_disjuncts', **kwargs)
    verbose = kwa('none', 'verbose', **kwargs)
    add_costs = kwargs.get("add_disjunct_costs", False)

    rules = deepcopy(categories)
    dj_counts = Counter()
    clusters = [i for i, x in enumerate(rules['cluster'])
                if i > 0 and x is not None]

    word_clusters = dict()

    for i in clusters:
        for word in rules['words'][i]:
            word_clusters[word] = i

    disjuncts = {}

    for cluster in clusters:
        djs = []
        for i, rule in enumerate(categories['disjuncts'][cluster]):
            if type(rule) is str:           # 'a- & was-' ⇒ (-9,-26) + reverse 81012
                x = rule.split()            # split protodisjunct into tokens

                lefts, rights = [], []      # Separate left connectors from right ones

                for y in x:
                    # If token is a connector and it belongs to any of the clusters
                    if (y not in ['&', ' ', '']) and (y[:-1] in word_clusters):
                        # Convert connector into a cluster index
                        if y[-1] == '+':    # positive for right connector
                            rights.append(word_clusters[y[:-1]])
                        elif y[-1] == '-':  # negative for the left one
                            lefts.append(-1 * word_clusters[y[:-1]])
                        else:               # error if connector is missing the sign at the end
                            # print('no sign?', y, 'in', x)
                            raise RuntimeError(f"No sign for '{y}' set in [{x}]")

                lefts.reverse()  # 81012
                dj = lefts + rights

                if len(dj) > 0:
                    djs.append(tuple(dj))   # tuple of cluster/connector indexes (negative for lefts, positive for rights)
                    dj_counts[tuple(dj)] += categories['dj_counts'][cluster][i]

        # This is probably where disjuncts cease to coincide their dj_counts counterparts
        #   because set() does not guarantee the same order as it is in the list djs and eliminates duplicates.
        rules['disjuncts'][cluster] = set(djs)

    # TODO: move this code to prune_cats and call it before induce_grammar
    # Add only top-frequency disjuncts:
    top_djs = set([x[0] for x in dj_counts.most_common(max_disjuncts)])

    # logger.debug("top_djs:\n" + str(top_djs))

    if add_costs:
        rules['cl_dj_cst'] = [[] if i==0 else None for i in range(len(rules['cluster']))]

    # Choose cost function according to specified argument, rev_count_cost if not specified
    cost_func = cost_functions.get(kwargs.get("disjunct_cost_func", "Not found"), rev_count_cost)

    pruned_clusters, pruned_words, trace = [], [], []

    clusters = [x for i, x in enumerate(rules['cluster'])
                if i > 0 and x is not None]

    for cluster in clusters:  # 81105 added -- blocked 81205
        # rules['disjuncts'][cluster] = top_djs & rules['disjuncts'][cluster]
        # - blocked 81205 -- might create rule without disjuncts ⇒ LG error
        # FIXME: add only rules with checked len(disjuncts) > 0
        i = rules['cluster'].index(cluster)

        # Add only cluster disjuncts with topmost frequencies
        djs = top_djs & rules['disjuncts'][i]

        # Add only non empty disjuncts
        if len(djs) > 0:
            rules['disjuncts'][i] = djs

            if add_costs:
                rules['cl_dj_cst'][i] = tuple([(d, cost_func(d)) for d in djs if d is not None])

        else:  # TODO: pop rules[...][i]
            # rules['disjuncts'][cluster] = rules['disjuncts'][cluster]  #
            # 81205 ad-hoc
            trace.append([cluster, rules['words'][i], rules['disjuncts'][i]])
            pruned_clusters.append(cluster)
            pruned_words.append(rules['words'][i])
            # TODO: remove entire row -- needs further disjuncts cleanup (errors in write_files.py)
            # for key in rules.keys():
            # del rules[key][i]  #  value = rules['key'].pop(i)
            # print('trace: cluster:', cluster, '-', (rules['words'][cluster]))
    # if len(trace) > 0:
    # print('removed cluster trace:', trace)
    # print('pruned_clusters:', pruned_clusters, 'pruned_words:', pruned_words)
    # TOD0?: remove disjuncts connected with deleted clusters...
    # TODO?: iterate: prune clusters ⇒ disjuncts ⇒ clusters ... ⇒ renumber & rename :(

    return rules, {
        'learned_rules': len([x for i, x in enumerate(rules['parent'])
                              if x == 0 and i > 0]),
        'total_clusters': len(rules['cluster']) - 1
    }

# Notes:

# 80802 poc05.py restructured: induce_grammar ⇒ grammar_inducer.py v~80625
# 81102 max_disjuncts ⇒ induce_grammar
# 81204 add_disjuncts, check_cats, prune_cats :: resolve rules with empty dj list
# 81231 cleanup
