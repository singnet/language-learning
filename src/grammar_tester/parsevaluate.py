import os
import sys
import random
import logging
import traceback

from typing import Tuple, List, Union, Callable

from ..common.absclient import AbstractProgressClient, AbstractFileParserClient
from ..common.dirhelper import traverse_dir_tree
from ..common.parsemetrics import ParseQuality, ParseMetrics
from ..common.optconst import *
from ..common.absclient import AbstractPipelineComponent
from ..common.cliutils import handle_path_string
from ..common.tokencount import unbox_tokens
from .parsestat import parse_quality
from .psparse import parse_postscript, get_link_set, prepare_tokens
from .lgmisc import print_output, get_output_suffix
from linkgrammar import ParseOptions, Dictionary, Sentence, Linkage


__all__ = ['load_parses', 'eval_parses', 'compare_ull_files', 'EvalError',
           'make_random', 'make_sequential', 'save_parses', 'tokenize_sentence', 'extract_parses']


PARSE_SENTENCE = 0
PARSE_LINK_SET = 1
PARSE_IGNORED = 2

logger = logging.getLogger(__name__)


class SentenceError(Exception):
    pass


class EvalError(Exception):

    def __init__(self, msg: str, file: str):
        super().__init__(msg)
        self._msg = msg
        self._file = file

    def __str__(self):
        return f"{self._file}: {self._msg}"


def extract_parses(data) -> List[Tuple[str, set]]:
    """
        Separates parses from data into format:
        [
            [ <sentence>, <set-of-link-tuples> ]
            ...
        ]
        <sentence> - text string
        <set-of-link-tuples> - set of tuples, where each tuple has two token indexes

        Each list is splitted into tokens using space.
    """
    parses: List[Tuple[str, set]] = []

    parse_index: int = 0            # index of the newly created parse
    line_index: int = 0             # file line index

    for bulk in data.split("\n\n"):

        if not len(bulk):
            continue

        line_count = line_index

        for line_index, line in enumerate(bulk.split("\n"), line_index):

            if line_index == line_count:
                parses.append(((line.replace("\n", "")).strip(), set()))
                continue

            if len(line):
                link = line.split()

                if len(link) not in [4, 5]:
                    raise SentenceError(f"Line #{line_index + 1} appears not to be a link: '{line}'")

                # Only token indexes are added to the set
                parses[parse_index][PARSE_LINK_SET].add((int(link[0]), int(link[2])))

        line_index += 2
        parse_index += 1

    return parses


def load_parses(file_name: str) -> List[Tuple[str, set]]:

    with open(file_name, "r", encoding="utf-8-sig") as file:
        data = file.read()

    try:
        parses = extract_parses(data)

    except SentenceError as err:
        raise EvalError(str(err), file_name)

    return parses


def save_parses(sentence_parses: List[Tuple[str, set]], file_name: str, options: int) -> None:
    """
    Print parses to file (for sequential and random eval methods)

    :param sentence_parses:     Parse info structure.
    :param file_name:           Path to file to save parses to.
    :param options:             Parse options bit mask.
    :return:                    None.
    """
    print("writing parses file to '{}'".format(file_name))

    with open(file_name, 'w') as fo:
        for sent in sentence_parses:
            print_output(["###LEFT-WALL###"] + (sent[0].strip()).split(), list(sent[1]), options, fo)

    print("Finished writing parses file")


def make_sequential(sentences: Union[List[Tuple[str, set]],List[str]], options: int, **kwargs) -> List[Tuple[str, set]]:
    """
    Make sequential parses (each word simply linked to the next one),
    to be used as baseline

    :param sentences:       List of either tuples of sentence and set of links in case of .ull input file format
                            or strings in case of text input file format.
    :param options:         Integer representing parse options bit masks.
    :return:                List of parses (tuples of sentence and set of links)
    """
    sequential_parses = []

    is_ull = True if isinstance(sentences, list) and isinstance(sentences[0], tuple) else \
        False if isinstance(sentences, list) and isinstance(sentences[0], str) else None

    if is_ull is None:
        raise ValueError(f"The first argument should be either List[Tuple[str, set] or List[str], "
                         f"but it is {sentences.__class__.__name__.capitalize()}"
                         f"[{sentences[0].__class__.__name__.capitalize()}]")

    for sp in sentences:
        sentence = sp[0] if is_ull else sp
        links = {(0, 1)}

        for i in range(1, len(sentence.split())):
            links.add((i, i + 1))

        sequential_parses.append((sentence.strip(), links))

    return sequential_parses


