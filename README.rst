=============================================
ONACOL (Oh No! Another COnfiguration Library)
=============================================

.. image:: https://badge.fury.io/py/onacol.svg
        :target: https://badge.fury.io/py/onacol

.. image:: https://github.com/calcite/onacol/actions/workflows/test.yaml/badge.svg?branch=main
        :target: https://github.com/calcite/onacol/actions/workflows/test.yaml

.. image:: https://readthedocs.org/projects/onacol/badge/?version=latest
        :target: https://onacol.readthedocs.io/en/latest/?version=latest
        :alt: Documentation Status

.. image:: https://coveralls.io/repos/github/calcite/onacol/badge.svg?branch=main
        :target: https://coveralls.io/github/calcite/onacol?branch=main
        :alt: Test coverage Status

.. image:: https://img.shields.io/lgtm/grade/python/g/calcite/onacol.svg?logo=lgtm&logoWidth=18
        :target: https://lgtm.com/projects/g/calcite/onacol/context:python
        :alt: Language grade: Python

.. image:: https://img.shields.io/pypi/pyversions/onacol
        :alt: PyPI - Python Version

Onacol is a low-opinionated configuration management library with following
features:

* YAML (=structured and hierarchical) configuration file support
* Environment variables support (explicit and implicit)
* CLI arguments support
* Configuration merging/overwriting/layering
* Parameter validation (via Cerberus_)
* Configuration schema, documentation and default values are defined in
  single YAML -> No code schema.
* Minimal dependencies

Comparison with other Python configuration libraries/frameworks
---------------------------------------------------------------

As the library name suggests, author is painfully aware this is not a unique
solution to the problem of application configuration. However, in the plethora
of existing solutions, none was completely fulfilling the features/requirements
mentioned above. So, with great reluctance,
`I had to make my own <https://xkcd.com/927/>`_.

Following table lists known/popular configuration frameworks and their
features relative to Onacol, but not comparing other features that some of those
libraries have and Onacol doesn't, so check them out - you may find it suits
your need better.


.. list-table:: Popular configuration framework comparison
    :widths: 30 10 10 10 10 10 10
    :header-rows: 1

    * - Framework
      - YAML
      - ENV vars
      - CLI args
      - Merging
      - Validation
      - No code schema
    * - Hydra_
      - ✔️
      - ✔️
      - ❓
      - ✔️
      - ✔️
      - ✖️
    * - Pydantic_
      - ❓
      - ❓
      - ✔️
      - ✔️
      - ✔️
      - ✖️
    * - Dynaconf_
      - ✔️
      - ❓
      - ✔️
      - ✔️
      - ✔️
      - ✖️
    * - python-dotenv_
      - ✖️
      - ✔️
      - ✖️
      - ✖️
      - ✖️
      - ✖️
    * - `Gin Config`_
      - ❓
      - ❓
      - ❓
      - ❓
      - ✔️
      - ✖️
    * - `Python Decouple`_
      - ✖️
      - ✖️
      - ✔️
      - ✔️
      - ✖️
      - ✖️
    * - OmegaConf_
      - ✔️
      - ✔️
      - ✔️
      - ✔️
      - ✔️
      - ✖️
    * - Confuse_
      - ✔️
      - ✔️
      - ❓
      - ✔️
      - ✔️
      - ✖️
    * - Everett_
      - ✔️
      - ✔️
      - ✔️
      - ❓
      - ✔️
      - ✖️
    * - parse_it_
      - ✔️
      - ✔️
      - ✔️
      - ✔️
      - ❓
      - ✖️
    * - Grift_
      - ✖️
      - ✖️
      - ✖️
      - ❓
      - ✔️
      - ✖️
    * - profig_
      - ✖️
      - ✔️
      - ✖️
      - ❓
      - ✔️
      - ✖️
    * - tweak_
      - ✔️
      - ✖️
      - ✖️
      - ✔️
      - ✖️
      - ✖️
    * - Bison_
      - ✔️
      - ❓
      - ✔️
      - ✔️
      - ✔️
      - ✖️
    * - Config-Man_
      - ✖️
      - ✔️
      - ✔️
      - ❓
      - ✔️
      - ✖️
    * - figga_
      - ✔️
      - ✖️
      - ✔️
      - ❓
      - ✖️
      - ✖️
    * - **Onacol**
      - ✔️
      - ✔️
      - ✔️
      - ✔️
      - ✔️
      - ✔️

