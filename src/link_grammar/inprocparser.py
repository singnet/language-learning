import sys
from subprocess import PIPE, Popen

from grammar_test.optconst import *
from grammar_test.psparse import *
from grammar_test.parsestat import *
from common.parsemetrics import *
from grammar_test.lgmisc import *

__all__ = ['parse_file_with_lgp']


class PSSentence:
    def __init__(self, sent_text):
        self.text = sent_text
        self.linkages = []

    def __str__(self):
        ret = self.text + "\n"

        for linkage in self.linkages:
            ret += linkage + "\n"

        return ret


def skip_lines(text: str, lines_to_skip: int) -> int:
    """
     Skip specified number of lines from the beginning of a text string.

    :param text: Text string with zero or many '\n' in.
    :param lines_to_skip: Number of lines to skip.
    :return: Return position of the first character after the specified number of lines is skipped.
    """
    l = len(text)

    pos = 0
    cnt = lines_to_skip

    while l and cnt:
        if text[pos] == "\n":
            cnt -= 1
        pos += 1
    return pos


def trim_garbage(text: str) -> int:
    """
    Strip all characters from the end of string until ']' is reached.

    :param text: Text string.
    :return: Return position of a character following ']' or zero in case of a null string.
    """
    l = len(text)-1

    while l:
        if text[l] == "]":
            return l+1
        l -= 1

    return 0


def parse_batch_ps_output(text: str, lines_to_skip: int=5) -> list:
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

#--------------------------------------
    # print(text[pos:end])
# --------------------------------------

    # Parse output to get sentences and linkages in postscript notation
    for sent in text[pos:end].split("\n\n"):

        sent = sent.replace("\n", "")

        post_start = sent.find("[")

        sentence = sent[:post_start]
        cur_sent = PSSentence(sentence)
        postscript = sent[post_start:]
        cur_sent.linkages.append(postscript)

        sentences.append(cur_sent)

    return sentences


def handle_stream_output0(text: str, linkage_limit: int, options: int, out_stream):
    """
    Handle link-parser output stream text depending on options' BIT_OUTPUT field.

    :param text: Stream output text.
    :param linkage_limit: Number of linkages taken into account when statistics estimation is made.
    :param options: Integer variable with multiple bit fields
    :param out_stream: Output file stream handle.
    :return:
    """
    total_full_ratio, total_none_ratio, total_avrg_ratio = (0.0, 0.0, 0.0)

    # Parse only if 'ull' output format is specified.
    if not (options & BIT_OUTPUT):

        # Parse output into sentences and assotiate a list of linkages for each one of them.
        sentences = parse_batch_ps_output(text)

        sentence_count = 0

        # Parse linkages and make statistics estimation
        for sent in sentences:
            linkage_count = 0

            sent_full_ratio, sent_none_ratio, sent_avrg_ratio = (0.0, 0.0, 0.0)

            # Parse and calculate statistics for each linkage
            for lnkg in sent.linkages:

                if linkage_count == 1:  # linkage_limit:
                    break

                tokens, links = parse_postscript(lnkg, options, out_stream)

                if not (options & BIT_OUTPUT):
                    print_output(tokens, links, options, out_stream)

                (f, n, a) = calc_stat(tokens)

                assert(a <= 1.0)

                sent_full_ratio += f
                sent_none_ratio += n
                sent_avrg_ratio += a

                linkage_count += 1

            if linkage_count > 1:
                sent_full_ratio /= float(linkage_count)
                sent_none_ratio /= float(linkage_count)
                sent_avrg_ratio /= float(linkage_count)

            total_full_ratio += sent_full_ratio
            total_none_ratio += sent_none_ratio
            total_avrg_ratio += sent_avrg_ratio

            sentence_count += 1

        if sentence_count > 1:
            total_full_ratio /= float(sentence_count)
            total_none_ratio /= float(sentence_count)
            total_avrg_ratio /= float(sentence_count)

            assert total_avrg_ratio <= 1.0

    # If output format is other than ull then simply write text to the output stream.
    else:
        print(text, file=out_stream)

    return (total_full_ratio, total_none_ratio, total_avrg_ratio)


