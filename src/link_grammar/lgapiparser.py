import re
import sys
from linkgrammar import LG_DictionaryError, LG_Error, ParseOptions, Dictionary, Sentence

from .optconst import *
from .parsemetrics import ParseMetrics
from .parsestat import parse_metrics, calc_stat
from .psparse import parse_postscript
from .lgmisc import get_output_suffix, print_output

__all__ = ['parse_file_with_api']


def parse_file_with_api(dict_path: str, corpus_path: str, output_path: str, linkage_limit: int, options: int) \
        -> ParseMetrics:
    """
    Link parser invocation routine.

    :param dict_path: name or path to the dictionary
    :param corpus_path: path to the test text file
    :param output_path: output file path
    :param linkage_limit: maximum number of linkages LG may return when parsing a sentence
    :param options: bit field. Use bit mask constants to set or reset one or multiple bits:
                BIT_CAPS  = 0x01    Keep capitalized letters in tokens untouched if set,
                                    make all lowercase otherwise.
                BIT_RWALL = 0x02    Keep all links with RIGHT-WALL if set, ignore them otherwise.
                BIT_STRIP = 0x04    Strip off token suffixes if set, remove them otherwise.
    :return: ParseMetrics instance.
    """

    input_file_handle = None
    output_file_handle = None

    # Sentence statistics variables
    total_metrics = ParseMetrics()

    line_count = 0                  # number of sentences in the corpus

    print("Info: Parsing a corpus file: '" + corpus_path + "'")
    print("Info: Using dictionary: '" + dict_path + "'")

    if output_path is not None:
        print("Info: Parses are saved in: '" + output_path+get_output_suffix(options) + "'")
    else:
        print("Info: Output file name is not specified. Parses are redirected to 'stdout'.")

    try:
        link_line = re.compile(r"\A[0-9].+")

        po = ParseOptions(min_null_count=0, max_null_count=999)
        po.linkage_limit = linkage_limit

        di = Dictionary(dict_path)

        input_file_handle = open(corpus_path)
        output_file_handle = sys.stdout if output_path is None else open(output_path+get_output_suffix(options), "w")

        for line in input_file_handle:

            # Filter out links when ULL parses are used as input
            if options & BIT_ULL_IN > 0 and link_line.match(line):
                continue

            # Skip empty lines to get proper statistics estimation and skip commented lines
            if len(line.strip()) < 1 or line.startswith("#"):
                continue

            sent = Sentence(line, di, po)
            linkages = sent.parse()

            sent_metrics = ParseMetrics()
            linkage_count = 0

            for linkage in linkages:

                # Only the first linkage is counted.
                if linkage_count == 1:
                    break

                tokens, links = parse_postscript(linkage.postscript().replace("\n", ""), options, output_file_handle)

                if not (options & BIT_OUTPUT):
                    print_output(tokens, links, options, output_file_handle)

                elif (options & BIT_OUTPUT_DIAGRAM) == BIT_OUTPUT_DIAGRAM:
                    print(linkage.diagram(), file=output_file_handle)

                elif (options & BIT_OUTPUT_POSTSCRIPT) == BIT_OUTPUT_POSTSCRIPT:
                    print(linkage.postscript(), file=output_file_handle)

                elif (options & BIT_OUTPUT_CONST_TREE) == BIT_OUTPUT_CONST_TREE:
                    print(linkage.constituent_tree(), file=output_file_handle)

                sent_metrics += parse_metrics(tokens)

                linkage_count += 1

            if linkage_count > 1:
                sent_metrics /= linkage_count

            if not linkage_count:
                sent_metrics.completely_unparsed_ratio += 1

            total_metrics += sent_metrics
            line_count += 1

        if line_count > 1:
            total_metrics /= line_count

        # Prevent interleaving "Dictionary close" messages
        ParseOptions(verbosity=0)

    except LG_DictionaryError as err:
        print("LG_DictionaryError: " + str(err))

    except LG_Error as err:
        print("LG_Error: " + str(err))

    except IOError as err:
        print("IOError: " + str(err))

    except FileNotFoundError as err:
        print("FileNotFoundError: " + str(err))

    finally:
        if input_file_handle is not None:
            input_file_handle.close()

        if output_file_handle is not None and output_file_handle != sys.stdout:
            output_file_handle.close()

        return total_metrics


