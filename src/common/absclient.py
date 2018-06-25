from abc import ABCMeta, abstractmethod

"""
    Abstract classes for service client definitions.
    
"""

from .parsemetrics import ParseMetrics, ParseQuality


__all__ = ['DashboardError', 'AbstractDashboardClient', 'AbstractConfigClient', 'AbstractGrammarTestClient',
           'AbstractFileParserClient', 'AbstractStatEventHandler']

DASH_UPDATE_PARSEABILITY = 1
DASH_UPDATE_PARSEQUALITY = 2
DASH_UPDATE_ALL = DASH_UPDATE_PARSEABILITY | DASH_UPDATE_PARSEQUALITY


class DashboardError(Exception):
    pass


class AbstractDashboardClient(metaclass=ABCMeta):
    """
    Base class for publishing parse results to abstract dashboard which can be either file, or Web service,
        or spreadsheet.
    """
    @abstractmethod
    def set_cell_by_indexes(self, row_index: int, col_index: int, value: object):
        pass

    @abstractmethod
    def set_cell_by_names(self, row_name: str, col_name: str, value: object):
        pass

    @abstractmethod
    def update_dashboard(self):
        """ Update dashboard values """
        pass


class AbstractConfigClient(metaclass=ABCMeta):
    """
    Base class for classes responsible for obtaining configuration information either from files
        or from Web services
    """
    @abstractmethod
    def get_config(self, config_name: str, comp_name: str) -> dict:
        """
        Retreave configuration from whatever source.

        :param config_name:     Configuration name string.
        :param comp_name:       Component name string.
        :return:                Dictionary instance holding configuration parameters.
        """
        pass

    @abstractmethod
    def save_config(self, config_name: str, comp_name: str) -> None:
        """
        Save configuration to whatever destination.

        :param config_name:     Configuration name string.
        :param comp_name:       Component name string.
        :return:                None
        """
        pass


class AbstractGrammarTestClient(metaclass=ABCMeta):
    """
    Base class responsible for induced grammar testing.
    """
    @abstractmethod
    def test(self, dict_path: str, corpus_path: str, output_path: str, reference_path: str, options: int) \
            -> (ParseMetrics, ParseQuality):
        pass


class AbstractFileParserClient(metaclass=ABCMeta):
    """
    Base class for parsers
    """
    @abstractmethod
    def parse(self, dict_path: str, corpus_path: str, output_path: str, ref_file: str, options: int) \
            -> (ParseMetrics, ParseQuality):
        pass


class AbstractStatEventHandler(metaclass=ABCMeta):
    """
    Base class for statistics event handlers
    """
    @abstractmethod
    def on_statistics(self, nodes: list, metrics: ParseMetrics, quality: ParseQuality) -> None:
        pass
