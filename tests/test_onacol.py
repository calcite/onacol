#!/usr/bin/env python

"""Tests for `onacol` package."""


import unittest
import os
from pathlib import Path

from ruamel.yaml import YAML

from onacol import ConfigManager, ConfigValidationError
from onacol.config_file import ConfigFileHandler, ConfigFileException
from onacol.config_schema import SchemaException
from onacol.flat_schema import UnknownConfigError, InvalidValueError


TESTS_DIR = Path(__file__).parent


DEFAULT_TEST_FILE = TESTS_DIR / "test_yamls/test_schema.yaml"
DEFAULT_DEFAULTS_FILE = TESTS_DIR / "test_yamls/test_defaults.yaml"
INVALID_YAML_DEFAULT_TEST_FILE = TESTS_DIR / "test_yamls/test_schema_invalid_yaml.yaml"
SELF_REFERENTIAL_DEFAULT_TEST_FILE = TESTS_DIR / "test_yamls/test_schema_self_reference.yaml"
TEST_OVERLAY_1 = TESTS_DIR / "test_yamls/test_overlay_1.yaml"
TEST_OVERLAY_LONGER_LIST = TESTS_DIR / "test_yamls/test_overlay_longer_list.yaml"
TEST_OVERLAY_SHORTER_LIST = TESTS_DIR / "test_yamls/test_overlay_shorter_list.yaml"
TEST_OVERLAY_INVALID_VALUE = TESTS_DIR / "test_yamls/test_overlay_invalid_value.yaml"
NONEXISTENT_OVERLAY = TESTS_DIR / "test_yamls/nonexistent_overlay.yaml"
TMP_FILE = TESTS_DIR / "schema_dump.tmp"

YAML_ACCESS = YAML()


class TestConfigFileHandler(unittest.TestCase):
    """ Tests also ConfigSchema (easier that way)."""

    def test_nominal(self):
        fh = ConfigFileHandler(DEFAULT_TEST_FILE)
        self.assertEqual(fh.default_config_file, DEFAULT_TEST_FILE)

    def test_schema_extraction(self):
        fh = ConfigFileHandler(DEFAULT_TEST_FILE)
        with open(DEFAULT_DEFAULTS_FILE) as yaml_file:
            defaults = YAML_ACCESS.load(yaml_file)

        self.assertDictEqual(fh.default_config, defaults)

    def test_no_defaults(self):
        fh = ConfigFileHandler(None)
        self.assertIsNone(fh.default_config_file)
        self.assertFalse(fh.has_defaults)

    def test_no_default_load_additional(self):
        fh = ConfigFileHandler(None)
        fh.load_additional_file(DEFAULT_TEST_FILE)

    def test_invalid_defaults(self):
        with self.assertRaises(ConfigFileException):
            fh = ConfigFileHandler(INVALID_YAML_DEFAULT_TEST_FILE)

    def test_self_referential_schema(self):
        with self.assertRaises(SchemaException):
            fh = ConfigFileHandler(SELF_REFERENTIAL_DEFAULT_TEST_FILE)

    def test_optional_files(self):
        optional_configs = [TEST_OVERLAY_1, NONEXISTENT_OVERLAY]

        with self.assertLogs("onacol", level="WARNING") as lm:
            fh = ConfigFileHandler(DEFAULT_TEST_FILE, optional_configs)

        self.assertEqual(lm.output,
                         [f"WARNING:onacol:Optional config file at {TESTS_DIR}/test_yamls/nonexistent_overlay.yaml not found."])
        self.assertEqual(fh.optional_config_files, optional_configs)

    def test_save_with_schema(self):
        fh = ConfigFileHandler(DEFAULT_TEST_FILE)
        with open(TMP_FILE, "w") as export_file:
            fh.save_with_schema(fh.configuration, export_file)

        with open(TMP_FILE) as yaml_file:
            dump = YAML_ACCESS.load(yaml_file)

        with open(DEFAULT_DEFAULTS_FILE) as yaml_file:
            orig = YAML_ACCESS.load(yaml_file)

        self.assertDictEqual(dump, orig)

    def test_save_with_schema_longer_list(self):
        fh = ConfigFileHandler(DEFAULT_TEST_FILE, [TEST_OVERLAY_LONGER_LIST])

        # print(fh.configuration["sensor_config"]["sensors"])

        with open(TMP_FILE, "w") as export_file:
            fh.save_with_schema(fh.configuration, export_file)

        with open(TMP_FILE) as yaml_file:
            dump = YAML_ACCESS.load(yaml_file)

        self.assertListEqual(dump["sensor_config"]["sensors"],
                             fh.configuration["sensor_config"]["sensors"])

    def test_save_with_schema_shorter_list(self):
        fh = ConfigFileHandler(DEFAULT_TEST_FILE, [TEST_OVERLAY_SHORTER_LIST])

        # print(fh.configuration["sensor_config"]["sensors"])

        with open(TMP_FILE, "w") as export_file:
            fh.save_with_schema(fh.configuration, export_file)

        with open(TMP_FILE) as yaml_file:
            dump = YAML_ACCESS.load(yaml_file)

        self.assertListEqual(dump["sensor_config"]["sensors"],
                             fh.configuration["sensor_config"]["sensors"])


