"""
.. module: onacol.env_var
   :synopsis: Processing for environment variables.

.. moduleauthor:: Josef Nevrly <josef.nevrly@gmail.com>
"""


class EnvVarHandler:

    SEPARATOR = "__"

    def __init__(self, flat_schema, prefix=None):
        self._flat_schema = flat_schema
        self._prefix = prefix.lstrip("_").upper() + self.SEPARATOR

        # Initialize env_var identifier mapping from the flat_schema

    def _build_mapping(self):

