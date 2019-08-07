import re
import os
import sys
import time
import logging
from typing import Optional, Union
from ..common.absclient import AbstractDashboardClient, DashboardError, AbstractPipelineComponent
from ..common.cliutils import handle_path_string

__all__ = ['TextFileDashboard', 'CONF_ROW_KEY', 'CONF_ROW_IND', 'CONF_COL_KEY', 'CONF_COL_IND', 'CONF_VAL_KEYS',
           'CONF_ROW_COUNT', 'CONF_COL_COUNT', 'CONF_FILE_PATH', 'CONF_COL_HEADERS']

CONF_ROW_KEY = "row_key"
CONF_ROW_IND = "row_indexes"
CONF_COL_KEY = "col_key"
CONF_COL_IND = "col_indexes"
CONF_VAL_KEYS = "value_keys"
CONF_ROW_COUNT = "row_count"
CONF_COL_COUNT = "col_count"
CONF_FILE_PATH = "file_path"
CONF_COL_HEADERS = "col_headers"
CONF_MULTI_ACCESS = "multi_access"


class ExclusiveLockError(Exception):
    pass


class ExclusiveLock:
    """
    Exclusive file lock class which is currently implemented as a simple flag file.

    """
    def __init__(self, file_path, delay_sec: float=0.001, attempts: int=3):

        self._file_path = f"{file_path}.lock"

        while os.path.isfile(self._file_path) and attempts:
            time.sleep(delay_sec)
            attempts -= 1

        if attempts:
            with open(self._file_path, "w") as file:
                return

        raise ExclusiveLockError(f"Unable to open {self._file_path} exclusively.")

    def __del__(self):
        if os.path.isfile(self._file_path):
            os.remove(self._file_path)


class TextFileDashboard(AbstractDashboardClient):
    """
    Class which implements text file serialization.
        Exceptions: IndexError, ValueError
    """
    def __init__(self, config: dict):

        self._logger = logging.getLogger("TextFileDashboard")
        self.check_config(self)

        self._multi_access = config.get(CONF_MULTI_ACCESS, False)

        self._path = handle_path_string(config[CONF_FILE_PATH])
        self._row_count = config[CONF_ROW_COUNT] + len(config.get(CONF_COL_HEADERS, []))
        self._col_count = config[CONF_COL_COUNT]
        self._dashboard = [list() for r in range(0, self._row_count)]

        self.alloc_dashboard()
        self._set_headers(config)

    def alloc_dashboard(self):
        """ Allocate dashboard """
        for row in self._dashboard:
            for i in range(0, self._col_count):
                row.append(None)

    def _set_headers(self, config: dict) -> None:
        """ Set column headers """
        headers = config.get(CONF_COL_HEADERS, None)

        if headers is not None:
            for row in range(0, len(headers)):
                cols_to_set = min(self._col_count, len(headers[row]))
                for col in range(0, cols_to_set):
                    self._dashboard[row][col] = headers[row][col]["title"]

    @staticmethod
    def check_config(config) -> bool:
        return True

    def set_row_names(self, names: list) -> None:
        """ Set name for each row """
        size = len(names)

        if size != self._row_count:
            raise ValueError("'names' list size does not match the number of rows allocated")

        values = [i for i in range(size)]
        self._row_names = dict(zip(names, values))

    def set_col_names(self, names: list) -> None:
        """ Set name for each column. """
        size = len(names)

        if size != self._col_count:
            raise ValueError("'names' list size does not match the number of columns allocated")

        values = [i for i in range(size)]
        self._col_names = dict(zip(names, values))

    def _get_row_index(self, row_name: str) -> int:
        """ Get row index by name """
        if not hasattr(self, "_row_names"):
            raise DashboardError("row names are not set")

        return self._row_names[row_name]

    def _get_col_index(self, col_name: str) -> int:
        """ Get column index by name """
        if not hasattr(self, "_col_names"):
            raise DashboardError("column names are not set")

        return self._col_names[col_name]

    def set_cell_by_indexes(self, row_index: int, col_index: int, value:object) -> None:
        """ Set cell value by row and column indexes. """
        self._dashboard[row_index][col_index] = value

    def set_cell_by_names(self, row_name: str, col_name: str, value:object) -> None:
        """ Set cell value by row and column names. """
        self._dashboard[self._get_row_index(row_name)][self._get_col_index(col_name)] = value

    def _update_table(self):
        """ Update current table from already existing file """
        if not os.path.isfile(self._path):
            return

        lock = ExclusiveLock(self._path)

        with open(self._path, "r") as file:
            table = file.readlines()

        # Remove trailing empty lines if any
        for item in table[::-1]:
            if len(item.rstrip()) > 0:
                break
            else:
                table.remove(item)

        # Get number of table rows
        row_count = len(table)

        # Check if table has the same dimentions
        if row_count != self._row_count:
            raise DashboardError(f"Table read from the existing file '{self._path}' has different number of rows: "
                                 f"{row_count} instead of {self._row_count}.")

        # Update table read from the file with the current table data
        for row in range(self._row_count):
            row_cells = table[row].split()

            cell_count = len(row_cells)

            if cell_count != self._col_count:
                raise DashboardError(f"Number of cells mismatch in row={row}, {cell_count} != {self._col_count}")

            for col in range(self._col_count):
                if self._dashboard[row][col] is None:
                    self._dashboard[row][col] = row_cells[col].strip()

        del lock

    def update_dashboard(self) -> None:

        try:
            if self._multi_access:
                self._update_table()

            with open(self._path, "w") as file:
                print(str(self), file=file)

        except IOError as err:
            self._logger.error("IOError: " + str(err))
            raise

    def __str__(self) -> str:
        """ Return dashboard as text string """
        text = ""

        for row in self._dashboard:
            text += '\t'.join(["N/A" if cell is None else str(cell) for cell in row]) + "\n"

        return text


