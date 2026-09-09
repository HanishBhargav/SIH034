from ..models import ComplianceStatus, Declaration, DeclarationState, RuleResult

RULE_ID = "DECL_008"
LEGAL_REFERENCE = "Legal Metrology (Packaged Commodities) Rules, 2011, Rule 6(8)"
_REVIEW_THRESHOLD = 0.70


def validate_veg_nonveg_dot(declaration: Declaration | None) -> RuleResult:
    if declaration is None:
        return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.FAIL, reason="Required vegetarian/non-vegetarian declaration is missing.", legal_reference=LEGAL_REFERENCE)
    if declaration.state in {DeclarationState.UNCERTAIN, DeclarationState.CONFLICTING} or declaration.confidence < _REVIEW_THRESHOLD:
        return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.REVIEW, reason="Vegetarian/non-vegetarian marking cannot be classified reliably.", confidence=declaration.confidence, evidence_regions=declaration.source_regions, legal_reference=LEGAL_REFERENCE)
    value = declaration.value
    if isinstance(value, dict):
        present = value.get("present")
        marking = value.get("marking") or value.get("symbol") or value.get("text")
        if present is False:
            return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.FAIL, reason="Required vegetarian/non-vegetarian marking is absent.", confidence=declaration.confidence, evidence_regions=declaration.source_regions, legal_reference=LEGAL_REFERENCE)
    else:
        present = None
        marking = str(value) if value is not None else None
    if not marking and present is not True:
        return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.FAIL, reason="Required vegetarian/non-vegetarian marking is missing.", confidence=declaration.confidence, evidence_regions=declaration.source_regions, legal_reference=LEGAL_REFERENCE)
    if present is True and not marking:
        return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.PASS, reason="Vegetarian/non-vegetarian marking is marked present by the observation layer.", confidence=declaration.confidence, evidence_regions=declaration.source_regions, legal_reference=LEGAL_REFERENCE)
    normalized = str(marking).strip().lower()
    if normalized in {"veg", "vegetarian", "non-veg", "nonveg", "non vegetarian", "green", "brown"}:
        return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.PASS, reason="Vegetarian/non-vegetarian marking is present.", confidence=declaration.confidence, evidence_regions=declaration.source_regions, legal_reference=LEGAL_REFERENCE)
    return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.REVIEW, reason="A marking was detected but its vegetarian/non-vegetarian classification is uncertain.", confidence=declaration.confidence, evidence_regions=declaration.source_regions, legal_reference=LEGAL_REFERENCE)
