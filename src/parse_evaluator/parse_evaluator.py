import os
import sys
import random

from linkgrammar import ParseOptions, Dictionary, Sentence, Linkage
from ..grammar_tester.psparse import parse_postscript
from ..common.optconst import *

__all__ = ['Evaluate_Alternative']

def Load_File(filename):
    """
        Loads a data file
    """
    with open(filename) as file:
        data = file.readlines()
    print("Finished loading")

    return data

def Print_parses(sentences, parses, filename):
    """
        Prints parses to file (for sequential and random eval methods)
    """
    print("writing parses file to '{}'".format(filename))
    with open(filename, 'w') as fo:
        for sent, parse in zip(sentences, parses):
            fo.write(" ".join(sent) + "\n")
            # Remove brackets from LG-unparsed words
            for link in parse:
                if link[1][0] == "[" and link[1][-1] == "]":
                    link[1] = link[1][1:-1]
                if link[3][0] == "[" and link[3][-1] == "]":
                    link[3] = link[3][1:-1]
                fo.write(" ".join(link) + "\n")
            fo.write("\n")

    print("Finished writing parses file")


def Get_Parses(data):
    """
        Reads parses from data, counting number of parses by newlines
        - sentences: list with tokenized sentences in data
        - parses: a list of lists containing the split links of each parse
        [
          [[link1-parse1][link2-parse1] ... ]
          [[link1-parse2][link2-parse2] ... ]
          ...
        ]
        Each list is splitted into tokens using space.
    """
    parses = []
    sentences = []
    parse_num = -1
    new_flag = True
    for line in data:
        if line == "\n":
            # get rid of sentences with no links
            new_flag = True
            continue
        if new_flag:
            new_flag = False
            curr_sent = line.split()
            if curr_sent[0] == "###LEFT-WALL###":
                curr_sent.pop(0)
            sentences.append(curr_sent)
            parses.append([])
            parse_num += 1
            continue
        parses[parse_num].append(line.split())

    return parses, sentences

def MakeSets(parse, sent_len, ignore_WALL, content_words):
    """
        Gets a list with links and its sentence's length and returns a
        set of sets for each link's ids, ignoring WALL and dot if requested
    """
    current_ignored = 0
    link_list = []
    if content_words:
        with open("/home/andres/MyOpenCogSources/language-learning/src/parse_evaluator/func_words.txt", 'r') as ff:
            func_words = ff.readlines()[0].split()
    for link in parse:
        if content_words:
            if (link[1].lower() in func_words or link[3].lower() in func_words):
                current_ignored += 1
                continue
        if ignore_WALL:
            if (link[0] == '0') or (link[2] == str(sent_len) and link[3] == "."):
                current_ignored += 1
                continue
        link_list.append([link[0], link[2]])

    # using sets for each link evaluates without link direction
    links_set = set(map(frozenset, link_list))
    return links_set, current_ignored

def Evaluate_Parses(test_parses, test_sents, ref_parses, ref_sents, verbose, ignore, filter, content, **kwargs):
    """
        Compares test_parses against ref_parses link by link,
        counting errors, 
    """
    filtered_sents = 0 # sentences filtered if filter is active
    evaluated_parses = 0
    ignored_links = 0   # ignored links from ref, if ignore is active
    sum_precision = 0
    sum_recall = 0
    output_path = kwargs.get("output_path", os.environ["PWD"])

    # if filter, we'll print to file accepted ref parses
    if filter:
        fa = open(f"{output_path}/accepted_parses.ull", "w")

    for ref_parse, test_parse, ref_sent, test_sent in zip(ref_parses, test_parses, ref_sents, test_sents):

        true_pos = 0
        false_neg = 0
        false_pos = 0

        # when filter is active, ignore sentence if they're not equal
        # or it contains any quotes (for dialogue sentences)
        if filter:
            joint_test_sent = " ".join(test_sent)
            joint_ref_sent = " ".join(ref_sent)
            #count_quotes = ref_sent[1:-1].count('"') # only internal quotes
            count_quotes = ref_sent.count('"') # any quotes
            if joint_ref_sent.lower() != joint_test_sent.lower() or count_quotes > 0:
                filtered_sents += 1
                continue

        # using sets to ignore link directions
        ref_sets, current_ignored = MakeSets(ref_parse, len(ref_sent), ignore, content)

        # if no links are left after ignore, skip parse
        if len(ref_sets) == 0:
            continue
        else:
            evaluated_parses += 1

        test_sets, dummy = MakeSets(test_parse, len(ref_sent), ignore, content)

        ignored_links += current_ignored

        # count current parse guesses
        true_pos = len(ref_sets.intersection(test_sets))
        false_neg = len(ref_sets) - true_pos
        false_pos = len(test_sets) - true_pos

        # only update precision and recall if test_sets has links left,
        # otherwise they are not counted (they are zero)
        if len(test_sets) != 0:
            # update global counts
            sum_precision += true_pos / (true_pos + false_pos)  # add parse's precision
            sum_recall += true_pos / (true_pos + false_neg)  # add parse's recall

        if verbose:
            print("Sentence: {}".format(" ".join(ref_sent)))
            print("Correct links: {}".format(true_pos))
            print("Missing links: {}".format(false_neg))
            print("Extra links: {}".format(false_pos))

        # print to file the processed parses
        if filter:
            fa.write(joint_ref_sent + "\n")
            for link in ref_parse:
                fa.write(" ".join(link) + "\n")
            fa.write("\n")

    precision = sum_precision / evaluated_parses # averages precision
    recall = sum_recall / evaluated_parses # averages recall
    print("\nAvg Precision: {:.2%}".format(precision))
    print("Avg Recall: {:.2%}".format(recall))
    print("Avg Fscore: {:.2%}\n".format(2 * precision * recall / (precision + recall)))
    print("A total of {} sentences filtered, {:.2%} of reference file".format(filtered_sents, float(filtered_sents) / len(ref_parses)))
    print("A total of {} parses evaluated, {:.2%} of reference file".format(evaluated_parses, float(evaluated_parses) / len(ref_parses)))
    print("{:.2f} ignored links per evaluated parse".format(ignored_links / evaluated_parses))
    if filter:
        fa.close() # close output file if opened
    
