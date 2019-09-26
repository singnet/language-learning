import os
import sys
import logging
from decimal import *
from time import time
from inspect import isclass

from ..common.absclient import AbstractGrammarTestClient, AbstractStatEventHandler, AbstractFileParserClient, \
    AbstractPipelineComponent, AbstractProgressClient
from ..common.dirhelper import traverse_dir_tree, create_dir
from ..common.parsemetrics import ParseMetrics, ParseQuality
from ..common.fileconfman import JsonFileConfigManager
from ..common.cliutils import handle_path_string, strip_quotes
from ..common.textprogress import TextProgress
from ..common.sentencecount import get_corpus_sentence_count
from ..common.tokencount import *
from ..common.optconst import *
from .textfiledashb import TextFileDashboardConf  # , HTMLFileDashboard

from .lgmisc import create_grammar_dir, get_output_suffix

from .lginprocparser import LGInprocParser


__all__ = ['test_grammar', 'GrammarTester', 'GrammarTestError']


class GrammarTestError(Exception):
    pass

CONF_MIN_WORD_CNT = "min_word_count"
CONF_MAX_SENT_LEN = "max_sentence_len"
CONF_STOP_TOKENS = "stop_tokens"
CONF_WORD_CNT_PATH = "word_count_path"

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

    def __init__(self, grmr: str, tmpl: str, limit: int, parser: AbstractFileParserClient,
                 evt_handler: AbstractStatEventHandler = None):

        if parser is None:
            raise AttributeError("'parser' argument can not be None.")

        if not isinstance(parser, AbstractFileParserClient):
            raise AttributeError("'parser' is not an instance of AbstractFileParserClient")

        if evt_handler is not None and not isinstance(evt_handler, AbstractStatEventHandler):
            raise AttributeError("'evt_handler' is not an instance of AbstractStatEventHandler")

        self._logger = logging.getLogger("GrammarTester")
        self._parser = parser
        self._event_handler = evt_handler
        self._grammar_root = grmr
        self._template_dir = tmpl
        self._linkage_limit = limit
        self._options = 0  # options
        self._is_dir_corpus = False
        self._is_dir_dict = False
        self._total_metrics = ParseMetrics()
        self._total_quality = ParseQuality()
        self._total_files = 0
        self._total_dicts = 0
        self._total_sentences = 0
        self._progress = None
        self._token_counts = {}
        self._test_kwargs = None

    @staticmethod
    def _save_stat(stat_path: str, metrics: ParseMetrics, quality: ParseQuality) -> None:
        """
        Save statistic estimation results into a file.

        :param stat_path:   Path to file.
        :param metrics:     ParseMetrics class pointer.
        :param quality:     ParseQulality class pointer.
        :return:            None
        """
        stat_file_handle = None

        try:
            stat_file_handle = sys.stdout if stat_path is None else open(stat_path, "w", encoding="utf-8")

            print(ParseMetrics.text(metrics), file=stat_file_handle)
            print(ParseQuality.text(quality), file=stat_file_handle)

        finally:
            if stat_file_handle is not None and stat_file_handle != sys.stdout:
                stat_file_handle.close()

    @staticmethod
    def _on_dict_dir(dict_dir_path: str, args: list) -> bool:
        """
        Callback function that duplicates internal subdirectory structure of the dictionary folder
        in destination root directory.

        :param dict_dir_path:   Path to a directory in dictionary tree.
        :param args:            List of arguments.
        :return:                True if subdirectory in the destination path is successfully created, False otherwise.
        """
        return create_dir(args[DICT_ARG_OUTP] + dict_dir_path[len(args[DICT_ARG_DICT]):])

    @staticmethod
    def _on_corp_dir(corp_dir_path: str, args: list) -> bool:
        """
        Callback function that duplicates internal subdirectory structure of the corpus folder
        in destination root directory.

        :param corp_dir_path:   Path to a directory in dictionary tree.
        :param args:            List of arguments.
        :return:                True if subdirectory in the destination path is successfully created, False otherwise.
        """
        return create_dir(args[CORP_ARG_DEST] + corp_dir_path[len(args[CORP_ARG_CORP]):])

    def _get_output_file_name(self, corpus_file_path: str, args: list) -> str:
        suff = get_output_suffix(self._options)
        return args[CORP_ARG_DEST] + "/" + os.path.split(corpus_file_path)[1] \
               + ("" if corpus_file_path.endswith(suff) else suff)

    def _get_ref_file_name(self, corpus_file_path: str, args: list):
        """ Return reference file path """

        if self._is_dir_corpus:
            if args[CORP_ARG_REFF] is None:
                return None

            ref_path = args[CORP_ARG_REFF] + corpus_file_path[len(args[CORP_ARG_CORP]):]

            if (self._options & BIT_ULL_IN) and ref_path.endswith(".ull"):
                return ref_path

            return ref_path + ".ull"

        return args[CORP_ARG_REFF]

    def _on_corpus_file(self, corpus_file_path: str, args: list) -> None:
        """
        Callback method which is called for each corpus file in corpus root path.

        :param corpus_file_path:    Path to a corpus file.
        :param args:                List of arguments
        :return:                    None
        """
        dict_path = args[CORP_ARG_LANG]

        start_time = time()
        out_file = self._get_output_file_name(corpus_file_path, args)
        ref_file = self._get_ref_file_name(corpus_file_path, args)

        file_metrics, file_quality = self._parser.parse(dict_path, corpus_file_path, out_file,
                                                        ref_file, self._options, self._progress, **self._test_kwargs)

        if self._options & (BIT_SEP_STAT | BIT_OUTPUT) == BIT_SEP_STAT:
            stat_name = out_file + ".stat"

            self._save_stat(stat_name, file_metrics, file_quality)

        file_metrics.parse_time = time() - start_time

        self._total_metrics += file_metrics
        self._total_quality += file_quality

        self._total_files += 1

        if self._progress is None:
            self._logger.info(os.path.split(out_file)[1] + " parse time: " + file_metrics.parse_time_str(file_metrics))

    def _on_dict_file(self, dict_file_path: str, args: list) -> None:
        """
        Callback method which is called for each dictionary file.

        :param dict_file_path:      Path to a .dict file.
        :param args:                Argument list.
        :return:                    None
        """
        self._total_metrics, self._total_quality = ParseMetrics(), ParseQuality()
        self._total_files = 0

        # start_time = time()
        dict_path = os.path.split(dict_file_path)[0]
        corp_path = args[DICT_ARG_CORP]
        dest_path = args[DICT_ARG_OUTP]

        dest_path += str(dict_path[len(args[DICT_ARG_DICT]):])

        # If BIT_LOC_LANG is set the language subdirectory is created in destination directory
        grmr_path = dest_path if self._options & BIT_LOC_LANG else self._grammar_root

        # Create new LG dictionary using .dict file and template directory with the rest of mandatory files.
        lang_path = dict_file_path if self._options & BIT_EXISTING_DICT else \
            create_grammar_dir(dict_file_path, grmr_path, self._template_dir, self._options)

        if os.path.isfile(corp_path):
            self._on_corpus_file(corp_path, [dest_path, lang_path] + args)

        elif os.path.isdir(corp_path):
            traverse_dir_tree(corp_path, "", [self._on_corpus_file, dest_path, lang_path] + args,
                                             [self._on_corp_dir, dest_path, lang_path] + args, True)

        # If output format is set to ULL
        if not (self._options & BIT_OUTPUT):
            stat_path = dest_path + "/" + os.path.split(corp_path)[1] + ".stat"  # + stat_suffix

            # Write statistics summary to a file
            self._save_stat(stat_path, self._total_metrics, self._total_quality)

            # Invoke on_statistics() event handler
            if self._is_dir_dict and self._event_handler is not None:

                self._event_handler.on_statistics((dict_path.split("/"))[::-1],
                                                  self._total_metrics, self._total_quality)

            if self._progress is None:
                self._logger.info(os.path.split(dict_file_path)[1] + " dictionary processing time: "
                      + self._total_metrics.parse_time_str(self._total_metrics))

        self._total_dicts += 1

    def test(self, dict_path: str, corpus_path: str, output_path: str, reference_path: str, options: int,
             progress: AbstractProgressClient = None, **kwargs) -> (ParseMetrics, ParseQuality):
        """
        Main method to initiate grammar test.

        :param dict_path:       Path to a dictionary file or directory.
        :param corpus_path:     Path to a corpus file or corpus root directory.
        :param output_path:     Output root path.
        :param reference_path:  Path to a reference file or reference root directory. In case of directory we assume
                                that it has the same internal structure with the same set of files in it as corpus
                                root directory.
        :param options:         Bitmask with parse options.
        :param progress:        Callback class reference derived from AbstractProgressClient to inform parse progress.
        :return:
        """
        self._options = options
        self._total_dicts = 0
        self._is_dir_corpus = os.path.isdir(corpus_path)
        self._is_dir_dict = os.path.isdir(dict_path)
        self._token_counts.clear()
        self._test_kwargs = kwargs

        if not (os.path.isfile(corpus_path) or os.path.isdir(corpus_path)):
            raise FileNotFoundError("Path '" + corpus_path + "' does not exist.")

        if not os.path.isdir(output_path):
            raise FileNotFoundError("Path '" + output_path + "' does not exist.")

        if reference_path is not None:
            if self._is_dir_corpus:
                if not os.path.isdir(reference_path):
                    raise GrammarTestError("If 'corpus_path' is a directory 'reference_path' "
                                           "should be an existing directory path too.")
            else:
                if not os.path.isfile(reference_path):
                    raise GrammarTestError("If 'corpus_path' is a file 'reference_path' should be an "
                                           "existing file path too.")

        # No need to duplicate subdirectory structure inside itself.
        if dict_path == output_path:
            self._options &= (~BIT_DPATH_CREATE)

        # Count total number of sentences across all corpus files
        self._total_sentences = get_corpus_sentence_count(corpus_path, self._options)

        # Either count or load token appearance data if min_word_count is specified
        if self._test_kwargs.get("min_word_count", 0) > 1:

            cnt_path = self._test_kwargs.get(CONF_WORD_CNT_PATH, None)

            self._token_counts = count_tokens(corpus_path, self._options) if cnt_path is None \
                else load_token_counts(cnt_path)

            # self._logger.debug(self._token_counts)
            self._test_kwargs["token_counts"] = self._token_counts

        # Create and set progress bar if it was not previously created
        if isclass(progress):
            bar = progress(total=self._total_sentences, desc="Overal execution", miniters=1)
            self._progress = bar

        # Set progress bar if it was passed as an instance reference
        elif progress is not None:
            self._progress = progress

        # Arguments for callback functions
        parse_args = [dict_path, corpus_path, output_path, reference_path]

        # If dict_path is a directory then call on_dict_file for every .dict file found.
        if self._is_dir_dict and not (self._options & BIT_EXISTING_DICT):
            dir_arg_list = [self._on_dict_dir]+parse_args if self._options & BIT_DPATH_CREATE else None

            traverse_dir_tree(dict_path, ("4.0.dict", "dict.db"), [self._on_dict_file]+parse_args, dir_arg_list, True)

        # Otherwise it can be either single .dict file name or name of LG preinstalled dictionary e.g. 'en'
        else:
            # If dict_path points to a single file no need to duplicate subdirectory structure
            if not self._is_dir_dict:
                self._options &= (~BIT_DPATH_CREATE)

            self._on_dict_file(dict_path, parse_args)

        if self._parser is not None:
            if progress is None:
                self._logger.info("\n\n")
            else:
                self._progress.write("\n\n")

        if not self._total_dicts:
            raise FileNotFoundError("No dictionary files found in '" + dict_path + "'")

        if self._progress is None:
            self._logger.info("Dictionaries processed: " + str(self._total_dicts))
            self._logger.info("Overal execution time: " + self._total_metrics.parse_time_str(self._total_metrics))

        return self._total_metrics, self._total_quality


