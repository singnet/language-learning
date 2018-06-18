"""
    This module is common for multiple Link Grammar parse scripts. 
        It exports:
            parse_file_with_api()   - function capable of parsing text files and calculating parse statistics.
            parse_corpus_files()    - function capable of traversing directory tree parsing each file.
"""
import sys
import re
import os
import shutil

from .dirhelper import *
from .optconst import *
from .parsemetrics import ParseMetrics
from .inprocparser import *
from .lgapiparser import *
from .lgmisc import LGParseError


__all__ = ['parse_corpus_files', 'LG_DICT_PATH', 'create_dir', 'create_grammar_dir', 'get_dir_name']

__version__ = "2.1.3"

LG_DICT_PATH = "/usr/local/share/link-grammar"




def get_dir_name(file_name:str) -> (str, str):
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


def save_stat0(stat_path:str, full_ratio:float, none_ratio:float, avrg_ratio:float):
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

        assert avrg_ratio <= 1, "Average ratio > 1"

        print("Total sentences parsed in full:\t{0[0]:2.2f}%\n"
              "Total sentences not parsed at all:\t{0[1]:2.2f}%\nAverage sentence parse:\t{0[2]:2.2f}%\n".format(
            (full_ratio * 100.0, none_ratio * 100.0, avrg_ratio * 100.0)), file=stat_file_handle)

    except IOError as err:
        print("IOError: " + str(err))

    except FileNotFoundError as err:
        print("FileNotFoundError: " + str(err))

    except OSError as err:
        print("OSError: " + str(err))

    finally:
        if stat_file_handle is not None and stat_file_handle != sys.stdout:
            stat_file_handle.close()


def save_stat(stat_path:str, metrics: ParseMetrics):
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

        print(ParseMetrics.text(metrics), file=stat_file_handle)

    except IOError as err:
        print("IOError: " + str(err))

    except FileNotFoundError as err:
        print("FileNotFoundError: " + str(err))

    except OSError as err:
        print("OSError: " + str(err))

    finally:
        if stat_file_handle is not None and stat_file_handle != sys.stdout:
            stat_file_handle.close()


