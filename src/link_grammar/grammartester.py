import os
import sys

from .absclient import AbstractGrammarTestClient, AbstractDashboardClient, AbstractFileParserClient
from .dirhelper import traverse_dir_tree, create_dir
from .parsemetrics import ParseMetrics, ParseQuality
from .lgparse import get_dir_name, create_grammar_dir
from .lgmisc import get_output_suffix

from .optconst import *

# from grammartest import traverse_dir_tree, ParseMetrics, get_dir_name, create_grammar_dir, create_dir


class GrammarTestError(Exception):
    pass

# on_corpus_file() argument list indexes
# [dest_path, lang_path, dict_path, corpus_path, output_path, reference_path]
CORP_ARG_DEST = 0
CORP_ARG_LANG = 1
CORP_ARG_DICT = 2
CORP_ARG_CORP = 3
CORP_ARG_OUTP = 4
CORP_ARG_REFF = 5

# on_dict_file() argument list indexes
# [dict_path, corpus_path, output_path, reference_path]
DICT_ARG_DICT = 0       # original dict_path
DICT_ARG_CORP = 1
DICT_ARG_OUTP = 2
DICT_ARG_REFF = 3


class GrammarTester(AbstractGrammarTestClient):

    def __init__(self, grmr: str, tmpl: str, limit: int, options: int, parser: AbstractFileParserClient,
                 dboard: AbstractDashboardClient=None):

        if parser is None:
            raise GrammarTestError("GrammarTestError: 'parser' argument can not be None.")

        if not isinstance(parser, AbstractFileParserClient):
            raise GrammarTestError("GrammarTestError: 'parser' is not an instance of AbstractFileParserClient")

        if not dboard is None and not isinstance(dboard, AbstractDashboardClient):
            raise GrammarTestError("ArgumentError: 'parser' is not an instance of AbstractParser")

        self._parser = parser
        self._dboard = dboard
        self._grammar_root = grmr
        self._template_dir = tmpl
        self._linkage_limit = limit
        self._options = options
        self._is_dir_corpus = False
        self._is_dir_dict = False
        self._total_metrics = ParseMetrics()
        self._total_quality = ParseQuality()
        self._total_files = 0
        self._total_dicts = 0

    @staticmethod
    def _save_stat(stat_path: str, metrics: ParseMetrics, quality: ParseQuality):
        """
        Save statistic estimation results into a file.

        :param stat_path: Path to file.
        :param full_ratio: Fully parsed sentences quantity to total number of sentences ratio.
        :param none_ratio: Completely unparsed sentences quantity to total number of sentences ratio.
        :param avrg_ratio: Average parse ratio.
        :return:
        """
        stat_file_handle = None

        try:
            stat_file_handle = sys.stdout if stat_path is None else open(stat_path, "w")

            assert metrics.average_parsed_ratio <= 1, "metrics.average_parsed_ratio > 1"
            assert quality.quality <= 1, "quality.quality = " + str(quality.quality)

            print(ParseMetrics.text(metrics), file=stat_file_handle)
            print(ParseQuality.text(quality), file=stat_file_handle)
            print("PQA:\t{0:2.2f}%".format(metrics.average_parsed_ratio*quality.quality*100), file=stat_file_handle)

        except IOError as err:
            print("IOError: " + str(err))

        except FileNotFoundError as err:
            print("FileNotFoundError: " + str(err))

        except OSError as err:
            print("OSError: " + str(err))

        except Exception as err:
            print("Exception: " + str(err))

        finally:
            if stat_file_handle is not None and stat_file_handle != sys.stdout:
                stat_file_handle.close()

    @staticmethod
    def _on_dict_dir(dict_dir_path: str, args: list) -> bool:
        """
        Callback function that duplicates internal subdirectory structure of the dictionary folder
        in destination root directory.

        :param dict_dir_path: Path to a directory in dictionary tree.
        :param args: List of arguments.
        :return: True if subdirectory in the destination path is successfully created, False otherwise.
        """
        return create_dir(args[DICT_ARG_OUTP] + dict_dir_path[len(args[DICT_ARG_DICT]):])

    @staticmethod
    def _on_corp_dir(corp_dir_path: str, args: list) -> bool:
        """
        Callback function that duplicates internal subdirectory structure of the corpus folder
        in destination root directory.

        :param corp_dir_path: Path to a directory in dictionary tree.
        :param args: List of arguments.
        :return: True if subdirectory in the destination path is successfully created, False otherwise.
        """
        # print(corp_dir_path)
        # print(args[CORP_ARG_DEST] + corp_dir_path[len(args[CORP_ARG_CORP]):])

        return create_dir(args[CORP_ARG_DEST] + corp_dir_path[len(args[CORP_ARG_CORP]):])

    def _get_output_file_name(self, corpus_file_path: str, args: list) -> str:
        return args[CORP_ARG_DEST] + "/" + os.path.split(corpus_file_path)[1]  # + get_output_suffix(self._options)
        # if self._is_dir_corpus:
        #     # Take corpus file name and append it to the destination path
        #     return args[CORP_ARG_DEST] + "/" + os.path.split(corpus_file_path)[1] # + get_output_suffix(self._options)
        # else:
        #     # Take corpus file name and append it to the destination path
        #     return args[CORP_ARG_DEST] + "/" + os.path.split(args[CORP_ARG_CORP])[1] # + get_output_suffix(self._options)

    def _get_ref_file_name(self, corpus_file_path: str, args: list):
        """ Return reference file path """

        if self._is_dir_corpus:
            if args[CORP_ARG_REFF] is None:
                return None

            return args[CORP_ARG_REFF] + corpus_file_path[len(args[CORP_ARG_CORP]):] + ".ref"

        return args[CORP_ARG_REFF]

    def _on_corpus_file(self, corpus_file_path: str, args: list) -> None:
        """
        Callback method which is called for each corpus file in corpus root path.

        :param corpus_file_path: Path to a corpus file.
        :param args: List of arguments
        :return: None
        """
        dict_path = args[CORP_ARG_LANG]

        try:
            out_file = self._get_output_file_name(corpus_file_path, args)
            ref_file = self._get_ref_file_name(corpus_file_path, args)

            # file_metrics, file_quality = ParseMetrics(), ParseQuality()

            file_metrics, file_quality = self._parser.parse(dict_path, corpus_file_path, out_file,
                                                            ref_file, self._options)

            if self._options & (BIT_SEP_STAT | BIT_OUTPUT) == BIT_SEP_STAT:
                stat_name = out_file + ".stat"
                stat_name += "2" if (self._options & BIT_LG_EXE) else ""

                assert file_metrics.average_parsed_ratio <= 1.0, "on_corpus_file(): file_metrics.average_parsed_ratio > 1.0"
                assert file_quality.quality <= 1.0, "on_corpus_file(): file_quality.quality > 1.0"

                self._save_stat(stat_name, file_metrics, file_quality)

            self._total_metrics += file_metrics
            self._total_quality += file_quality
            self._total_files += 1

        except Exception as err:
            print("_on_corpus_file(): " + str(err))

    def _on_dict_file(self, dict_file_path: str, args: list) -> None:
        """
        Callback method which is called for each dictionary file.

        :param dict_file_path: Path to a .dict file.
        :param args: Argument list.
        :return: None
        """
        self._total_metrics, self._total_quality = ParseMetrics(), ParseQuality()
        self._total_files = 0

        try:
            dict_path = os.path.split(dict_file_path)[0]
            corp_path = args[DICT_ARG_CORP]
            dest_path = args[DICT_ARG_OUTP] + str(dict_path[len(args[DICT_ARG_DICT]):])

            # If BIT_LOC_LANG is set the language subdirectory is created in destination directory
            grmr_path = dest_path if self._options & BIT_LOC_LANG else self._grammar_root

            # Create new LG dictionary using .dict file and template directory with the rest of mandatory files.
            lang_path = create_grammar_dir(dict_file_path, grmr_path, self._template_dir, self._options)

            if os.path.isfile(corp_path):
                self._on_corpus_file(corp_path, [dest_path, lang_path] + args)

            elif os.path.isdir(corp_path):
                traverse_dir_tree(corp_path, "", [self._on_corpus_file, dest_path, lang_path] + args,
                                                 [self._on_corp_dir, dest_path, lang_path] + args, True)

            if self._total_files > 1:
                self._total_metrics /= float(self._total_files)
                self._total_quality /= float(self._total_files)

            stat_suffix = "2" if (self._options & BIT_LG_EXE) == BIT_LG_EXE else ""
            stat_path = dest_path + "/" + os.path.split(corp_path)[1] + ".stat" + stat_suffix

            assert self._total_metrics.average_parsed_ratio <= 1.0, "on_dict_file(): _total_metrics.average_parsed_ratio > 1.0"
            assert self._total_quality.quality <= 1.0, "on_dict_file(): _total_quality.quality > 1.0"

            self._save_stat(stat_path, self._total_metrics, self._total_quality)

        except Exception as err:
            print("_on_dict_file(): "+str(err))

        # if self._is_dir_dict: # and not self._dboard is None:
        #     names = dict_path[len(args[DICT_ARG_DICT])+1:].split("/")[-2:]
        #     print(names)

            # self._dboard.set_cell_by_names(names[1].decode(), names[0].decode(), self._total_metrics.average_parsed_ratio*100)

        self._total_dicts += 1

    def test(self, dict_path: str, corpus_path: str, output_path: str, reference_path: str) \
            -> (ParseMetrics, ParseQuality):
        """
        Main method to initiate grammar test.

        :param dict_path: Path to a dictionary file or directory.
        :param corpus_path: Path to a corpus file or corpus root directory.
        :param output_path: Output root path.
        :param reference_path: Path to a reference file or reference root directory. In case of directory we assume
                                that it has the same internal structure with the same set of files in it as corpus
                                root directory.
        :return:
        """
        self._total_dicts = 0
        self._is_dir_corpus = os.path.isdir(corpus_path)
        self._is_dir_dict = os.path.isdir(dict_path)

        # print(self._is_dir_dict, self._is_dir_corpus, corpus_path)

        if not reference_path is None:
            if self._is_dir_corpus and not os.path.isdir(reference_path):
                raise GrammarTestError("GrammarTestError: If 'corpus_path' is a directory 'reference_path' should be an "
                                       "existing directory path too.")
            else:
                if not os.path.isfile(reference_path):
                    raise GrammarTestError("GrammarTestError: If 'corpus_path' is a file 'reference_path' should be an "
                                           "existing file path too.")

        try:
            # Arguments for callback functions
            parse_args = [dict_path, corpus_path, output_path, reference_path]

            # If dict_path is a directory then call on_dict_file for every .dict file found.
            if self._is_dir_dict:
                traverse_dir_tree(dict_path, ".dict", [self._on_dict_file]+parse_args, [self._on_dict_dir]+parse_args,
                                  # lambda : [self._on_dict_dir]+parse_args if self._options & BIT_DPATH_CREATE else [],
                                  True)

            # Otherwise it can be either single .dict file name or name of LG preinstalled dictionary e.g. 'en'
            else:
                # If dict_path points to a single file no need to duplicate subdirectory structure
                self._options &= (~BIT_DPATH_CREATE)
                self._on_dict_file(dict_path, parse_args)

        except GrammarTestError as err:
            raise GrammarTestError("GrammarTestError: " + str(err))

        except Exception as err:
            raise GrammarTestError("Exception: " + str(err))

        finally:
            return self._total_metrics, self._total_quality


# def parse_file_with_api(dict_path: str, corpus_path: str, output_path: str, linkage_limit: int, options: int) \
#         -> ParseMetrics:



def parse_corpus(src_dir: str, dst_dir: str, dict_dir: str, grammar_dir: str, template_dir: str,
                       linkage_limit: int, options: int, reference_path: str) -> ParseMetrics:

    gt = GrammarTester(grammar_dir, template_dir, linkage_limit, options, None)

    return gt.test(dict_dir, src_dir, dst_dir, reference_path)


# parse_corpus(corp, dest, dict, grmr, tmpl, limit, opts, ref)
