from dataclasses import dataclass
from typing import Any

from .loader import load_applicability_rules, load_mvp_rules, load_rule6_rules


@dataclass(frozen=True)
class RuleDefinition:
    rule_id: str
    source: dict[str, Any]
    data: dict[str, Any]


def _merge_values(base: Any, overlay: Any) -> Any:
    """Merge layered rule metadata without discarding fields from earlier layers."""
    if isinstance(base, dict) and isinstance(overlay, dict):
        merged = dict(base)
        for key, value in overlay.items():
            merged[key] = _merge_values(merged[key], value) if key in merged else value
        return merged

    if isinstance(base, list) and isinstance(overlay, list):
        merged = list(base)
        for value in overlay:
            if value not in merged:
                merged.append(value)
        return merged

    return overlay


def _index_rules(payload: dict[str, Any]) -> dict[str, RuleDefinition]:
    indexed: dict[str, RuleDefinition] = {}
    for rule in payload["rules"]:
        rule_id = rule["rule_id"]
        if rule_id in indexed:
            raise ValueError(f"Duplicate rule_id within rule layer: {rule_id}")
        indexed[rule_id] = RuleDefinition(
            rule_id=rule_id,
            source=rule["source"],
            data=rule,
        )
    return indexed


def load_rule_registry(repo_root=None) -> dict[str, RuleDefinition]:
    """Load the frozen rule layers into one deterministic merged registry.

    The MVP, applicability, and Rule 6 files intentionally overlap on some
    rule IDs. Later layers enrich earlier definitions rather than creating
    duplicate executable rules.
    """
    registry: dict[str, RuleDefinition] = {}

    for payload in (
        load_mvp_rules(repo_root),
        load_applicability_rules(repo_root),
        load_rule6_rules(repo_root),
    ):
        for rule_id, definition in _index_rules(payload).items():
            if rule_id not in registry:
                registry[rule_id] = definition
                continue

            existing = registry[rule_id]
            registry[rule_id] = RuleDefinition(
                rule_id=rule_id,
                source=_merge_values(existing.source, definition.source),
                data=_merge_values(existing.data, definition.data),
            )

    return registry


def get_rule(rule_id: str, repo_root=None) -> RuleDefinition:
    registry = load_rule_registry(repo_root)
    try:
        return registry[rule_id]
    except KeyError as exc:
        raise KeyError(f"Unknown rule_id: {rule_id}") from exc
