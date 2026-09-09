from collections.abc import Iterable

from ..models import ComplianceStatus, Measurement, RuleResult

FONT_RULE_ID = "FONT_001"
NUMERAL_RULE_ID = "MRP_003"
_REVIEW_THRESHOLD = 0.70

# Rule 7 Table-I: minimum height in mm by principal-display-panel area.
# Each tuple is (upper_bound_inclusive, normal_height, formed_height).
_HEIGHT_BANDS = (
    (50.0, 1.0, 2.0),
    (100.0, 1.5, 3.0),
    (500.0, 2.5, 4.0),
    (2500.0, 4.0, 6.0),
    (float("inf"), 6.0, 6.0),
)


def _measurement_type(measurement: Measurement) -> str:
    return measurement.type.strip().lower().replace("-", "_").replace(" ", "_")


def _find_measurement(measurements: Iterable[Measurement], names: set[str]) -> Measurement | None:
    for measurement in measurements:
        if _measurement_type(measurement) in names:
            return measurement
    return None


def _panel_area(measurements: list[Measurement]) -> Measurement | None:
    return _find_measurement(
        measurements,
        {
            "principal_display_panel_area",
            "pdp_area",
            "panel_area",
        },
    )


def _required_height(area_cm2: float, formed: bool) -> float:
    for upper_bound, normal_height, formed_height in _HEIGHT_BANDS:
        if area_cm2 <= upper_bound:
            return formed_height if formed else normal_height
    raise AssertionError("unreachable")


def _valid_mm_measurement(measurement: Measurement | None, description: str) -> RuleResult | None:
    if measurement is None:
        return RuleResult(
            rule_id=FONT_RULE_ID,
            status=ComplianceStatus.REVIEW,
            reason=f"M1 did not provide a reliable physical {description} measurement; manual review is required.",
            legal_reference="Legal Metrology (Packaged Commodities) Rules, 2011, Rule 7",
        )
    if measurement.unit.strip().lower() != "mm":
        return RuleResult(
            rule_id=FONT_RULE_ID,
            status=ComplianceStatus.REVIEW,
            reason=f"M1 provided {description} in a non-mm unit; physical size cannot be evaluated reliably.",
            confidence=measurement.confidence,
            evidence_regions=measurement.source_regions,
            legal_reference="Legal Metrology (Packaged Commodities) Rules, 2011, Rule 7",
        )
    if measurement.value <= 0 or measurement.confidence < _REVIEW_THRESHOLD:
        return RuleResult(
            rule_id=FONT_RULE_ID,
            status=ComplianceStatus.REVIEW,
            reason=f"M1's {description} measurement is too uncertain for an automatic legal-size decision.",
            confidence=measurement.confidence,
            evidence_regions=measurement.source_regions,
            legal_reference="Legal Metrology (Packaged Commodities) Rules, 2011, Rule 7",
        )
    method = measurement.method.strip().lower()
    if not any(token in method for token in ("calibr", "pixel_to_mm", "scale_reference", "physical")):
        return RuleResult(
            rule_id=FONT_RULE_ID,
            status=ComplianceStatus.REVIEW,
            reason=f"M1 did not indicate a physically calibrated method for {description}; manual review is required.",
            confidence=measurement.confidence,
            evidence_regions=measurement.source_regions,
            legal_reference="Legal Metrology (Packaged Commodities) Rules, 2011, Rule 7",
        )
    return None


def _validate_height(
    rule_id: str,
    measurement: Measurement | None,
    area: Measurement | None,
    *,
    formed: bool,
    description: str,
) -> RuleResult:
    legal_reference = "Legal Metrology (Packaged Commodities) Rules, 2011, Rule 7"

    if area is None:
        return RuleResult(
            rule_id=rule_id,
            status=ComplianceStatus.REVIEW,
            reason="M1 did not provide principal display panel area, so the Rule 7 minimum height band cannot be determined.",
            legal_reference=legal_reference,
        )
    if area.unit.strip().lower() not in {"cm2", "cm²"} or area.value <= 0 or area.confidence < _REVIEW_THRESHOLD:
        return RuleResult(
            rule_id=rule_id,
            status=ComplianceStatus.REVIEW,
            reason="Principal display panel area from M1 is missing, invalid, or too uncertain for an automatic Rule 7 decision.",
            confidence=area.confidence,
            evidence_regions=area.source_regions,
            legal_reference=legal_reference,
        )

    measurement_check = _valid_mm_measurement(measurement, description)
    if measurement_check is not None:
        measurement_check.rule_id = rule_id
        measurement_check.legal_reference = legal_reference
        return measurement_check

    required = _required_height(area.value, formed)
    assert measurement is not None
    status = ComplianceStatus.PASS if measurement.value >= required else ComplianceStatus.FAIL
    mode = "formed/blown/molded" if formed else "normal"
    reason = (
        f"Measured {description} height is {measurement.value:.2f} mm; Rule 7 requires at least "
        f"{required:.2f} mm for a {area.value:.2f} cm² principal display panel ({mode} case)."
    )
    return RuleResult(
        rule_id=rule_id,
        status=status,
        reason=reason,
        confidence=min(measurement.confidence, area.confidence),
        evidence_regions=list(dict.fromkeys(measurement.source_regions + area.source_regions)),
        legal_reference=legal_reference,
    )


def validate_font_height(measurements: list[Measurement]) -> RuleResult:
    """Validate generic numeral/letter height under Rule 7 Table-I."""
    area = _panel_area(measurements)
    measurement = _find_measurement(
        measurements,
        {"font_height", "letter_height", "numeral_letter_height"},
    )
    formed = _find_measurement(measurements, {"font_height_formed", "letter_height_formed", "numeral_letter_height_formed"}) is not None
    if measurement is None and formed:
        measurement = _find_measurement(measurements, {"font_height_formed", "letter_height_formed", "numeral_letter_height_formed"})
    return _validate_height(FONT_RULE_ID, measurement, area, formed=formed, description="numeral/letter")


def validate_mrp_numeral_height(measurements: list[Measurement]) -> RuleResult:
    """Validate the physical height of the printed MRP value's numerals."""
    area = _panel_area(measurements)
    measurement = _find_measurement(
        measurements,
        {"mrp_numeral_height", "mrp_value_numeral_height"},
    )
    formed = _find_measurement(measurements, {"mrp_numeral_height_formed", "mrp_value_numeral_height_formed"}) is not None
    if measurement is None and formed:
        measurement = _find_measurement(measurements, {"mrp_numeral_height_formed", "mrp_value_numeral_height_formed"})
    result = _validate_height(NUMERAL_RULE_ID, measurement, area, formed=formed, description="MRP numeral")
    # FAQ 45 clarifies that this numeral-size check is for the MRP value,
    # not the "MRP Rs." prefix or "inclusive of all taxes" suffix.
    return result
