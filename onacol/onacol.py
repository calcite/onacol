"""Main module."""
import sys

from cerberus import Validator

from config_file import ConfigFileHandler

from base import OnacolException


class ConfigValidationError(OnacolException):
    pass


class ConfigManager:

    def __init__(self, default_config_file, optional_files=None):
        self._file_manager = ConfigFileHandler(default_config_file, optional_files)
        self._validator = None
        self._config = self._file_manager.configuration

        if self._file_manager.config_schema is not None:
            self._validator = Validator(
                self._file_manager.config_schema.schema,
                schema_registry=self._file_manager.config_schema.schema_registry,
                allow_unknown=True
            )

    def validate(self):
        if self._validator is None:
            return

        res = self._validator.validate(self._config)

        if res is False:
            raise ConfigValidationError(
                f"Invalid configuration: {self._validator.errors}")

    def generate_config_file(self, config, output_file):
        self._file_manager.save_with_schema(config, output_file)

    def generate_config_example(self, output_file):
        self.generate_config_file(self._file_manager.default_config,
                                  output_file)

if __name__ == "__main__":
    cm = ConfigManager(r"../tests/test_schema.yaml")
    print(cm._file_manager.config_schema.schema)
    print(cm._file_manager.config_schema.defaults)
    print(cm._config)
    print(cm._file_manager.config_schema.flat_schema)
    cm.validate()
    cm.generate_config_example(sys.stdout)