def test_grammar(corpus_path: str, output_path: str, dict_path: str, grammar_path: str, template_path: str,
                       linkage_limit: int, options: int, reference_path: str, timeout: int=1, **kwargs) \
        -> (Decimal, Decimal, Decimal, Decimal):
    """
    Test grammar(s) over specified corpus providing numerical estimation of parsing quality.

    :param corpus_path:     Path to either corpus file or corpus directory.
    :param output_path:     Path to a directory where all output files to be stored.
    :param dict_path:       Path to either .dict file or to a directory with multiple .dict files.
    :param grammar_path:    Root path where grammar subdirectories are created.
    :param template_path:   Path to a grammar directory which is used as template when producing new grammar(s).
    :param linkage_limit:   Linkage limit variable for Link Grammar API/link-parser
    :param options:         Bit mask used as a single source of options.
    :param reference_path:  Path to either reference file or a directory with reference files which is used for parse
                            quality estimation.
    :param timeout:         Timeout value used by Link Grammar to restrict maximum amount of time spent for parsing
                            a single sentence.
    :return:                (parse-ability, F1, precision, recall)
    """
    # parser = LGInprocParser(linkage_limit) if options & BIT_LG_EXE else LGApiParser(linkage_limit)
    parser = LGInprocParser(linkage_limit, timeout)

    gt = GrammarTester(grammar_path, template_path, linkage_limit, parser)

    # bar = TextProgress(total=100)

    logger = logging.getLogger("test_grammar")

    logger.debug(kwargs)

    # pm, pq = gt.test(dict_path, corpus_path, output_path, reference_path, options, None)
    pm, pq = gt.test(dict_path, corpus_path, output_path, reference_path, options, TextProgress, **kwargs)

    return \
        pm.parseability(pm), \
        pq.f1(pq), \
        pq.precision_val(pq), \
        pq.recall_val(pq)

