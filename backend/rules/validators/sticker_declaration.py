from ..models import ComplianceStatus, Declaration, DeclarationState, RuleResult

RULE_ID = "STICKER_001"
LEGAL_REFERENCE = "Legal Metrology (Packaged Commodities) Rules, 2011, Rule 6(3)"
_REVIEW_THRESHOLD = 0.70


def validate_sticker_declaration(declaration: Declaration | None) -> RuleResult:
    if declaration is None:
        return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.REVIEW, reason="Sticker usage could not be determined from the observation.", legal_reference=LEGAL_REFERENCE)
    if declaration.state in {DeclarationState.UNCERTAIN, DeclarationState.CONFLICTING} or declaration.confidence < _REVIEW_THRESHOLD:
        return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.REVIEW, reason="Sticker usage cannot be classified reliably.", confidence=declaration.confidence, evidence_regions=declaration.source_regions, legal_reference=LEGAL_REFERENCE)
    value = declaration.value if isinstance(declaration.value, dict) else {"type": str(declaration.value)}
    sticker_type = str(value.get("type") or value.get("purpose") or "").strip().lower()
    covers_original_mrp = value.get("covers_original_mrp")
    alters_mandatory = value.get("alters_mandatory_declaration")
    if alters_mandatory is True:
        return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.FAIL, reason="Sticker appears to alter or make a mandatory declaration.", confidence=declaration.confidence, evidence_regions=declaration.source_regions, legal_reference=LEGAL_REFERENCE)
    if sticker_type in {"mrp_reduction", "reduced_mrp", "mrp reduction"}:
        if covers_original_mrp is True:
            return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.FAIL, reason="A reduced-MRP sticker must not cover the original MRP declaration.", confidence=declaration.confidence, evidence_regions=declaration.source_regions, legal_reference=LEGAL_REFERENCE)
        return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.PASS, reason="Reduced-MRP sticker is permitted without covering the original MRP declaration.", confidence=declaration.confidence, evidence_regions=declaration.source_regions, legal_reference=LEGAL_REFERENCE)
    if sticker_type in {"non_mandatory", "additional", "additional_information"}:
        return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.PASS, reason="Sticker is identified as additional non-mandatory information.", confidence=declaration.confidence, evidence_regions=declaration.source_regions, legal_reference=LEGAL_REFERENCE)
    return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.REVIEW, reason="Sticker purpose could not be reliably classified under the permitted exceptions.", confidence=declaration.confidence, evidence_regions=declaration.source_regions, legal_reference=LEGAL_REFERENCE)
