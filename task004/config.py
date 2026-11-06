"""Strict configuration for the synthetic-only TASK-004 harness."""

from dataclasses import asdict, dataclass, fields
import json
import math
from pathlib import Path


MAX_TIMEOUT_S = 3600
MAX_SAMPLE_INTERVAL_S = 60


class ConfigError(ValueError):
    """Configuration is invalid; messages never include supplied values."""


def _integer(name, value, minimum, maximum=None):
    if type(value) is not int or value < minimum:
        raise ConfigError(f"{name} must be an integer >= {minimum}")
    if maximum is not None and value > maximum:
        raise ConfigError(f"{name} must be <= {maximum}")


def _number(name, value, minimum, inclusive=False, maximum=None):
    if type(value) not in (int, float):
        raise ConfigError(f"{name} must be a finite number")
    try:
        valid = math.isfinite(value)
    except (OverflowError, TypeError):
        valid = False
    if not valid or (value < minimum if inclusive else value <= minimum):
        relation = ">=" if inclusive else ">"
        raise ConfigError(f"{name} must be finite and {relation} {minimum}")
    if maximum is not None and value > maximum:
        raise ConfigError(f"{name} must be <= {maximum}")


@dataclass(frozen=True)
class Config:
    n_ctx: int
    runtime: str = "mock"
    thinking: bool = False
    max_new_tokens: int = 96
    timeout_s: float = 5.0
    startup_timeout_s: float = 5.0
    sample_interval_s: float = 0.05
    min_available_ram_bytes: int = 67_108_864
    min_free_disk_bytes: int = 10_485_760
    image_long_edge_px: int | None = None
    max_image_tokens: int | None = None
    mock_scenario: str = "success"
    mock_delay_s: float = 0.0

    def __post_init__(self):
        if self.runtime != "mock":
            raise ConfigError("runtime must be mock; real model execution is disabled")
        if self.thinking is not False:
            raise ConfigError("thinking must be false")
        _integer("n_ctx", self.n_ctx, 1)
        _integer("max_new_tokens", self.max_new_tokens, 1, 96)
        _number("timeout_s", self.timeout_s, 0, maximum=MAX_TIMEOUT_S)
        _number("startup_timeout_s", self.startup_timeout_s, 0, maximum=MAX_TIMEOUT_S)
        _number("sample_interval_s", self.sample_interval_s, 0.01, inclusive=True,
                maximum=MAX_SAMPLE_INTERVAL_S)
        _integer("min_available_ram_bytes", self.min_available_ram_bytes, 0)
        _integer("min_free_disk_bytes", self.min_free_disk_bytes, 0)
        _number("mock_delay_s", self.mock_delay_s, 0, inclusive=True, maximum=MAX_TIMEOUT_S)
        if (self.image_long_edge_px is None) != (self.max_image_tokens is None):
            raise ConfigError("image_long_edge_px and max_image_tokens must be set together")
        if self.image_long_edge_px is not None:
            _integer("image_long_edge_px", self.image_long_edge_px, 1, 768)
            _integer("max_image_tokens", self.max_image_tokens, 1)
        if self.mock_scenario not in (
            "success", "malformed_json", "http_error", "disconnect", "slow", "health_failure"
        ):
            raise ConfigError("unsupported mock_scenario")

    def to_dict(self):
        return asdict(self)


def parse_config(data):
    """Validate even programmatically constructed configs; no coercion/default context."""
    if not isinstance(data, dict):
        raise ConfigError("configuration must be a JSON object")
    allowed = {field.name for field in fields(Config)}
    if any(key not in allowed for key in data):
        raise ConfigError("unknown configuration keys")
    if "n_ctx" not in data:
        raise ConfigError("n_ctx is required")
    return Config(**data)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ConfigError("duplicate JSON object keys")
        result[key] = value
    return result


def _invalid_constant(_value):
    raise ConfigError("nonfinite JSON numbers are not permitted")


def load_config(path):
    try:
        text = Path(path).read_text(encoding="utf-8")
        data = json.loads(text, object_pairs_hook=_unique_object, parse_constant=_invalid_constant)
    except ConfigError:
        raise
    except (OSError, UnicodeError, ValueError, RecursionError) as error:
        raise ConfigError("configuration could not be read as UTF-8 JSON") from error
    return parse_config(data)
