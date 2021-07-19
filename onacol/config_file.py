from ruamel.yaml import YAML, YAMLError
from cascadict import CascaDict

from base import OnacolException
from config_schema import ConfigSchema

YAML_ACCESS = YAML()


class ConfigFileException(OnacolException):
    pass


class ConfigFileManager:

    def __init__(self, default_file, optional_file_locations=None):
        self._default_file = default_file
        self._config = None
        self._schema = None
        self._schema_yaml = None  # Stored separately to preserve comments
        self._optional_file_locations = optional_file_locations or []
        self.load_files()

    @property
    def default_config_file(self):
        return self._default_file

    @property
    def default_config(self):
        return self._schema.defaults if self.has_defaults else None

    @property
    def optional_config_files(self):
        return self._optional_file_locations

    @property
    def configuration(self):
        return self._config

    @property
    def config_schema(self):
        return self._schema if self.has_defaults else None

    @property
    def has_defaults(self):
        return self._default_file is not None

    def _load_yaml_file(self, yaml_file_path):
        try:
            with open(yaml_file_path) as yaml_file:
                return YAML_ACCESS.load(yaml_file)
        except YAMLError as ye:
            raise ConfigFileException(f"Cannot parse config file: {str(ye)}")
        except FileNotFoundError as fnf:
            raise ConfigFileException(f"Error reading file: {str(fnf)}")

    def load_files(self):
        self._schema = None
        self._config = None

        if self.has_defaults:
            self._schema_yaml = self._load_yaml_file(self._default_file)
            self._schema = ConfigSchema(self._schema_yaml)
            self._config = CascaDict(self._schema.defaults)

        for opt_file in self._optional_file_locations:
            if self._config is None:
                self._config = CascaDict(self._load_yaml_file(opt_file))
            else:
                self._config.cascade(self._load_yaml_file(opt_file))

    def save_with_schema(self, config, save_file):
        YAML_ACCESS.dump(
            self._schema.schema_to_yaml(self._schema_yaml, config),
            save_file
        )
