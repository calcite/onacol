"""
.. module: onacol.config_file
   :synopsis: Classes and utilities for loading and saving of the configuration
                files.

.. moduleauthor:: Josef Nevrly <josef.nevrly@gmail.com>
"""
from typing import Union, List, TextIO

from ruamel.yaml import YAML, YAMLError
from cascadict import CascaDict

from base import OnacolException
from config_schema import ConfigSchema

YAML_ACCESS = YAML()


class ConfigFileException(OnacolException):
    pass


class ConfigFileHandler:

    def __init__(self, default_file_path: str,
                 optional_file_paths: Union[List[str], None] = None):
        self._default_file_path = default_file_path
        self._config = None
        self._schema = None
        self._schema_yaml = None  # Stored separately to preserve comments
        self._optional_file_paths = optional_file_paths or []
        self.load_files()

    @property
    def default_config_file(self) -> str:
        return self._default_file_path

    @property
    def default_config(self) -> Union[dict, None]:
        return self._schema.defaults if self.has_defaults else None

    @property
    def optional_config_files(self) -> List[str]:
        return self._optional_file_paths

    @property
    def configuration(self) -> dict:
        return self._config

    @property
    def config_schema(self) -> Union[dict, None]:
        return self._schema if self.has_defaults else None

    @property
    def has_defaults(self) -> bool:
        return self._default_file_path is not None

    @staticmethod
    def _load_yaml_file(yaml_file_path: str) -> dict:
        try:
            with open(yaml_file_path) as yaml_file:
                return YAML_ACCESS.load(yaml_file)
        except YAMLError as ye:
            raise ConfigFileException(f"Cannot parse config file: {str(ye)}")
        except FileNotFoundError as fnf:
            raise ConfigFileException(f"Error reading file: {str(fnf)}")

    def load_files(self) -> None:
        """ Load default and optional config file and parse them into the
            configuration.
        """
        self._schema = None
        self._config = None

        if self.has_defaults:
            self._schema_yaml = self._load_yaml_file(self._default_file_path)
            self._schema = ConfigSchema(self._schema_yaml)
            self._config = CascaDict(self._schema.defaults)

        for opt_file in self._optional_file_paths:
            if self._config is None:
                self._config = CascaDict(self._load_yaml_file(opt_file))
            else:
                self._config.cascade(self._load_yaml_file(opt_file))

    def save_with_schema(self, config: dict, save_file: TextIO) -> None:
        """ Save the configuration to the YAML file, keeping the original
            schema file form (including comments etc.).

        :param config: The configuration to be saved.
        :param save_file: Destination file-like (text) object.
        """
        # This dump converts None values to empty strings
        # (that is valid YAML 1.2)
        # Leaving as it is, if it becomes problem, here is a solution:
        # https://stackoverflow.com/a/44314840
        YAML_ACCESS.dump(
            self._schema.schema_to_yaml(self._schema_yaml, config),
            save_file
        )
