from collections.abc import Mapping

from ..models import ComplianceStatus, Declaration, DeclarationState, RuleResult

RULE_ID = "ECOM_001"
LEGAL_REFERENCE = "Legal Metrology (Packaged Commodities) Rules, 2011, Rule 6(10)"
_REVIEW_THRESHOLD = 0.70
_BASE_FIELDS = (
    "manufacturer_or_packer_details",
    "commodity_name",
    "net_quantity",
    "mrp",
    "consumer_care",
)


def validate_ecommerce_mandatory_declarations(
    declaration: Declaration | None,
    *,
    is_imported: bool | None,
    best_before_use_by_applicable: bool | None,
    dimensions_applicable: bool | None,
) -> RuleResult:
    if declaration is None:
        return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.FAIL, reason="Required e-commerce mandatory declarations are missing from the listing.", legal_reference=LEGAL_REFERENCE)
    if declaration.state in {DeclarationState.UNCERTAIN, DeclarationState.CONFLICTING} or declaration.confidence < _REVIEW_THRESHOLD:
        return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.REVIEW, reason="E-commerce declaration evidence cannot be classified reliably.", confidence=declaration.confidence, evidence_regions=declaration.source_regions, legal_reference=LEGAL_REFERENCE)
    if not isinstance(declaration.value, Mapping):
        return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.REVIEW, reason="E-commerce mandatory declarations must be supplied as a structured mapping.", confidence=declaration.confidence, evidence_regions=declaration.source_regions, legal_reference=LEGAL_REFERENCE)

    required = list(_BASE_FIELDS)
    if is_imported is True:
        required.append("country_of_origin")
    elif is_imported is None:
        return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.REVIEW, reason="Import status is required to determine the e-commerce declaration set.", confidence=declaration.confidence, evidence_regions=declaration.source_regions, legal_reference=LEGAL_REFERENCE)
    if best_before_use_by_applicable is True:
        required.append("best_before_use_by")
    elif best_before_use_by_applicable is None:
        return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.REVIEW, reason="Best-before/use-by applicability is unresolved for the e-commerce listing.", confidence=declaration.confidence, evidence_regions=declaration.source_regions, legal_reference=LEGAL_REFERENCE)
    if dimensions_applicable is True:
        required.append("dimensions")
    elif dimensions_applicable is None:
        return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.REVIEW, reason="Dimension applicability is unresolved for the e-commerce listing.", confidence=declaration.confidence, evidence_regions=declaration.source_regions, legal_reference=LEGAL_REFERENCE)

    missing = [field for field in required if declaration.value.get(field) in (None, "", False)]
    if missing:
        return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.FAIL, reason=f"E-commerce listing is missing mandatory declaration(s): {', '.join(missing)}. The manufacture/packing month and year is intentionally excluded from this check.", confidence=declaration.confidence, evidence_regions=declaration.source_regions, legal_reference=LEGAL_REFERENCE)
    if "manufacture_month_year" in declaration.value:
        return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.PASS, reason="All required Rule 6(1) e-commerce declarations are present; manufacture/packing month and year is not required online under Rule 6(10).", confidence=declaration.confidence, evidence_regions=declaration.source_regions, legal_reference=LEGAL_REFERENCE)
    return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.PASS, reason="All required Rule 6(1) e-commerce declarations are present; manufacture/packing month and year is correctly excluded from the online requirement.", confidence=declaration.confidence, evidence_regions=declaration.source_regions, legal_reference=LEGAL_REFERENCE)
