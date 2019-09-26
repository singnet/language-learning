import sys
import os
import re
import logging
from subprocess import PIPE, Popen

from ..common.absclient import AbstractFileParserClient, AbstractProgressClient
from ..common.sentencecount import get_sentence_count
from ..common.sedcommands import get_sed_cmd_common_part
from ..common.tokencount import unbox_tokens
from .psparse import *
from .parsestat import *
from ..common.parsemetrics import *
from .lgmisc import *
from .parsevaluate import load_parses, tokenize_sentence, unbox_tokens, EvalError
from .lgpcommands import *
from .linkgrammarver import get_lg_version, get_lg_dict_version


__all__ = ['LGInprocParser']


class PSSentence:
    def __init__(self, sent_text):
        self.text = sent_text
        self.linkages = []
        self.valid = True

    def __str__(self):
        ret = self.text + "\n"

        for linkage in self.linkages:
            ret += linkage + "\n"

        return ret


class LGInprocParser(AbstractFileParserClient):

    MAX_SENTENCE_LENGTH = 99999

    def __init__(self, limit: int = 100, timeout=1, verbosity=1):
        self._logger = logging.getLogger("LGInprocParser")
        self._linkage_limit = limit
        self._timeout = timeout
        self._out_stream = None
        self._ref_stream = None
        self._counter = 0
        self._lg_version, self._lg_dict_path = get_lg_version()
        self._lg_verbosity = verbosity
        self._stop_tokens_set = None
        self._min_word_count = 0
        self._max_sentence_len = LGInprocParser.MAX_SENTENCE_LENGTH
        self._token_counts = None

    def _parse_batch_ps_output(self, text: str, options: int) -> list:
        """
        Parse postscript returned by link-parser executable in a form where each sentence is followed by zero
            or many postscript notated linkages. Postscript linkages are usually represented by three lines
            enclosed in brackets.

        :param text:        String variable with postscript output returned by link-parser.
        :param options:     Parsing options.
        :return:            List of PSSentence.

        """
        sentences = []

        pos = skip_command_response(text)
        end = trim_garbage(text)

        if pos > end:
            end = text.rfind("No complete linkages found.")

        validity_mask = (options & (BIT_EXCLUDE_TIMEOUTED | BIT_EXCLUDE_PANICED | BIT_EXCLUDE_EXPLOSION))

        prev_sent = None

        pattern = re.compile(r"\n\n[^\s]", re.M)

        # Parse output to get sentences and linkages in postscript notation
        for block in re.split(pattern, text[pos:end]):  # text[pos:end].split("\n\n"):

            block = block.strip()

            # Check if the LG output block contains only one parse
            parses = split_ps_parses(block)

            for sent in parses:

                # Get echoed sentence out of postscript output parse
                sentence = get_sentence_text(sent)

                # If sentence is not found in the output stream then check if the next bulk of text is another linkage
                #   of the same sentence. Otherwise exception is in order.
                lnk_data = get_linkage_cost(sent)

                # Get postscript starting position after parsing LG error and warning messages
                post_start, post_errors = skip_linkage_header(sent)

                # Check if the postscript linkage is valid
                is_valid = (not (post_errors & validity_mask)) and post_start > 0

                if is_valid and (sentence is None and lnk_data is None):
                    raise LGParseError(f"Neither sentence nor linkage were found in '{sent}'")

                # Check if it's a new sentence or just another linkage
                if sentence is not None:
                    # If the text block is a sentence then add another sentence to the sentence list.
                    #   The linkage will be added to the newly created sentence.
                    cur_sent = PSSentence(sentence)
                    cur_sent.valid = is_valid
                    sentences.append(cur_sent)

                else:
                    # If the text block is another linkage then it will be added to the previous sentence
                    cur_sent = prev_sent

                # Separate period with space if not already separated
                sentence = sentence[:-1] + " ." if sentence is not None and sentence[-1:] == r"." else sentence

                postscript = sent[post_start:].replace("\n", "") if is_valid \
                    else r"[([" + r"])([".join(sentence.split(" ")) + r"])][][0]"

                if cur_sent is None:
                    raise LGParseError(f"Empty list element for text block: {sent}")

                cur_sent.linkages.append(postscript)

                prev_sent = cur_sent

        return sentences

    def _check_token_counts(self, tokens: List[str]) -> bool:
        if self._token_counts is None:
            return True

        # The sentence is considered invalid if any of the sentence tokens appears less then 'min_word_count' times.
        for token in unbox_tokens(tokens):
            if not token.startswith(r"###") and self._token_counts.get(token, 0) < self._min_word_count:
                # self._logger.debug(f"{token}")
                return False

        return True

    def _handle_stream_output(self, text: str, options: int, out_stream, ref_path: str) -> (ParseMetrics, ParseQuality):
        """
        Handle link-parser output stream text depending on options' BIT_OUTPUT field.

        :param text:        Stream output text.
        :param options:     Integer variable with multiple bit fields.
        :param out_stream:  Output file stream handle.
        :param ref_path:    Reference file path.
        :return:            Tuple (ParseMetrics, ParseQuality)
        """
        total_metrics, total_quality = ParseMetrics(), ParseQuality()

        ref_parses = []

        # Parse only if 'ull' output format is specified.
        if not (options & BIT_OUTPUT):

            if options & BIT_PARSE_QUALITY and ref_path is not None:
                ref_parses = load_parses(ref_path)

            # Parse output into sentences and assotiate a list of linkages for each one of them.
            sentences = self._parse_batch_ps_output(text, options)

            if options & BIT_PARSE_QUALITY and ref_path is not None:
                len_ref, len_par = len(ref_parses), len(sentences)

                if len(ref_parses) != len(sentences):
                    string = "\n".join([sent.text for sent in sentences])
                    self._logger.debug(string)
                    raise LGParseError("Number of sentences in corpus and reference files missmatch. "
                                       "Reference file '{}' does not match "
                                       "its corpus counterpart {} != {}.".format(ref_path, len_ref, len_par))

            # Parse linkages and make statistics estimation
            for sentence_count, sent in enumerate(sentences):

                if not len(sent.linkages) or not sent.valid:
                    total_metrics.skipped_sentences += 1
                    continue

                # Parse postscript notated linkage and get two lists with tokens and links in return.
                tokens, links = parse_postscript(sent.linkages[0], options)

                if not len(tokens):
                    raise LGParseError(f"No tokens for sentence: '{sent.linkages[0].text}'")

                # Filter tokens to match parse options
                prepared = prepare_tokens(tokens, options)

                # Strip suffixes, convert to lower case and make a set out of token list
                lcased_token_set = set(prepared)
                # lcased_token_set = { strip_token(token.lower()) for token in tokens }

                # The sentence is skipped if one of the following is true:
                #   - stop token list is not empty and the sentence contains at least one of the stop tokens
                #   - sentence length exceeds 'max_sentence_len' value
                #   - one of the sentence tokens has count less then specified by 'min_word_count'
                if self._stop_tokens_set is not None and len(lcased_token_set & self._stop_tokens_set) or \
                        len(prepared) > self._max_sentence_len or not self._check_token_counts(prepared):

                    # Increment skipped sentence counter and continue with the next sentence
                    total_metrics.skipped_sentences += 1
                    continue

                # Print out links in ULL-format
                print_output(tokens, links, options, out_stream)

                # Calculate parse ability etc.
                total_metrics += parse_metrics(prepared)

                # Calculate parse quality if the option is set
                if (options & BIT_PARSE_QUALITY) and len(ref_parses):
                    ref_set = get_link_set(unbox_tokens(tokenize_sentence(ref_parses[sentence_count][0])),
                                           ref_parses[sentence_count][1], options)
                    total_quality += parse_quality(get_link_set(tokens, links, options), ref_set)

        # If output format is other than ull then simply write text to the output stream.
        else:
            print(text, file=out_stream)

        return total_metrics, total_quality

    def parse(self, dict_path: str, corpus_path: str, output_path: str, ref_file: str, options: int,
              progress: AbstractProgressClient = None, **kwargs) -> (ParseMetrics, ParseQuality):
        """
        Link parser invocation routine. Runs link-parser executable in a separate process.

        :param dict_path:       Name or path to the dictionary.
        :param corpus_path:     Path to the test text file.
        :param output_path:     Output file path.
        :param ref_file:        Reference file path.
        :param options:         Bit mask representing parsing options.
        :param progress:        Progress instance reference.
        :return:                Tuple (ParseMetrics, ParseQuality).
        """
        if progress is None:
            self._logger.info("Link Grammar version: {}\n"
                  "Link Grammar dictionaries: {}".format(self._lg_version, self._lg_dict_path))

        if not (options & BIT_EXISTING_DICT):
            dict_ver = get_lg_dict_version(dict_path)

            self._logger.debug(f"Dictionary version: {dict_ver}, link-parser version: {self._lg_version}")

            if dict_ver != "sql-dict" and dict_ver != "0.0.0" and (self._lg_version < "5.5.0" and dict_ver >= "5.5.0" or
                    self._lg_version >= "5.5.0" and dict_ver < "5.5.0"):
                raise LGParseError(f"Wrong dictionary version: {dict_ver}, expected: {self._lg_version}")

        # Issue #184 modifications
        stop_tokens = kwargs.get("stop_tokens", None)

        self._stop_tokens_set = set([token.strip() for token in stop_tokens.split(" ")]) if stop_tokens is not None \
            else None

        self._max_sentence_len = kwargs.get("max_sentence_len", LGInprocParser.MAX_SENTENCE_LENGTH)

        # Zero max_sentence_len means unlimited sentence length
        if not self._max_sentence_len:
            self._max_sentence_len = LGInprocParser.MAX_SENTENCE_LENGTH

        self._min_word_count = kwargs.get("min_word_count", 0)
        self._token_counts = kwargs.get("token_counts", None)

        sentence_count = 0

        bar = None

        if progress is None:
            self._logger.info(f"Parsing a corpus file: '{corpus_path}'")
            self._logger.info(f"Using dictionary: '{dict_path}'")

            if output_path is not None:
                self._logger.info(f"Parses are saved in: '{output_path}'")
            else:
                self._logger.info("Output file name is not specified. Parses are redirected to 'stdout'.")

            if ref_file is not None:
                self._logger.info(f"Reference file: '{ref_file}'")
            else:
                self._logger.info("Reference file name is not specified. Parse quality is not calculated.")

        sed_cmd = get_sed_cmd_common_part(options) + [corpus_path]

        out_stream = None
        ret_metrics = ParseMetrics()
        ret_quality = ParseQuality()

        raw_stream, err_stream = None, None

        try:
            # Get number of sentences in input file
            sentence_count = get_sentence_count(corpus_path, options)

            if progress is not None:
                progress_type = type(progress)
                bar = progress_type(total=sentence_count, desc=os.path.split(corpus_path)[1],
                                    unit="sentences", leave=True)
            else:
                self._logger.info(f"Number of sentences: {sentence_count}")

            lgp_cmd = get_linkparser_command(options, dict_path, self._linkage_limit, self._timeout, self._lg_verbosity)

            self._logger.debug(str(lgp_cmd))

            out_stream = sys.stdout if output_path is None \
                else open(output_path, "w", encoding="utf-8")

            with Popen(sed_cmd, stdout=PIPE) as proc_grep, \
                 Popen(lgp_cmd, stdin=proc_grep.stdout, stdout=PIPE, stderr=PIPE) as proc_pars:

                # Closing grep output stream will terminate it's process.
                proc_grep.stdout.close()

                # Read pipes to get complete output returned by link-parser
                raw_stream, err_stream = proc_pars.communicate()

                # Check return code to make sure the process completed successfully.
                if proc_pars.returncode != 0:
                    raise ParserError(f"Process '{lgp_cmd[0]}' terminated with exit code: {proc_pars.returncode} "
                                      f"and error message:\n'{err_stream.decode()}'.")

                # Take an action depending on the output format specified by 'options'
                ret_metrics, ret_quality = self._handle_stream_output(raw_stream.decode("utf-8-sig"), options,
                                                                      out_stream, ref_file)

                if progress is not None:
                    progress.update(sentence_count)

                if bar is not None:
                    bar.update(sentence_count)

                if not (options & BIT_OUTPUT) \
                        and ret_metrics.sentences + ret_metrics.skipped_sentences != sentence_count:

                    path_len = len(corpus_path)

                    raise LGParseError("Number of sentences does not match. "
                          "Read: {}, Parsed: {}, File: {}".format(sentence_count,
                                                                  ret_metrics.sentences + ret_metrics.skipped_sentences,
                                                                  corpus_path if path_len < 31
                                                                                else "..." + corpus_path[path_len-27:]))

        except LGParseError:
            self._logger.debug(err_stream.decode("utf-8-sig"))

            with open(output_path + ".raw", "w") as r:
                r.write(raw_stream.decode("utf-8-sig"))

            with open(output_path + ".err", "w") as e:
                e.write(err_stream.decode("utf-8-sig"))

            raise

        except EvalError as err:
            raise LGParseError(err)

        finally:
            if bar is not None:
                del bar

            if out_stream is not None and out_stream != sys.stdout:
                out_stream.close()

        return ret_metrics, ret_quality
