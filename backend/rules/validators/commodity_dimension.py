from collections.abc import Mapping

from ..models import ComplianceStatus, Declaration, DeclarationState, RuleResult

RULE_ID = "DECL_005"
LEGAL_REFERENCE = "Legal Metrology (Packaged Commodities) Rules, 2011, Rule 6(1)(f)"
_REVIEW_THRESHOLD = 0.70


def _valid_dimension(value) -> bool:
    return isinstance(value, (int, float)) and value > 0


def validate_commodity_dimension(declaration: Declaration | None) -> RuleResult:
    if declaration is None:
        return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.FAIL, reason="Required commodity dimensions are missing.", legal_reference=LEGAL_REFERENCE)
    if declaration.state in {DeclarationState.UNCERTAIN, DeclarationState.CONFLICTING} or declaration.confidence < _REVIEW_THRESHOLD:
        return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.REVIEW, reason="Commodity dimensions cannot be determined reliably.", confidence=declaration.confidence, evidence_regions=declaration.source_regions, legal_reference=LEGAL_REFERENCE)
    value = declaration.value
    if not isinstance(value, Mapping):
        return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.REVIEW, reason="Commodity dimensions are not in a parseable structured form.", confidence=declaration.confidence, evidence_regions=declaration.source_regions, legal_reference=LEGAL_REFERENCE)
    required = ("length", "width", "height")
    present = [key for key in required if key in value]
    if not present:
        return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.FAIL, reason="No commodity dimensions were declared.", confidence=declaration.confidence, evidence_regions=declaration.source_regions, legal_reference=LEGAL_REFERENCE)
    if any(not _valid_dimension(value[key]) for key in present):
        return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.REVIEW, reason="One or more declared dimensions are invalid or non-positive.", confidence=declaration.confidence, evidence_regions=declaration.source_regions, legal_reference=LEGAL_REFERENCE)
    if len(present) < 3:
        return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.REVIEW, reason="Dimension declaration is incomplete; commodity-specific requirements need review.", confidence=declaration.confidence, evidence_regions=declaration.source_regions, legal_reference=LEGAL_REFERENCE)
    unit = str(value.get("unit", "")).strip()
    if not unit:
        return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.REVIEW, reason="Dimension unit is missing.", confidence=declaration.confidence, evidence_regions=declaration.source_regions, legal_reference=LEGAL_REFERENCE)
    return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.PASS, reason="Commodity dimensions are present in a valid structured form.", confidence=declaration.confidence, evidence_regions=declaration.source_regions, legal_reference=LEGAL_REFERENCE)
