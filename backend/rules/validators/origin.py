from typing import Any

from ..models import ComplianceStatus, Declaration, RuleResult

RULE_ID = "DECL_002"
LEGAL_REFERENCE = "Legal Metrology (Packaged Commodities) Rules, 2011, Rule 6(1)(aa)"


def _is_meaningful(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, dict):
        return any(bool(str(item).strip()) for item in value.values() if item is not None)
    return True


def validate_origin_declaration(
    declaration: Declaration | None,
    *,
    is_imported: bool | None,
) -> RuleResult:
    """Validate country-of-origin declaration when import status is known.

    This validator checks the presence and extraction confidence of the declaration.
    It does not infer country of origin from other text and does not determine whether
    a particular origin statement satisfies every category-specific legal requirement.
    """
    if is_imported is False:
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.PASS,
            reason="Country-of-origin declaration is not required by this rule for a package identified as non-imported.",
            legal_reference=LEGAL_REFERENCE,
        )

    if is_imported is None:
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.REVIEW,
            reason="Import status is unknown, so applicability of the country-of-origin declaration cannot be established.",
            legal_reference=LEGAL_REFERENCE,
        )

    if declaration is None:
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.FAIL,
            reason="Imported package has no country-of-origin declaration evidence.",
            legal_reference=LEGAL_REFERENCE,
        )

    evidence = list(declaration.source_regions)
    if not _is_meaningful(declaration.value):
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.FAIL,
            reason="Country-of-origin declaration is missing or empty for an imported package.",
            confidence=declaration.confidence,
            evidence_regions=evidence,
            legal_reference=LEGAL_REFERENCE,
        )

    if declaration.confidence < 0.70:
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.REVIEW,
            reason="Country-of-origin declaration was detected, but extraction confidence is below the review threshold.",
            confidence=declaration.confidence,
            evidence_regions=evidence,
            legal_reference=LEGAL_REFERENCE,
        )

    return RuleResult(
        rule_id=RULE_ID,
        status=ComplianceStatus.PASS,
        reason="Country-of-origin declaration evidence was detected for an imported package.",
        confidence=declaration.confidence,
        evidence_regions=evidence,
        legal_reference=LEGAL_REFERENCE,
    )
