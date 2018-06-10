import os
from .lgmisc import LGParseError

__all__ = ['traverse_dir', 'create_dir', 'traverse_dir_tree']


def traverse_dir_tree(root: str, file_ext: str, file_arg_list: list=None, dir_arg_list: list=None,
                           is_recursive: bool=False):
    """
    Perform argument check and if all the arguments are properly specified call `traverse_directory` which actualy
        does the job.

    :param root: Root directory to start traversing from.
    :param file_ext: File extension to filter out unnecessary files.
    :param file_arg_list: List where the first element is a callback function pointer to be envoke for each file along
                            the way and the rest are its additional arguments.
    :param dir_arg_list: List where the first element is a callback function pointer to be envoke for each directory
                            along the way and the rest are its additional arguments.
    :param is_recursive: Boolean value that tells the function to recursively call itself for each subdirectory.
    :return:
    """
    # At least one of the two callback function arguments should be specified.
    if file_arg_list is None and dir_arg_list is None:
        raise ValueError("No callback arguments specified.")

    # Check the first callback argument list
    if file_arg_list is not None:

        if len(file_arg_list) == 0:
            raise ValueError("Empty argument list for 'file_arg_list'.")

        if not callable(file_arg_list[0]):
            raise ValueError("The argument you specified in 'file_arg_list[0]' field is not callable.")

    # Check the second callback argument list.
    if dir_arg_list is not None:

        if len(dir_arg_list) == 0:
            raise ValueError("Empty argument list for 'dir_arg_list'.")

        if not callable(dir_arg_list[0]):
            raise ValueError("The argument you specified in 'dir_arg_list[0]' field is not callable.")

    try:
        # If all the arguments are correct start traversing
        traverse_directory(root, file_ext, file_arg_list, dir_arg_list, is_recursive)
    except Exception as err:
        print("traverse_dir_tree(): ")

def traverse_directory(root: str, file_ext: str, file_arg_list: list=None, dir_arg_list: list=None, is_recursive=False):
    """
    Traverse directory tree and call callback functions for each file and subdirectory.

    :param root: Root directory to start traversing from.
    :param file_ext: File extention to filter files by type.
    :param on_file: Callback function pointer to be called each time the file is found.
    :param on_dir: Callback function pointer to be called each time the folder is found.
    :param is_recursive: Tells the function to recursively traverse directory tree if set to True, otherwise if False.
    :return:
    """
    with os.scandir(root) as scandir:
        for entry in scandir:

            if entry.is_dir():
                is_traversing = is_recursive

                if dir_arg_list is not None:
                    is_traversing = (is_traversing and dir_arg_list[0](entry.path, dir_arg_list[1:]))

                if is_traversing:
                    traverse_directory(entry.path, file_ext, file_arg_list, dir_arg_list, True)

            elif entry.is_file() and (len(file_ext) < 1 or (len(file_ext) and entry.path.endswith(file_ext))):
                if file_arg_list is not None:
                    # try:
                    file_arg_list[0](entry.path, file_arg_list[1:])

                    # except Exception as err:
                    #     print("traverse_directory(): " + str(err))




def traverse_dir(root, file_ext, on_file, on_dir=None, is_recursive=False):
    """
    Traverse directory tree and call callback functions for each file and subdirectory.

    :param root: Root directory to start traversing from.
    :param file_ext: File extention to filter files by type.
    :param on_file: Callback function pointer to be called each time the file is found.
    :param on_dir: Callback function pointer to be called each time the folder is found.
    :param is_recursive: Tells the function to recursively traverse directory tree if set to True, otherwise if False.
    :return:
    """
    for entry in os.scandir(root):

        if entry.is_dir():
            is_traversing = is_recursive

            if on_dir is not None:
                is_traversing = (is_traversing and on_dir(entry.path))

            if is_traversing:
                traverse_dir(entry.path, file_ext, on_file, on_dir, True)

        elif entry.is_file() and (len(file_ext) < 1 or (len(file_ext) and entry.path.endswith(file_ext))):
            if on_file is not None:
                try:
                    on_file(entry.path)
                except LGParseError as err:
                    print("LGParseError: " + str(err))


def traverse_dir0(root, file_ext, on_file, on_dir=None, is_recursive=False):
    """
    Traverse directory tree and call callback functions for each file and subdirectory.

    :param root: Root directory to start traversing from.
    :param file_ext: File extention to filter files by type.
    :param on_file: Callback function pointer to be called each time the file is found.
    :param on_dir: Callback function pointer to be called each time the folder is found.
    :param is_recursive: Tells the function to recursively traverse directory tree if set to True, otherwise if False.
    :return:
    """
    for entry in os.scandir(root):

        if entry.is_dir():
            is_traversing = is_recursive

            if on_dir is not None:
                is_traversing = (is_traversing and on_dir(entry.path))

            if is_traversing:
                traverse_dir(entry.path, file_ext, on_file, on_dir, True)

        elif entry.is_file() and (len(file_ext) < 1 or (len(file_ext) and entry.path.endswith(file_ext))):
            if on_file is not None:
                try:
                    on_file(entry.path)
                except LGParseError as err:
                    print("LGParseError: " + str(err))


def create_dir(new_path) -> bool:
    """ Create directory specified by <new_path> """
    try:
        # If the subdirectory does not exist in destination root create it.
        if not os.path.isdir(new_path):
            # print(new_path)
            os.mkdir(new_path)

    except OSError as err:
        print("OSError: " + str(err))
        return False

    return True
