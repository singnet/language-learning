from common.absclient import AbstractDashboardClient, DashboardError, AbstractStatEventHandler
from common.parsemetrics import ParseMetrics, ParseQuality

CONF_ROW_KEY = "row_key"
CONF_ROW_IND = "row_indexes"
CONF_COL_KEY = "col_key"
CONF_COL_IND = "col_indexes"
CONF_VAL_KEYS = "value_keys"


class TextFileDashboard(AbstractDashboardClient, AbstractStatEventHandler):
    """
    Class which implements text file serialization.
        Exceptions: IndexError, ValueError
    """
    def __init__(self, row_count: int, col_count: int, file_path: str):
        self._path = file_path
        self._row_count = row_count
        self._col_count = col_count
        self._dashboard = [list() for r in range(0, row_count)]
        self._config = None

        for row in self._dashboard:
            for i in range(0, col_count):
                row.append(None)

    def on_statistics(self, nodes: list, metrics: ParseMetrics, quality: ParseQuality):
        # Get row index by row key
        row_key = self._config[CONF_ROW_KEY].format(*nodes)
        row_ind = self._config[CONF_ROW_IND][row_key].format(*nodes)

        # Get column index by name
        col_key = self._config[CONF_COL_KEY].format(*nodes)
        col_ind = self._config[CONF_COL_IND][col_key].format(*nodes)

        # Get value key string by column index
        val_str = self._config[CONF_VAL_KEYS][col_ind].format(nodes=nodes,
                                                              parseability=metrics.parseability(metrics),
                                                              parsequality=quality.parse_quality(quality))

        # Put value into the table
        self.set_cell_by_indexes(row_ind, col_ind, val_str)

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

    def update_dashboard(self):
        try:
            with open(self._path, "w") as file:
                if hasattr(self, "_col_names") and len(self._col_names) > 0:
                    print('"' + '";"'.join(list(self._col_names.keys())) + '"', file=file)

                for row in self._dashboard:
                    print('"' + '";"'.join(row) + '"', file=file)

        except IOError as err:
            print("IOError: " + str(err))

