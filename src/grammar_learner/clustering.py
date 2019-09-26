# language-learning/src/grammar_learner/clustering.py                   # 90221
import logging
import numpy as np
import pandas as pd
import warnings
with warnings.catch_warnings():
    warnings.filterwarnings("ignore",category=DeprecationWarning)
    from sklearn.cluster import KMeans
    from sklearn.metrics import pairwise_distances, silhouette_score
from statistics import mode
from random import randint
from operator import itemgetter
from .utl import UTC, kwa


def cluster_id(n, nmax):
    def int2az(n, l = 'ABCDEFGHJKLMNOPQRSTUVWXYZ'):
        return (int2az(n // 25) + l[n % 25]).lstrip("A") if n > 0 else "A"
    return int2az(n).zfill(len(int2az(nmax))).replace('0', 'A')


def cluster_words_kmeans(words_df, n_clusters, init = 'k-means++', n_init = 10):
    # words_df: pandas DataFrame
    # init: 'k-means++', 'random', ndarray with random seed
    # n_init: number of initializations (runs), default 10
    words_list = words_df['word'].tolist()

    if n_clusters < 2:                                                  # 90104
        return pd.DataFrame.from_dict(
            {'cluster': 'B', 'cluster_words': [words_list]}), 0, 0

    df = words_df.copy()
    del df['word']
    # fails? = KMeans(init='random', n_clusters=n_clusters, n_init=30)
    # kmeans_model = KMeans(init='k-means++', n_clusters=n_clusters, n_init=10)
    kmeans_model = KMeans(init = init, n_clusters = n_clusters, n_init = n_init)
    kmeans_model.fit(df)
    labels = kmeans_model.labels_
    inertia = kmeans_model.inertia_
    centroids = np.asarray(kmeans_model.cluster_centers_[:(max(labels) + 1)])
    silhouette = silhouette_score(df, labels, metric = 'euclidean')

    cdf = pd.DataFrame(centroids)
    cdf = cdf.applymap(lambda x: x if abs(x) > 1e-12 else 0.)
    cdf.columns = [x + 1 if type(x) == int else x for x in cdf.columns]
    cols = cdf.columns.tolist()

    def cluster_word_list(i):
        return [words_list[j] for j, x in enumerate(labels) if x == i]

    cdf['cluster'] = cdf.index
    cdf['cluster_words'] = cdf['cluster'].apply(cluster_word_list)
    cdf['cluster'] = cdf['cluster'].apply(lambda x: cluster_id(x + 1, len(cdf)))
    cols = ['cluster', 'cluster_words'] + cols
    cdf = cdf[cols]

    return cdf, silhouette, inertia


def number_of_clusters(vdf, **kwargs):                                  # 90104
    logger = logging.getLogger(__name__ + "number_of_clusters")
    algorithm = kwa('kmeans', 'clustering', **kwargs)
    criteria = kwa('silhouette', 'cluster_criteria', **kwargs)
    level = kwa(1.0, 'cluster_level', **kwargs)
    verbose = kwa('none', 'verbose', **kwargs)
    crange = kwa((2, 48, 3), 'cluster_range', **kwargs)
    # crange :: cluster range:
    # (10) = (10,10) = (10,10,n) :: 10 clusters
    # (10,40,5) :: min, max, step
    # (10,40,5,n) :: min, max, step, m tests for each step

    if len(crange) < 2 or crange[1] == crange[0]:
        return crange[0]
    elif len(crange) == 4:
        attempts = crange[3]
    else:
        attempts = 1

    sil_range = pd.DataFrame(columns = ['Np', 'Nc', 'Silhouette', 'Inertia'])

    # Check number of clusters <= word vector dimensionality
    max_clusters = min(max(crange[0], crange[1]), len(vdf),
                       max([x for x in list(vdf) if isinstance(x, int)]))
    #?if max([x for x in list(vdf) if isinstance(x,int)]) < cluster_range[0]+1:
    #    max_clusters = min(cluster_range[1], len(vdf))  # FIXME: hack 80420!
    if max([x for x in list(vdf) if isinstance(x, int)]) == 2:
        return 4  # FIXME: hack Turtle 80420!
    n_clusters = max_clusters

    lst = []
    for k in range(attempts):
        for i, j in enumerate(range(crange[0], max_clusters, crange[2])):
            cdf, silhouette, inertia = cluster_words_kmeans(vdf, j)
            sil_range.loc[i] = [j, len(cdf), round(silhouette, 4),
                                round(inertia, 2)]
            if level > 0.9999:  # 1 - max Silhouette index
                n_clusters = \
                    sil_range.loc[sil_range['Silhouette'].idxmax()]['Nc']
            elif level < 0.0001:  # 0 - max number of clusters
                n_clusters = sil_range.loc[sil_range['Nc'].idxmax()]['Nc']
            else:
                thresh = level * sil_range \
                    .loc[sil_range['Silhouette'].idxmax()]['Silhouette']
                n_clusters = min(sil_range.loc[sil_range['Silhouette'] >
                                               thresh]['Nc'].tolist())
            lst.append(int(n_clusters))

    if len(lst) < 1:                                                    # 90104
        logger.debug("number_of_clusters » empty lst")
        return 1

    dct = dict()
    for n in lst:
        if n in dct:
            dct[n] += 1
        else:
            dct[n] = 1

    #if len(dct) <= 0:                                                  # 90104
    #    logger.debug("Empty dictionary 'dct'")

    f_mean: float = np.mean(lst)
    n_clusters = 0 if np.isnan(f_mean) else int(round(f_mean, 0))

    n2 = list(dct.keys())[list(dct.values()).index(max(list(dct.values())))]
    if n2 != n_clusters:
        if len(list(dct.values())) == len(set(list(dct.values()))):
            n3 = mode(lst)  # FIXME: Might get error?
        else:
            n3 = n_clusters
        n_clusters = int(round((n_clusters + n2 + n3) / 3.0, 0))

    return int(n_clusters)


def best_clusters(vdf, **kwargs):                                       # 90104
    logger = logging.getLogger(__name__ + ".best_clusters")
    algo = kwa('kmeans', 'clustering', **kwargs)
    criteria = kwa('silhouette', 'cluster_criteria', **kwargs)
    level = kwa(1.0, 'cluster_level', **kwargs)
    verbose = kwa('none', 'verbose', **kwargs)
    crange = kwa([2, 50, 2], 'cluster_range', **kwargs)
    # crange = kwa(10, 'cluster_range', **kwargs)
    # crange :: cluster range:
    # [10], [10,10] :: 10 clusters
    # [10,10,n]     :: 10 clusters, n tests
    # [10,40,5]     :: min, max, step ⇒ number_of_clusters
    # [10,40,5,n]   :: min, max, step, n tests for each step ⇒ number_of_clusters
    # [40,10,m]     :: max, min, optimum: max of m top results
    #                                     with the same number of clusters
    if type(crange) is int:
        crange = [crange, crange]
    init = 'k-means++'
    n_init = 10
    if type(algo) is str:
        if algo == 'kmeans':
            algorithm = 'kmeans'
            init = 'k-means++'
            n_init = 10
    elif type(algo) in [tuple, list]:
        if algo[0] == 'kmeans':
            algorithm = 'kmeans'
            if len(algo) > 1 and algo[1][0] == 'r': init = 'random'
            if len(algo) > 2:
                try: n_init = int(algo[2])
                except: n_init = 10

    if crange[0] == crange[1]:  # given n_clusters
        if len(crange) > 2 and crange[2] > 1:  # run crange[2] times
            lst = []
            for n in range(crange[2]):
                try:
                    c, s, i = cluster_words_kmeans(vdf, crange[0], init, n_init)
                    lst.append((n, crange[0], c, s, i))
                except:
                    if n == crange[2] - 1 and len(lst) == 0:
                        return 0, 0, 0
                    else:
                        continue
            lst.sort(key = itemgetter(3), reverse = True)
            if len(lst) > 0:
                return lst[0][2], lst[0][3], lst[0][4]
            else:
                return 0, 0, 0
        else:  # run once
            clusters, silhouette, inertia = cluster_words_kmeans(vdf, crange[0])
            return clusters, silhouette, inertia

    elif crange[1] > crange[0]:  # 80809 option: legacy search in a given range
        n_clstrs = number_of_clusters(vdf, **kwargs)
        if n_clstrs < 2:                                                # 90104
            return pd.DataFrame.from_dict(
                {'cluster': 'B', 'cluster_words': [vdf['word'].tolist()]}), 0, 0

        if len(crange) > 3 and crange[3] > 1:
            lst = []
            for n in range(crange[3]):
                try:
                    c, s, i = cluster_words_kmeans(vdf, n_clstrs, init, n_init)
                    lst.append((n, n_clstrs, c, s, i))
                except:
                    if n == crange[3] - 1 and len(lst) == 0:
                        return 0, 0, 0
                    else:
                        continue
            lst.sort(key = itemgetter(3), reverse = True)
            return lst[0][2], lst[0][3], lst[0][4]
        else:
            clusters, silhouette, inertia = cluster_words_kmeans(vdf, n_clstrs)
            return clusters, silhouette, inertia
    else:  # TODO: elif algorithm == 'kmeans'
        # Check number of clusters <= word vector dimensionality
        max_clusters = min(max(crange[0], crange[1]), len(vdf),
                           max([x for x in list(vdf) if isinstance(x, int)]))
        if max([x for x in list(vdf) if isinstance(x, int)]) == 2:
            max_clusters = 4  # FIXME: hack 80420: 2D word space ⇒ 4 clusters
        c = pd.DataFrame(columns = ['cluster', 'cluster_words'])
        s = 0
        i = 0
        while max_clusters > crange[0]:
            try:
                c, s, i = cluster_words_kmeans(vdf, max_clusters, init, n_init)
                break
            except:
                max_clusters -= 1
        n_clusters = max_clusters  # 80623: cure case max < crange.min
        if level < 0.1:
            return c, s, i  # return max possible number of clusters
        else:
            lst = []
            lst.append((0, max_clusters, c, s, i))
            min_clusters = min(crange[0], crange[1])
            if min_clusters > max_clusters:  # overkill?
                return c, s, i
            else:  # check min clusters, find min viable # FIXME: overkill?
                while min_clusters < max_clusters:
                    try:
                        c, s, i = cluster_words_kmeans(vdf, min_clusters,
                                                       init, n_init)
                        break
                    except:
                        min_clusters += 1
            lst.append((1, min_clusters, c, s, i))
            middle = int((min_clusters + max_clusters) / 2)
            c, s, i = cluster_words_kmeans(vdf, middle, init, n_init)
            lst.append((2, middle, c, s, i))
            lst.sort(key = itemgetter(3), reverse = True)

            ntop = 1
            while ntop < crange[2]:
                no = lst[0][1]
                c, s, i = cluster_words_kmeans(vdf, no, init, n_init)
                lst.append((len(lst), no, c, s, i))
                dn = int(round(0.6 * abs(no - lst[ntop][1]), 0))
                if ntop > crange[2] / 2.0:
                    dn = 1
                if no > min_clusters:
                    nm = max(no - dn, min_clusters)
                    c, s, i = cluster_words_kmeans(vdf, nm, init, n_init)
                    lst.append((len(lst), nm, c, s, i))
                if no < max_clusters:
                    nm = min(no + dn, max_clusters)
                    c, s, i = cluster_words_kmeans(vdf, nm, init, n_init)
                    lst.append((len(lst), nm, c, s, i))
                lst.sort(key = itemgetter(3), reverse = True)
                for n, x in enumerate(lst):
                    ntop = n + 1
                    if x[1] != lst[n + 1][1]:
                        break

            n_clstrs = int(lst[0][1])
            clusters = lst[0][2]
            silhouette = float(lst[0][3])
            inertia = float(lst[0][4])

            return clusters, silhouette, inertia


def group_links(links, **kwargs):  # Group «ILE»                        # 90209
    logger = logging.getLogger(__name__ + ".group_links")

    thresh = kwa(1, 'min_word_count', **kwargs) - 1                     # 90209

    df = links.copy()
    df['links'] = [[x] for x in df['link']]
    del df['link']
    df = df.groupby('word').agg({'links': 'sum', 'count': 'sum'}).reset_index()
    df['words'] = [[x] for x in df['word']]
    del df['word']

    if thresh > 0: df = df.loc[df['count'] > thresh]                    # 90209

    df2 = df.copy().reset_index()
    df2['links'] = df2['links'].apply(lambda x: tuple(sorted(x)))
    df3 = df2.groupby('links')['count'].apply(sum).reset_index()
    df4 = df2.groupby('links')['words'].apply(sum).reset_index()
    if df4['links'].tolist() == df3['links'].tolist():
        df4['counts'] = df3['count']
    else:
        logger.error("group_links: df4['counts'] != df3['count'] ERROR!")
    df4['words'] = df4['words'].apply(lambda x: sorted(list(x)))
    df4['links'] = df4['links'].apply(lambda x: sorted(list(x)))
    df4 = df4[['words', 'links', 'counts']] \
        .sort_values(by = 'words', ascending = True)
    df4.index = range(1, len(df4) + 1)
    df4['cluster'] = range(1, len(df4) + 1)
    df4['cluster'] = df4['cluster'].apply(lambda x: cluster_id(x, len(df4)))
    df4 = df4.rename(columns = {'words': 'cluster_words', 'links': 'disjuncts'})
    df4 = df4[['cluster', 'cluster_words', 'disjuncts', 'counts']]

    return df4


def random_clusters(links, **kwargs):
    crange = kwa((20, 70, 2), 'cluster_range', **kwargs)
    if crange[0] == crange[1]:
        n_clusters = crange[0]
    else:
        n_clusters = randint(min(crange[0], crange[1]),
                             max(crange[0], crange[1]))
    df = links.copy()
    df['disjuncts'] = [[x] for x in df['link']]
    del df['link']
    df = df.groupby('word').agg(
        {'disjuncts': 'sum', 'count': 'sum'}).reset_index()
    df['cluster'] = n_clusters
    df['cluster'] = df['cluster'].apply(lambda x: randint(1, x))
    df['cluster_words'] = [[x] for x in df['word']]
    del df['word']
    df = df.groupby('cluster') \
        .agg({'cluster_words': 'sum', 'disjuncts': 'sum', 'count': 'sum'}) \
        .reset_index()
    df['cluster'] = df['cluster'].apply(lambda x: cluster_id(x, n_clusters))

    return df

# Notes:

# 80428 group_links :: Group identical Lexical Entries (ILE)
# 80617 kmeans_model = KMeans(init='random', n_clusters=n_clusters,
# n_init=30)   #fails?
# 80725 POC 0.1-0.4 deleted, 0.5 restructured. This module was
# src/clustering/poc05.py
# 80802 poc05 restructured,
# cluster_words_kmeans moved here (from kmeans.py) for further dev
# number_of_clusters copied to kmeans.py: tmp poc05 "stable" baseline
# group_links moved here from category_learner.py
# clusters2list, clusters2dict removed
# 80809 update: (30,60,3,[3]) - old range + repeat / (120,30,3) -- search opt
# 80825 random_clusters
# 81022 refactoring
# TODO: n_clusters ⇒ best_clusters: return best clusters (word lists), centroids
# 81231 cleanup
# 90104 resolve Turtle MST LW crash: 1 cluster
# 90209 group_links: add min_word_count to 80925 legacy version
# 90221 kmeans defaults updated for Grammar Learner tutorial
