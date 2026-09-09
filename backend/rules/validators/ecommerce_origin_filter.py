from collections.abc import Mapping

from ..models import ComplianceStatus, Declaration, DeclarationState, RuleResult

RULE_ID = "ECOM_002"
LEGAL_REFERENCE = "Legal Metrology (Packaged Commodities) Rules, 2011, Rule 6(10A), G.S.R. 128(E), 13 February 2026"
_REVIEW_THRESHOLD = 0.70


def validate_ecommerce_country_origin_filter(declaration: Declaration | None) -> RuleResult:
    if declaration is None:
        return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.FAIL, reason="The e-commerce listing does not provide the required country-of-origin filter for imported products.", legal_reference=LEGAL_REFERENCE)
    if declaration.state in {DeclarationState.UNCERTAIN, DeclarationState.CONFLICTING} or declaration.confidence < _REVIEW_THRESHOLD:
        return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.REVIEW, reason="Country-of-origin filter evidence cannot be classified reliably.", confidence=declaration.confidence, evidence_regions=declaration.source_regions, legal_reference=LEGAL_REFERENCE)
    value = declaration.value
    if value is True:
        return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.PASS, reason="The required searchable and sortable country-of-origin filter is reported as present.", confidence=declaration.confidence, evidence_regions=declaration.source_regions, legal_reference=LEGAL_REFERENCE)
    if not isinstance(value, Mapping):
        return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.REVIEW, reason="Country-of-origin filter evidence is not in a parseable structured form.", confidence=declaration.confidence, evidence_regions=declaration.source_regions, legal_reference=LEGAL_REFERENCE)
    required = ("filter_present", "searchable", "sortable", "country_of_origin")
    missing_or_false = [key for key in required if value.get(key) is not True]
    if missing_or_false:
        return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.FAIL, reason=f"The country-of-origin filter is incomplete: {', '.join(missing_or_false)}.", confidence=declaration.confidence, evidence_regions=declaration.source_regions, legal_reference=LEGAL_REFERENCE)
    return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.PASS, reason="The imported-product listing provides a searchable and sortable country-of-origin filter as required.", confidence=declaration.confidence, evidence_regions=declaration.source_regions, legal_reference=LEGAL_REFERENCE)
