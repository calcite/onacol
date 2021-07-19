import copy

from cerberus import Validator, schema_registry
from cerberus.schema import SchemaRegistry

from base import OnacolException


class SchemaException(OnacolException):
    pass


def _has_subelement(source_element, subelement):
    try:
        return subelement in source_element
    except TypeError:
        return False


def _get_subelement(source_element, subelement, default=None):
    try:
        return source_element.get(subelement, default)
    except AttributeError:
        return default


class ConfigSchema:

    OC_SCHEMA = "oc_schema"
    OC_SCHEMA_ID = "oc_schema_id"
    OC_DESC = "oc_desc"
    OC_DEFAULT = "oc_default"

    OC_TOKENS = [OC_SCHEMA, OC_SCHEMA_ID, OC_DESC, OC_DEFAULT]

    def __init__(self, schema_source):
        self._schema_source = schema_source
        self._schema = None
        self._defaults = None
        self._descriptions = None
        self._validator = None
        self._schema_registry = SchemaRegistry()
        self.load_schema(self._schema_source)

    @property
    def schema(self):
        return self._schema

    @property
    def schema_registry(self):
        return self._schema_registry

    @property
    def defaults(self):
        return self._defaults

    @property
    def descriptions(self):
        return self._descriptions

    def _element_is_leaf(self, source_element):
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

    def load_schema(self, schema_source):
        self._schema, self._defaults, self._descriptions = \
            self._process_schema_element(schema_source, top_level=True)
        # self._validator = Validator(self._schema)

    def _process_schema_element(self, schema_source, top_level=False):
        schema = None
        default = None
        description = None
        if self._element_is_leaf(schema_source):
            if _has_subelement(schema_source, self.OC_SCHEMA):
                schema = schema_source[self.OC_SCHEMA]
            else:
                schema = None

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
                    _schema, _default, _description = \
                        self._process_schema_element(v)
                    if _schema is not None:
                        schema["schema"][k] = _schema
                    default[k] = _default
                    description[k] = _description

            elif isinstance(schema_source, list):
                # Process list
                schema = {"type": "list", "schema": {}}
                default = []
                description = []
                i = 0
                for item in schema_source:
                    _schema, _default, _description = \
                        self._process_schema_element(item)
                    if (i == 0) and (_schema is not None):
                        schema["schema"] = _schema
                    default.append(_default)
                    description.append(description)
                    i += 1

            if _has_subelement(schema_source, self.OC_SCHEMA):
                if isinstance(schema_source[self.OC_SCHEMA], dict):
                    schema.update(schema_source[self.OC_SCHEMA])
                else:
                    schema["schema"] = schema_source[self.OC_SCHEMA]

            if _has_subelement(schema_source, self.OC_SCHEMA_ID):
                if schema_source[self.OC_SCHEMA_ID] == schema["schema"]:
                    raise SchemaException(
                        f"Schema self reference for {schema['schema']}")
                if schema["schema"]:
                    self._schema_registry.add(schema_source[self.OC_SCHEMA_ID],
                                              schema["schema"])

        # For top-level element, remove the type & schema declaration
        if top_level:
            schema = schema["schema"]

        return schema, default, description

    def _export_schema_element(self, schema_element, config_data):
        export = None
        if self._element_is_leaf(schema_element):
            if isinstance(schema_element, dict):
                for token in self.OC_TOKENS:
                    schema_element.pop(token, None)
            schema_element = config_data
        else:
            # It's just a branching to deeper dict or list
            if isinstance(schema_element, dict):
                for k, v in schema_element.items():
                    if k in self.OC_TOKENS:
                        schema_element.pop(k)
                        continue

                    self._export_schema_element(v, config_data[k])

            elif isinstance(schema_element, list):

                trim_length = 0
                for i, item in enumerate(schema_element):
                    try:
                        self._export_schema_element(item, config_data[i])
                    except KeyError:
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


