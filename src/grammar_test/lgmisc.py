import re
import os
import shutil

from .optconst import *

__all__ = ['get_output_suffix', 'print_output', 'LGParseError', 'LG_DICT_PATH', 'create_grammar_dir', 'get_dir_name']


LG_DICT_PATH = "/usr/local/share/link-grammar"

LINK_1ST_TOKEN_INDEX = 0
LINK_2ND_TOKEN_INDEX = 1


class LGParseError(Exception):
    pass


def get_dir_name(file_name: str) -> (str, str):
    """
    Extract template grammar directory name and a name for new grammar directory

    :param file_name: Grammar file name. It should have the following notation:

                '<grammar-name>_<N>C_<yyyy-MM-dd>_<hhhh>.4.0.dict' (e.g. poc-turtle_8C_2018-03-03_0A10.4.0.dict)

                          grammar-name      Name of the language the grammar file was created for
                          N                 Number of clusters used while creating the grammar followed by literal 'C'.
                          yyyy-MM-dd        Dash delimited date, where yyyy - year (e.g. 2018), MM - month,
                                            dd - day of month.
                          hhhh              Hexadecimal sequential number.

                          4.0.dict suffix is mandatory for any grammar definition file and should not be ommited.

    :return: tuple (template_grammar_directory_name, grammar_directory_name)
    """
    p = re.compile(
        '(/?([+._:\w\d=~-]*/)*)(([a-zA-Z-]+)_[0-9]{1,3}C_[0-9]{4}-[0-9]{2}-[0-9]{2}_[0-9A-F]{4})\.(4\.0\.dict)')
    m = p.match(file_name)

    return (None, None) if m is None else (m.group(4), m.group(3))


def create_grammar_dir(dict_file_path, grammar_path, template_path, options) -> str:
    """
    Create grammar directory using specified .dict file and other files from template directory.

    :param dict_file_path: Path to .dict file.
    :param grammar_path: Path to a directory where newly created grammar should be stored.
    :param template_path: Path to template directory or language name installed with LG.
    :param options: Bit field that specifies multiple parsing options.
    :return: Path to newly created grammar directory.
    """

    if len(dict_file_path) == 0:
        raise LGParseError("Dictionary file name should not be empty.")

    if not os.path.isfile(dict_file_path):
        # The path is not specified correctly.
        if dict_file_path.find("/") >= 0:
            raise LGParseError("Dictionary path does not exist.")

        # If 'dict_file_path' is LG language short name such as 'en' then there must be a dictionary folder with the
        #   same name. If that's the case there is no need to create grammar folder, simply return the same name.
        #   Let LG handle it.
        elif os.path.isdir(LG_DICT_PATH + "/" + dict_file_path):
            return dict_file_path
        else:
            raise LGParseError("Dictionary path does not exist.")

    # Extract grammar name and a name of the new grammar directory from the file name
    (template_dict_name, dict_path) = get_dir_name(dict_file_path)

    if dict_path is None:
        raise LGParseError("Dictionary file name is expected to have proper notation." + dict_file_path)

    dict_path = grammar_path + "/" + dict_path if dict_path is not None else dict_file_path

    # If template_dir is not specified
    if template_path is None:
        template_path = LG_DICT_PATH + "/" + template_dict_name

    # If template_dir is simply a language name such as 'en'
    elif template_path.find("/") == -1:
        template_path = LG_DICT_PATH + "/" + template_path

    # Raise exception if template_path does not exist
    if not os.path.isdir(template_path):
        raise FileNotFoundError("Directory '{0}' does not exist.".format(template_path))

    try:
        if os.path.isdir(dict_path):
            print("Info: Directory '" + dict_path + "' already exists.")

            if options & BIT_RM_DIR > 0:
                shutil.rmtree(dict_path, True)
                print("Info: Directory '" + dict_path + "' has been removed. Option '-r' was specified.")

        if not os.path.isdir(dict_path):
            # Create dictionary directory using existing one as a template
            shutil.copytree(template_path, dict_path)
            print("Info: Directory '" + dict_path + "' with template files has been created.")

            # Replace dictionary file '4.0.dict' with a new one
            shutil.copy(dict_file_path, dict_path + "/4.0.dict")
            print("Info: Dictionary file has been replaced with '" + dict_file_path + "'.")

    except IOError as err:
        print("IOError: " + str(err))
        return ""

    except FileNotFoundError as err:
        print("FileNotFoundError: " + str(err))
        return ""

    except OSError as err:
        print("OSError: " + str(err))
        return ""

    else:
        return dict_path


def get_output_suffix(options: int) -> str:
    """ Return output file name suffix depending on set options """

    out_format = options & BIT_OUTPUT

    suff = ""  # "2" if (options & BIT_LG_EXE) else ""

    if (out_format & BIT_OUTPUT_CONST_TREE) == BIT_OUTPUT_CONST_TREE:
        return ".tree" + suff
    elif (out_format & BIT_OUTPUT_DIAGRAM) == BIT_OUTPUT_DIAGRAM:
        return ".diag" + suff
    elif (out_format & BIT_OUTPUT_POSTSCRIPT) == BIT_OUTPUT_POSTSCRIPT:
        return ".post" + suff
    else:
        return ".ull" + suff


def print_output(tokens: list, raw_links: list, options: int, ofl) -> None:
    """
    Print links in ULL format to the output specified by 'ofl' variable.

    :param tokens:      List of tokens.
    :param raw_links:   List of links (unfiltered).
    :param options:     Bitmask with parsing options.
    :param ofl:         Output file handle.
    :return:            None
    """
    rwall_index = -1

    i = 0

    for token in tokens:
        if not token.startswith("###"):
            ofl.write(token + ' ')
        else:
            if token.find("RIGHT-WALL") >= 0:
                rwall_index = i
        i += 1

    ofl.write('\n')

    links = sorted(raw_links, key=lambda x: (x[0], x[1]))

    for link in links:
        # Filter out all links with LEFT-WALL if 'BIT_NO_LWALL' is set
        # if (options & BIT_NO_LWALL) and (link[LINK_1ST_TOKEN_INDEX] == 0 or link[LINK_2ND_TOKEN_INDEX] == 0):
        if (options & BIT_ULL_NO_LWALL) and (link[LINK_1ST_TOKEN_INDEX] == 0 or link[LINK_2ND_TOKEN_INDEX] == 0):
            continue

        # Filter out all links with RIGHT-WALL if 'BIT_RWALL' is not set
        if (options & BIT_RWALL) != BIT_RWALL and rwall_index >= 0 \
                and (link[LINK_1ST_TOKEN_INDEX] == rwall_index or link[LINK_2ND_TOKEN_INDEX] == rwall_index):
            continue

        token_count = len(tokens)
        index1, index2 = link[LINK_1ST_TOKEN_INDEX], link[LINK_2ND_TOKEN_INDEX]

        if index1 < token_count and index2 < token_count:
            print(index1, tokens[index1], index2, tokens[index2], file=ofl)
        else:
            print(tokens)
            print(token_count, (index1, index2))

    print('', file=ofl)