def make_random(sentences: Union[List[Tuple[str, set]],List[str]], options: int, **kwargs) -> List[Tuple[str, set]]:
    """
    Make random parses (from LG-parser "any"), to use as baseline

    :param sentences:       List of either tuples of sentence and set of links in case of .ull input file format
                            or strings in case of text input file format.
    :param options:         Integer representing parse options bit masks.
    :return:                List of parses (tuples of sentence and set of links)
    """
    any_dict = Dictionary('any') # Opens dictionary only once
    po = ParseOptions(min_null_count=0, max_null_count=999)
    po.linkage_limit = int(kwargs.get("limit", 100))
    options |= BIT_STRIP
    options |= BIT_CAPS

    if isinstance(sentences[0], tuple):
        is_ull = True
    elif isinstance(sentences[0], str):
        is_ull = False
    else:
        raise ValueError("The first argument should be either List[Tuple[str, set] or List[str].")

    random_parses = []

    for sent in sentences:
        words = tokenize_sentence(sent[0] if is_ull else sent)
        num_words = len(words)

        # substitute words with numbers, to avoid token-splitting by LG "any"
        fake_words = [f"w{x}" for x in range(1, num_words)]
        # fake_words = [f"w{x}" for x in range(1, num_words + 1)]
        sent_string = " ".join(fake_words)
        sentence = Sentence(sent_string, any_dict, po)
        linkages = sentence.parse()
        num_parses = len(linkages)                          # check nbr of linkages in sentence

        links = []

        if num_parses > 0:
            idx = random.randint(0, num_parses - 1)         # choose a random linkage index
            linkage = Linkage(idx, sentence, po._obj)       # get the random linkage
            tokens, links = parse_postscript(linkage.postscript().replace("\n", ""), options)

            if num_words != len(tokens):
                logger.error(f"Number of tokens mismatch:\n{words}\n{tokens}\nfor sentence:\n{sent[0]}")

        random_parses.append((sent[0], set(links)))

    return random_parses


def tokenize_sentence(sentence: str) -> List[str]:
    """
    Split sentence into tokens by spaces.

    :param sentence:        Sentence string.
    :return:                List of tokens.
    """
    tokens = sentence.split()

    return ["###LEFT-WALL###"] + tokens if tokens[0] != r"###LEFT-WALL###" else tokens


