"""Deterministic rec-class string -> canonical L0-L4 mapper."""
from __future__ import annotations
import yaml
from functools import lru_cache
from pathlib import Path

TAXONOMY = Path(__file__).resolve().parents[2] / "protocol" / "taxonomy.yaml"


class TaxonomyError(ValueError):
    """Raised when a rec-class string cannot be mapped."""


@lru_cache(maxsize=1)
def _load() -> dict:
    return yaml.safe_load(TAXONOMY.read_text())


def map_to_canonical(body: str, rec_string: str, *, probe_level: str | None = None) -> str | None:
    data = _load()
    body = body.lower()
    if body not in data["body_mappings"]:
        raise TaxonomyError(f"Unknown body: {body!r} (expected one of {sorted(data['body_mappings'])})")
    mapping = data["body_mappings"][body]

    if probe_level is not None:
        return None if mapping.get(probe_level) is None else probe_level

    needle = rec_string.strip().lower()
    for level, aliases in mapping.items():
        if aliases is None:
            continue
        for alias in aliases:
            if alias.strip().lower() == needle:
                return level
    raise TaxonomyError(f"unknown rec-class for {body}: {rec_string!r}")
