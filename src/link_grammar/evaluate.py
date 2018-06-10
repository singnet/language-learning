import sys
import os


from .dirhelper import traverse_dir
from .parsestat import calc_parse_quality, parse_quality
from .parsemetrics import ParseQuality
from .lgparse import traverse_dir


__all__ = ['load_ull_file', 'get_parses', 'eval_parses', 'compare_ull_files', 'EvalError']


PARSE_SENTENCE = 0
PARSE_LINK_SET = 1
PARSE_IGNORED = 2


class EvalError(Exception):
    pass


def load_ull_file(filename):
    """
        Loads a data file
    """
    with open(filename) as file:
        data = file.readlines()
    return data


def get_parses(data, ignore_wall: bool=True, sort_parses: bool=True):
    """
        Separates parses from data into format:
        [
            [ <sentence>, <set-of-link-tuples>, <ignored-link-count> ]
            ...
        ]
        <sentence> - text string
        <set-of-link-tuples> - set of tuples, where each tuple has two token indexes
        <ignored-link-count> - integer value representing the number links which were not added to the set of tuples.

        Each list is splitted into tokens using space.
    """
    parses = []              # list of parses where each parse consists of two elements: sentence and the set of links
    parse = []
    
    for line in data:

        # Suppose that sentence line always starts with a letter
        if line[0].isalpha() or line[0] == "[":
            
            if len(parse) > 0:
                parses.append(parse)
                parse = []
                
            parse.append((((line.replace("[", "")).replace("]", "")).replace("\n", "")).strip())
            parse.append(set())
            parse.append(int(0))

        # Parses are always start with a digit
        elif line[0].isdigit():
            link = line.split()
    
            assert len(link) == 4

            # Do not add LW and period links to the set if 'ignore_wall' is specified
            if ignore_wall and (link[1] == "." or link[3] == "."
                                or link[1].startswith(r"###") or link[3].startswith(r"###")):

                parse[PARSE_IGNORED] += 1   # count ignored links
                continue

            # Only token indexes are added to the set
            parse[PARSE_LINK_SET].add((int(link[0]), int(link[2])))
            
    # Last parse should always be added to the list
    if len(parse) > 0:
        parses.append(parse)

    if sort_parses:
        parses.sort()

    # print(parses, file=sys.stdout)

    return parses


# def eval_parses1(test_parses: list, ref_parses: list, verbose: bool, ignore=bool, ofile=sys.stdout):
#     """
#         Compares test_parses against ref_parses link by link
#         counting errors
#     """
#     total_linkages = len(ref_parses)        # in gold standard
#     extra_links = 0.0                       # links present in test, but not in ref
#     missing_links = 0.0                     # links present in ref, but not in test
#     ignored_links = 0.0                     # ignored links, if ignore is active
#     quality_ratio = 0.0                     # quality ratio
#
#     if len(ref_parses) != len(test_parses):
#         print("Error: files don't contain same parses. "
#               "Number of sentences missmatch. Ref={}, Test={}".format(len(ref_parses), len(test_parses)))
#         return
#
#     for ref_parse, test_parse in zip(ref_parses, test_parses):
#
#         if ref_parse[0] != test_parse[0]:
#             print(ref_parse[0], file=ofile)
#             print(test_parse[0], file=ofile)
#             print("Error: Something went wrong. Sentences missmatch.", file=ofile)
#             return
#
#         # if verbose:
#         #     print("Sentence: {}".format(" ".join(ref_sent)), file=ofile)
#         #     print("Missing links: {}".format(current_missing), file=ofile)
#         #     print("Extra links: {}".format(len(test_sets)), file=ofile)
#
#         (m, e, q) = calc_parse_quality(test_parse[1], ref_parse[1])
#
#         missing_links += m
#         extra_links += e
#         quality_ratio += q
#         ignored_links += test_parse[2]
#
#     if total_linkages > 1:
#         missing_links /= float(total_linkages)
#         extra_links   /= float(total_linkages)
#         quality_ratio /= float(total_linkages)
#         ignored_links /= float(total_linkages)
#
#     print("\nParse quality: {0:2.2f}%".format(quality_ratio*100.0), file=ofile)
#     print("A total of {} links".format(total_linkages), file=ofile)
#     print("Average ignored links: {0:2.2f}".format(ignored_links), file=ofile)
#     print("Average missing links: {0:2.2f}".format(missing_links), file=ofile)
#     print("Average extra links:  {0:2.2f}".format(extra_links), file=ofile)


