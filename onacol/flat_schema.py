"""
.. module: onacol.env_var
   :synopsis: Processing for bles.

.. moduleauthor:: Josef Nevrly <josef.nevrly@gmail.com>
"""
from functools import reduce
from typing import Any, NamedTuple
from enum import Enum
from collections import namedtuple
import operator
import json

from cerberus import Validator  # type: ignore

from .base import OnacolException


class UnknownConfigError(OnacolException):
    pass


class InvalidValueError(OnacolException):
    pass


class FlatValueType(Enum):
    VALUE = "val"
    LIST = "list"


FlatSchemaMetadata = namedtuple("FlatSchemaMetadata", "value_type data_type")


class FlatSchemaHandler:

    ENV_VAR_SEPARATOR_CHAR = "_"
    CLI_OPT_SEPARATOR_CHAR = "-"
    SEPARATOR = 2*ENV_VAR_SEPARATOR_CHAR

    def __init__(self, flat_schema: dict, env_var_prefix: str = ""):
        self._flat_schema = flat_schema
        self._prefix = env_var_prefix.lstrip(
            self.ENV_VAR_SEPARATOR_CHAR).upper() + self.ENV_VAR_SEPARATOR_CHAR

        # Initialize env_var identifier mapping from the flat_schema
        # The point of this mapping is, that there should be no limits on
        # how is the configuration schema defined, including config elements
        # that contain separator strings. With this limit, there is no way
        # how to make a two-way mapping from flat schema to real schema
        # and back. So, we need to always have one-way mapping from flat schema
        # to the real schema for both
        #   * env_vars (that are capitalized with prefix)
        #   * cli options (that may or may not be lowercase and have no prefix)
        self._env_var_mapping = {self._prefix +
                                 self.SEPARATOR.join(path).upper(): path
                                 for path, v in self._flat_schema.items()}
        self._cli_opt_mapping = {
            self.SEPARATOR.join(path).replace(self.ENV_VAR_SEPARATOR_CHAR,
                                              self.CLI_OPT_SEPARATOR_CHAR
                                              ): path
            for path, v in self._flat_schema.items()}

    @staticmethod
    def _get_config_value(config, config_path):
        return reduce(operator.getitem, config_path, config)

    def _get_mapped_path(self, mapping, path):
        try:
            return mapping[path]
        except KeyError:
            raise UnknownConfigError(
                f"No configuration exist for {path}")

    def _set_mapped_value(self, config, mapping, path, value):
        mapped_path = self._get_mapped_path(mapping, path)
        metadata = self._flat_schema[mapped_path]

        # Check whether the mapped path points to a value or list
        # If it's from the list, we assume the contents is a JSON encoded list
        if metadata.value_type == FlatValueType.LIST:
            try:
                converted_value = json.loads(value)
                if not isinstance(converted_value, list):
                    raise InvalidValueError(
                        f"Only values of type list expected for {path}")
            except json.JSONDecodeError as e:
                raise InvalidValueError(
                    f"Value {value} is not valid JSON: {str(e)}")
        else:
            # For values, we may try to coerce type conversion, because all
            # values may be string
            if isinstance(value, str) and metadata.data_type is not None:
                # Get possible conversion types from the Cerberos
                type_def = Validator.types_mapping[metadata.data_type]
                # try to convert value from string
                for val_type in type_def.included_types:
                    if isinstance(val_type, tuple):
                        # Somehow, the Cerberus types_mapping wraps int
                        # into an additional tuple...
                        val_type = val_type[0]
                    try:
                        converted_value = val_type(value)
                        break
                    except ValueError:
                        pass
                else:
                    converted_value = value
            else:
                converted_value = value

        self._get_config_value(config, mapped_path[:-1])[mapped_path[-1]] = \
            converted_value

    def _get_config_path_env_var(self, env_var_name):
        return self._get_mapped_path(self._env_var_mapping, env_var_name)

    def _get_config_path_cli_opt(self, cli_opt_name):
        return self._get_mapped_path(self._cli_opt_mapping, cli_opt_name)

    def get_config_from_env_var(self, config: dict, env_var_name: str) -> Any:
        return self._get_config_value(
            config, self._get_config_path_env_var(env_var_name))

    def get_config_from_cli_opt(self, config: dict, cli_opt_name: str) -> Any:
        return self._get_config_value(
            config, self._get_config_path_cli_opt(cli_opt_name))

    def set_config_from_env_var(self, config: dict,
                                env_var_name: str,
                                value: Any) -> None:
        """ Sets value in configuration provided as environment variable.

        :param config:  The configuration dict.
        :param env_var_name:  Environment variable name.
        :param value:  Environment variable value.
        """
        self._set_mapped_value(
            config, self._env_var_mapping, env_var_name, value)

    def set_config_from_cli_opt(self, config: dict,
                                cli_opt_name: str,
                                value: Any) -> None:
        """ Sets value in configuration provided as CLI optional argument.

        :param config:  The configuration dict.
        :param cli_opt_name:  CLI optional argument name.
        :param value:  CLI optional argument value.
        """
        self._set_mapped_value(
            config, self._cli_opt_mapping, cli_opt_name, value)

    def is_prefixed_env_var(self, env_var_name: str) -> bool:
        """ Checks if given environment variable has the specified prefix.

        :param env_var_name: Name of the environment variable.
        :return: True if env_var has specified prefix, False otherwise.
        """
        return env_var_name.startswith(self._prefix)

    def is_valid_cli_opt(self, cli_opt_name: str) -> bool:
        """ Check if CLI optional argument is a valid configuration name.

        :param cli_opt_name: CLI optional argument name.
        :return: True if valid, False otherwise.
        """
        try:
            self._get_config_path_cli_opt(cli_opt_name)
            return True
        except UnknownConfigError:
            return False

