"""
.. module: onacol.config_file
   :synopsis: Classes and utilities for loading and saving of the configuration
                files.

.. moduleauthor:: Josef Nevrly <josef.nevrly@gmail.com>
"""
from typing import Union, List, TextIO
import logging

from ruamel.yaml import YAML, YAMLError
from cascadict import CascaDict  # type: ignore

from .base import OnacolException
from .config_schema import ConfigSchema

YAML_ACCESS = YAML()

logger = logging.getLogger("onacol")


class ConfigFileException(OnacolException):
    pass


class ConfigFileHandler:

    def __init__(self, default_file_path: str,
                 optional_file_paths: Union[List[str], None] = None):
        """

        :param default_file_path:   Path with default configuration file that
                                    also defines the configuration schema.
        :param optional_file_paths: List of additional/optional configuration
                                    files that will be merged on top of the
                                    default configuration file.
        """
        self._default_file_path = default_file_path
        self._config = CascaDict({})
        self._schema: ConfigSchema = ConfigSchema({})
        self._schema_yaml: dict = {}  # Stored separately to preserve comments
        self._optional_file_paths = optional_file_paths or []
        self.load_files()

    @property
    def default_config_file(self) -> str:
        return self._default_file_path

    @property
    def default_config(self) -> dict:
        return self._schema.defaults

    @property
    def optional_config_files(self) -> List[str]:
        return self._optional_file_paths

    @property
    def configuration(self) -> dict:
        return self._config

    @configuration.setter
    def configuration(self, value: dict):
        self._config = value

    @property
    def config_schema(self) -> ConfigSchema:
        return self._schema

    @property
    def flat_schema(self) -> dict:
        return self._schema.flat_schema

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
        # except FileNotFoundError as fnf:
        #     raise ConfigFileException(f"Error reading file: {str(fnf)}")

    def load_files(self) -> None:
        """ Load default and optional config file and parse them into the
            configuration.
        """
        if self.has_defaults:
            self._schema_yaml = self._load_yaml_file(self._default_file_path)
            self._schema = ConfigSchema(self._schema_yaml)
            self._config = CascaDict(self._schema.defaults)
        else:
            self._config = CascaDict({})
            self._schema = ConfigSchema({})

        for opt_file in self._optional_file_paths:
            try:
                self.load_additional_file(opt_file)
            except FileNotFoundError:
                logger.warning("Optional config file at %s not found.",
                               opt_file)

    def load_additional_file(self, file_path):
        """ Load additional config file. If previous config is defined, it will
            be merged on top of the previous config.
        :param file_path:  Config file path.
        """
        if self._config:
            self._config = self._config.cascade(self._load_yaml_file(file_path))
        else:
            self._config = CascaDict(self._load_yaml_file(file_path))

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