Installation
------------

As usually with pip::

    $ pip install onacol

Usage
-----

Default configuration file & schema
+++++++++++++++++++++++++++++++++++

The whole point of this library is the definition of both default configuration
and configuration schema in one YAML file (i.e. single source of configuration
truth).

Let's start with a simple ``default_config.yaml`` file that is part of an example
application's package. This example file contains default values for the
configuration.

.. code-block:: yaml

    general:
        # Logging level for this application.
        log_level: INFO

    ui:
        # Address and port of the UI webserver
        addr: 0.0.0.0
        port: 8888

    sensors:
        sensor_reset_interval: 30.0  # Sensor reset interval in seconds
        connected_units:
            - id: 0                     # Sensor ID <0, 16>
              name: "Basic sensor"
              min_trigger_limit: 30     # Minimal triggering limit [cm]
              max_trigger_limit: 120    # Maximal triggering limit [cm]
            - id: 1
              name: "Additional sensor"
              min_trigger_limit: 40
              max_trigger_limit: 100

This file can be used as it is. However, we can add a schema definition to the
structure, that will allow parameter validation and automatic type conversion.

This is done by adding metadata to the YAML structure. Following metadata are
recognized by Onacol:

* ``oc_schema``: Cerberus_ validator/schema definitions.
* ``oc_default``: Default value (if metadata are attached to the YAML element, it
  can no longer bear the value directly).
* ``oc_schema_id``: Definition of a schema reference (see
  `Repeating schema elements`_)

Schema metadata are NOT MANDATORY. We can only provide them to parameters for
which we think validation (or type conversion) may be useful.

.. code-block:: yaml

    general:
        # Logging level for this application.
        log_level: INFO

    ui:
        # Address and port of the UI webserver
        addr:
            oc_default: 0.0.0.0
            oc_schema:
                type: string
                regex: "^(?:[0-9]{1,3}\\.){3}[0-9]{1,3}$"

        port:
            oc_default: 8888
            oc_schema:
                type: integer

    sensors:
        sensor_reset_interval:          # Sensor reset interval in seconds
            oc_default: 30.0
            oc_schema:
                type: float
                min: 0.0
                max: 100.0
        connected_units:
            - id:                       # Sensor ID <0, 16>
                oc_default: 0
                oc_schema:
                    type: integer
                    min: 0
                    max: 16
              name: "Basic sensor"
              min_trigger_limit:        # Minimal triggering limit [cm]
                oc_default: 30
                oc_schema:
                    type: integer
                    min: 0
                    max: 200
              max_trigger_limit:        # Maximal triggering limit [cm]
                oc_default: 120
                oc_schema:
                    type: integer
                    min: 0
                    max: 200
            - id: 1
              name: "Additional sensor"
              min_trigger_limit: 40
              max_trigger_limit: 100

Note that for list definitions, schema is added only to the first element of the
list. Other elements will be validated based on the first element's schema.


Loading and validating configuration in an application
++++++++++++++++++++++++++++++++++++++++++++++++++++++

Onacol is used by the application via the ``ConfigManager`` instance.
``ConfigManager`` can load configurations from multiple sources (files,
command line optional arguments, environment variables), but does not do it
automatically - the sources and order is up to the app implementation.

A complete minimalistic example of an application (using Click_ as a CLI
framework):

