"""Load and save personas as YAML so panels are versionable and shareable."""

from __future__ import annotations

from pathlib import Path

import yaml

from synthpanel.persona.models import Persona


def load_personas(path: str | Path) -> list[Persona]:
    """Load a list of personas from a YAML file (a top-level sequence)."""
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ValueError("persona file must contain a top-level YAML list")
    return [Persona.model_validate(item) for item in raw]


def save_personas(personas: list[Persona], path: str | Path) -> None:
    """Write personas to a YAML file, dropping unset/None fields for readability."""
    data = [p.model_dump(exclude_none=True, exclude_defaults=True) for p in personas]
    Path(path).write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
