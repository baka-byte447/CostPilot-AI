"""Small parsing helpers to keep request handlers tidy."""

from typing import Iterable, List, Union


def to_float(value, default: float = 0.0) -> float:
	try:
		return float(value)
	except (TypeError, ValueError):
		return default


def to_int(value, default: int = 0) -> int:
	try:
		return int(value)
	except (TypeError, ValueError):
		return default


def to_bool(value, default: bool = False) -> bool:
	if isinstance(value, bool):
		return value
	if isinstance(value, str):
		return value.strip().lower() in {"1", "true", "yes", "y"}
	return default


def split_comma_separated(value: Union[str, Iterable[str]]) -> List[str]:
	if value is None:
		return []
	if isinstance(value, str):
		return [item.strip() for item in value.split(",") if item.strip()]
	return [str(item).strip() for item in value if str(item).strip()]


__all__ = [
	"to_float",
	"to_int",
	"to_bool",
	"split_comma_separated",
]
