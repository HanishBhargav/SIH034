from collections.abc import Callable
from typing import Any

from .applicability import ApplicabilityStatus, evaluate_chapter_ii
from .models import ComplianceResult, ComplianceStatus, M2Input, OverallStatus, RuleResult
from .rule_registry import RuleDefinition, load_rule_registry
from .validators.commodity_name import validate_commodity_name

Validator = Callable[[Any], RuleResult]

_VALIDATORS: dict[str, Validator] = {
    "DECL_003": validate_commodity_name,
}


def _legal_reference(rule: RuleDefinition) -> str:
    source = rule.source
    document = source.get("document", "Unknown legal source")
    rule_number = source.get("rule", "?")
    sub_rule = source.get("sub_rule")
    return f"{document}, Rule {rule_number}{f'({sub_rule})' if sub_rule else ''}"


def _review_result(rule: RuleDefinition, reason: str) -> RuleResult:
    return RuleResult(
        rule_id=rule.rule_id,
        status=ComplianceStatus.REVIEW,
        reason=reason,
        legal_reference=_legal_reference(rule),
    )


def _select_applicable_rules(
    inspection: M2Input,
    registry: dict[str, RuleDefinition],
) -> list[RuleDefinition]:
    """Select the MVP rules supported by the current deterministic engine."""
    decision = evaluate_chapter_ii(inspection.context)
    if decision.status != ApplicabilityStatus.APPLICABLE:
        return []

    selected: list[RuleDefinition] = []
    for rule in registry.values():
        applicability = rule.data.get("applicability") or {}
        when = applicability.get("when")
        if when == {"field": "chapter_ii_applicable", "equals": True}:
            selected.append(rule)

    return selected


def evaluate(inspection: M2Input, repo_root=None) -> ComplianceResult:
    """Run the currently implemented M2 rules for one inspection."""
    registry = load_rule_registry(repo_root)
    chapter_ii = evaluate_chapter_ii(inspection.context)

    if chapter_ii.status == ApplicabilityStatus.NOT_APPLICABLE:
        return ComplianceResult(
            inspection_id=inspection.inspection_id,
            overall_status=OverallStatus.NOT_APPLICABLE,
        )

    if chapter_ii.status == ApplicabilityStatus.REVIEW:
        return ComplianceResult(
            inspection_id=inspection.inspection_id,
            overall_status=OverallStatus.REVIEW_REQUIRED,
            results=[
                RuleResult(
                    rule_id="APP_001",
                    status=ComplianceStatus.REVIEW,
                    reason=chapter_ii.reason,
                    legal_reference="Legal Metrology (Packaged Commodities) Rules, 2011, Rule 3",
                )
            ],
            review_count=1,
        )

    results: list[RuleResult] = []
    for rule in _select_applicable_rules(inspection, registry):
        validator = _VALIDATORS.get(rule.rule_id)
        if validator is None:
            results.append(
                _review_result(
                    rule,
                    "Rule is applicable, but its validator has not yet been implemented in the current MVP engine.",
                )
            )
            continue

        declaration = inspection.declarations.get(rule.data.get("field"))
        result = validator(declaration)
        # Keep the legal reference authoritative from the registry rather than
        # trusting a validator's hard-coded reference.
        result.legal_reference = _legal_reference(rule)
        results.append(result)

    pass_count = sum(result.status == ComplianceStatus.PASS for result in results)
    fail_count = sum(result.status == ComplianceStatus.FAIL for result in results)
    review_count = sum(result.status == ComplianceStatus.REVIEW for result in results)

    if fail_count:
        overall_status = OverallStatus.NON_COMPLIANT
    elif review_count:
        overall_status = OverallStatus.REVIEW_REQUIRED
    else:
        overall_status = OverallStatus.COMPLIANT

    return ComplianceResult(
        inspection_id=inspection.inspection_id,
        overall_status=overall_status,
        results=results,
        applicable_rule_count=len(results),
        pass_count=pass_count,
        fail_count=fail_count,
        review_count=review_count,
    )
