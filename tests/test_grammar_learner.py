# !/usr/bin/env python3
'''Grammar Learner 0.6 tests 2018-09-29: unittest
Run test:
$ cd language-learning
$ source activate ull
$ python tests/test_grammar_learner.py
'''
#from pathlib import Path
#print('Running' if __name__ == '__main__' else 'Importing', Path(__file__).resolve())

import os, sys
import unittest
from decimal import Decimal

module_path = os.path.abspath(os.path.join('.'))
if module_path not in sys.path: sys.path.append(module_path)
from src.grammar_learner.utl import UTC
from src.grammar_learner.read_files import check_dir
from src.grammar_learner.learner import learn_grammar
from src.grammar_learner.pqa_table import pqa_meter
# from ull.grammartest.optconst import *


class TestGrammarLearner(unittest.TestCase):

    def setUp(self):    # FIXME: should run before every test, but would not?!
        input_parses = module_path + '/tests/data/POC-Turtle/MST_fixed_manually/'
        batch_dir = module_path + '/output/Test_Grammar_Learner_' + str(UTC())[:10] + '/'
        kwargs = {  # defaults
            'input_parses'  :   input_parses,   # path to directory with input parses
            'output_grammar':   batch_dir   ,   # filename or path
            'output_categories' :    ''     ,   # = output_grammar if '' or not set
            'output_statistics' :    ''     ,   # = output_grammar if '' or not set
            'temp_dir'          :    ''     ,   # temporary files = language-learning/tmp if '' or not set
            'parse_mode'    :   'given'     ,   # 'given' (default) / 'explosive' (next)
            'left_wall'     :   'LEFT-WALL' ,   # '','none' - don't use / 'LEFT-WALL' - replace ###LEFT-WALL###
            'period'        :   True        ,   # use period in links learning: True/False
            'context'       :   2           ,   # 1: connectors / 2,3...: disjuncts
            'window'        :   'mst'       ,   # 'mst' / reserved options for «explosive» parsing
            'weighting'     :   'ppmi'      ,   # 'ppmi' / future options
            'group'         :   True        ,   # group items after link parsing
            'distance'      :   False       ,   # reserved options for «explosive» parsing
            'word_space'    :   'discrete'  ,   # 'vectors' / 'discrete' - no dimensionality reduction
            'dim_max'       :   100         ,   # max vector space dimensionality
            'sv_min'        :   0.1         ,   # minimal singular value (fraction of the max value)
            'dim_reduction' :   'none'      ,   # 'svm' / 'none' (discrete word_space, group)
            'clustering'    :   'group'     ,   # 'kmeans' / 'group'~'identical_entries' / future options
            'cluster_range' :   (2,48,1)    ,   # min, max, step
            'cluster_criteria': 'silhouette',   # optimal clustering criteria
            'cluster_level' :   1.0         ,   # level = 0, 1, 0.-0.99..: 0 - max number of clusters
            'categories_generalization': 'off', # 'off' / 'cosine' - cosine similarity, 'jaccard'
            'categories_merge'      :   0.8 ,   # merge categories with similarity > this 'merge' criteria
            'categories_aggregation':   0.2 ,   # aggregate categories with similarity > this criteria
            'grammar_rules' :   2           ,   # 1: 'connectors' / 2 - 'disjuncts' / 0 - 'words' (TODO?)
            'rules_generalization'  :  'off',   # 'off' / 'cosine' - cosine similarity, 'jaccard'
            'rules_merge'           :   0.8 ,   # merge rules with similarity > this 'merge' criteria
            'rules_aggregation'     :   0.2 ,   # aggregate rules similarity > this criteria
            'tmpath': module_path + '/tmp/',    # legacy, default if not temp_dir
            'verbose': 'min',       # display intermediate results: 'none', 'min', 'mid', 'max'
            'linkage_limit': 1000   # Link Grammar parameter for tests
        }
        # Additional (optional) parameters for parse_metrics (_abiity & _quality):
        # 'test_corpus': module_path + '/data/POC-Turtle/poc-turtle-corpus.txt',
        # 'reference_path': module_path + '/data/POC-Turtle/poc-turtle-parses-expected.txt',
        # 'template_path': 'poc-turtle',  # FIXME: changed in June 2018 Grammar Tester
        pass

    '''Legacy ~ POC.0.3 test ~ as it was before 2018-09-29
    def test_turtle_diled(self):
        corpus = 'POC-Turtle'
        dataset = 'MST_fixed_manually'
        input_parses = module_path + '/tests/data/POC-Turtle/MST-fixed-manually/'
        base  = module_path + '/tests/data/POC-Turtle/' + \
            '/2018-04-25/turtle_dILEd_LW+dot+_2018-04-25_0008.4.0.dict'
        batch_dir = module_path + '/output/test_grammar_learner_' + str(UTC())[:10]
        prj_dir = batch_dir + '/Turtle_dILEd_LW_and_period/'
        if check_dir(prj_dir, create=True, verbose='max'):
            output_categories = prj_dir
            output_grammar = prj_dir
        kwargs = {
            'left_wall'     :   'LEFT-WALL' ,
            'period'        :   True        ,
            'context'       :   2           ,
            'word_space'    :   'discrete'  ,
            'dim_reduction' :   'none'      ,
            'clustering'    :   'group'     ,
            'grammar_rules' :   2           ,
            'categories_generalization' :   'off' ,
            'rules_generalization'      :   'off' ,
            'tmpath'        :   module_path + '/tmp/',
            'verbose'       :   'min'
        }
        response = learn_grammar(input_parses, output_categories, output_grammar, **kwargs)
        with open(response['grammar_file'], 'r') as f:
            rules = f.read().splitlines()
        rule_list = [line for line in rules if line[0:1] in ['"', '(']]
        with open(base, 'r') as f: lst = f.read().splitlines()
        base_list = [line for line in lst if line[0:1] in ['"', '(']]
        if len(rule_list) == len(base_list):
            if kwargs['verbose'] == 'debug':
                print('\nTest results vs baseline:')
                for i,rule in enumerate(base_list):
                    print(rule_list[i])
                    print(rule)
            assert rule_list == base_list
        else: assert len(rule_list) == len(base_list)
    '''


    def test_turtle_no_generalization(self):
        base  = module_path + '/tests/data/POC-Turtle/' + \
            'no_generalization/dict_8C_2018-10-21_0006.4.0.dict'
        input_parses = module_path + '/tests/data/POC-Turtle/MST-fixed-manually/'
        batch_dir = module_path + '/output/test_grammar_learner_' + str(UTC())[:10]
        prj_dir = batch_dir + '/turtle_lw_&_dot_no_generalization/'
        if check_dir(prj_dir, create=True, verbose='max'):
            outpath = prj_dir
        kwargs = {
            'input_parses'  :   input_parses,
            'output_grammar':   outpath,
            'left_wall'     :   'LEFT-WALL' ,
            'period'        :   True        ,
            'context'       :   2           ,
            'word_space'    :   'discrete'  ,
            'dim_reduction' :   'none'      ,
            'clustering'    :   'group'     ,
            'grammar_rules' :   2           ,
            'categories_generalization' :   'off' ,
            'rules_generalization'      :   'off' ,
            'tmpath'        :   module_path + '/tmp/',
            'verbose'       :   'min'
        }
        response = learn_grammar(**kwargs)
        with open(response['grammar_file'], 'r') as f:
            rules = f.read().splitlines()
        rule_list = [line for line in rules if line[0:1] in ['"', '(']]
        with open(base, 'r') as f: lst = f.read().splitlines()
        base_list = [line for line in lst if line[0:1] in ['"', '(']]
        if len(rule_list) == len(base_list):
            if kwargs['verbose'] in ['debug']:
                print('\nlen(rule_list) = len(base_list) =', len(rule_list))
                print('\nrule_list:', rule_list)
                print('\nbase_list:', base_list)
                print('\nrule_list == base_list:', rule_list == base_list)
            assert rule_list == base_list
        else:
            print('\nlen(rule_list) =', len(rule_list),
                  '!= len(base_list) =', len(base_list))
            assert len(rule_list) == len(base_list), f"\nlen(rule_list)={len(rule_list)}" \
                                                     f"\nlen(base_list)={len(base_list)}" \
                                                     f"\nrule_list:\n{rule_list}" \
                                                     f"\nbase_list:\n{base_list}"

    def test_turtle_generalize_rules(self):
        base  = module_path + '/tests/data/POC-Turtle/' + \
            'generalized_rules/dict_6C_2018-10-03_0006.4.0.dict'
        input_parses = module_path + '/tests/data/POC-Turtle/MST-fixed-manually/'
        batch_dir = module_path + '/output/test_grammar_learner_' + str(UTC())[:10]
        prj_dir = batch_dir + '/turtle_lw_&_dot_generalized_rules/'
        if check_dir(prj_dir, create=True, verbose='max'):
            outpath = prj_dir
        kwargs = {
            'input_parses'  :   input_parses,
            'output_grammar':   outpath,
            'left_wall'     :   'LEFT-WALL' ,
            'period'        :   True        ,
            'context'       :   2           ,
            'word_space'    :   'discrete'  ,
            'dim_reduction' :   'none'      ,
            'clustering'    :   'group'     ,
            'grammar_rules' :   2           ,
            'categories_generalization' :   'off'    ,
            'rules_generalization'      :   'jaccard',
            'tmpath'        :   module_path + '/tmp/',
            'verbose'       :   'none'
        }
        response = learn_grammar(**kwargs)
        with open(response['grammar_file'], 'r') as f:
            rules = f.read().splitlines()
        rule_list = [line for line in rules if line[0:1] in ['"', '(']]
        with open(base, 'r') as f: lst = f.read().splitlines()
        base_list = [line for line in lst if line[0:1] in ['"', '(']]
        if len(rule_list) == len(base_list):
            assert rule_list == base_list
        else:
            assert len(rule_list) == len(base_list), f"\nlen(rule_list)={len(rule_list)}" \
                                                     f"\nlen(base_list)={len(base_list)}" \
                                                     f"\nrule_list:\n{rule_list}" \
                                                     f"\nbase_list:\n{base_list}"
            # assert len(rule_list) == len(base_list)


    def test_pqa_turtle_diled_no_generalization(self):
        input_parses = module_path + '/tests/data/POC-Turtle/MST-fixed-manually'
        batch_dir = module_path + '/output/test_grammar_learner_' + str(UTC())[:10]
        prj_dir = batch_dir + '/turtle_pqa_diled_no_generalization/'
        if check_dir(prj_dir, create=True, verbose='max'): outpath = prj_dir
        # cp,rp :: (test) corpus_path and reference_path:
        cp = module_path + '/tests/data/POC-Turtle/poc-turtle-corpus.txt'
        rp = input_parses + '/poc-turtle-parses-gold.txt'
        kwargs = {
            'input_parses'  :   input_parses,
            'output_grammar':   outpath,
            'left_wall'     :   '' ,
            'period'        :   False        ,
            'context'       :   2           ,
            'word_space'    :   'discrete'  ,
            'dim_reduction' :   'none'      ,
            'clustering'    :   'group'     ,
            'grammar_rules' :   2           ,
            'categories_generalization' :   'off' ,
            'rules_generalization'      :   'off' ,
            'tmpath'        :   module_path + '/tmp/',
            'linkage_limit' :   1000,
            'verbose'       :   'min'
        }
        re = learn_grammar(**kwargs)
        # 81019 changes:    # FIXME: DEL comments
        # a, q, qa = pqa_meter(re['grammar_file'], outpath, cp, rp, **kwargs)
        # print('parse-ability, parse-quality:', a, q)
        # assert a*q > 0.99
        # self.assertTrue(a*q*Decimal("100") > 0.99, str(a) + " * " + str(q) + " * 100 !> 0.99")
        pa, f1, precision, recall = pqa_meter(re['grammar_file'], outpath, cp, rp, **kwargs)
        # pa, f1, precision, recall: <float> 0.0 - 1.0
        self.assertTrue(pa*recall > 0.99, str(pa) + " * " + str(recall) + " > 0.99")


    def test_pqa_turtle_ddrkd_no_generalization(self):
        input_parses = module_path + '/tests/data/POC-Turtle/MST-fixed-manually/'
        batch_dir = module_path + '/output/test_grammar_learner_' + str(UTC())[:10]
        prj_dir = batch_dir + '/turtle_pqa_ddrkd_no_generalization/'
        if check_dir(prj_dir, create=True, verbose='max'):
            outpath = prj_dir
        # cp,rp :: (test) corpus_path and reference_path:
        cp = module_path + '/tests/data/POC-Turtle/poc-turtle-corpus.txt'
        rp = input_parses + '/poc-turtle-parses-gold.txt'
        kwargs = {
            'input_parses'  :   input_parses,
            'output_grammar':   outpath,
            'left_wall'     :   '' ,
            'period'        :   False       ,
            'context'       :   2           ,
            'word_space'    :   'vectors'   ,
            'dim_reduction' :   'svd'       ,
            'clustering'    :   ('kmeans','kmeans++',18),
            #-'cluster_range' :   (2,50,9)    ,
            'cluster_range' :   (20, 2, 9)  ,
            'grammar_rules' :   2           ,
            'categories_generalization' :   'off' ,
            'rules_generalization'      :   'off' ,
            'tmpath'        :   module_path + '/tmp/',
            'linkage_limit' :   1000,
            'verbose'       :   'min'
        }
        re = learn_grammar(**kwargs)
        pa, f1, precision, recall = pqa_meter(re['grammar_file'], outpath, cp, rp, **kwargs)
        self.assertTrue(pa*recall > 0.99, str(pa) + " * " + str(recall) + " > 0.99")

    def test_pqa_english_noamb_diled_no_generalization(self):
        input_parses = module_path + '/tests/data/POC-English-NoAmb/MST-fixed-manually/'
        batch_dir = module_path + '/output/test_grammar_learner_' + str(UTC())[:10]
        prj_dir = batch_dir + '/noamb_pqa_diled_no_generalization/'
        if check_dir(prj_dir, create=True, verbose='max'):
            outpath = prj_dir
        # cp,rp :: (test) corpus_path and reference_path:
        cp = module_path + '/data/POC-English-NoAmb/poc_english_noamb_corpus.txt'
        rp = input_parses + '/poc-english_noAmb-parses-gold.txt'
        kwargs = {
            'input_parses'  :   input_parses,
            'output_grammar':   outpath,
            'left_wall'     :   ''          ,
            'period'        :   False       ,
            'context'       :   2           ,
            'word_space'    :   'discrete'  ,
            'dim_reduction' :   'none'      ,
            'clustering'    :   'group'     ,
            'grammar_rules' :   2           ,
            'categories_generalization' :   'off' ,
            'rules_generalization'      :   'off' ,
            'tmpath'        :   module_path + '/tmp/',
            'linkage_limit' :   1000,
            'verbose'       :   'min'
        }
        re = learn_grammar(**kwargs)
        pa, f1, precision, recall = pqa_meter(re['grammar_file'], outpath, cp, rp, **kwargs)
        self.assertTrue(pa*recall > 0.99, str(pa) + " * " + str(recall) + " > 0.99")


    def test_pqa_english_noamb_ddrkd_no_generalization(self):
        input_parses = module_path + '/tests/data/POC-English-NoAmb/MST-fixed-manually/'
        batch_dir = module_path + '/output/test_grammar_learner_' + str(UTC())[:10]
        prj_dir = batch_dir + '/noamb_pqa_ddrkd_no_generalization/'
        if check_dir(prj_dir, create=True, verbose='max'):
            outpath = prj_dir
        # cp,rp :: (test) corpus_path and reference_path:
        cp = module_path + '/data/POC-English-NoAmb/poc_english_noamb_corpus.txt'
        rp = input_parses + '/poc-english_noAmb-parses-gold.txt'
        kwargs = {
            'input_parses'  :   input_parses,
            'output_grammar':   outpath,
            'left_wall'     :   '' ,
            'period'        :   False        ,
            'context'       :   2           ,
            'word_space'    :   'vectors'   ,
            'dim_reduction' :   'svd'       ,
            'clustering'    :   ('kmeans','kmeans++',18)  ,
            'cluster_range' :   (12, 12, 5),
            'grammar_rules' :   2           ,
            'categories_generalization' :   'off' ,
            'rules_generalization'      :   'off' ,
            'tmpath'        :   module_path + '/tmp/',
            'linkage_limit' :   1000,
            'verbose'       :   'min'
        }
        # Sometimes pqa_meter(with test_grammar updated 2018-10-19) returns pa,recall = 0,0
        # FIXME: check with further test_grammar updates and delete.
        x = 0.
        n = 0
        while x < 0.1 :
            re = learn_grammar(**kwargs)
            pa, f1, precision, recall = pqa_meter(re['grammar_file'], outpath, cp, rp, **kwargs)
            print(f'\nnoAmb dDRKd: pa {round(pa,3)}, f1 {round(f1,3)}, precision {round(precision,3)}, recall {round(recall,3)} \n')
            x = pa * recall
            n += 1
            if n > 24: break
        self.assertTrue(pa*recall > 0.99, str(pa) + " * " + str(recall) + " > 0.99")


if __name__ == '__main__':
    unittest.main()