def parse_corpus_files(src_dir: str, dst_dir: str, dict_dir: str, grammar_dir: str, template_dir: str,
                       linkage_limit: int, options: int, reference_path: str) -> ParseMetrics:
    """
    Traverse corpus folder parsing each file in that folder and subfolders. The function recreates source directory
        structure within the destination one and stores parsing results in newly created directory structure.

    :param src_dir: Source directory with corpus files.
    :param dst_dir: Destination directory to store parsing result files.
    :param dict_dir: Path to dictionary directory or file
    :param grammar_dir: Root directory path to store newly created grammar.
    :param template_dir: Path to template dictionary directory
    :param linkage_limit: Maximum number of linkages. Parammeter for LG API.
    :param options: Parse options bit field.
    :param reference_path: Path to either reference file or directory with reference files depending on weather a file
                            or directory is specified in src_dir. In later case files with the same names are being
                            compared.
    :return: Tuple of ParseMetrics and ParseQuality.
    """
    total_metrics = ParseMetrics()

    def on_dict_file(path):
        """
        Callback function envoked for every .dict file specified.

        :param path: Path to .dict file
        :return:
        """

        print("@@@@@@@@@@@@@@@@@@@@@@" + path)

        return

        file_count = 0

        new_grammar_path = ""
        new_dst_dir = dst_dir
        stat_path = None

        def recreate_struct(dir_path) -> bool:
            """
            Callback function that recreates directory structure of the source folder
            within the destination root directory.
            """
            return create_dir(new_dst_dir + "/" + dir_path[len(src_dir) + 1:])

        def on_corpus_file(file_path):

            # *******************************************************************
            print("!!!!!! " + file_path)
            # *******************************************************************

            ptr_parse = parse_file_with_lgp if (options & BIT_LG_EXE) else parse_file_with_api

            p, f = os.path.split(file_path)
            dst_file = os.path.join(new_dst_dir, f)

            try:
                nonlocal file_count
                nonlocal total_metrics

                file_metrics = ptr_parse(new_grammar_path, file_path, dst_file, linkage_limit, options)

                # If output format is ULL and separate statistics option is specified
                if options & (BIT_SEP_STAT | BIT_OUTPUT) == BIT_SEP_STAT:
                    stat_name = dst_file + ".stat"
                    stat_name += "2" if (options & BIT_LG_EXE) else ""

                    assert file_metrics.average_parsed_ratio <= 1.0, "on_corpus_file(): a_ratio > 1.0"

                    save_stat(stat_name, file_metrics)

                total_metrics += file_metrics
                file_count += 1

            except OSError as err:
                print("OSError: " + str(err))


        # =============================================================================
        # def on_dict_file(path):
        # =============================================================================
        print("\nInfo: Testing grammar: '" + path + "'")

        # grammar_folder = output_dir if (options & BIT_LOC_LANG) == BIT_LOC_LANG else grammar_dir

        new_grammar_path = create_grammar_dir(path, grammar_dir, template_dir, options)

        # Create subdirectory in dst_dir for newly created grammar
        gpath, gname = os.path.split(new_grammar_path)

        new_dst_dir = dst_dir

        # Create subdirectory in dst_dir for newly created grammar
        if not (options & BIT_DPATH_CREATE):
            new_dst_dir = dst_dir + "/" + gname

            if not create_dir(new_dst_dir):
                print("Error: Unable to create grammar subfolder: '{}'".format(gname))
                return
        else:
            end_pos = path.rfind("/")
            new_dst_dir = dst_dir + path[len(dict_dir):end_pos] if end_pos > 0 else path[len(dict_dir)-1:]

        # print("new_dst_dir='" + new_dst_dir + "'")

        stat_suffix = "2" if (options & BIT_LG_EXE) == BIT_LG_EXE else ""

        # If src_dir is a directory then on_corpus_file() is invoked for every corpus file of the directory tree
        if os.path.isdir(src_dir):
            dpath, dname = os.path.split(src_dir)
            stat_path = new_dst_dir + "/" + dname + ".stat" + stat_suffix
            traverse_dir(src_dir, "", on_corpus_file, recreate_struct, True)

        # If src_dir is a file then simply call on_corpus_file() for it
        elif os.path.isfile(src_dir):
            fpath, fname = os.path.split(src_dir)
            stat_path = new_dst_dir + "/" + fname + ".stat" + stat_suffix
            on_corpus_file(src_dir)

        # Update statistics only if 'ull' output format is specified.
        if (options & BIT_OUTPUT):
            return

        nonlocal total_metrics

        if file_count > 1:
            total_metrics /= float(file_count)

        save_stat(stat_path, total_metrics)

    def recreate_dict_struct(dir_path) -> bool:
        """
        Callback function that recreates directory structure of the source folder
        within the destination root directory.
        """
        return create_dir(dst_dir + "/" + dir_path[len(dict_dir) + 1:])

    # =============================================================================================================
    # def parse_corpus_files(src_dir, dst_dir, dict_dir, grammar_dir, template_dir, linkage_limit, options) -> int:
    # =============================================================================================================
    try:
        # *******************************************
        print("%%%%%%%%%%%%% " + dict_dir)
        # *******************************************

        f_ptr = recreate_dict_struct if (options & BIT_DPATH_CREATE) == BIT_DPATH_CREATE else None

        # If dict_dir is the name of directory, hopefully with multiple .dict files to test
        #   then traverse the specified directory handling every .dict file in there.
        if os.path.isdir(dict_dir):
            traverse_dir(dict_dir, ".dict", on_dict_file, None, True)
            # traverse_dir(dict_dir, ".dict", on_dict_file, f_ptr, True)
            # traverse_dir(dict_dir, ".dict", lambda x: print(x), f_ptr, True)

        # Otherwise dict_dir might be either .dict file name, or LG-shipped language name.
        else:
            on_dict_file(dict_dir)

    except LGParseError as err:
        raise LGParseError("LGParseError: " + str(err))

    except Exception as err:
        raise LGParseError("Exception: " + str(err))

    finally:
        return total_metrics