def eval_parses(test_parses: list, ref_parses: list, options: int) \
        -> (ParseQuality, str, list):
    """
        Compares test_parses against ref_parses link by link
        counting errors

    :param test_parses:     List of test parses in format, prepared by get_parses.
    :param ref_parses:      List of reference parses.
    :param options:         Compare options.
    :return:                ParseQuality class instance filled with the result data.
    """
    total_parse_quality = ParseQuality()

    if len(ref_parses) != len(test_parses):
        raise SentenceError("Number of sentences missmatch. Ref={len(ref_parses}, Test={len(test_parses)}")

    logger.info("\nTest Set\tReference Set\tIntersection\tRecall\tPrecision\tF1")
    logger.info("-" * 75)

    tokenization_discrepancies = ""
    accepted_parses = []

    for ref_parse, test_parse in zip(ref_parses, test_parses):

        # Tokenize sentences
        ref_raw_tokens = tokenize_sentence(ref_parse[PARSE_SENTENCE])
        test_raw_tokens = tokenize_sentence(test_parse[PARSE_SENTENCE])

        # Sentences with original case but having only one space as a separator
        ref_as_is, test_as_is = " ".join(unbox_tokens(ref_raw_tokens[1:])), " ".join(unbox_tokens(test_raw_tokens[1:]))

        # Lowercase sentences
        ref_lcase, test_lcase = ref_as_is.lower(), test_as_is.lower()

        # Lowercase sentences without spaces to ignore tokenization
        ref_merged, test_merged = ref_lcase.replace(" ", ""), test_lcase.replace(" ", "")

        # Check if two sentences are the same in terms of meaning
        if ref_merged != test_merged:
            if (options & BIT_IGNORE_SENT_MISMATCH):
                logger.warning(f"Sentences mismatch:\n{ref_as_is}\n{test_as_is}")
            else:
                raise SentenceError(f"Sentences mismatch:\n{ref_as_is}\n{test_as_is}")

        # Check if two sentences are having all word letters in the same case
        if ref_as_is != test_as_is:
            logger.warning(f"Sentences differ in letter cases:\n{ref_as_is}\n{test_as_is}")

        # Make up token sets according to specified options
        test_token_set = set(prepare_tokens(unbox_tokens(test_raw_tokens), options))
        ref_token_set = set(prepare_tokens(unbox_tokens(ref_raw_tokens), options))

        # Make up link sets according to specified options
        test_set = get_link_set(test_raw_tokens, test_parse[PARSE_LINK_SET], options)
        ref_set = get_link_set(ref_raw_tokens, ref_parse[PARSE_LINK_SET], options)

        # Check if two sentences are having the same tokenization
        if ref_lcase != test_lcase:
            warning = f"Sentence appear to have different tokenization:\n{ref_lcase}\n" \
                f"in tokens:{sorted(list(ref_token_set - test_token_set))}" \
                f"<--->{sorted(list(test_token_set - ref_token_set))}\n"

            if (options & BIT_STRICT_TOKENIZATION):
                raise SentenceError(warning)

            tokenization_discrepancies += warning

        # Filter sentences containing direct speech (any sentetence with double quotes) if the flag is set
        if (options & BIT_FILTER_DIR_SPEECH) and (ref_as_is.count('"') or len(ref_set) < 1
                                                  or ref_lcase != test_lcase):
            total_parse_quality.skipped_sentences += 1
            continue

        # Make up another list with accepted parses to be stored in file
        accepted_parses.append(test_parse)
        # accepted_parses.append(ref_parse)

        pq = parse_quality(test_set, ref_set)

        pq.ignored = (len(test_parse[PARSE_LINK_SET]) - len(test_set))

        logger.info(f"{test_parse[0]}")
        logger.info("{} {} {} {} {} {}".format(test_set, ref_set, test_set & ref_set,
              ParseQuality.recall_str(pq), ParseQuality.precision_str(pq), ParseQuality.f1_str(pq)))

        total_parse_quality += pq

    return total_parse_quality, tokenization_discrepancies, accepted_parses


