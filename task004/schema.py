"""Validate the small JSON Schema keyword subset used by our bundled schemas.

No remote references, coercion, optional packages or network resolution.
"""
import json
import math
from pathlib import Path
import re


ANNOTATIONS = {"$schema", "title", "description"}
KEYWORDS = {"const", "enum", "type", "required", "properties", "additionalProperties",
            "items", "pattern", "minimum", "maximum", "exclusiveMinimum"}
TYPES = {"null", "object", "array", "string", "boolean", "integer", "number"}


def check_schema(schema):
    """Reject unsupported or malformed contracts instead of silently ignoring them."""
    if type(schema) is not dict:
        raise ValueError("SCHEMA_DEFINITION_INVALID")
    if set(schema) - KEYWORDS - ANNOTATIONS:
        raise ValueError("SCHEMA_UNSUPPORTED_KEYWORD")
    kinds = schema.get("type", [])
    kinds = [kinds] if isinstance(kinds, str) else kinds
    if (type(kinds) is not list or any(type(kind) is not str or kind not in TYPES for kind in kinds)
            or ("type" in schema and not kinds)):
        raise ValueError("SCHEMA_DEFINITION_INVALID")
    if "enum" in schema and (type(schema["enum"]) is not list or not schema["enum"]):
        raise ValueError("SCHEMA_DEFINITION_INVALID")
    required = schema.get("required", [])
    if type(required) is not list or any(type(key) is not str for key in required):
        raise ValueError("SCHEMA_DEFINITION_INVALID")
    if "additionalProperties" in schema and type(schema["additionalProperties"]) is not bool:
        raise ValueError("SCHEMA_DEFINITION_INVALID")
    for bound in ("minimum", "maximum", "exclusiveMinimum"):
        if bound in schema:
            value = schema[bound]
            if not (type(value) is int or (type(value) is float and math.isfinite(value))):
                raise ValueError("SCHEMA_DEFINITION_INVALID")
    if "pattern" in schema:
        try:
            if type(schema["pattern"]) is not str:
                raise ValueError("SCHEMA_DEFINITION_INVALID")
            re.compile(schema["pattern"])
        except re.error:
            raise ValueError("SCHEMA_DEFINITION_INVALID") from None
    properties = schema.get("properties", {})
    if type(properties) is not dict or any(type(key) is not str for key in properties):
        raise ValueError("SCHEMA_DEFINITION_INVALID")
    for child in properties.values():
        check_schema(child)
    if "items" in schema:
        check_schema(schema["items"])


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
        if "maximum" in schema and value > schema["maximum"]:
            raise ValueError("SCHEMA_MAXIMUM")
        if "exclusiveMinimum" in schema and value <= schema["exclusiveMinimum"]:
            raise ValueError("SCHEMA_EXCLUSIVE_MINIMUM")


def validate_artifact(value, name):
    if name not in ("run", "manifest"):
        raise ValueError("SCHEMA_NAME")
    schema = json.loads((Path(__file__).parent / "schemas" / f"{name}.schema.json").read_text(encoding="utf-8"))
    check_schema(schema)
    validate(value, schema)
