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

.. image:: https://img.shields.io/pypi/pyversions/onacol
        :alt: PyPI - Python Version

Onacol is a low-opinionated configuration management library with following
features:

* YAML (=structured and hierarchical) configuration file support
* Environment variables support
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
    * - `Python Decouple`_
      - ✖️
      - ✖️
      - ✔️
      - ✔️
      - ✖️
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

Let's start with a simple `default_config.yaml` file that is part of an
application's package. This file contains default values for the configuration.

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

* `oc_schema`: Cerberus_ validator/schema definitions.
* `oc_default`: Default value (if metadata are attached to the YAML element, it
  can no longer bear the value directly.
* `oc_schema_id`: Definition of a schema reference (see TODO)

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
                regex: "^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$"

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

Onacol is used by the application via the `ConfigManager` instance.
`ConfigManager` can load configurations from multiple sources (files,
command line optional arguments, environment variables), but does not do it
automatically - the sources and order is up to the app implementation.

Example (using Click_ as a CLI framework):
TODO


* Free software: MIT license
* Documentation: https://onacol.readthedocs.io.


Features
--------

* TODO

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.


Limitations
-----------

Variable-count structures must be contained in lists.
Comments following oc_* tags are not kept.

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
