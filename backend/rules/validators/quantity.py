from typing import Any

from ..models import ComplianceStatus, Declaration, RuleResult

RULE_ID = "QTY_001"
LEGAL_REFERENCE = (
    "Legal Metrology (Packaged Commodities) Rules, 2011, "
    "Rule 6(1)(c), related Rule 12"
)


def _numeric_quantity(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip().replace(",", "")
        try:
            return float(text)
        except ValueError:
            return None
    return None


def validate_net_quantity(declaration: Declaration | None) -> RuleResult:
    """Validate presence, parseability, and extraction confidence of net quantity.

    This validator does not decide commodity-specific Rule 12 exceptions or perform
    unit conversion. Those decisions belong to the quantity-unit validator/context
    layer and unresolved cases must remain reviewable.
    """
    if declaration is None:
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.FAIL,
            reason="Net quantity declaration is missing.",
            legal_reference=LEGAL_REFERENCE,
        )

    evidence = list(declaration.source_regions)
    value = _numeric_quantity(declaration.value)

    if value is None:
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.FAIL,
            reason="Net quantity declaration is present but cannot be reliably parsed as a numeric quantity.",
            confidence=declaration.confidence,
            evidence_regions=evidence,
            legal_reference=LEGAL_REFERENCE,
        )

    if value <= 0:
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.FAIL,
            reason="Net quantity must contain a positive declared quantity.",
            confidence=declaration.confidence,
            evidence_regions=evidence,
            legal_reference=LEGAL_REFERENCE,
        )

    if declaration.confidence < 0.70:
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.REVIEW,
            reason="Net quantity was detected, but extraction confidence is below the review threshold.",
            confidence=declaration.confidence,
            evidence_regions=evidence,
            legal_reference=LEGAL_REFERENCE,
        )

    return RuleResult(
        rule_id=RULE_ID,
        status=ComplianceStatus.PASS,
        reason="Net quantity declaration was detected and parsed as a positive numeric quantity; commodity-specific unit exceptions remain outside this validator.",
        confidence=declaration.confidence,
        evidence_regions=evidence,
        legal_reference=LEGAL_REFERENCE,
    )
