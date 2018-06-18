import re
import sys
from linkgrammar import LG_DictionaryError, LG_Error, ParseOptions, Dictionary, Sentence

from .optconst import *
from .parsemetrics import ParseMetrics, ParseQuality
from .parsestat import parse_metrics, parse_quality
from .psparse import parse_postscript, prepare_tokens, get_link_set
from .lgmisc import get_output_suffix, print_output
from .absclient import AbstractFileParserClient
from .parsevaluate import load_ull_file, get_parses


__all__ = ['LGApiParser']


class LGApiParser(AbstractFileParserClient):

    def __init__(self, limit: int=1000):
        self._linkage_limit = limit

    def parse(self, dict_path: str, corpus_path: str, output_path: str, ref_path: str, options: int) \
            -> (ParseMetrics, ParseQuality):
        """
        Link Grammar API parser invokation routine.

        :param dict_path:       Dictionary file or directory path.
        :param corpus_path:     Corpus file or directory path.
        :param output_path:     Output file or directory path.
        :param ref_path:        Reference file or directory path.
        :param options:         Bit field. See `optconst.py` for details
        :return:                Tuple (ParseMetrics, ParseQuality)
        """
        input_file_handle = None
        output_file_handle = None

        ref_parses = []

        # Sentence statistics variables
        total_metrics, total_quality = ParseMetrics(), ParseQuality()

        sentence_count = 0                  # number of sentences in the corpus

        print("Info: Parsing a corpus file: '" + corpus_path + "'")
        print("Info: Using dictionary: '" + dict_path + "'")

        if output_path is not None:
            print("Info: Parses are saved in: '" + output_path+get_output_suffix(options) + "'")
        else:
            print("Info: Output file name is not specified. Parses are redirected to 'stdout'.")

        try:
            if options & BIT_PARSE_QUALITY and ref_path is not None:
                try:
                    data = load_ull_file(ref_path)
                    ref_parses = get_parses(data, (options & BIT_NO_LWALL) == BIT_NO_LWALL, False)

                except Exception as err:
                    print("Exception: " + str(err))

            link_line = re.compile(r"\A[0-9].+")

            po = ParseOptions(min_null_count=0, max_null_count=999)
            po.linkage_limit = self._linkage_limit

            di = Dictionary(dict_path)

            input_file_handle = open(corpus_path)
            output_file_handle = sys.stdout if output_path is None \
                                            else open(output_path+get_output_suffix(options), "w")

            for line in input_file_handle:

                # Filter out links when ULL parses are used as input
                if options & BIT_ULL_IN > 0 and link_line.match(line):
                    continue

                # Skip empty lines to get proper statistics estimation and skip commented lines
                if len(line.strip()) < 1:  # or line.startswith("#"):
                    continue

                # Tokenize and parse the sentence
                sent = Sentence(line, di, po)
                linkages = sent.parse()

                sent_metrics, sent_quality = ParseMetrics(), ParseQuality()
                linkage_count = 0

                for linkage in linkages:

                    # Only the first linkage is counted.
                    if linkage_count == 1:
                        break

                    if (options & BIT_OUTPUT_DIAGRAM) == BIT_OUTPUT_DIAGRAM:
                        print(linkage.diagram(), file=output_file_handle)

                    elif (options & BIT_OUTPUT_POSTSCRIPT) == BIT_OUTPUT_POSTSCRIPT:
                        print(linkage.postscript(), file=output_file_handle)

                    elif (options & BIT_OUTPUT_CONST_TREE) == BIT_OUTPUT_CONST_TREE:
                        print(linkage.constituent_tree(), file=output_file_handle)

                    elif not (options & BIT_OUTPUT):

                        tokens, links = parse_postscript(linkage.postscript().replace("\n", ""), options,
                                                         output_file_handle)

                        # Print ULL formated parses
                        print_output(tokens, links, options, output_file_handle)

                        # Calculate parseability
                        sent_metrics += parse_metrics(prepare_tokens(tokens, options))

                        # Calculate parse quality if the option is set
                        if options & BIT_PARSE_QUALITY and len(ref_parses):
                            sent_quality += parse_quality(get_link_set(tokens, links, options),
                                                          ref_parses[sentence_count][1])

                    linkage_count += 1

                assert sent_metrics.average_parsed_ratio <= 1.0, "sent_metrics.average_parsed_ratio > 1.0"
                assert sent_quality.quality <= 1.0, "sent_quality.quality > 1.0"

                total_metrics += sent_metrics
                total_quality += sent_quality

                # if not linkage_count:
                #     sent_metrics.completely_unparsed_ratio += 1

                sentence_count += 1

            total_metrics.sentences = sentence_count
            total_quality.sentences = sentence_count

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

            return total_metrics, total_quality
