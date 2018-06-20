import os

__all__ = ['strip_quotes', 'strip_trailing_slash', 'handle_path_string', 'strip_brackets']


def strip_brackets(text) -> str:
    """
    Strips starting and trailing brackets from input string

    :param text: Text string to strip the brackets from.
    :return: Text string without brackets.
    """
    if text is None:
        return ""

    if text.startswith("[") and text.endswith("]"):
        return text[1:len(text) - 1]

    return text


def strip_quotes(text) -> str:
    """
    Strips starting and trailing quotes from input string

    :param text: Text string to strip the quotes from.
    :return: Text string without quotes.
    """
    if text is None:
        return ""

    l = len(text)

    if l == 0:
        return text

    start = 0 if text[0] != "'" and text[0] != '"' else 1
    end = l if text[l-1] != "'" and text[l-1] != '"' else l-1

    return text[start:end]


def strip_trailing_slash(text) -> str:
    """
    Strip trailing slash if any.

    :param text: Path string
    :return: Path string without trailing slash.
    """
    if text is None:
        return ""

    l = len(text)

    if not l:
        return ""

    end = l-1 if text[l-1] == "/" else l
    return text[:end]


def handle_path_string(text) -> str:
    """
    Strip off single or double quotes if any, replace tilda with home directory path
        and finally strip trailing slash if any.

    :param text: Path string.
    :return: Path string prepared to be used as an input parameter to any other function.
    """
    return strip_trailing_slash(strip_quotes(text)).replace("~", os.environ['HOME'])
