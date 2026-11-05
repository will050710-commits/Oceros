"""Validate the small JSON Schema keyword subset used by our bundled schemas.

No remote references, coercion, optional packages or network resolution.
"""
import json
import math
from pathlib import Path
import re


def validate(value, schema):
    if "const" in schema and (type(value) is not type(schema["const"]) or value != schema["const"]):
        raise ValueError("SCHEMA_CONST")
    if "enum" in schema and value not in schema["enum"]:
        raise ValueError("SCHEMA_ENUM")
    kinds = schema.get("type", [])
    kinds = [kinds] if isinstance(kinds, str) else kinds
    checks = {"null": value is None, "object": type(value) is dict, "array": type(value) is list,
              "string": type(value) is str, "boolean": type(value) is bool,
              "integer": type(value) is int,
              "number": type(value) is int or (type(value) is float and math.isfinite(value))}
    if kinds and not any(checks[kind] for kind in kinds):
        raise ValueError("SCHEMA_TYPE")
    if type(value) is dict:
        if not set(schema.get("required", [])).issubset(value):
            raise ValueError("SCHEMA_REQUIRED")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False and set(value) - set(properties):
            raise ValueError("SCHEMA_UNKNOWN_FIELD")
        for key, child in value.items():
            if key in properties:
                validate(child, properties[key])
    if type(value) is list:
        for item in value:
            validate(item, schema.get("items", {}))
    if type(value) is str and "pattern" in schema and not re.fullmatch(schema["pattern"], value):
        raise ValueError("SCHEMA_PATTERN")
    if type(value) in (int, float):
        if "minimum" in schema and value < schema["minimum"]:
            raise ValueError("SCHEMA_MINIMUM")


def validate_artifact(value, name):
    if name not in ("run", "manifest"):
        raise ValueError("SCHEMA_NAME")
    schema = json.loads((Path(__file__).parent / "schemas" / f"{name}.schema.json").read_text(encoding="utf-8"))
    validate(value, schema)