def parse_corpus_files0(src_dir, dst_dir, dict_dir, grammar_dir, template_dir, linkage_limit, options) -> int:
    """
    Traverse corpus folder parsing each file in that folder and subfolders. The function recreates source directory
        structure within the destination one and stores parsing results in newly created directory structure.
    :param src_dir: Source directory with corpus files.
    :param dst_dir: Destination directory to store parsing result files.
    :param dict_dir: Path to dictionary directory or file
    :param grammar_dir: Root directory path to store newly created grammar.
    :param template_dir: Path to template dictionary directory
    :param linkage_limit: Maximum number of linkages. Parammeter for LG API.
    :param options: Parse options bit field.
    :return:
    """
    def on_dict_file(path):
        """
        Callback function envoked for every .dict file specified.

        :param path: Path to .dict file
        :return:
        """
        file_count = 0
        full_ratio = 0.0
        none_ratio = 0.0            # probably should be 1.0
        avrg_ratio = 0.0

        new_grammar_path = ""
        new_dst_dir = dst_dir

        def recreate_struct(dir_path) -> bool:
            """
            Callback function that recreates directory structure of the source folder
            within the destination root directory.
            """
            return create_dir(new_dst_dir + "/" + dir_path[len(src_dir) + 1:])

        def on_corpus_file(file_path):

            ptr_parse = parse_file_with_lgp if (options & BIT_LG_EXE) else parse_file_with_api

            p, f = os.path.split(file_path)
            dst_file = os.path.join(new_dst_dir, f)

            try:
                nonlocal file_count
                nonlocal full_ratio
                nonlocal none_ratio
                nonlocal avrg_ratio

                f_ratio, n_ratio, a_ratio = ptr_parse(new_grammar_path, file_path, dst_file, linkage_limit, options)

                # If output format is ULL and separate statistics option is specified
                if options & (BIT_SEP_STAT | BIT_OUTPUT) == BIT_SEP_STAT:
                    stat_name = dst_file + ".stat"
                    stat_name += "2" if (options & BIT_LG_EXE) else ""

                    assert a_ratio <= 1.0, "on_corpus_file(): a_ratio <= 1.0"

                    save_stat(stat_name, f_ratio, n_ratio, a_ratio)

                file_count += 1
                full_ratio += f_ratio
                none_ratio += n_ratio
                avrg_ratio += a_ratio

            except OSError as err:
                print(str(err))


        # =============================================================================
        # def on_dict_file(path):
        # =============================================================================
        file_count = 0
        full_ratio = 0.0
        none_ratio = 0.0
        avrg_ratio = 0.0
        stat_path = None

        print("\nInfo: Testing grammar: '" + path + "'")

        # grammar_folder = output_dir if (options & BIT_LOC_LANG) == BIT_LOC_LANG else grammar_dir

        new_grammar_path = create_grammar_dir(path, grammar_dir, template_dir, options)

        # Create subdirectory in dst_dir for newly created grammar
        gpath, gname = os.path.split(new_grammar_path)

        new_dst_dir = dst_dir

        # Create subdirectory in dst_dir for newly created grammar
        if not (options & BIT_DPATH_CREATE):
            new_dst_dir = dst_dir + "/" + gname

            if not create_dir(new_dst_dir):
                print("Error: Unable to create grammar subfolder: '{}'".format(gname))
                return
        else:
            end_pos = path.rfind("/")
            new_dst_dir = dst_dir + path[len(dict_dir):end_pos] if end_pos > 0 else path[len(dict_dir)-1:]

        # print("new_dst_dir='" + new_dst_dir + "'")

        stat_suffix = "2" if (options & BIT_LG_EXE) == BIT_LG_EXE else ""

        # If src_dir is a directory then on_corpus_file() is invoked for every corpus file of the directory tree
        if os.path.isdir(src_dir):
            dpath, dname = os.path.split(src_dir)
            stat_path = new_dst_dir + "/" + dname + ".stat" + stat_suffix
            traverse_dir(src_dir, "", on_corpus_file, recreate_struct, True)

        # If src_dir is a file then simply call on_corpus_file() for it
        elif os.path.isfile(src_dir):
            fpath, fname = os.path.split(src_dir)
            stat_path = new_dst_dir + "/" + fname + ".stat" + stat_suffix
            on_corpus_file(src_dir)

        # Update statistics only if 'ull' output format is specified.
        if (options & BIT_OUTPUT):
            return

        if file_count > 1:
            full_ratio /= float(file_count)
            none_ratio /= float(file_count)
            avrg_ratio /= float(file_count)

        save_stat(stat_path, full_ratio, none_ratio, avrg_ratio)


    def recreate_dict_struct(dir_path) -> bool:
        """
        Callback function that recreates directory structure of the source folder
        within the destination root directory.
        """
        return create_dir(dst_dir + "/" + dir_path[len(dict_dir) + 1:])

    # =============================================================================================================
    # def parse_corpus_files(src_dir, dst_dir, dict_dir, grammar_dir, template_dir, linkage_limit, options) -> int:
    # =============================================================================================================
    try:
        f_ptr = recreate_dict_struct if (options & BIT_DPATH_CREATE) == BIT_DPATH_CREATE else None

        # If dict_dir is the name of directory, hopefully with multiple .dict files to test
        #   then traverse the specified directory handling every .dict file in there.
        if os.path.isdir(dict_dir):
            traverse_dir(dict_dir, ".dict", on_dict_file, f_ptr, True)

        # Otherwise dict_dir might be either .dict file name, or LG shiped language name.
        else:
            on_dict_file(dict_dir)

    except LGParseError as err:
        print("LGParseError: " + str(err))
        return 1

    except Exception as err:
        print("Exception: " + str(err))
        return 2

    return 0

