from typing import Any

from ..models import ComplianceStatus, Declaration, RuleResult

RULE_ID = "QTY_002"
LEGAL_REFERENCE = (
    "Legal Metrology (Packaged Commodities) Rules, 2011, "
    "Rule 12(2), read with Rule 13"
)


_UNIT_ALIASES = {
    "g": "g",
    "gram": "g",
    "grams": "g",
    "kg": "kg",
    "kilogram": "kg",
    "kilograms": "kg",
    "cm": "cm",
    "centimetre": "cm",
    "centimeter": "cm",
    "m": "m",
    "metre": "m",
    "meter": "m",
    "dm": "dm",
    "square centimetre": "cm2",
    "square centimeter": "cm2",
    "cm2": "cm2",
    "cm²": "cm2",
    "square metre": "m2",
    "square meter": "m2",
    "m2": "m2",
    "m²": "m2",
    "square decimetre": "dm2",
    "square decimeter": "dm2",
    "dm2": "dm2",
    "dm²": "dm2",
    "ml": "ml",
    "millilitre": "ml",
    "milliliter": "ml",
    "litre": "l",
    "liter": "l",
    "l": "l",
    "L": "l",
    "cm3": "cm3",
    "cm³": "cm3",
    "cubic centimetre": "cm3",
    "cubic centimeter": "cm3",
    "dm3": "dm3",
    "dm³": "dm3",
    "cubic decimetre": "dm3",
    "cubic decimeter": "dm3",
    "m3": "m3",
    "m³": "m3",
    "cubic metre": "m3",
    "cubic meter": "m3",
    "number": "number",
    "unit": "unit",
    "piece": "piece",
    "pair": "pair",
    "set": "set",
    "n": "number",
    "u": "unit",
}

_FORBIDDEN_NUMBER_UNITS = {"dozen", "score", "gross", "great gross"}

_UNIT_FAMILIES = {
    "g": "mass",
    "kg": "mass",
    "cm": "length",
    "m": "length",
    "cm2": "area",
    "dm2": "area",
    "m2": "area",
    "ml": "volume",
    "l": "volume",
    "cm3": "volume",
    "dm3": "volume",
    "m3": "volume",
    "number": "number",
    "unit": "number",
    "piece": "number",
    "pair": "number",
    "set": "number",
}


def _normalize_unit(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    text = " ".join(value.strip().lower().split())
    if text in _FORBIDDEN_NUMBER_UNITS:
        return text
    return _UNIT_ALIASES.get(text)


def validate_quantity_unit(
    declaration: Declaration | None,
    *,
    expected_measure_type: str | None = None,
) -> RuleResult:
    """Validate the declared quantity unit without inventing commodity exceptions.

    Rule 12 determines the broad quantity measure (mass, length, area, volume,
    or number), while Rule 13 governs the unit representation. Fourth Schedule
    exceptions and commodity-specific mappings are intentionally not inferred here.
    """
    if declaration is None:
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.FAIL,
            reason="Net quantity unit declaration is missing.",
            legal_reference=LEGAL_REFERENCE,
        )

    evidence = list(declaration.source_regions)
    raw_unit = getattr(declaration, "unit", None)
    normalized = _normalize_unit(raw_unit)

    if normalized is None:
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.REVIEW,
            reason="The detected quantity unit is missing or not recognized as a supported standard unit; manual review is required.",
            confidence=declaration.confidence,
            evidence_regions=evidence,
            legal_reference=LEGAL_REFERENCE,
        )

    if normalized in _FORBIDDEN_NUMBER_UNITS:
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.FAIL,
            reason="Dozen, score, gross, or great gross must not be used as the quantity indication on a package.",
            confidence=declaration.confidence,
            evidence_regions=evidence,
            legal_reference=LEGAL_REFERENCE,
        )

    family = _UNIT_FAMILIES[normalized]
    expected = expected_measure_type.strip().lower() if isinstance(expected_measure_type, str) else None
    expected_aliases = {
        "weight": "mass",
        "measure": None,
        "count": "number",
    }
    expected = expected_aliases.get(expected, expected)

    if expected is not None and expected not in {"mass", "length", "area", "volume", "number"}:
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.REVIEW,
            reason="Commodity measure type is not recognized; the Rule 12 quantity-measure pathway cannot be resolved automatically.",
            confidence=declaration.confidence,
            evidence_regions=evidence,
            legal_reference=LEGAL_REFERENCE,
        )

    if expected is not None and family != expected:
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.FAIL,
            reason=f"Declared unit belongs to the {family} family, but the available commodity context requires {expected}.",
            confidence=declaration.confidence,
            evidence_regions=evidence,
            legal_reference=LEGAL_REFERENCE,
        )

    if normalized == "kg" and isinstance(declaration.value, (int, float)) and declaration.value < 1:
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.FAIL,
            reason="A quantity below one kilogram must be expressed in grams rather than kilograms.",
            confidence=declaration.confidence,
            evidence_regions=evidence,
            legal_reference=LEGAL_REFERENCE,
        )

    if normalized == "l" and isinstance(declaration.value, (int, float)) and declaration.value < 1:
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.FAIL,
            reason="A quantity below one litre must be expressed in millilitres rather than litres.",
            confidence=declaration.confidence,
            evidence_regions=evidence,
            legal_reference=LEGAL_REFERENCE,
        )

    if declaration.confidence < 0.70:
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.REVIEW,
            reason="The quantity unit was detected, but extraction confidence is below the review threshold.",
            confidence=declaration.confidence,
            evidence_regions=evidence,
            legal_reference=LEGAL_REFERENCE,
        )

    if expected is None:
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.REVIEW,
            reason="The quantity unit is recognized, but commodity measure type or a Fourth Schedule exception is not established; manual review is required.",
            confidence=declaration.confidence,
            evidence_regions=evidence,
            legal_reference=LEGAL_REFERENCE,
        )

    return RuleResult(
        rule_id=RULE_ID,
        status=ComplianceStatus.PASS,
        reason="The declared quantity unit matches the available commodity measure type and the supported Rule 13 representation.",
        confidence=declaration.confidence,
        evidence_regions=evidence,
        legal_reference=LEGAL_REFERENCE,
    )
