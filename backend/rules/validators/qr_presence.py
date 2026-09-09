from ..models import ComplianceStatus, Declaration, DeclarationState, RuleResult

RULE_ID = "QR_001"
LEGAL_REFERENCE = "Legal Metrology (Packaged Commodities) Rules, 2011, Rule 6(4A)"
_REVIEW_THRESHOLD = 0.70


def validate_qr_presence(declaration: Declaration | None) -> RuleResult:
    if declaration is None:
        return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.PASS, reason="Barcode/GTIN/QR declaration is optional and no such declaration was observed.", legal_reference=LEGAL_REFERENCE)
    if declaration.state in {DeclarationState.UNCERTAIN, DeclarationState.CONFLICTING} or declaration.confidence < _REVIEW_THRESHOLD:
        return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.REVIEW, reason="Observed barcode/GTIN/QR declaration cannot be classified reliably.", confidence=declaration.confidence, evidence_regions=declaration.source_regions, legal_reference=LEGAL_REFERENCE)
    value = declaration.value
    if isinstance(value, dict):
        kind = str(value.get("type") or value.get("format") or "").strip().lower()
        payload = value.get("value") or value.get("payload")
    else:
        kind = "qr" if isinstance(value, str) else ""
        payload = value
    if kind in {"qr", "barcode", "gtin", "ean", "upc"} and payload not in (None, ""):
        return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.PASS, reason="Observed barcode/GTIN/QR declaration is present and parseable.", confidence=declaration.confidence, evidence_regions=declaration.source_regions, legal_reference=LEGAL_REFERENCE)
    return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.REVIEW, reason="An optional code declaration was observed but its type or payload could not be reliably parsed.", confidence=declaration.confidence, evidence_regions=declaration.source_regions, legal_reference=LEGAL_REFERENCE)
