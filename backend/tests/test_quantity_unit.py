from backend.rules.models import ComplianceStatus, QuantityDeclaration
from backend.rules.validators.quantity_unit import validate_quantity_unit


def declaration(value, unit, confidence=0.95):
    return QuantityDeclaration(
        value=value,
        unit=unit,
        confidence=confidence,
        source_regions=["R03"],
    )


def test_mass_unit_matches_expected_type():
    result = validate_quantity_unit(
        declaration(500, "g"),
        expected_measure_type="mass",
    )
    assert result.status == ComplianceStatus.PASS


def test_volume_unit_matches_expected_type():
    result = validate_quantity_unit(
        declaration(500, "ml"),
        expected_measure_type="volume",
    )
    assert result.status == ComplianceStatus.PASS


def test_number_unit_matches_expected_type():
    result = validate_quantity_unit(
        declaration(10, "piece"),
        expected_measure_type="number",
    )
    assert result.status == ComplianceStatus.PASS


def test_unit_family_mismatch_fails():
    result = validate_quantity_unit(
        declaration(500, "ml"),
        expected_measure_type="mass",
    )
    assert result.status == ComplianceStatus.FAIL


def test_sub_one_kg_cannot_be_declared_in_kg():
    result = validate_quantity_unit(
        declaration(0.5, "kg"),
        expected_measure_type="mass",
    )
    assert result.status == ComplianceStatus.FAIL


def test_sub_one_litre_cannot_be_declared_in_litre():
    result = validate_quantity_unit(
        declaration(0.5, "L"),
        expected_measure_type="volume",
    )
    assert result.status == ComplianceStatus.FAIL


def test_forbidden_dozen_unit_fails():
    result = validate_quantity_unit(
        declaration(1, "dozen"),
        expected_measure_type="number",
    )
    assert result.status == ComplianceStatus.FAIL


def test_unknown_unit_requires_review():
    result = validate_quantity_unit(
        declaration(500, "oz"),
        expected_measure_type="mass",
    )
    assert result.status == ComplianceStatus.REVIEW


def test_unknown_measure_type_requires_review():
    result = validate_quantity_unit(declaration(500, "g"))
    assert result.status == ComplianceStatus.REVIEW


def test_low_confidence_requires_review():
    result = validate_quantity_unit(
        declaration(500, "g", confidence=0.60),
        expected_measure_type="mass",
    )
    assert result.status == ComplianceStatus.REVIEW


def test_missing_declaration_fails():
    result = validate_quantity_unit(None, expected_measure_type="mass")
    assert result.status == ComplianceStatus.FAIL
