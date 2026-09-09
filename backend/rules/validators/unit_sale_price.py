from ..models import ComplianceStatus, Declaration, DeclarationState, RuleResult

RULE_ID = "USP_001"
LEGAL_REFERENCE = "Legal Metrology (Packaged Commodities) Rules, 2011, Rule 6(11)"
_REVIEW_THRESHOLD = 0.70


def _normalise_unit(unit: str | None) -> str:
    if not unit:
        return ""
    value = unit.strip().lower().replace("₹", "rs").replace("/", " per ")
    aliases = {
        "g": "g", "gram": "g", "grams": "g", "per g": "g", "rs per g": "g",
        "kg": "kg", "kilogram": "kg", "kilograms": "kg", "per kg": "kg", "rs per kg": "kg",
        "ml": "ml", "millilitre": "ml", "millilitres": "ml", "per ml": "ml", "rs per ml": "ml",
        "l": "l", "litre": "l", "litres": "l", "liter": "l", "liters": "l", "per l": "l", "rs per l": "l",
        "cm": "cm", "centimetre": "cm", "centimetres": "cm", "per cm": "cm", "rs per cm": "cm",
        "m": "m", "metre": "m", "metres": "m", "meter": "m", "meters": "m", "per m": "m", "rs per m": "m",
        "number": "number", "unit": "number", "no": "number", "nos": "number", "per number": "number",
    }
    return aliases.get(value, value)


def _expected_unit(quantity: float, unit: str) -> str | None:
    unit = unit.strip().lower()
    if unit in {"g", "kg"}:
        return "g" if quantity < 1000 else "kg"
    if unit in {"ml", "l"}:
        return "ml" if quantity < 1000 else "l"
    if unit in {"cm", "m"}:
        return "cm" if quantity < 100 else "m"
    if unit in {"number", "unit", "no", "nos"}:
        return "number"
    return None


def _quantity_in_base(quantity: float, unit: str) -> float:
    unit = unit.strip().lower()
    if unit == "kg":
        return quantity * 1000
    if unit == "l":
        return quantity * 1000
    if unit == "m":
        return quantity * 100
    return quantity


def validate_unit_sale_price(
    declaration: Declaration | None,
    *,
    net_quantity: Declaration | None,
    mrp: Declaration | None,
) -> RuleResult:
    evidence = []
    if declaration is not None:
        evidence = declaration.source_regions
    if net_quantity is None or net_quantity.value is None or not net_quantity.unit:
        return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.REVIEW, reason="Net quantity is required to determine the prescribed unit sale price.", legal_reference=LEGAL_REFERENCE)
    if mrp is None or mrp.value is None:
        return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.REVIEW, reason="MRP is required to determine the expected unit sale price.", legal_reference=LEGAL_REFERENCE)
    if net_quantity.state in {DeclarationState.UNCERTAIN, DeclarationState.CONFLICTING} or net_quantity.confidence < _REVIEW_THRESHOLD:
        return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.REVIEW, reason="Net quantity cannot be relied upon to calculate unit sale price.", confidence=net_quantity.confidence, evidence_regions=net_quantity.source_regions, legal_reference=LEGAL_REFERENCE)
    try:
        quantity = float(net_quantity.value)
        mrp_value = float(mrp.value)
    except (TypeError, ValueError):
        return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.REVIEW, reason="Net quantity or MRP is not numerically parseable for unit sale price calculation.", evidence_regions=evidence, legal_reference=LEGAL_REFERENCE)
    if quantity <= 0 or mrp_value < 0:
        return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.REVIEW, reason="Net quantity and MRP must be valid positive values for unit sale price calculation.", evidence_regions=evidence, legal_reference=LEGAL_REFERENCE)

    expected_unit = _expected_unit(quantity, net_quantity.unit)
    if expected_unit is None:
        return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.REVIEW, reason="The quantity unit is not supported for automatic unit sale price validation.", evidence_regions=evidence, legal_reference=LEGAL_REFERENCE)

    base_quantity = _quantity_in_base(quantity, net_quantity.unit)
    exempt = (net_quantity.unit.strip().lower() in {"g", "ml"} and quantity <= 10)
    if exempt:
        if declaration is None:
            return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.PASS, reason="Unit sale price declaration is not required for a package of 10 g/ml or less.", legal_reference=LEGAL_REFERENCE)

    if declaration is None or declaration.state == DeclarationState.MISSING:
        expected = mrp_value / base_quantity
        if round(expected, 2) == round(mrp_value, 2):
            return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.PASS, reason="Unit sale price declaration is not required because retail sale price equals unit sale price.", legal_reference=LEGAL_REFERENCE)
        return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.FAIL, reason="Required unit sale price declaration is missing.", legal_reference=LEGAL_REFERENCE)
    if declaration.state in {DeclarationState.UNCERTAIN, DeclarationState.CONFLICTING} or declaration.confidence < _REVIEW_THRESHOLD:
        return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.REVIEW, reason="Unit sale price declaration cannot be classified reliably.", confidence=declaration.confidence, evidence_regions=evidence, legal_reference=LEGAL_REFERENCE)

    value = declaration.value
    declared_value = value.get("value") if isinstance(value, dict) else value
    declared_unit = declaration.unit or (value.get("unit") if isinstance(value, dict) else None)
    try:
        declared_value = float(declared_value)
    except (TypeError, ValueError):
        return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.FAIL, reason="Unit sale price is not numerically parseable.", confidence=declaration.confidence, evidence_regions=evidence, legal_reference=LEGAL_REFERENCE)
    if declared_value < 0 or _normalise_unit(declared_unit) != expected_unit:
        return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.FAIL, reason=f"Unit sale price must be declared per {expected_unit} for the observed net quantity.", confidence=declaration.confidence, evidence_regions=evidence, legal_reference=LEGAL_REFERENCE)

    expected_value = mrp_value / base_quantity
    if round(declared_value, 2) != round(expected_value, 2):
        return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.FAIL, reason=f"Declared unit sale price does not match the calculated value of {expected_value:.2f} per {expected_unit} after rounding to two decimal places.", confidence=declaration.confidence, evidence_regions=evidence, legal_reference=LEGAL_REFERENCE)
    return RuleResult(rule_id=RULE_ID, status=ComplianceStatus.PASS, reason="Unit sale price is present, uses the prescribed unit, and matches the calculated value after rounding to two decimal places.", confidence=declaration.confidence, evidence_regions=evidence, legal_reference=LEGAL_REFERENCE)