def eval_parses(test_parses: list, ref_parses: list, verbose: bool, ofile=sys.stdout) -> ParseQuality:
    """
        Compares test_parses against ref_parses link by link
        counting errors

    :param test_parses: List of test parses in format, prepared by get_parses.
    :param ref_parses: List of reference parses.
    :param verbose: Boolean value which enables intermediate result output if set to True.
    :param ofile: Output file handle.
    :return: ParseQuality class instance filled with the result data.
    """
    total_linkages = len(ref_parses)        # in gold standard

    total_parse_quality = ParseQuality()

    if len(ref_parses) != len(test_parses):
        raise EvalError("Error: files don't contain same parses. "
                        "Number of sentences missmatch. Ref={}, Test={}".format(len(ref_parses), len(test_parses)))

    for ref_parse, test_parse in zip(ref_parses, test_parses):

        if ref_parse[PARSE_SENTENCE] != test_parse[PARSE_SENTENCE]:
            raise EvalError("Error: Something went wrong. Sentences missmatch." +
                            ref_parse[PARSE_SENTENCE] + "\n" + test_parse[PARSE_SENTENCE])

        pq = parse_quality(test_parse[PARSE_LINK_SET], ref_parse[PARSE_LINK_SET])

        pq.ignored += test_parse[PARSE_IGNORED]

        if verbose:
            print(ParseQuality.text(pq), file=sys.stdout)

        total_parse_quality += pq

    if total_linkages > 1:
        total_parse_quality /= float(total_linkages)

    print(ParseQuality.text(total_parse_quality), file=ofile)

    return total_parse_quality


def compare_ull_files(test_path, ref_file, verbose, ignore_left_wall) -> ParseQuality:
    """
    Initiate evaluation process for one or multiple files.

    :param test_path: Path to file(s) to be tested.
    :param ref_file: Path to reference file(s).
    :param verbose: Boolean value which eables intermediate result output if set to True.
    :param ignore_left_wall: Boolean value which tells the script to ignore LEFT-WALL and period links if set to True.
    :return: ParseQuality class instance holding parse quality results for the whole corpus (all files if test_path is
                a directory name).
    """
    total_parse_quality = ParseQuality()
    total_file_count = 0

    def evaluate(test_file):
        """ Callback evaluation function """

        nonlocal total_parse_quality
        nonlocal total_file_count

        print("\nComparing parses:")
        print("-----------------")
        print("File being tested: '" + test_file + "'")
        print("Reference file   : '" + ref_file + "'")

        suffix = "" if test_file[-1] != "2" else "2"

        out_file = test_file + ".stat" + suffix

        print("Result file      : '" + out_file + "'")

        mode = "a" if os.path.isfile(out_file) else "w"

        try:
            ref_data = load_ull_file(ref_file)
            ref_parses = get_parses(ref_data, ignore_left_wall)

            test_data = load_ull_file(test_file)
            test_parses = get_parses(test_data, ignore_left_wall)

            with open(out_file, mode) as ofile:
                print("Reference file   : '" + ref_file + "'", file=ofile)

                total_parse_quality += eval_parses(test_parses, ref_parses, verbose, ofile)
                total_file_count += 1

        except IOError as err:
            print("IOError: " + str(err))

        except Exception as err:
            print("Exception: " + str(err))

    try:
        # If specified name is a file.
        if os.path.isfile(test_path):
            evaluate(test_path)

        # If specified name is a directory.
        elif os.path.isdir(test_path):
            traverse_dir(test_path, ".ull2", evaluate, None, True)

        # If file or directory does not exist.
        else:
            raise("Error: File or directory '" + test_path + "' does not exist.")

        if total_file_count > 1:
            total_parse_quality /= float(total_file_count)

    except IOError as err:
        print("IOError: " + str(err))

    except Exception as err:
        print("Exception: " + str(err))

    finally:
        return total_parse_quality
