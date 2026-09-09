from typing import Any

from ..models import ComplianceStatus, Declaration, DeclarationState, RuleResult

RULE_ID = "DECL_007"
LEGAL_REFERENCE = "Legal Metrology (Packaged Commodities) Rules, 2011, Rule 6(7)"
_REVIEW_THRESHOLD = 0.70


def validate_gm_food_declaration(declaration: Declaration | None) -> RuleResult:
    if declaration is None:
        return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.FAIL, reason="GM declaration is missing.", legal_reference=LEGAL_REFERENCE)
    if declaration.state in {DeclarationState.UNCERTAIN, DeclarationState.CONFLICTING}:
        return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.REVIEW, reason="GM declaration could not be classified reliably.", confidence=declaration.confidence, evidence_regions=declaration.source_regions, legal_reference=LEGAL_REFERENCE)
    if declaration.confidence < _REVIEW_THRESHOLD:
        return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.REVIEW, reason="GM declaration confidence is below the deterministic threshold.", confidence=declaration.confidence, evidence_regions=declaration.source_regions, legal_reference=LEGAL_REFERENCE)
    value: Any = declaration.value
    if isinstance(value, dict):
        present = value.get("present")
        text = value.get("text")
    else:
        present = None
        text = str(value) if value is not None else None
    if present is False:
        return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.FAIL, reason="Required GM declaration is absent.", confidence=declaration.confidence, evidence_regions=declaration.source_regions, legal_reference=LEGAL_REFERENCE)
    if present is True or (isinstance(text, str) and text.strip()):
        if isinstance(text, str) and text.strip().upper() == "GM":
            return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.PASS, reason="GM declaration is present.", confidence=declaration.confidence, evidence_regions=declaration.source_regions, legal_reference=LEGAL_REFERENCE)
        if present is True and text is None:
            return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.PASS, reason="GM declaration is marked present by the observation layer.", confidence=declaration.confidence, evidence_regions=declaration.source_regions, legal_reference=LEGAL_REFERENCE)
        return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.REVIEW, reason="GM declaration is present but its exact required marking could not be confirmed.", confidence=declaration.confidence, evidence_regions=declaration.source_regions, legal_reference=LEGAL_REFERENCE)
    return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.FAIL, reason="Required GM declaration is missing.", confidence=declaration.confidence, evidence_regions=declaration.source_regions, legal_reference=LEGAL_REFERENCE)
