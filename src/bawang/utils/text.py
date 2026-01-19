from typing import Iterable


def clean_whitespace(value: str) -> str:
    return " ".join(value.split())


def truncate(value: str, max_len: int) -> str:
    if len(value) <= max_len:
        return value
    return value[: max_len - 3].rstrip() + "..."


def first_non_empty(values: Iterable[str]) -> str:
    for value in values:
        if value:
            return value
    return ""