.. code-block:: python

    """Console script for onacol_test."""
    import sys
    import click
    import pkg_resources

    from onacol import ConfigManager

    # Localizing the defaults/schema configuration YAML in the package
    DEFAULT_CONFIG_FILE = pkg_resources.resource_filename("onacol_test",
                                                          "default_config.yaml")

    # This must be here in order to retrieve args and options
    # that are not Click related (see https://stackoverflow.com/a/32946412)
    @click.command(context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True
    ))
    @click.pass_context
    # The rest is the usual Click stuff
    @click.option("--config", type=click.Path(exists=True), default=None,
                  help="Path to the configuration file.")
    @click.option("--get-config-template", type=click.File("w"), default=None,
                  help="Write default configuration template to the file.")
    def main(ctx, config, get_config_template):
        # Wrap optional config file into a list
        user_config_file = [config] if config else []

        # Instantiate config_manager
        config_manager = ConfigManager(DEFAULT_CONFIG_FILE,
                                       env_var_prefix="OCTEST",
                                       optional_files=user_config_file
                                       )

        # Generate configuration for the --get-config-template option
        # Then finish the application
        if get_config_template:
            config_manager.generate_config_example(get_config_template)
            return

        # Load (implicit) environment variables
        config_manager.config_from_env_vars()

        # Parse all extra command line options
        config_manager.config_from_cli_args(ctx.args)

        # Validate the config
        config_manager.validate()

        # Finally, let's review interesting bits of the config
        print("---------<Application configuration>-------------")
        print(f"Log level: {config_manager.config['general']['log_level']}")
        print(f"UI: {config_manager.config['ui']['addr']} "
              f"(port: {config_manager.config['ui']['port']})")
        print(f"Sensor reset interval: "
              f"{config_manager.config['sensors']['sensor_reset_interval']}")
        print(f"Sensors:")
        for sensor in config_manager.config["sensors"]["connected_units"]:
            print(f"\t {sensor['name']} [{sensor['id']}] \t Trigger limits: "
                  f"({sensor['min_trigger_limit']}, {sensor['max_trigger_limit']})")


    if __name__ == "__main__":
        sys.exit(main())  # pragma: no cover

In this example, the application is bundling the ``default_config.yaml`` from
the examples above as the default configuration/schema file.
Then it accepts additional configuration file via command
option, and on the top it uses the environment variables and additional
configuration via command line options. Configuration from all sources
are layered/overwritten on the top of the current configuration.

As you can see in the code, the sources of configuration as well as their
prioritization depend on the order of which ``ConfigManager`` methods are
called, there is no default and even the validation must be called explicitly.

Configuration using additional file
+++++++++++++++++++++++++++++++++++

In the example app, additional config file are loaded with the ``--config``
optional command line argument, that is used in the ``ConfigManager``'s
``optional_files`` init option. There is also the ``ConfigManager.config_from_file``
method to do this anytime after init.

Let's use the following config file (``my_config.yaml``):

.. code-block:: yaml

    general:
        log_level: DEBUG

    ui:
        port: 127.0.0.1

And load it with the app::

    $ python main.py --config my_config.yaml
    ---------<Application configuration>-------------
    Log level: DEBUG
    UI: 127.0.0.1 (port: 8888)
    Sensor reset interval: 30.0
    Sensors:
             Basic sensor [0]        Trigger limits: (30, 120)
             Additional sensor [1]   Trigger limits: (40, 100)

As you can see, the relevant default config parameters have been overwritten,
the others stay default. This layering works over configuration dicts of
unlimited depth, but does not work with lists (by design).

Configuration using environment variables
+++++++++++++++++++++++++++++++++++++++++

There are two ways how to use environment variables with Onacol:

* **Implicit way** - Onacol detects environment variables with defined prefix
  and use them to overwrite current configuration.
* **Explicit way** - environment variables are referenced in the configuration
  files and Onacol resolves the references upon loading the file.

Using environment variables implicitly
**************************************

In the example app source, we defined the ``env_var_prefix`` with value
``OCTEST``. Using the ``ConfigManager.config_from_env_vars`` method  will then
make Onacol parse existing environment variables for names
starting with the chosen prefix, and then use the rest of the name as path for
the configuration structure (using uppercase and ``__`` as the level separator).

