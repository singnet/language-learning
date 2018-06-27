from ull.common.absclient import AbstractDashboardClient, DashboardError, AbstractStatEventHandler
from ull.common.parsemetrics import ParseMetrics, ParseQuality
from ull.common.absclient import AbstractConfigClient
from ull.common.cliutils import handle_path_string

CONF_ROW_KEY = "row_key"
CONF_ROW_IND = "row_indexes"
CONF_COL_KEY = "col_key"
CONF_COL_IND = "col_indexes"
CONF_VAL_KEYS = "value_keys"
CONF_ROW_COUNT = "row_count"
CONF_COL_COUNT = "col_count"
CONF_FILE_PATH = "file_path"
CONF_COL_HEADERS = "col_headers"

class TextFileDashboard(AbstractDashboardClient, AbstractStatEventHandler):
    """
    Class which implements text file serialization.
        Exceptions: IndexError, ValueError
    """
    def __init__(self, cfg_man: AbstractConfigClient):

        if not isinstance(cfg_man, AbstractConfigClient):
            raise Exception("'cfg_man' should be an instance of AbstractConfigClient base class")

        self._config = cfg_man.get_config("", "dash-board")[0]

        self.check_config(self)

        self._path = handle_path_string(self._config[CONF_FILE_PATH])
        self._row_count = self._config[CONF_ROW_COUNT]
        self._col_count = self._config[CONF_COL_COUNT]
        self._dashboard = [list() for r in range(0, self._row_count)]

        # print(self._config)

        for row in self._dashboard:
            for i in range(0, self._col_count):
                row.append(None)

        self._set_headers()

    def _set_headers(self):
        """ Set column headers """
        headers = self._config[CONF_COL_HEADERS]
        for row in range(0, len(headers)):
            for col in range(0, self._col_count):
                # print(headers[row][col])
                self._dashboard[row][col] = headers[row][col]["title"]

    @staticmethod
    def check_config(config):
        pass

    def on_statistics(self, nodes: list, metrics: ParseMetrics, quality: ParseQuality):

        # Return if dashboard is not configured.
        if self._config is None:
            return

        # row_key, col_key = None, None
        row_ind, col_ind = None, None

        try:
            # Get row and column keys
            row_key = self._config[CONF_ROW_KEY].format(*nodes)
            col_key = self._config[CONF_COL_KEY].format(*nodes)

            # Get row and column indexes
            row_ind = self._config[CONF_ROW_IND][row_key]
            col_ind = self._config[CONF_COL_IND][col_key]

        except IndexError as err:
            print("on_statatistics(): IndexError: " + str(err))
            return

        except KeyError as err:
            print("on_statatistics(): KeyError: " + str(err))
            return

        for row in row_ind:
            for col in col_ind:

                val_str = None

                try:
                    # Get value key string by column index
                    val_str = self._config[CONF_VAL_KEYS][col].format(nodes=nodes,
                                                                      parseability=metrics.parseability_str(metrics),
                                                                      parsequality=quality.parse_quality_str(quality))

                except IndexError as err:
                    print("on_statatistics():2: IndexError: " + str(err))
                    continue

                except KeyError as err:
                    print("on_statatistics():2: KeyError: " + str(err))
                    continue

                # Put value into the table
                self.set_cell_by_indexes(row, col, val_str)

    def set_row_names(self, names: list):
        """ Set name for each row. """
        size = len(names)

        if size != self._row_count:
            raise ValueError("'names' list size does not match the number of rows allocated")

        values = [i for i in range(size)]
        self._row_names = dict(zip(names, values))

    def set_col_names(self, names: list):
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

    def set_cell_by_indexes(self, row_index: int, col_index: int, value:object):
        """ Set cell value by row and column indexes. """
        self._dashboard[row_index][col_index] = value

    def set_cell_by_names(self, row_name: str, col_name: str, value:object):
        """ Set cell value by row and column names. """
        self._dashboard[self._get_row_index(row_name)][self._get_col_index(col_name)] = value

    def _fill_empty_cells(self):
        """ Replace None with text string """
        for row in range(0, self._row_count):
            for col in range(0, self._col_count):
                if self._dashboard[row][col] is None:
                    self._dashboard[row][col] = "  N/A  "

    def update_dashboard(self):

        # Return if dashboard is not configured.
        if self._config is None:
            return

        try:
            self._fill_empty_cells()

            with open(self._path, "w") as file:

                for row in self._dashboard:
                    print('"' + '";"'.join(row) + '"', file=file)

        except IOError as err:
            print("IOError: " + str(err))