# class HTMLFileDashboard(TextFileDashboard):
#
#     def __init__(self, cfg_man: AbstractConfigClient):
#         super().__init__(cfg_man)
#
#     def update_dashboard(self):
#
#         # Return if dashboard is not configured.
#         if self._config is None:
#             return
#
#         try:
#             self._fill_empty_cells()
#
#             with open(self._path, "w") as file:
#
#                 print("<html><head>!!!</head><body><table>", file=file)
#
#                 for row in self._dashboard:
#                     print("<tr><td>" + "</td><td>".join(row) + "</td></tr>", file=file)
#
#                 print("</table></body></html>", file=file)
#
#         except IOError as err:
#             print("IOError: " + str(err))


class TextFileDashboardComponent(AbstractPipelineComponent):

    def __init__(self, **kwargs):
        self._board = TextFileDashboard(kwargs)

    def __exit__(self):
        self._board.update_dashboard()

    def __del__(self):
        self._board.update_dashboard()

    @staticmethod
    def _convert_to_int(line: Union[str, int]) -> int:
        # Do nothing if specified parameter is already int
        if isinstance(line, int):
            return line

        pattern = re.compile("^\s*[-+]?\s*\d+|[-+]{1}\s*\d+")

        arg_list = [a.replace(' ', '') for a in re.findall(pattern, line)]

        if not len(arg_list):
            raise ValueError(f"Can't convert '{line}' to integer.")

        sum = 0

        for num in arg_list:
            sum += int(num)

        return sum

    def set(self, **kwargs):
        # logging.debug(f"{kwargs}")

        self._board.set_cell_by_indexes(self._convert_to_int(kwargs["row"]),
                                        self._convert_to_int(kwargs["col"]),
                                        str(kwargs["val"]).format(**kwargs))

    def validate_parameters(self, **kwargs) -> bool:
        return True

    def run(self, **kwargs) -> dict:
        return {}
