import sys
from subprocess import PIPE, Popen
from decimal import *

from .absclient import AbstractFileParserClient
from .optconst import *
from .psparse import *
from .parsestat import *
from .parsemetrics import *
from .lgmisc import *
from .evaluate import get_parses, load_ull_file, eval_parses

__all__ = ['LGInprocParser']


class PSSentence:
    def __init__(self, sent_text):
        self.text = sent_text
        self.linkages = []

    def __str__(self):
        ret = self.text + "\n"

        for linkage in self.linkages:
            ret += linkage + "\n"

        return ret


class LGInprocParser(AbstractFileParserClient):

    def __init__(self, limit: int=1000):
        self._linkage_limit = limit
        self._out_stream = None
        self._ref_stream = None
        self._counter = 0

    def _parse_batch_ps_output(self, text: str, lines_to_skip: int=4) -> list:
        """
        Parse postscript returned by link-parser executable in a form where each sentence is followed by zero
            or many postscript notated linkages. Postscript linkages are usually represented by three lines
            enclosed in brackets.
        :param text: String variable with postscript output returned by link-parser.
        :param lines_to_skip: Number of lines to skip before start parsing the text. It is necessary when additional
                    parameters specified, when link-parser is invoked. In that case link-parser writes those parameter
                    values on startup.
        """
        sentences = []

        pos = skip_lines(text, lines_to_skip)
        end = trim_garbage(text)

        sent_count = 0
        sent_set = set()

        # Parse output to get sentences and linkages in postscript notation
        for sent in text[pos:end].split("\n\n"):

            sent = sent.replace("\n", "")

            # As it turned out a sentence may start from '[', so simple `sent.find("[")` will fail to tell sentence from postscript.
            post_start = sent.find("[(")

            sentence = sent[:post_start]
            cur_sent = PSSentence(sentence)
            postscript = sent[post_start:]
            cur_sent.linkages.append(postscript)

            sentences.append(cur_sent)

            sent_set.add(cur_sent.text)
            sent_count += 1

        # assert len(sent_set) == sent_count, "Duplicate sentences!"
        if len(sent_set) != sent_count:
            print("Duplicate sentences found!")

        return sentences


    def _handle_stream_output(self, text: str, options: int, out_stream, ref_path: str):
        """
        Handle link-parser output stream text depending on options' BIT_OUTPUT field.

        :param text: Stream output text.
        :param linkage_limit: Number of linkages taken into account when statistics estimation is made.
        :param options: Integer variable with multiple bit fields
        :param out_stream: Output file stream handle.
        :return:
        """
        total_metrics, total_quality = ParseMetrics(), ParseQuality()

        ref_parses = []

        # Parse only if 'ull' output format is specified.
        if not (options & BIT_OUTPUT):

            if options & BIT_PARSE_QUALITY and ref_path is not None:
                try:
                    ref_parses = get_parses(load_ull_file(ref_path), options & BIT_NO_LWALL == BIT_NO_LWALL, False)
                    # print(ref_parses[3])

                except Exception as err:
                    print("Exception: " + str(err))

            # Parse output into sentences and assotiate a list of linkages for each one of them.
            sentences = self._parse_batch_ps_output(text)

            sentence_count = 0

            # Parse linkages and make statistics estimation
            for sent in sentences:
                linkage_count = 0

                sent_metrics, sent_quality = ParseMetrics(), ParseQuality()

                # Parse and calculate statistics for each linkage
                for lnkg in sent.linkages:

                    if linkage_count == 1:  # linkage_limit:
                        break

                    # Parse postscript notated linkage and get two lists with tokens and links in return.
                    tokens, links = parse_postscript(lnkg, options, out_stream)

                    # Print out links in ULL-format
                    print_output(tokens, links, options, out_stream)

                    # Calculate parseability statistics
                    sent_metrics += parse_metrics(prepare_tokens(tokens, options))

                    # Calculate parse quality if the option is set
                    if options & BIT_PARSE_QUALITY and len(ref_parses):
                        temp_quality = parse_quality(get_link_set(tokens, links, options),
                                                      ref_parses[sentence_count][1])

                        assert temp_quality.quality <= 1.0, "temp_quality.quality = " + str(temp_quality.quality)

                        sent_quality += temp_quality

                    linkage_count += 1

                assert sent_metrics.average_parsed_ratio <= 1.0, "sent_metrics.average_parsed_ratio > 1.0"
                assert sent_quality.quality <= 1.0, "sent_quality.quality > 1.0"

                total_metrics += sent_metrics
                total_quality += sent_quality

                sentence_count += 1

            total_metrics.sentences = sentence_count

            if sentence_count > 1:
                total_quality /= Decimal(sentence_count)

        # If output format is other than ull then simply write text to the output stream.
        else:
            print(text, file=out_stream)

        assert total_quality.quality <= 1.0, "total_quality.quality > 1.0"

        return total_metrics, total_quality


    def parse(self, dict_path: str, corpus_path: str, output_path: str, ref_file: str, options: int) \
            -> (ParseMetrics, ParseQuality):
        """
        Link parser invocation routine. Runs link-parser executable in a separate process.

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

        print("Info: Parsing a corpus file: '" + corpus_path + "'")
        print("Info: Using dictionary: '" + dict_path + "'")

        if output_path is not None:
            print("Info: Parses are saved in: '" + output_path+get_output_suffix(options) + "'")
        else:
            print("Info: Output file name is not specified. Parses are redirected to 'stdout'.")

        if ref_file is not None:
            print("Info: Reference file: '" + ref_file + "'")
        else:
            print("Info: Reference file name is not specified. Parse quality is not calculated.")

        reg_exp = "^\D.+$" if (options & BIT_ULL_IN) == BIT_ULL_IN else "^[^#].+$"

        # Make command option list depending on the output format specified.
        if not (options & BIT_OUTPUT) or (options & BIT_OUTPUT_POSTSCRIPT):
            cmd = ["link-parser", dict_path, "-echo=1", "-postscript=1", "-graphics=0", "-verbosity=0"]
        elif options & BIT_OUTPUT_CONST_TREE:
            cmd = ["link-parser", dict_path, "-echo=1", "-constituents=1", "-graphics=0", "-verbosity=0"]
        else:
            cmd = ["link-parser", dict_path, "-echo=1", "-graphics=1", "-verbosity=0"]

        out_stream = None
        ret_metrics = ParseMetrics()
        ret_quality = ParseQuality()

        try:
            out_stream = sys.stdout if output_path is None else open(output_path+get_output_suffix(options), "w")

            with Popen(["grep", "-P", reg_exp, corpus_path], stdout=PIPE) as proc_grep, \
                 Popen(cmd, stdin=proc_grep.stdout, stdout=PIPE, stderr=PIPE) as proc_pars:

                # Closing grep output stream will terminate it's process.
                proc_grep.stdout.close()

                # Read pipes to get complete output returned by link-parser
                raw, err = proc_pars.communicate()

                # Check return code to make sure the process completed successfully.
                if proc_pars.returncode:
                    LGParseError("Process '{0}' terminated with exit code: {1} "
                                 "and error message:\n'{2}'.".format(cmd[0], proc_pars.returncode, err.decode()))

                # with open("/home/alex/data2/parses/raw-output" + str(self._counter) + ".txt", "w") as f:
                #     f.write(raw.decode())
                #     self._counter += 1

                # Take an action depending on the output format specified by 'options'
                ret_metrics, ret_quality = self._handle_stream_output(raw.decode(), options, out_stream, ref_file)

        except LGParseError as err:
            print("LGParseError: " + str(err))

        except IOError as err:
            print("IOError: " + str(err))

        except FileNotFoundError as err:
            print("FileNotFoundError: " + str(err))

        except OSError as err:
            print("OSError: " + str(err))

        except Exception as err:
            print("Exception: " + str(err))

        finally:
            if out_stream is not None and out_stream != sys.stdout:
                out_stream.close()

            return ret_metrics, ret_quality
