from __future__ import annotations

import re
from typing import Optional


_MONEY_PATTERN = re.compile(r"\$([0-9]+(?:\.[0-9]+)?)")


def normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def slugify(value: str) -> str:
    value = normalize_whitespace(value).lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def money_to_float(value: str) -> Optional[float]:
    match = _MONEY_PATTERN.search(value.replace(",", ""))
    if not match:
        return None
    return float(match.group(1))


def extract_all_money_values(value: str) -> list[float]:
    return [float(match) for match in _MONEY_PATTERN.findall(value.replace(",", ""))]


def split_labeled_money_values(value: str) -> list[tuple[str, float]]:
    compact = normalize_whitespace(value)
    labeled = re.findall(r"\$([0-9]+(?:\.[0-9]+)?)\s*\(([^)]+)\)", compact)
    if labeled:
        return [(label.strip(), float(amount)) for amount, label in labeled]

    amounts = extract_all_money_values(compact)
    if len(amounts) == 1:
        return [("default", amounts[0])]
    return []


def first_non_empty(*values: Optional[str]) -> str:
    for value in values:
        if value:
            text = normalize_whitespace(value)
            if text:
                return text
    return ""
