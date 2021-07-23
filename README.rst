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
of existing solutions, none was completely fullfilling the features mentioned
above. Following table lists known/popular configuration frameworks and their
features relative to Onacol. You may find some of those suits your need better.

.. list-table:: Popular configuration frameworks comparison
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
      - |:heavy_check_mark:|
      - |:heavy_check_mark:|
      - |:question:|
      - |:heavy_check_mark:|
      - |:heavy_check_mark:|
      - |:heavy_multiplication_x:|

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
