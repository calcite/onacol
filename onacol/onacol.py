"""
.. module: onacol.onacol
   :synopsis: Main module

.. moduleauthor:: Josef Nevrly <josef.nevrly@gmail.com>
"""
import os
from typing import List, TextIO, Any

from cerberus import Validator  # type: ignore
from cascadict import CascaDict  # type: ignore

from .config_file import ConfigFileHandler
from .flat_schema import FlatSchemaHandler

from .base import OnacolException


class ConfigValidationError(OnacolException):
    pass


class ConfigManager:

    def __init__(self, default_config_file_path: str,
                 optional_files: List[str] = None,
                 env_var_prefix: str = ""):
        """

        :param default_config_file_path: Path to the file with the default
                                         configuration with (optional)
                                         validation schema metadata.
        :param optional_files:   List of optional config files.
        :param env_var_prefix:   Prefix used for environment variables that
                                 shall be loaded as config.
        """
        self._file_handler = ConfigFileHandler(default_config_file_path,
                                               optional_files)
        self._flat_schema_handler = FlatSchemaHandler(
            self._file_handler.flat_schema, env_var_prefix=env_var_prefix)
        self._validator = None

        if self._file_handler.config_schema:
            self._validator = Validator(
                self._file_handler.config_schema.schema,
                schema_registry=self._file_handler.config_schema.schema_registry,
                allow_unknown=True
            )

    @property
    def config(self) -> CascaDict:
        """ The configuration dictionary. """
        return self._file_handler.configuration

    @config.setter
    def config(self, value: CascaDict):
        self._file_handler.configuration = value

    def validate(self):
        """ Validate the configuration.
        :return: None.
        :raises: :class:`onacol.ConfigValidationError` if configuration
                 is not valid.
        """
        if self._validator is None:
            return

        res = self._validator.validate(self.config)

        if res is False:
            raise ConfigValidationError(
                f"Invalid configuration: {self._validator.errors}")

    def _generate_config_file(self, config: dict, output_file: TextIO) -> None:
        self._file_handler.save_with_schema(config, output_file)

    def generate_config_example(self, output_file: TextIO) -> None:
        self._generate_config_file(self._file_handler.default_config,
                                   output_file)

    def export_current_config(self, output_file: TextIO) -> None:
        self._generate_config_file(self.config, output_file)

    def get_cli_opt_conf_value(self, cli_opt_name: str) -> None:
        return self._flat_schema_handler.get_config_from_cli_opt(
            self.config, cli_opt_name
        )

    def set_cli_opt_conf_value(self, cli_opt_name: str, value: Any) -> Any:
        self._flat_schema_handler.set_config_from_cli_opt(
            self.config, cli_opt_name, value
        )

    def get_env_var_conf_value(self, env_var_name: str) -> Any:
        return self._flat_schema_handler.get_config_from_env_var(
            self.config, env_var_name
        )

    def set_env_var_conf_value(self, env_var_name: str, value: Any) -> None:
        return self._flat_schema_handler.set_config_from_env_var(
            self.config, env_var_name, value
        )

    def merge_env_vars(self, env_var_list: list) -> None:
        """ Merge environment variables from the list with the current
            configuration.
            (Creates new layer in the layered config).

        :param env_var_list:  List of tuples (env_var_name, env_var_value).
        """
        self.config = self.config.cascade()
        for env_var_name, value in env_var_list:
            self.set_env_var_conf_value(env_var_name, value)

    def merge_cli_opts(self, cli_opt_list: list) -> None:
        """ Merge CLI optional arguments from the list with the
            current configuration.
            (Creates new layer in the layered config).

        :param cli_opt_list: List of tuples (cli_opt_name, cli_opt_value).
        """
        self.config = self.config.cascade()
        for cli_opt_name, value in cli_opt_list:
            self.set_cli_opt_conf_value(cli_opt_name, value)

    def config_from_env_vars(self) -> None:
        """ Parse current system's environment variables, merge those with
            valid prefix to the current configuration.
        """
        env_var_list = [(env_var_name, value) for env_var_name, value
                        in os.environ.items() if
                        self._flat_schema_handler.is_prefixed_env_var(
                            env_var_name)]
        self.merge_env_vars(env_var_list)

    def config_from_cli_opts(self, cli_opt_list: list) -> None:
        """ Parse provided CLI optional argument list, merge those with
            valid names to the current configuration.
        """
        parsed_cli_opt_list = [(cli_opt_name, value) for cli_opt_name, value
                        in cli_opt_list if
                        self._flat_schema_handler.is_valid_cli_opt(cli_opt_name)
                               ]
        self.merge_cli_opts(parsed_cli_opt_list)

    def config_from_file(self, file_path: str) -> None:
        """ Load configuration from additional file.
            Configuration will be merged on top of the default/existing config.

        :param file_path: Configuration file path.
        """
        self._file_handler.load_additional_file(file_path)

    def config_from_dict(self, config_dict: dict) -> None:
        """ Load configuration from a dictionary.
            Configuration will be merged on top of the default/existing config.

        :param config_dict:  Configuration dict.
        """
        self.config = self.config.cascade(config_dict)
