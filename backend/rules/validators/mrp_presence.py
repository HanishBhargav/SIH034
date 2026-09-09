from typing import Any

from ..models import ComplianceStatus, Declaration, RuleResult

RULE_ID = "MRP_001"
LEGAL_REFERENCE = "Legal Metrology (Packaged Commodities) Rules, 2011, Rule 6(1)(e)"


def _is_meaningful(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return True


def validate_mrp_presence(declaration: Declaration | None) -> RuleResult:
    """Validate presence and extraction confidence of the MRP declaration.

    This validator checks only whether an MRP declaration is present and reliably
    extracted. MRP numeric formatting, tax-inclusive wording, rounding, and other
    format requirements belong to separate MRP validators.
    """
    if declaration is None:
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.FAIL,
            reason="MRP declaration is missing.",
            legal_reference=LEGAL_REFERENCE,
        )

    evidence = list(declaration.source_regions)
    if not _is_meaningful(declaration.value):
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.FAIL,
            reason="MRP declaration is missing or empty.",
            confidence=declaration.confidence,
            evidence_regions=evidence,
            legal_reference=LEGAL_REFERENCE,
        )

    if declaration.confidence < 0.70:
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.REVIEW,
            reason="MRP was detected, but extraction confidence is below the review threshold.",
            confidence=declaration.confidence,
            evidence_regions=evidence,
            legal_reference=LEGAL_REFERENCE,
        )

    return RuleResult(
        rule_id=RULE_ID,
        status=ComplianceStatus.PASS,
        reason="A non-empty MRP declaration was detected.",
        confidence=declaration.confidence,
        evidence_regions=evidence,
        legal_reference=LEGAL_REFERENCE,
    )
