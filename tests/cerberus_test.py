import sys

from cerberus import Validator
from ruamel.yaml import YAML, YAMLError
import sys

SCHEMA = {
    "general": {
        "type": "dict",
        "schema": {
            # "log_level": {
            #     "type": "string"
            # }
        }
    }
}

v = Validator(SCHEMA, allow_unknown=True)

yaml = YAML()

with open(r"cerb_test.yaml") as yaml_file:
    document = yaml.load(yaml_file)

v_res = v.validate(document)
print(v_res)
document.yaml_add_eol_comment("Foobar", "can_bus")
yaml.dump(document, sys.stdout)