def Make_Sequential(sents, **kwargs):
    """
        Make sequential parses (each word simply linked to the next one), 
        to use as baseline
    """
    output_path = kwargs.get("output_path", os.environ["PWD"])

    sequential_parses = []
    for sent in sents:
        parse = [["0", "###LEFT-WALL###", "1", sent[0]]] # include left-wall
        for i in range(1, len(sent)):
            parse.append([str(i), sent[i - 1], str(i + 1), sent[i]])
        #parse.append([str(i), sent[i - 1], str(i + 1), sent[i]] for i in range(1, len(sent)))
        sequential_parses.append(parse)

    Print_parses(sents, sequential_parses, f"{output_path}/sequential_parses.ull")

    return sequential_parses

def Make_Random(sents, **kwargs):
    """
        Make random parses (from LG-parser "any"), to use as baseline
    """
    output_path = kwargs.get("output_path", os.environ["PWD"])

    any_dict = Dictionary('any') # Opens dictionary only once
    po = ParseOptions(min_null_count=0, max_null_count=999)
    po.linkage_limit = 100
    options = 0x00000000 | BIT_STRIP #| BIT_ULL_IN
    options |= BIT_CAPS

    random_parses = []
    for sent in sents:
        num_words = len(sent)
        curr_sent = sent[:]
        curr_sent.insert(0, "###LEFT-WALL###")
        curr_parse = []
        # subtitute words with numbers, to avoid token-splitting by LG "any"
        fake_words = ["w{}".format(x) for x in range(1, num_words + 1)]
        sent_string = " ".join(fake_words)
        sentence = Sentence(sent_string, any_dict, po)
        linkages = sentence.parse()
        num_parses = len(linkages) # check nbr of linkages in sentence
        if num_parses > 0:
            idx = random.randint(0, num_parses - 1) # choose a random linkage index
            linkage = Linkage(idx, sentence, po._obj) # get the random linkage
            tokens, links = parse_postscript(linkage.postscript().replace("\n", ""), options)
            for link in links:
                llink = link[0]
                rlink = link[1]
                # attach words from sent, which are the actual words
                curr_parse.append([str(llink), curr_sent[llink], str(rlink), curr_sent[rlink]])

            random_parses.append(curr_parse)

    Print_parses(sents, random_parses, f"{output_path}/random_parses.ull")

    return random_parses

def Compare_Tokenization(ref_sentences, test_sentences, **kwargs):
    """
        Compares tokenization differences between parse files. Ignores caps
        and LG-unparsed (bracketed) tokens.
        Writes tok_diff.txt file with sentences that have different tokenization, and
        shows the different tokens
    """
    output_path = kwargs.get("output_path", os.environ["PWD"])

    with open(f"{output_path}/tok_diff.txt", "w") as ft:
        for ref_sent, test_sent in zip(ref_sentences, test_sentences):
            new_ref = []
            new_test = []
            for token_ref in ref_sent:
                token_ref = token_ref.lower()
                if token_ref[0] == "[" and token_ref[-1] == "]":
                    token_ref = token_ref[1:-1]
                new_ref.append(token_ref)
            for token_test in test_sent:
                token_test = token_test.lower()
                if token_test[0] == "[" and token_test[-1] == "]":
                    token_test = token_test[1:-1]
                new_test.append(token_test)
            if new_ref != new_test:
                set_ref = set(new_ref)
                set_test = set(new_test)
                ft.write("Sentence Differs:\n{}\nin tokens:{}<--->{}\n".format(" ".join(ref_sent), sorted(list(set_ref - set_test)), sorted(list(set_test - set_ref))))

def Evaluate_Alternative(ref_file, test_file, verbose, ignore_WALL, sequential, random_flag, filter_sentences, compare_tokenization, content, **kwargs):

    ref_data = Load_File(ref_file)
    ref_parses, ref_sents = Get_Parses(ref_data) 
    if sequential:
        test_parses = Make_Sequential(ref_sents, **kwargs)
        test_sents = ref_sents
    elif random_flag:
        test_parses = Make_Random(ref_sents, **kwargs)
        test_sents = ref_sents
    else:
        test_data = Load_File(test_file)
        test_parses, test_sents = Get_Parses(test_data) 
    if len(test_parses) != len(ref_parses):
        sys.exit(f"ERROR: Number of parses differs in files: {len(test_parses)}, {len(ref_parses)}")
    if compare_tokenization:
        print("Comparing tokenization only...")
        Compare_Tokenization(ref_sents, test_sents, **kwargs)
        return # exit
    Evaluate_Parses(test_parses, test_sents, ref_parses, ref_sents, verbose, ignore_WALL, filter_sentences, content, **kwargs)