class TestConfigManagerInitialization(unittest.TestCase):
    """Tests for `onacol` package."""

    def setUp(self):
        """Set up test fixtures, if any."""
        pass

    def tearDown(self):
        """Tear down test fixtures, if any."""
        pass

    def test_nominal(self):
        cm = ConfigManager(DEFAULT_TEST_FILE, env_var_prefix="ONAC")

    def test_no_defaults(self):
        cm = ConfigManager(None, env_var_prefix="ONAC")

    def test_no_defaults_validation(self):
        cm = ConfigManager(None, env_var_prefix="ONAC")
        cm.config_from_file(DEFAULT_DEFAULTS_FILE)
        cm.validate()


class TestConfigManager(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures, if any."""
        self._cm = ConfigManager(DEFAULT_TEST_FILE, env_var_prefix="ONAC")

    def tearDown(self):
        """Tear down test fixtures, if any."""
        pass

    def test_validation_pass(self):
        CONFIG_DICT = {"bottom_sensor": {"preactivation_timeout": 3}}
        self._cm.config_from_dict(CONFIG_DICT)
        self._cm.validate()
        self.assertEqual(
            self._cm.config["bottom_sensor"]["preactivation_timeout"],
            CONFIG_DICT["bottom_sensor"]["preactivation_timeout"]
        )

    def test_validation_failure(self):
        self._cm.config_from_file(TEST_OVERLAY_INVALID_VALUE)
        with self.assertRaises(ConfigValidationError):
            self._cm.validate()

    def test_generate_config_example(self):
        with open(TMP_FILE, "w") as dump_file:
            self._cm.generate_config_example(dump_file)

    def test_export_current_config(self):
        with open(TMP_FILE, "w") as dump_file:
            self._cm.export_current_config(dump_file)

    def test_env_var_config(self):
        # Add some env var
        PREAC_TIMEOUT = 6
        os.environ["ONAC_BOTTOM_SENSOR__PREACTIVATION_TIMEOUT"] = str(PREAC_TIMEOUT)
        self._cm.config_from_env_vars()
        self._cm.validate()
        self.assertEqual(
            self._cm.config["bottom_sensor"]["preactivation_timeout"],
            PREAC_TIMEOUT)

    def test_unknown_env_var(self):
        os.environ["ONAC_BOTTOM_SENSOR__SOMETHING_STUPID"] = "foobar"
        with self.assertRaises(UnknownConfigError):
            self._cm.config_from_env_vars()
        del os.environ["ONAC_BOTTOM_SENSOR__SOMETHING_STUPID"]

    def test_env_var_json(self):
        os.environ["ONAC_SENSOR_CONFIG__SENSORS"] = \
            '[{"id": 2, "name": "json_sensor", "min_trigger_limit": 65, "max_trigger_limit": 200}]'
        self._cm.config_from_env_vars()
        self._cm.validate()
        self.assertEqual(
            self._cm.config["sensor_config"]["sensors"][0]["name"],
            "json_sensor")
        del os.environ["ONAC_SENSOR_CONFIG__SENSORS"]

    def test_env_var_json_invalid(self):
        os.environ["ONAC_SENSOR_CONFIG__SENSORS"] = \
            '[{"id": 2, "name": "json_sensor", "min_trigger_limit": 65, "max_trigger_limit": 200]'
        with self.assertRaises(InvalidValueError):
            self._cm.config_from_env_vars()
        del os.environ["ONAC_SENSOR_CONFIG__SENSORS"]

    def test_env_var_json_non_list(self):
        os.environ["ONAC_SENSOR_CONFIG__SENSORS"] = \
            '{"id": 2, "name": "json_sensor", "min_trigger_limit": 65, "max_trigger_limit": 200}'
        with self.assertRaises(InvalidValueError):
            self._cm.config_from_env_vars()
        del os.environ["ONAC_SENSOR_CONFIG__SENSORS"]

    def test_cli_opt_config(self):
        PREAC_TIMEOUT = 8
        CHANNEL = "can314"
        ADDR = "127.0.0.1"
        CLI_OPTS = [
            ("bottom-sensor--preactivation-timeout", str(PREAC_TIMEOUT)),
            ("can-bus--sensor-can--channel", "can314"),
            ("ui--addr", ADDR)
        ]
        self._cm.config_from_cli_opts(CLI_OPTS)
        self._cm.validate()
        self.assertEqual(
            self._cm.config["bottom_sensor"]["preactivation_timeout"],
            PREAC_TIMEOUT)
        self.assertEqual(
            self._cm.config["can_bus"]["sensor_can"]["channel"], CHANNEL)
        self.assertEqual(
            self._cm.config["ui"]["addr"], ADDR)

    def test_cli_args_config(self):
        PREAC_TIMEOUT = 8
        CHANNEL = "can314"
        ADDR = "127.0.0.1"
        CLI_ARGS = ["--random-single-flag",
                    "--bottom-sensor--preactivation-timeout",
                    str(PREAC_TIMEOUT),
                    "--two-arg-option",
                    "2", "3",
                    "--can-bus--sensor-can--channel",
                    "can314",
                    "--ui--addr",
                    ADDR,
                    "--final-trailing-flag"
                    ]

        self._cm.config_from_cli_args(CLI_ARGS)
        self._cm.validate()
        self.assertEqual(
            self._cm.config["bottom_sensor"]["preactivation_timeout"],
            PREAC_TIMEOUT)
        self.assertEqual(
            self._cm.config["can_bus"]["sensor_can"]["channel"], CHANNEL)
        self.assertEqual(
            self._cm.config["ui"]["addr"], ADDR)

    def test_cli_opt_bad_conversion(self):
        RESET_INTERVAL = 30.1
        CLI_OPTS = [
            ("control-config--sensor-reset-interval", str(RESET_INTERVAL)),
        ]
        self._cm.config_from_cli_opts(CLI_OPTS)
        with self.assertRaises(ConfigValidationError):
            self._cm.validate()

    def test_unknown_cli_opt(self):
        CLI_OPTS = [("bottom-sensor--something-stupid", "foobar")]
        self._cm.config_from_cli_opts(CLI_OPTS)

    def test_get_cli_opt_config_value(self):
        val = self._cm.get_cli_opt_conf_value("bottom-sensor--preactivation-timeout")
        self.assertEqual(
            val, self._cm.config["bottom_sensor"]["preactivation_timeout"]
        )

    def test_get_env_var_config_value(self):
        val = self._cm.get_env_var_conf_value(
            "ONAC_BOTTOM_SENSOR__PREACTIVATION_TIMEOUT")
        self.assertEqual(
            val, self._cm.config["bottom_sensor"]["preactivation_timeout"]
        )








