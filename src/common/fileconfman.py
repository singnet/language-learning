import json

from .absclient import AbstractConfigClient

__all__ = ['JsonFileConfigManager']


class JsonFileConfigManager(AbstractConfigClient):

    def __init__(self, file_path: str):
        self._file_path = file_path
        self._data = None

    def get_config(self, config_name: str, comp_name: str) -> dict:
        """
        Retreave named configuration for selected component from JSON file.

        :param config_name:     Configuration name string (not used in this particular derived class method).
        :param comp_name:       Component name string.
        :return:                Dictionary instance holding configuration parameters.
        """
        if self._data is None:
            with open(self._file_path, "r") as json_data_file:
                self._data = json.load(json_data_file)

        for cfg in self._data:
            if cfg["component"] == comp_name:
                return cfg['parameters']

        return {}

    def save_config(self, config_name: str, comp_name: str) -> None:
        """
        Save configuration to JSON file.

        :param config_name:     Configuration name string.
        :param comp_name:       Component name string.
        :return:                None
        """
        print("save_config() is not implemented.")
