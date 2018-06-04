#!/usr/bin/env python3

import sys
import os
import getopt
import platform

from grammartest import parse_corpus_files, LGParseError, handle_path_string, strip_quotes, LG_DICT_PATH
from grammartest.optconst import *

__version__ = "2.3.3"


def main(argv):
    """
Usage: grammar-test2.py -i <input_path> [-o <output_path> -d <dict_path>]  [OPTIONS]

    dict_path           Path to grammar definition file (or directory with multiple such files) to be tested.
                        The files should be in proper Link Grammar .dict format. Language short name such as 'en' or
                        'ru' may also be specified. If no '-d' option is specified English dictionary ('en') is used
                        by default.
    input_path          Input corpus file or directory path. In case of directory the script will traverse all
                        subdirectories, parsing each file in there and calculating statistics for the whole corpus.
    output_path         Output directory path to store parse text files in. sys.stdout is used if not specified.
                        The program stores parses as text files one output file per one input file in
                        <output_path>/<dict_name> directory keeping the same file name for the output file.
                        The output file format depends on '-f' option specified. ULL format used if ommited.
                        If directory path is specified as <input_path>, the whole subdirectory tree is recreated
                        inside <output_path>/<dict_name>/ where each output file corresponds to the same input one.

    OPTIONS:
        -h  --help              Print usage info.
        -c  --caps              Leave CAPS untouched.
        -w  --right-wall        Keep RIGHT-WALL tokens.
        -r  --rm-dir            Remove grammar directory if it already exists.
        -n  --no-strip          Do not strip token suffixes.
        -u  --ull-input         ULL links are used as input. This option should be specified to use only sentences
                                    and filter out link lines.
        -l  --linkage-limit     Maximum number of linkages Link Grammar may return when parsing a sentence.
                                Default is one linkage.
        -g  --grammar-dir       Directory path where newly created grammar should be stored.
        -t  --template-dir      LG grammar directory to be used as template when creating new grammars directories.
                                If short name such as 'ru' is used, default route LG path for specified grammar is used.
        -f  --output-format     Parse output format, can be "ull" (default), "diagram", "postscript", "constituent"
        -e  --link-parser-exe   Use link-parser executable called in a separate process instead of API calls.
                                It could be handy when LG API crashes while parsing some specific dictionary rules or
                                test corpus sentences.
        -x  --no-left-wall      Exclude LEFT-WALL and period from statistics estimation.
        -s  --separate-stat     Generate separate statistics for each input file.
        -R  --reference         Path to reference file if single file specified by option '-i' as input corpus or path
                                to a directory with a number of reference files. In later case files with the same names
                                are being compared.
    """

    dict_path       = None
    input_path      = None
    output_path     = None
    options         = 0x00000000 | BIT_STRIP | BIT_ULL_IN
    linkage_limit   = None
    grammar_path    = None
    template_path   = None
    reference_path  = None

    print("grammar-test2.py ver." + __version__)
    print("Python v." + platform.python_version())

    try:
        opts, args = getopt.getopt(argv, "hcwrnubqexsLd:i:o:l:g:t:f:R:", ["help", "caps", "right-wall", "rm-dir",
                                                                        "no-strip", "ull-input", "best-linkage",
                                                                        "dict-path-recreate", "link-parser-exe",
                                                                        "no-left-wall", "separate-stat",
                                                                        "local-lang-dir", "dictionary=", "input=",
                                                                        "output=", "linkage-limit=", "grammar-dir=",
                                                                        "template-dir=", "output-format", "reference"])

        for opt, arg in opts:
            if opt in ("-h", "--help"):
                print(main.__doc__)
                return 0
            elif opt in ("-c", "--caps"):
                options |= BIT_CAPS
            elif opt in ("-w", "--right-wall"):
                options |= BIT_RWALL
            elif opt in ("-r", "--rm-dir"):
                options |= BIT_RM_DIR
            elif opt in ("-n", "--no-strip"):
                options &= (~BIT_STRIP)
            elif opt in ("-b", "--best-linkage"):
                options |= BIT_BEST_LINKAGE
            elif opt in ("-q", "--dict-path-recreate"):
                options |= BIT_DPATH_CREATE
            elif opt in ("-u", "--ull-input"):
                options |= BIT_ULL_IN
            elif opt in ("-e", "--link-parser-exe"):
                options |= BIT_LG_EXE
            elif opt in ("-x", "--no-left-wall"):
                options |= BIT_NO_LWALL
            elif opt in ("-s", "--separate-stat"):
                options |= BIT_SEP_STAT
            elif opt in ("-L", "--local-lang-dir"):
                options |= BIT_LOC_LANG
            elif opt in ("-d", "--dictionary"):
                dict_path = handle_path_string(arg)
            elif opt in ("-i", "--input"):
                input_path = handle_path_string(arg)
            elif opt in ("-o", "--output"):
                output_path = handle_path_string(arg)
            elif opt in ("-l", "--linkage-limit"):
                linkage_limit = int(arg)
            elif opt in ("-g", "--grammar-dir"):
                grammar_path = handle_path_string(arg)
            elif opt in ("-t", "--template-dir"):
                template_path = handle_path_string(arg)
            elif opt in ("-f", "--output-format"):
                form = strip_quotes(arg).lower()
                if form == "diagram":
                    options |= BIT_OUTPUT_DIAGRAM
                elif form == "postscript":
                    options |= BIT_OUTPUT_POSTSCRIPT
                elif form == "constituent":
                    options |= BIT_OUTPUT_CONST_TREE
            elif opt in ("-R", "--reference"):
                reference_path = handle_path_string(arg)

        # print("options=" + bin(options) + " (" + hex(options) + ")")

    except getopt.GetoptError:
        print(main.__doc__)
        return 1

    if input_path is None:
        print("Error: Input file path is not specified.")
        print(main.__doc__)
        return 1

    if linkage_limit is None:
        linkage_limit = 1

    if template_path is None:
        template_path = "en"

    if grammar_path is None:
        grammar_path = LG_DICT_PATH

    if output_path is None:
        output_path = os.environ['PWD']

    if dict_path is None:
        dict_path = "en"

    # if reference_path is None:
    #     reference_path

    try:
        parse_corpus_files(input_path, output_path, dict_path, grammar_path, template_path,
                           linkage_limit, options, reference_path)

    except LGParseError as err:
        print(str(err))
        return 2

    except OSError as err:
        print(str(err))
        return 3

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
