from backend.rules.models import ComplianceStatus, Declaration
from backend.rules.validators.commodity_dimension import validate_commodity_dimension


def declaration(value, confidence=0.96):
    return Declaration(value=value, confidence=confidence, source_regions=["R13"])


def test_complete_dimensions_pass():
    result = validate_commodity_dimension(declaration({"length": 10, "width": 5, "height": 2, "unit": "cm"}))
    assert result.status == ComplianceStatus.PASS


def test_missing_dimensions_fail():
    assert validate_commodity_dimension(None).status == ComplianceStatus.FAIL


def test_incomplete_dimensions_require_review():
    result = validate_commodity_dimension(declaration({"length": 10, "width": 5, "unit": "cm"}))
    assert result.status == ComplianceStatus.REVIEW


def test_invalid_dimensions_require_review():
    result = validate_commodity_dimension(declaration({"length": -1, "width": 5, "height": 2, "unit": "cm"}))
    assert result.status == ComplianceStatus.REVIEW


def test_missing_unit_requires_review():
    result = validate_commodity_dimension(declaration({"length": 10, "width": 5, "height": 2}))
    assert result.status == ComplianceStatus.REVIEW


def test_low_confidence_requires_review():
    result = validate_commodity_dimension(declaration({"length": 10, "width": 5, "height": 2, "unit": "cm"}, 0.69))
    assert result.status == ComplianceStatus.REVIEW