def parse_file_with_api0(dict_path, corpus_path, output_path, linkage_limit, options) \
        -> (float, float, float):
    """
    Link parser invocation routine.

    :param dict_path: name or path to the dictionary
    :param corpus_path: path to the test text file
    :param output_path: output file path
    :param linkage_limit: maximum number of linkages LG may return when parsing a sentence
    :param options: bit field. Use bit mask constants to set or reset one or multiple bits:
                BIT_CAPS  = 0x01    Keep capitalized letters in tokens untouched if set,
                                    make all lowercase otherwise.
                BIT_RWALL = 0x02    Keep all links with RIGHT-WALL if set, ignore them otherwise.
                BIT_STRIP = 0x04    Strip off token suffixes if set, remove them otherwise.
    :return: tuple (float, float, float):
                - percentage of totally parsed sentences;
                - percentage of completely unparsed sentences;
                - percentage of parsed sentences;
    """

    input_file_handle = None
    output_file_handle = None

    # Sentence statistics variables
    sent_full = 0                   # number of fully parsed sentences
    sent_none = 0                   # number of completely unparsed sentences
    sent_stat = 0.0                 # average value of parsed sentences (linkages)

    line_count = 0                  # number of sentences in the corpus

    print("Info: Parsing a corpus file: '" + corpus_path + "'")
    print("Info: Using dictionary: '" + dict_path + "'")

    if output_path is not None:
        print("Info: Parses are saved in: '" + output_path+get_output_suffix(options) + "'")
    else:
        print("Info: Output file name is not specified. Parses are redirected to 'stdout'.")

    try:
        link_line = re.compile(r"\A[0-9].+")

        po = ParseOptions(min_null_count=0, max_null_count=999)
        po.linkage_limit = linkage_limit

        di = Dictionary(dict_path)

        input_file_handle = open(corpus_path)
        output_file_handle = sys.stdout if output_path is None else open(output_path+get_output_suffix(options), "w")

        for line in input_file_handle:

            # Filter out links when ULL parses are used as input
            if options & BIT_ULL_IN > 0 and link_line.match(line):
                continue

            # Skip empty lines to get proper statistics estimation and skip commented lines
            if len(line.strip()) < 1 or line.startswith("#"):
                continue

            sent = Sentence(line, di, po)
            linkages = sent.parse()

            # Number of linkages taken in statistics estimation
            linkage_countdown = 1

            temp_full = 0
            temp_none = 0
            temp_stat = 0.0

            for linkage in linkages:
#=============================================================================================================
                if (options & BIT_OUTPUT_DIAGRAM) == BIT_OUTPUT_DIAGRAM:
                    print(linkage.diagram(), file=output_file_handle)

                elif (options & BIT_OUTPUT_POSTSCRIPT) == BIT_OUTPUT_POSTSCRIPT:
                    print(linkage.postscript(), file=output_file_handle)

                elif (options & BIT_OUTPUT_CONST_TREE) == BIT_OUTPUT_CONST_TREE:
                    print(linkage.constituent_tree(), file=output_file_handle)

                tokens, links = parse_postscript(linkage.postscript().replace("\n", ""), options, output_file_handle)

                if not (options & BIT_OUTPUT):
                    print_output(tokens, links, options, output_file_handle)

                (f, n, s) = calc_stat(tokens)

                if linkage_countdown:
                    temp_full += f
                    temp_none += n
                    temp_stat += s
                    linkage_countdown -= 1

            if len(linkages) > 0:
                sent_full += temp_full
                sent_none += temp_none
                sent_stat += temp_stat / float(len(linkages))
            else:
                sent_none += 1

            line_count += 1

        # Prevent interleaving "Dictionary close" messages
        ParseOptions(verbosity=0)

    except LG_Error as err:
        print(str(err))

    except IOError as err:
        print(str(err))

    except FileNotFoundError as err:
        print(str(err))

    finally:
        if input_file_handle is not None:
            input_file_handle.close()

        if output_file_handle is not None and output_file_handle != sys.stdout:
            output_file_handle.close()

        return (0.0, 0.0, 0.0) if line_count == 0 else (float(sent_full) / float(line_count),
                                                        float(sent_none) / float(line_count),
                                                        sent_stat / float(line_count))
