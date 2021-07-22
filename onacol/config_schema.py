"""
.. module: onacol.config_schema
   :synopsis: Classes and utilities for parsing and manipulation of the
                configuration schema.

.. moduleauthor:: Josef Nevrly <josef.nevrly@gmail.com>
"""
from typing import Any, List, Union
import copy

from cerberus.schema import SchemaRegistry  # type: ignore

from .base import OnacolException
from .flat_schema import FlatValueType, FlatSchemaMetadata


class SchemaException(OnacolException):
    pass


def _has_subelement(source_element: Any, subelement: Any) -> bool:
    """ Fail-safe check if sub-element is part of the source element.
    """
    try:
        return (subelement in source_element)
    except TypeError:
        return False


# def _get_subelement(source_element: Any,
#                     subelement: Any,
#                     default: Any = None) -> Any:
#     """ Get sub-element from the source element. If not possible, gracefully
#         return default value.
#     """
#     try:
#         return source_element.get(subelement, default)
#     except AttributeError:
#         return default


class ConfigSchema:

    OC_SCHEMA = "oc_schema"
    OC_SCHEMA_ID = "oc_schema_id"
    OC_DESC = "oc_desc"
    OC_DEFAULT = "oc_default"

    # All yaml tokens used for onacol schema metadata.
    # Note: OC_DESC is to collect descriptions. This feature is not used in the
    # current API, but is kept there in case...
    OC_TOKENS = [OC_SCHEMA, OC_SCHEMA_ID, OC_DESC, OC_DEFAULT]

    def __init__(self, schema_source: dict):
        """
        :param schema_source: Configuration schema dictionary.
        """
        self._schema_source: dict = schema_source
        self._schema: dict = {}
        self._flat_schema: dict = {}  # Used for ENV_VAR list
        self._defaults: dict = {}
        self._descriptions: dict = {}
        self._validator = None
        self._schema_registry = SchemaRegistry()
        self.parse_schema(self._schema_source)

    def __bool__(self):
        return bool(self._schema)

    @property
    def schema(self) -> dict:
        """ Configuration schema.
        """
        return self._schema

    @property
    def flat_schema(self) -> dict:
        """ Flattened configuration schema
            (used for mapping environment variables).
        """
        return self._flat_schema

    @property
    def schema_registry(self) -> SchemaRegistry:
        """ Cerberus SchemaRegistry object used for configuration validation.
        """
        return self._schema_registry

    @property
    def defaults(self) -> dict:
        """ Configuration default values. """
        return self._defaults

    # @property
    # def descriptions(self) -> dict:
    #     """ Config item descriptions (not used in current version.)"""
    #     return self._descriptions

    def _element_is_leaf(self, source_element: Any) -> bool:
        """ Check if current configuration element is a leaf in terms of
            configuration tree traversal (i.e. it has no deeper levels).
        """
        # Leaf element means it either just has a value, or it contains
        # dict that is purely onacol related metadata
        if isinstance(source_element, dict):
            # Check if it has only onacol metadata
            for k in source_element.keys():
                if k not in self.OC_TOKENS:
                    return False
            return True
        elif isinstance(source_element, list):
            return False
        else:
            # It's just a value
            return True

    def parse_schema(self, schema_source: dict):
        """ Parse default configuration including schema metadata.
            During parsing, the schema for validation, default configuration
            values and flattened schema for environment variable parsing is
            processed.
        """
        self._flat_schema = {}

        # No meaning parsing empty schema
        if not schema_source:
            return

        self._schema, self._defaults, self._descriptions = \
            self._process_schema_element(schema_source, [], top_level=True)

    def _process_schema_element(self, schema_source: Any,
                                document_path: Union[List[str], None],
                                top_level: bool=False) -> tuple:
        """ Recursively parse given configuration element.

        :param schema_source:  Element of the configuration schema.
        :param document_path:  List of keys marking element's path
                                in the configuration hierarchy or None for
                                processing leaf elements.
        :param top_level:      Flag for identifying top-level element
                                (root of the configuration tree).
        :return:  Tuple (schema, defaults, description) with parsed elements of
                    schema, default values and element descriptions.
                    Element descriptions are not used in the current version
                    of the library.
        """
        schema = None  # type: ignore
        default = None
        description = None
        if self._element_is_leaf(schema_source):
            if _has_subelement(schema_source, self.OC_SCHEMA):
                schema = schema_source[self.OC_SCHEMA]
            else:
                schema = None

            # Register this path as possible env_var vector
            if document_path is not None:
                self._flat_schema[tuple(document_path)] = FlatSchemaMetadata(
                    FlatValueType.VALUE,
                    schema.get("type") if schema else None
                )

            # Process default value
            try:
                default = schema_source[self.OC_DEFAULT]
            except (KeyError, TypeError):
                default = schema_source

            # If description is present, put it in the description map
            try:
                description = schema_source[self.OC_DESC]
            except (KeyError, TypeError):
                description = None
        else:
            # It's just a branching to deeper dict or list
            if isinstance(schema_source, dict):

                # Process dict
                schema = {"type": "dict", "schema": {}}
                default = {}
                description = {}
                for k, v in schema_source.items():
                    if k in self.OC_TOKENS:
                        continue

                    # We will be doing further branching
                    if document_path is not None:
                        d_path = document_path.copy()
                        d_path.append(k)
                    else:
                        d_path = None   # type: ignore

                    _schema, _default, _description = \
                        self._process_schema_element(
                            v, d_path)

                    if _schema is not None:
                        schema["schema"][k] = _schema
                    default[k] = _default
                    description[k] = _description

            elif isinstance(schema_source, list):
                # Lists cannot be expanded as env_var names, so just
                # register this path as possible env_var vector
                if document_path is not None:
                    self._flat_schema[tuple(document_path)] = \
                        FlatSchemaMetadata(FlatValueType.LIST, None)

                # Process list
                schema = {"type": "list", "schema": {}}
                default = []
                description = []
                i = 0
                for item in schema_source:
                    _schema, _default, _description = \
                        self._process_schema_element(item, None)
                    if (i == 0) and (_schema is not None):
                        schema["schema"] = _schema
                    default.append(_default)
                    description.append(description)
                    i += 1

            if _has_subelement(schema_source, self.OC_SCHEMA):
                if isinstance(schema_source[self.OC_SCHEMA], dict):
                    schema.update(schema_source[self.OC_SCHEMA])  # type: ignore
                else:
                    schema["schema"] = schema_source[self.OC_SCHEMA]  # type: ignore

            if _has_subelement(schema_source, self.OC_SCHEMA_ID):
                if schema_source[self.OC_SCHEMA_ID] == schema["schema"]:  # type: ignore
                    raise SchemaException(
                        f"Schema self reference for {schema['schema']}")  # type: ignore
                if schema["schema"]:  # type: ignore
                    self._schema_registry.add(schema_source[self.OC_SCHEMA_ID],
                                              schema["schema"])  # type: ignore

        # For top-level element, remove the type & schema declaration
        if top_level:
            schema = schema["schema"]  # type: ignore

        return schema, default, description

    def _export_schema_element(self, schema_element: Any,
                               config_data: Any) -> Any:
        """ Recursively parse through the schema and current config to generate
            YAML file that retains the format of the default config file
            (including comments etc.) but contains the current config data.

        :param schema_element:  Element of the configuration schema.
        :param config_data:     Element of the current configuration, mathcing
                                element of the configuration schema.
        :return: Element of the final config file export.
        """
        if self._element_is_leaf(schema_element):
            return config_data
        else:
            # It's just a branching to deeper dict or list
            pop_list = []
            if isinstance(schema_element, dict):
                for k, v in schema_element.items():
                    if k in self.OC_TOKENS:
                        pop_list.append(k)
                        continue

                    schema_element[k] = \
                        self._export_schema_element(v, config_data[k])

                for k in pop_list:
                    schema_element.pop(k)

            elif isinstance(schema_element, list):

                trim_length = 0
                for i, item in enumerate(schema_element):
                    try:
                        schema_element[i] = \
                            self._export_schema_element(item, config_data[i])
                    except IndexError:
                        trim_length += 1

                # Trim the end or append extra config
                if trim_length > 0:
                    for i in range(trim_length):
                        schema_element.pop()
                else:
                    len_schema = len(schema_element)
                    len_config = len(config_data)
                    if len_schema < len_config:
                        for i in range(len_schema, len_config):
                            schema_element.append(config_data[i])

            return schema_element

    def schema_to_yaml(self, schema_yaml, config):
        """ Strips original schema document of schema metadata, replacing them
            with config values.

        :param schema:  Schema dict (as generated by Ruamel YAML)
        :param config:  Configuration dict.
        :return:  Schema dict updated by the configuration dict and stripped of
                    the Onacol metadata.
        """

        temp = copy.deepcopy(schema_yaml)
        self._export_schema_element(temp, config)
        return temp