def handle_stream_output(text: str, linkage_limit: int, options: int, out_stream):
    """
    Handle link-parser output stream text depending on options' BIT_OUTPUT field.

    :param text: Stream output text.
    :param linkage_limit: Number of linkages taken into account when statistics estimation is made.
    :param options: Integer variable with multiple bit fields
    :param out_stream: Output file stream handle.
    :return:
    """
    total_metrics = ParseMetrics()

    # Parse only if 'ull' output format is specified.
    if not (options & BIT_OUTPUT):

        print("************************* ULL start***********************************")

        # Parse output into sentences and assotiate a list of linkages for each one of them.
        sentences = parse_batch_ps_output(text)

        sentence_count = 0

        # Parse linkages and make statistics estimation
        for sent in sentences:
            linkage_count = 0

            # ********************************************************************************
            print(sent.text, sent.linkages)
            # ********************************************************************************

            sent_metrics = ParseMetrics()

            # Parse and calculate statistics for each linkage
            for lnkg in sent.linkages:

                if linkage_count == 1:  # linkage_limit:
                    break

                # Parse postscript notated linkage and get two lists with tokens and links in return.
                tokens, links = parse_postscript(lnkg, options, out_stream)

                # Print out links in ULL-format
                print_output(tokens, links, options, out_stream)

                # Calculate parseability statistics
                sent_metrics += parse_metrics(tokens)

                assert(sent_metrics.average_parsed_ratio <= 1.0)

                linkage_count += 1

            if linkage_count > 1:
                sent_metrics /= float(linkage_count)

            total_metrics += sent_metrics

            sentence_count += 1

        if sentence_count > 1:
            total_metrics /= float(sentence_count)

            assert total_metrics.average_parsed_ratio <= 1.0

        print("************************* ULL end ***********************************")

    # If output format is other than ull then simply write text to the output stream.
    else:
        print(text, file=out_stream)

    return total_metrics


def parse_file_with_lgp(dict_path: str, corpus_path: str, output_path: str, linkage_limit: int, options: int) \
        -> ParseMetrics:
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

            # Take an action depending on the output format specified by 'options'
            ret_metrics += handle_stream_output(raw.decode(), linkage_limit, options, out_stream)

    except LGParseError as err:
        print(str(err))

    except IOError as err:
        print(str(err))

    except FileNotFoundError as err:
        print(str(err))

    except OSError as err:
        print("OSError: " + str(err))

    except Exception as err:
        print("Exception: " + str(err))

    finally:
        if out_stream is not None and out_stream != sys.stdout:
            out_stream.close()

        return ret_metrics


def parse_file_with_lgp0(dict_path, corpus_path, output_path, linkage_limit, options) \
        -> (float, float, float):
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
    :return: tuple (float, float, float):
                - percentage of totally parsed sentences;
                - percentage of completely unparsed sentences;
                - percentage of parsed sentences;
    """

    print("Info: Parsing a corpus file: '" + corpus_path + "'")
    print("Info: Using dictionary: '" + dict_path + "'")

    if output_path is not None:
        print("Info: Parses are saved in: '" + output_path+get_output_suffix(options) + "'")
    else:
        print("Info: Output file name is not specified. Parses are redirected to 'stdout'.")

    # Statistics return value initialization
    ret_tup = (0.0, 0.0, 0.0)

    reg_exp = "^\D.+$" if (options & BIT_ULL_IN) == BIT_ULL_IN else "^[^#].+$"

    # Make command option list depending on the output format specified.
    if not (options & BIT_OUTPUT) or (options & BIT_OUTPUT_POSTSCRIPT):
        cmd = ["link-parser", dict_path, "-echo=1", "-postscript=1", "-graphics=0", "-verbosity=0"]
    elif options & BIT_OUTPUT_CONST_TREE:
        cmd = ["link-parser", dict_path, "-echo=1", "-constituents=1", "-graphics=0", "-verbosity=0"]
    else:
        cmd = ["link-parser", dict_path, "-echo=1", "-graphics=1", "-verbosity=0"]

    out_stream = None

    try:
        out_stream = sys.stdout if output_path is None else open(output_path+get_output_suffix(options), "w")

        with Popen(["grep", "-P", reg_exp, corpus_path], stdout=PIPE) as proc_grep, \
             Popen(cmd, stdin=proc_grep.stdout, stdout=PIPE) as proc_pars:

            # Closing grep output stream will terminate it's process.
            proc_grep.stdout.close()

            # Read pipe to get complete output returned by link-parser
            text = proc_pars.communicate()[0].decode()

            # Take an action depending on the output format specified by 'options'
            ret_tup = handle_stream_output0(text, linkage_limit, options, out_stream)

    except IOError as err:
        print(str(err))

    except FileNotFoundError as err:
        print(str(err))

    except OSError as err:
        print("OSError: " + str(err))

    except Exception as err:
        print("Exception: " + str(err))

    finally:
        if out_stream is not None and out_stream != sys.stdout:
            out_stream.close()

        return ret_tup