def compare_ull_files(test_path, ref_path, options: int, **kwargs) -> ParseQuality:
    """
    Initiate evaluation process for one or multiple files.

    :param test_path:       Path to file(s) to be tested.
    :param ref_path:        Path to reference file(s).
    :param options:         Bit mask integer representing options.
    :return:                ParseQuality class instance holding parse quality results for the whole corpus
                            (all files if test_path is a directory name).
    """
    total_parse_quality = ParseQuality()
    total_file_count = 0

    stat_file = f"{kwargs.get('output_path', os.environ['PWD'])}/{os.path.split(handle_path_string(test_path))[1]}.stat"

    parser_type = kwargs.get("parser_type", "link-grammar-exe")

    # Dictionary with function reference and argument index tuples
    parsers = {"sequential": (make_sequential, 1), "random": (make_random, 1)}

    # Actual function and argument index
    operation, arg_index = parsers.get(parser_type, (None, None))

    is_multifile = os.path.isdir(test_path)

    logger.debug(f"is_multifile={is_multifile}")

    def save_parse_quality(pq: ParseQuality, file_path: str) -> None:

        with open(file_path, "w") as ofile:
            print(ParseQuality.text(pq), file=ofile)

    def save_tokenization_discrepancies(discr: str, file_path: str) -> None:

        with open(file_path, "w") as ofile:
            print(discr, file=ofile)

    def evaluate(test_file: str, args: list = None) -> None:
        """
        Evaluation function

        :param test_file:       Path to a test file.
        :param args             Additional argument list.
        :return:                None.
        """
        nonlocal total_parse_quality
        nonlocal total_file_count

        file_name = os.path.split(test_file)[1]

        logger.debug(f"file_name = {file_name}")

        dest_path = kwargs.get("output_path", os.environ["PWD"])
        stat_file = f"{dest_path}/{file_name}.stat"
        flt_file  = f"{dest_path}/{file_name}.flt"
        diff_file = f"{dest_path}/{file_name}.diff"

        suff = get_output_suffix(options)
        ull_file  = f"{dest_path}/{file_name}{'' if file_name.endswith(suff) else suff}"

        # 'ref_path' should point to reference file if corpus is a single file,
        # path to reference corpus directory otherwise. In later case name of each reference file must exactly match
        # the name of the corresponding corpus file.
        ref_file = f"{ref_path}/{file_name}" if is_multifile else ref_path

        logger.info("\nComparing parses:")
        logger.info("-----------------")
        logger.info(f"File being tested: '{test_file}'")
        logger.info(f"Reference file   : '{ref_file}'")
        logger.info(f"Result file      : '{stat_file}'")

        try:
            ref_parses = load_parses(ref_file)

            # Load parse file if simple evaluation is expected.
            if operation is None:
                test_parses = load_parses(test_file)

            # Perform parsing and saving if random or sequential parses are expected.
            else:
                test_parses = operation(ref_parses, options)
                save_parses(test_parses, ull_file, options)

            # Here comes parse evaluation
            file_quality, tok_discr, accepted = eval_parses(test_parses, ref_parses, options)

            if is_multifile and (options & BIT_SEP_STAT):
                save_parse_quality(file_quality, stat_file)

            if len(tok_discr):
                save_tokenization_discrepancies(tok_discr, diff_file)
                logger.warning(f"Tokenization discrepancies found. Check '{diff_file}' for details.")

            total_parse_quality += file_quality
            total_file_count += 1

            # Save accepted parses if filter is activated
            if (options & BIT_FILTER_DIR_SPEECH) and len(accepted):
                save_parses(accepted, flt_file, options)

        except SentenceError as err:
            raise EvalError(str(err), file_name)

    if not (os.path.isfile(test_path) or os.path.isdir(test_path)):
        raise FileNotFoundError("Path '" + test_path + "' does not exist.")

    if ref_path is None:
        raise ValueError("Reference corpus is not specified")

    output_path = kwargs.get("output_path", os.environ["PWD"])

    if output_path is None or not os.path.isdir(output_path):
        raise FileNotFoundError(f"Path '{output_path}' does not exist.")

    # If corpus is a directory with multiple files
    if os.path.isdir(test_path):
        if not os.path.isdir(ref_path):
            raise ValueError("If 'corpus_path' is a directory 'reference_path' "
                             "should be an existing directory path too.")

        # Evaluate each file of the corpus and summarize statistics
        traverse_dir_tree(test_path, ".ull", [evaluate], None, True)

    # If corpus is a single file
    else:
        if not os.path.isfile(ref_path):
            raise ValueError("If 'corpus_path' is a file 'reference_path' should be an "
                             "existing file path too.")

        # Evaluate a single file
        evaluate(test_path)

    # Save corpus statistics to a file
    save_parse_quality(total_parse_quality, stat_file)

    logger.info("\n" + total_parse_quality.text(total_parse_quality))

    return total_parse_quality


PARAM_TST_PATH = 'input_path'
PARAM_REF_PATH = 'ref_path'
PARAM_OUT_PATH = 'output_path'


class ParseEvaluatorComponent(AbstractPipelineComponent):
    """
    ParseEvaluatorComponent is responsible for comparing two corpora and calculate parse quality statistics.

    """
    def __init__(self, **kwargs):
        pass

    def validate_parameters(self, **kwargs):
        """ Validate configuration parameters """
        ret_val = True

        if kwargs.get(PARAM_TST_PATH, None) is None:
            print("Error: parameter '{}' is not specified.".format(PARAM_TST_PATH))
            ret_val = False

        if kwargs.get(PARAM_REF_PATH, None) is None:
            print("Error: parameter '{}' is not specified.".format(PARAM_REF_PATH))
            ret_val = False

        if kwargs.get(PARAM_OUT_PATH, None) is None:
            print("Error: parameter '{}' is not specified.".format(PARAM_OUT_PATH))
            ret_val = False

        return ret_val

    def run(self, **kwargs):
        """ Execute component code """

        options = (get_options(kwargs) | BIT_ULL_IN)

        input_path = kwargs.get(PARAM_TST_PATH, None)

        if input_path:
            input_path = handle_path_string(input_path)

        ref_path = kwargs.get(PARAM_REF_PATH, None)

        if ref_path:
            ref_path = handle_path_string(ref_path)

        output_path = kwargs.get(PARAM_OUT_PATH, None)

        if output_path:
            output_path = handle_path_string(output_path)

        pq = compare_ull_files(input_path, ref_path, options, output_path=output_path)

        return {"F1": pq.f1_str(pq), "recall": pq.recall_str(pq), "precision": pq.precision_str(pq)}