Let's continue with the previous example::

    $ export OCTEST_SENSORS__SENSOR_RESET_INTERVAL=20.1
    $ python main.py --config my_config.yaml
    Log level: DEBUG
    UI: 127.0.0.1 (port: 8888)
    Sensor reset interval: 20.1
    Sensors:
             Basic sensor[0] Trigger limits: (30, 120)
             Additional sensor[1] Trigger limits: (40, 100)

Again, environment variable overwrites the original value. Environment variable
values are always strings. However, as we defined schema and type for the
configuration parameter ``sensor_reset_interval``, it was automatically
converted to integer. Although schema is not mandatory, it's always useful for
parameters that can be configured via environment variables.

When schema is not defined, Onacol tries to apply JSON conversion rules to
the value of the environment variable. That helps in most cases, but can
cause problems if you pass value such as "1.2". In that case, it will be
automatically converted to float. If you want to receive it as string, you
must define schema for that particular config.

It is also possible to overwrite entire lists with environment variables.
To do that, use again JSON as format::

    $ export OCTEST_SENSORS__CONNECTED_UNITS='[{"id": 2, "name": "JSON sensor", "min_trigger_limit": 10, "max_trigger_limit": 90}]'
    $ python main.py --config my_config.yaml
    ---------<Application configuration>-------------
    Log level: DEBUG
    UI: 127.0.0.1 (port: 8888)
    Sensor reset interval: 30.0
    Sensors:
             JSON sensor [2]         Trigger limits: (10, 90)

As explained above, lists are always overwritten completely, no layering.
It is not possible to use JSON to overwrite dicts in the configuration
structure.

Using environment variables explicitly
**************************************

Environment variables can be also explicitly referred in the configuration YAML
file with syntax ``${oc_env:ENV_VAR}``:

.. code-block:: yaml

    general:
        log_level: DEBUG

    ui:
        addr: ${oc_env:MY_ADDR}

This reference is being resolved before the YAML is parsed (it's a primitive
regex substitution). Therefore the YAML type conversion is used for non-string
values. Explicit environment variable references can be only used in file-type
configuration sources. Example::

    $ export MY_ADDR=192.168.1.10
    $ python main.py --config my_config.yaml
    ---------<Application configuration>-------------
    Log level: DEBUG
    UI: 192.168.1.10 (port: 8888)
    Sensor reset interval: 30.0
    Sensors:
             Basic sensor [0]        Trigger limits: (30, 120)
             Additional sensor [1]   Trigger limits: (40, 100)

In explicitly used environment variables, where schema is not defined, then
of course YAML default conversion rules are used.

Configuration using command-line options
++++++++++++++++++++++++++++++++++++++++

Command-line optional arguments can be also parsed by Onacol to retrieve
configuration parameters. The logic is very similar to the implicit usage of
environment variables, but no prefix is used and the level separator is ``--``::

    $ python main.py --config my_config.yaml --ui--port 8080  --sensors--sensor-reset-interval 15.8
    ---------<Application configuration>-------------
    Log level: DEBUG
    UI: 127.0.0.1 (port: 8080)
    Sensor reset interval: 15.8
    Sensors:
             Basic sensor [0]        Trigger limits: (30, 120)
             Additional sensor [1]   Trigger limits: (40, 100)

As with implicit environment variable, config parameters with defined schema get
automatically converted to their types. It's also allowed to use JSON lists.

Generation of an example/template config file
+++++++++++++++++++++++++++++++++++++++++++++

Default configuration/schema can be used to generate an example (template)
config file with ``ConfigManager.generate_config_example`` method. This file
has the schema information stripped, but retains the comments  used in the
defaults YAML file.

The example app has the `--get-config-template` option to demonstrate it::

    $ python main.py --get-config-template config_template.yaml

will generate following `config_template.yaml` file:

