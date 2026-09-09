from dataclasses import dataclass
from typing import Any

from .loader import load_applicability_rules, load_mvp_rules, load_rule6_rules


@dataclass(frozen=True)
class RuleDefinition:
    rule_id: str
    source: dict[str, Any]
    data: dict[str, Any]


def _index_rules(payload: dict[str, Any]) -> dict[str, RuleDefinition]:
    indexed: dict[str, RuleDefinition] = {}
    for rule in payload["rules"]:
        rule_id = rule["rule_id"]
        if rule_id in indexed:
            raise ValueError(f"Duplicate rule_id across registry: {rule_id}")
        indexed[rule_id] = RuleDefinition(
            rule_id=rule_id,
            source=rule["source"],
            data=rule,
        )
    return indexed


def load_rule_registry(repo_root=None) -> dict[str, RuleDefinition]:
    """Load the frozen working rule layers into one deterministic index."""
    registry: dict[str, RuleDefinition] = {}

    for payload in (
        load_mvp_rules(repo_root),
        load_applicability_rules(repo_root),
        load_rule6_rules(repo_root),
    ):
        for rule_id, definition in _index_rules(payload).items():
            if rule_id in registry:
                raise ValueError(f"Duplicate rule_id across registry: {rule_id}")
            registry[rule_id] = definition

    return registry


def get_rule(rule_id: str, repo_root=None) -> RuleDefinition:
    registry = load_rule_registry(repo_root)
    try:
        return registry[rule_id]
    except KeyError as exc:
        raise KeyError(f"Unknown rule_id: {rule_id}") from exc
