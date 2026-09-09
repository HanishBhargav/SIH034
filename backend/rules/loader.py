"""Load and validate machine-readable M2 rule data."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class RuleDataError(ValueError):
    """Raised when a rule-data file is missing or structurally invalid."""


REQUIRED_TOP_LEVEL_KEYS = {"schema_version", "rule_set", "rules"}
REQUIRED_RULE_KEYS = {"rule_id", "source"}


def load_rule_file(path: str | Path) -> dict[str, Any]:
    """Load one JSON rule-data file and perform structural validation."""
    rule_path = Path(path)

    if not rule_path.is_file():
        raise RuleDataError(f"Rule-data file not found: {rule_path}")

    try:
        with rule_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as exc:
        raise RuleDataError(f"Invalid JSON in {rule_path}: {exc}") from exc

    if not isinstance(data, dict):
        raise RuleDataError(f"Rule-data root must be an object: {rule_path}")

    missing = REQUIRED_TOP_LEVEL_KEYS - data.keys()
    if missing:
        raise RuleDataError(
            f"Missing top-level keys in {rule_path}: {sorted(missing)}"
        )

    rules = data["rules"]
    if not isinstance(rules, list):
        raise RuleDataError(f"'rules' must be a list: {rule_path}")

    for index, rule in enumerate(rules):
        if not isinstance(rule, dict):
            raise RuleDataError(f"Rule at index {index} is not an object: {rule_path}")

        missing_rule_keys = REQUIRED_RULE_KEYS - rule.keys()
        if missing_rule_keys:
            raise RuleDataError(
                f"Rule at index {index} missing keys "
                f"{sorted(missing_rule_keys)}: {rule_path}"
            )

        if not isinstance(rule["rule_id"], str) or not rule["rule_id"].strip():
            raise RuleDataError(
                f"Rule at index {index} has an invalid rule_id: {rule_path}"
            )

        if not isinstance(rule["source"], dict):
            raise RuleDataError(
                f"Rule {rule['rule_id']} has an invalid source object: {rule_path}"
            )

    return data


def load_mvp_rules(repo_root: str | Path | None = None) -> dict[str, Any]:
    """Load the September 2026 MVP rule registry from the repository root."""
    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[2]
    return load_rule_file(root / "rules-data" / "mvp-rules-sept-2026.json")


def load_applicability_rules(repo_root: str | Path | None = None) -> dict[str, Any]:
    """Load the September 2026 applicability reconciliation layer."""
    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[2]
    return load_rule_file(root / "rules-data" / "applicability-sept-2026-v1.json")


def load_rule6_rules(repo_root: str | Path | None = None) -> dict[str, Any]:
    """Load the frozen September 2026 Rule 6 working map."""
    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[2]
    return load_rule_file(root / "rules-data" / "rule6-reconciliation-sept-2026.json")