.. code-block:: yaml

    general:
        # Logging level for this application.
      log_level: INFO

    ui:
        # Address and port of the UI webserver
      addr: 0.0.0.0
      port: 8888
    sensors:
      sensor_reset_interval: 30.0       # Sensor reset interval in seconds
      connected_units:
      - id: 0                           # Sensor ID <0, 16>
        name: Basic sensor
        min_trigger_limit: 30           # Minimal triggering limit [cm]
        max_trigger_limit: 120          # Maximal triggering limit [cm]
      - id: 1
        name: Additional sensor
        min_trigger_limit: 40
        max_trigger_limit: 100

The comments are retained by the magic of `Ruamel YAML`_, and there are some
limits. For proper retaining of comments, try to put the comments at the end
of line and avoid above-line comments where the preceding element is a schema
element.

Exporting current configuration to a config file
++++++++++++++++++++++++++++++++++++++++++++++++

The current state of the configuration can be dumped to a file using
the ``ConfigManager.export_current_config`` method.

Repeating schema elements
+++++++++++++++++++++++++

In case the configuration schema has repeating elements, it's possible to define
schema for just one element, declare a reference for it with ``oc_schema_id``
and then refer other elements to that schema definition directly with
``oc_schema``:

.. code-block:: yaml

    network_interfaces:
        ethernet_interface:
            name:       # Element name
                oc_default: "eth0"
                oc_schema:
                    type: string
            id:
                oc_default: 0
                oc_schema:
                    type: integer
            ip_addr:
                oc_default:  192.168.1.2
                oc_schema:
                    type: string
                    regex: "^(?:[0-9]{1,3}\\.){3}[0-9]{1,3}$"

            # Here we declare re-usable schema
            oc_schema_id: network_interface_item
        wifi_interface:
            name: wifi
            id: 1
            ip_addr: 192.168.2.3
            oc_schema: network_interface_item    # Here we reference the previously declared schema:

Configuration layering
++++++++++++++++++++++

When default or current configuration gets overwritten with new config values,
the previous values are kept internally and can be accessed. This is done using
the cascading features of CascaDict_ (the configuration structure is kept in
``ConfigManager.config`` as ``CascaDict`` instance).

If you are not interested in this, just use it as if it was a regular ``dict``.

Other notes
+++++++++++

* For any sort of configuration with variable amount of elements, use lists,
  not dicts. Onacol is written on assumption that the configuration tree
  consists of more-or-less fixed dicts and variable length lists.
* To create a default config/schema that shall enforce the end user to overwrite
  some parameters, use ``null`` as the default value and use schema with
  ``nullable: false`` - see `Cerberos docs <https://docs.python-cerberus.org/en/stable/validation-rules.html#nullable>`_.
  Validation will then report error when this value is not overwritten.

License
-------
Free software: MIT license

Documentation
-------------

Full docs at https://onacol.readthedocs.io.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
.. _Cerberus: https://docs.python-cerberus.org/en/stable/
.. _Hydra: https://hydra.cc/
.. _Config-Man: https://github.com/mmohaveri/config-man
.. _Dynaconf: https://github.com/rochacbruno/dynaconf
.. _Pydantic: https://pydantic-docs.helpmanual.io/
.. _python-dotenv: https://github.com/theskumar/python-dotenv
.. _`Gin Config`: https://github.com/google/gin-config
.. _OmegaConf: https://github.com/omry/omegaconf
.. _Confuse: https://github.com/beetbox/confuse
.. _`Python Decouple`: https://github.com/henriquebastos/python-decouple
.. _parse_it: https://github.com/naorlivne/parse_it
.. _grift: https://github.com/kensho-technologies/grift
.. _profig: https://github.com/dhagrow/profig
.. _tweak: https://github.com/kislyuk/tweak
.. _Bison: https://github.com/edaniszewski/bison
.. _figga: https://github.com/berislavlopac/figga
.. _Click: https://click.palletsprojects.com
.. _CascaDict: https://github.com/JNevrly/cascadict
.. _`Ruamel YAML`: https://yaml.readthedocs.io/en/latest/
.. _Everett: https://github.com/willkg/everett
