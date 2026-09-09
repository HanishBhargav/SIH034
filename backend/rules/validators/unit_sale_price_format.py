from ..models import ComplianceStatus, Declaration, DeclarationState, RuleResult

RULE_ID = "USP_002"
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
        grams = quantity * 1000 if unit == "kg" else quantity
        return "g" if grams < 1000 else "kg"
    if unit in {"ml", "l"}:
        millilitres = quantity * 1000 if unit == "l" else quantity
        return "ml" if millilitres < 1000 else "l"
    if unit in {"cm", "m"}:
        centimetres = quantity * 100 if unit == "m" else quantity
        return "cm" if centimetres < 100 else "m"
    if unit in {"number", "unit", "no", "nos"}:
        return "number"
    return None


def validate_unit_sale_price_format(
    declaration: Declaration | None,
    *,
    net_quantity: Declaration | None,
) -> RuleResult:
    evidence = declaration.source_regions if declaration is not None else []

    if declaration is None or declaration.state == DeclarationState.MISSING:
        # Presence/exemption is handled by USP_001. This rule only evaluates
        # the format when a declaration is actually available.
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.PASS,
            reason="No unit sale price declaration is available for format validation; presence and exemption are evaluated by USP_001.",
            legal_reference=LEGAL_REFERENCE,
        )

    if declaration.state in {DeclarationState.UNCERTAIN, DeclarationState.CONFLICTING} or declaration.confidence < _REVIEW_THRESHOLD:
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.REVIEW,
            reason="Unit sale price declaration cannot be classified reliably for format validation.",
            confidence=declaration.confidence,
            evidence_regions=evidence,
            legal_reference=LEGAL_REFERENCE,
        )

    if net_quantity is None or net_quantity.value is None or not net_quantity.unit:
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.REVIEW,
            reason="Net quantity is required to determine the prescribed unit sale price format.",
            evidence_regions=evidence,
            legal_reference=LEGAL_REFERENCE,
        )

    if net_quantity.state in {DeclarationState.UNCERTAIN, DeclarationState.CONFLICTING} or net_quantity.confidence < _REVIEW_THRESHOLD:
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.REVIEW,
            reason="Net quantity cannot be relied upon to determine the prescribed unit sale price format.",
            confidence=net_quantity.confidence,
            evidence_regions=net_quantity.source_regions,
            legal_reference=LEGAL_REFERENCE,
        )

    value = declaration.value
    declared_value = value.get("value") if isinstance(value, dict) else value
    declared_unit = declaration.unit or (value.get("unit") if isinstance(value, dict) else None)

    try:
        quantity = float(net_quantity.value)
        numeric_value = float(declared_value)
    except (TypeError, ValueError):
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.FAIL,
            reason="Unit sale price or net quantity is not numerically parseable.",
            confidence=declaration.confidence,
            evidence_regions=evidence,
            legal_reference=LEGAL_REFERENCE,
        )

    if quantity <= 0 or numeric_value < 0:
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.FAIL,
            reason="Unit sale price and net quantity must be valid non-negative/positive values.",
            confidence=declaration.confidence,
            evidence_regions=evidence,
            legal_reference=LEGAL_REFERENCE,
        )

    expected_unit = _expected_unit(quantity, net_quantity.unit)
    if expected_unit is None:
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.REVIEW,
            reason="The quantity unit is not supported for automatic unit sale price format validation.",
            evidence_regions=evidence,
            legal_reference=LEGAL_REFERENCE,
        )

    if _normalise_unit(declared_unit) != expected_unit:
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.FAIL,
            reason=f"Unit sale price must be expressed per {expected_unit} for the observed net quantity.",
            confidence=declaration.confidence,
            evidence_regions=evidence,
            legal_reference=LEGAL_REFERENCE,
        )

    # The rule permits a whole number without decimal places, otherwise the
    # displayed amount must be rounded to the nearest two decimal places.
    if round(numeric_value, 2) != numeric_value:
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.FAIL,
            reason="Unit sale price must be rounded to the nearest two decimal places; a whole number may be shown without decimal places.",
            confidence=declaration.confidence,
            evidence_regions=evidence,
            legal_reference=LEGAL_REFERENCE,
        )

    return RuleResult(
        rule_id=RULE_ID,
        status=ComplianceStatus.PASS,
        reason="Unit sale price uses the prescribed quantity basis and is rounded to at most two decimal places.",
        confidence=declaration.confidence,
        evidence_regions=evidence,
        legal_reference=LEGAL_REFERENCE,
    )
