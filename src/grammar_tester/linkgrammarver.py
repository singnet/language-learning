from subprocess import PIPE, Popen
from typing import Tuple, Optional
import os
import re


class LGVersionParseError(Exception):
    pass


def handle_version_response(text: str) -> Tuple[str, str]:
    """
    Parse 'link-parser --version' response

    :param text:    link-parser output text string
    :return:        Tuple (<version>, <dictionary_path>) on success, None otherwise.
    """
    text = text.replace("\n", " ")

    ver_search_str = "link-grammar-"
    ver_search_len = len(ver_search_str)
    ver_pos = text.find(ver_search_str)

    if ver_pos < 0:
        raise LGVersionParseError("handle_version_response() unable to parse: " + text)

    ver_pos += ver_search_len
    ver = text[ver_pos:ver_pos + 5]

    if ver >= "5.5.0":
        pth_search_str = "DICTIONARY_DIR="
        pth_search_len = len(pth_search_str)
        pth_pos = text.find(pth_search_str)
        pth_end = text.find(" ", pth_pos)

        if pth_pos < 0 or pth_end < 0:
            raise LGVersionParseError("handle_version_response() unable to parse: " + text)

        pth_pos += pth_search_len
        pth = text[pth_pos:pth_end]

    else:
        pth = None

    return ver, pth


def get_lg_version() -> (str, str):
    """
    Get Link Grammar version and preinstalled dictionary path

    :return:    Tuple: (<version string>, <dictionary path>)
    """

    version, dict_path = None, None

    try:

        with Popen(["link-parser", "--version"], stdout=PIPE, stderr=PIPE) as proc_pars:

            # Read pipes to get complete output returned by link-parser
            raw, err = proc_pars.communicate()

            # Check return code to make sure the process completed successfully.
            if proc_pars.returncode != 0:
                raise Exception("Process '{0}' terminated with exit code: {1} "
                                "and error message:\n'{2}'.".format("link-parser --version",
                                                                    proc_pars.returncode, err.decode()))

            # Take an action depending on the output format specified by 'options'
            version, dict_path = handle_version_response(raw.decode("utf-8-sig"))

    except LGVersionParseError as err:
        print("get_lg_version(): " + str(err))
        raise

    except KeyboardInterrupt:
        print("get_lg_version(): Ctrl+C triggered.")
        raise

    except Exception as err:
        print("get_lg_version(): Exception: " + str(type(err)) + str(err))
        raise

    return version, dict_path


# def get_lg_dict_version(dict_path: str) -> str:
#     """
#     Return Link Grammar version that can be used with dictionary specified by 'dict_path'
#
#     :param dict_path:   Path to LG dictionary file/directory
#     :return:
#     """
#
#     if os.path.isdir(dict_path):
#         dict_path += "/4.0.dict"
#
#     with open(dict_path, "r") as file:
#         text = file.read()
#
#         # Find 'UNKNOWN-WORD' rule
#         pos = text.find("UNKNOWN-WORD")
#
#         # Any LG version can be used if the rule is not found
#         if pos < 0:
#             return "0.0.0"
#
#         # For LG 5.5.x 'UNKNOWN-WORD' should be enclosed in '<>'
#         return "5.5.0" if pos > 0 and text[pos-1:pos] == "<" else "5.4.0"

def get_lg_dict_version(dict_path: str) -> str:
    """
    Return Link Grammar version that can be used with dictionary specified by 'dict_path'

    :param dict_path:   Path to LG dictionary file/directory
    :return:
    """
    re_dict_rule = re.compile(r'^([^%\n][<]?UNKNOWN-WORD[>]?\s*:.+?;\s*)$', re.M | re.S)

    dict_path2 = dict_path

    if os.path.isdir(dict_path):
        dict_path2 += "/dict.db"
        dict_path += "/4.0.dict"

    if os.path.isfile(dict_path2):
        # In case dict is a binary file, returns special "version"
        return "sql-dict"

    with open(dict_path, "r") as file:
        text = file.read()

        text = "\n".join(re.findall(re_dict_rule, text))

        # Find 'UNKNOWN-WORD' rule
        pos = text.find("UNKNOWN-WORD")

        # Any LG version can be used if the rule is not found
        if pos < 0:
            return "0.0.0"

        # For LG 5.5.x 'UNKNOWN-WORD' should be enclosed in '<>'
        return "5.5.0" if pos > 0 and text[pos-1:pos] == "<" else "5.4.0"
