import sys
import os

try:
    from link_grammar.parsestat import calc_parse_quality
    from link_grammar.lgparse import traverse_dir
except:
    from parsestat import calc_parse_quality
    from lgparse import traverse_dir


__all__ = ['Load_File', 'Get_Parses', 'MakeSets', 'Evaluate_Parses', 'get_parses', 'eval_parses', 'compare_ull_files']


def Load_File(filename):
    """
        Loads a data file
    """
    with open(filename) as file:
        data = file.readlines()
    return data


def get_parses(data, ignore_wall:bool=True):
    """
        Separates parses from data into format:
        [
          [[sentence-parse1][link1-parse1][link2-parse1] ... ]
          [[sentence-parse2][link1-parse2][link2-parse2] ... ]
          ...
        ]
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

                parse[2] += 1   # count ignored links
                continue

            # Only token indexes are added to the set
            parse[1].add((link[0], link[2]))
            
    # Last parse should always be added to the list
    if len(parse) > 0:
        parses.append(parse)

    parses.sort()

    # print(parses, file=sys.stdout)

    return parses


def eval_parses(test_parses:list, ref_parses:list, verbose:bool, ignore=bool, ofile=sys.stdout):
    """
        Compares test_parses against ref_parses link by link
        counting errors
    """
    total_linkages = len(ref_parses)        # in gold standard
    extra_links = 0.0                       # links present in test, but not in ref
    missing_links = 0.0                     # links present in ref, but not in test
    ignored_links = 0.0                     # ignored links, if ignore is active
    quality_ratio = 0.0                     # quality ratio

    if len(ref_parses) != len(test_parses):
        print("Error: files don't contain same parses. "
              "Number of sentences missmatch. Ref={}, Test={}".format(len(ref_parses), len(test_parses)))
        return

    for ref_parse, test_parse in zip(ref_parses, test_parses):

        if ref_parse[0] != test_parse[0]:
            print(ref_parse[0], file=ofile)
            print(test_parse[0], file=ofile)
            print("Error: Something went wrong. Sentences missmatch.", file=ofile)
            return

        # if verbose:
        #     print("Sentence: {}".format(" ".join(ref_sent)), file=ofile)
        #     print("Missing links: {}".format(current_missing), file=ofile)
        #     print("Extra links: {}".format(len(test_sets)), file=ofile)

        (m, e, q) = calc_parse_quality(test_parse[1], ref_parse[1])

        missing_links += m
        extra_links += e
        quality_ratio += q
        ignored_links += test_parse[2]

    if total_linkages > 1:
        missing_links /= float(total_linkages)
        extra_links   /= float(total_linkages)
        quality_ratio /= float(total_linkages)
        ignored_links /= float(total_linkages)

    print("\nParse quality: {0:2.2f}%".format(quality_ratio*100.0), file=ofile)
    print("A total of {} links".format(total_linkages), file=ofile)
    print("Average ignored links: {0:2.2f}".format(ignored_links), file=ofile)
    print("Average missing links: {0:2.2f}".format(missing_links), file=ofile)
    print("Average extra links:  {0:2.2f}".format(extra_links), file=ofile)


def Get_Parses(data, ignore_wall=True):
    """
        Separates parses from data into format:
        [
          [[sentence-parse1][link1-parse1][link2-parse1] ... ]
          [[sentence-parse2][link1-parse2][link2-parse2] ... ]
          ...
        ]
        Each list is splitted into tokens using space.

        Token renumeration added. Works only when ignore_wall=True.
    """
    parses = []
    parse_num = -1
    new_flag = True

    links_skipped = 0

    for line in data:

        if line == "\n":
            new_flag = True
            continue

        if new_flag:
            parse_num += 1
            new_flag = False
            parses.append([[(((line.replace("[", "")).replace("]", "")).replace("\n", "")).strip()]])
            links_skipped = 0
            continue

        parse = line.split()

        assert len(parse) == 4

        if ignore_wall and (parse[1] == "." or parse[3] == "."
                            or parse[1].startswith(r"###") or parse[3].startswith(r"###")):
            links_skipped += 1
            continue

        new_parse = []

        for i, element in zip(range(len(parse)), parse):
            new_element = element if (i & 1) else int(element) # - links_skipped
            new_parse.append(new_element)

        # print(new_parse)
        parses[parse_num].append(new_parse)

    parses.sort()

    # print(parses)

    return parses


def MakeSets(parse):
    """
        Gets a list with links (without full sentence) and
        and makes sets for each link's ids
    """
    link_sets = [{(link[0], link[1]), (link[2], link[3])} for link in parse]
    return link_sets


def Evaluate_Parses(test_parses, ref_parses, verbose, ignore, ofile):
    """
        Compares test_parses against ref_parses link by link
        counting errors
    """
    total_links = 0     # in gold standard
    #extra_links = 0     # links present in test, but not in ref
    missing_links = 0   # links present in ref, but not in test
    ignored_links = 0   # ignored links, if ignore is active

    for ref_parse, test_parse in zip(ref_parses, test_parses):
        current_missing = 0
        ref_sent = ref_parse.pop(0)[0].split()
        test_sent = test_parse.pop(0)[0].split()

        if ref_sent != test_sent:
            print(ref_sent, file=ofile)
            print(test_sent, file=ofile)
            print("Error: files don't contain same parses", file=ofile)

            print(ref_sent)
            print(test_sent)
            print("Error: files don't contain same parses")
            return

        ref_sets = MakeSets(ref_parse)  # using sets to ignore link directions
        test_sets = MakeSets(test_parse)
        sent_length = str(len(ref_sent))

        # loop over every ref link and try to find it in test
        for ref_link in ref_sets:
            if ignore:
                if (('0', '###LEFT-WALL###') in ref_link) or ((sent_length, ".") in ref_link):
                    ignored_links += 1
                    continue
            total_links += 1
            if ref_link in test_sets:
                test_sets.remove(ref_link)
            else:
                current_missing += 1 # count links not contained in test

        if verbose:
            print("Sentence: {}".format(" ".join(ref_sent)), file=ofile)
            print("Missing links: {}".format(current_missing), file=ofile)
            print("Extra links: {}".format(len(test_sets)), file=ofile)

        #extra_links += len(test_sets) # count links not contained in reference
        missing_links += current_missing

    score = 1 - missing_links / total_links
    print("\nParses score: {0:2.2f}".format(score*100.0), file=ofile)
    print("A total of {} links".format(total_links), file=ofile)
    print("A total of {} ignored links".format(ignored_links), file=ofile)
    print("A total of {} missing links".format(missing_links), file=ofile)
    #print("A total of {} extra links".format(extra_links))


def compare_ull_files(test_path, ref_file, verbose, ignore_WALL):
    """ Initiates evaluation process for one or multiple files."""

    def evaluate(test_file):
        """ Callback evaluation function """
        print("\nComparing parses:")
        print("-----------------")
        print("File being tested: '" + test_file + "'")
        print("Reference file   : '" + ref_file + "'")

        out_file = test_file + ".qc"
        print("Result file      : '" + out_file + "'")

        try:
            test_data = Load_File(test_file)
            # test_parses = Get_Parses(test_data)

            test_parses = get_parses(test_data, ignore_WALL)

            ref_data = Load_File(ref_file)
            # ref_parses = Get_Parses(ref_data)

            ref_parses = get_parses(ref_data, ignore_WALL)

            with open(out_file, "w") as ofile:
                print("Reference file   : '" + ref_file + "'", file=ofile)
                # Evaluate_Parses(test_parses, ref_parses, verbose, ignore_WALL, ofile)

                eval_parses(test_parses, ref_parses, verbose, ignore_WALL, ofile)

        except IOError as err:
            print("IOError: " + str(err))

        except Exception as err:
            print("Exception: " + str(err))


    # If specified name is a file.
    if os.path.isfile(test_path):
        evaluate(test_path)

    # If specified name is a directory.
    elif os.path.isdir(test_path):
        traverse_dir(test_path, ".ull2", evaluate, None, True)

    # If file or directory does not exist.
    else:
        raise("Error: File or directory '" + test_path + "' does not exist.")
