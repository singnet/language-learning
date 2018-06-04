import os

from .absclient import AbstractGrammarTestClient, AbstractDashboardClient, AbstractFileParserClient
from .dirhelper import traverse_dir_tree, create_dir
from .parsemetrics import ParseMetrics
from .lgparse import get_dir_name, create_grammar_dir

# from grammartest import traverse_dir_tree, ParseMetrics, get_dir_name, create_grammar_dir, create_dir


class GrammarTestError(Exception):
    pass

# on_corpus_file() argument list indexes
CORP_ARG_DEST = 0
CORP_ARG_DICT = 1
CORP_ARG_CORP = 2
CORP_ARG_OUTP = 3
CORP_ARG_REFF = 4

# on_dict_file() argument list indexes
# [dict_path, corpus_path, output_path, reference_path]

DICT_ARG_DICT = 0                           # original dict_path
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
        self._total_metrics = ParseMetrics()
        self._total_files = 0

    def _on_dict_dir(self, dict_dir_path: str, args: list) -> bool:
        """
        Callback function that recreates internal directory structure of the dictionary folder
        within the destination root directory.

        :param dict_dir_path: Path to a directory in dictionary tree.
        :param args: List of arguments.
        :return: True if subdirectory in the destination path is successfully created, False otherwise.
        """
        return create_dir(args[DICT_ARG_OUTP] + dict_dir_path[len(args[DICT_ARG_DICT]):])

    def _on_corpus_file(self, corpus_file_path: str, args: list) -> None:
        """
        Callback method which is called for each corpus file in corpus root path.

        :param corpus_file_path: Path to a corpus file.
        :param args: List of arguments
        :return: None
        """
        dict_path = args[CORP_ARG_DICT]

        out_file = args[CORP_ARG_DEST] + corpus_file_path[len(args[CORP_ARG_CORP]):]
        ref_file = args[CORP_ARG_REFF] if self._is_dir_corpus == False else out_file + ".ull2"

        print([dict_path, corpus_file_path, out_file, self._linkage_limit, self._options, ref_file])

        try:
            self._total_metrics += self._parser.parse(dict_path, corpus_file_path, out_file, self._options)

        except Exception as err:
            print(str(err))

    def _on_dict_file(self, dict_file_path: str, args: list) -> None:
        """
        Callback method which is called for each dictionary file.

        :param dict_file_path: Path to a .dict file.
        :param args: Argument list.
        :return: None
        """
        # Extract grammar name from grammar file path
        _, grammar = get_dir_name(dict_file_path)

        # Create new dictionary using .dict file and template directory with the rest of mandatory files
        #   for LG dictionary
        dict_path = create_grammar_dir(dict_file_path, self._grammar_root, self._template_dir, self._options)

        # [dict_path, corpus_path, output_path, reference_path]

        corp_path = args[DICT_ARG_CORP]

        if os.path.isfile(corp_path):
            self._on_corpus_file(corp_path, [args[DICT_ARG_OUTP], dict_path] + args[1:])

        elif os.path.isdir(corp_path):
            dest_path = args[DICT_ARG_OUTP] + "/" + grammar

            if create_dir(dest_path):
                traverse_dir_tree(corp_path, "", [self._on_corpus_file, dest_path, dict_path] + args[1:], None, True)


    def test(self, dict_path: str, corpus_path: str, output_path: str, reference_path: str) -> ParseMetrics:
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
        self._is_dir_corpus = os.path.isdir(corpus_path)

        if not reference_path is None:
            if self._is_dir_corpus and not os.path.isdir(reference_path):
                raise GrammarTestError("GrammarTestError: If 'corpus_path' is a directory 'reference_path' should be an "
                                       "existing directory path too.")
            else:
                if not os.path.isfile(reference_path):
                    raise GrammarTestError("GrammarTestError: If 'corpus_path' is a file 'reference_path' should be an "
                                           "existing file path too.")

        self._total_metrics = ParseMetrics()
        self._total_files = 0

        try:
            # Arguments for callback functions
            parse_args = [dict_path, corpus_path, output_path, reference_path]

            # If dict_path is a file then simply call on_dict_file
            if os.path.isfile(dict_path):
                self._on_dict_file(dict_path, parse_args)

            # If dict_path is a directory then call on_dict_file for every .dict file found.
            elif os.path.isdir(dict_path):
                traverse_dir_tree(dict_path, ".dict", [self._on_dict_file]+parse_args,
                                  [self._on_dict_dir]+parse_args, True)

            if self._total_files > 1:
                self._total_metrics /= float(self._total_files)

        except GrammarTestError as err:
            raise GrammarTestError("GrammarTestError: " + str(err))

        except Exception as err:
            raise GrammarTestError("Exception: " + str(err))

        finally:
            return self._total_metrics




# def parse_file_with_api(dict_path: str, corpus_path: str, output_path: str, linkage_limit: int, options: int) \
#         -> ParseMetrics:



def parse_corpus(src_dir: str, dst_dir: str, dict_dir: str, grammar_dir: str, template_dir: str,
                       linkage_limit: int, options: int, reference_path: str) -> ParseMetrics:

    gt = GrammarTester(grammar_dir, template_dir, linkage_limit, options, None)

    return gt.test(dict_dir, src_dir, dst_dir, reference_path)


# parse_corpus(corp, dest, dict, grmr, tmpl, limit, opts, ref)
