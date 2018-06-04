from abc import ABCMeta, abstractmethod

"""
    Abstract classes for service client definitions.
    
"""

from .parsemetrics import ParseMetrics


__all__ = ['DashboardError', 'AbstractDashboardClient', 'AbstractConfigClient', 'AbstractGrammarTestClient',
           'AbstractFileParserClient']

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
    def get_config(self):
        pass

    @abstractmethod
    def save_config(self):
        pass


class AbstractGrammarTestClient(metaclass=ABCMeta):
    """
    Base class responsible for induced grammar testing.
    """
    @abstractmethod
    def test(self, dict_path: str, corpus_path: str, output_path: str, reference_path: str) -> ParseMetrics:
        pass


class AbstractFileParserClient(metaclass=ABCMeta):
    """
    Base class fot parsers
    """
    @abstractmethod
    def parse(self, dict_path: str, corpus_path: str, output_path: str, options: int) -> ParseMetrics:
        pass
