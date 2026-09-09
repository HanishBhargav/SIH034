from typing import Any

from ..models import ComplianceStatus, Declaration, RuleResult

RULE_ID = "DECL_001"
LEGAL_REFERENCE = "Legal Metrology (Packaged Commodities) Rules, 2011, Rule 6(1)(a)"


def _is_meaningful(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, dict):
        return any(bool(str(item).strip()) for item in value.values() if item is not None)
    return True


def validate_party_declaration(declaration: Declaration | None) -> RuleResult:
    """Validate presence of manufacturer/packer/importer declaration evidence.

    This MVP validator checks declaration presence and extraction confidence only.
    It does not infer whether a party is legally the manufacturer, packer, or importer,
    nor does it validate the legal sufficiency of an address.
    """
    if declaration is None:
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.FAIL,
            reason="Manufacturer/packer/importer declaration is missing.",
            legal_reference=LEGAL_REFERENCE,
        )

    evidence = list(declaration.source_regions)
    if not _is_meaningful(declaration.value):
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.FAIL,
            reason="Manufacturer/packer/importer declaration is missing or empty.",
            confidence=declaration.confidence,
            evidence_regions=evidence,
            legal_reference=LEGAL_REFERENCE,
        )

    if declaration.confidence < 0.70:
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.REVIEW,
            reason="Party declaration was detected, but extraction confidence is below the review threshold.",
            confidence=declaration.confidence,
            evidence_regions=evidence,
            legal_reference=LEGAL_REFERENCE,
        )

    return RuleResult(
        rule_id=RULE_ID,
        status=ComplianceStatus.PASS,
        reason="Manufacturer/packer/importer declaration evidence was detected.",
        confidence=declaration.confidence,
        evidence_regions=evidence,
        legal_reference=LEGAL_REFERENCE,
    )
