from backend.rules.models import ComplianceStatus, Declaration
from backend.rules.validators.gm_food import validate_gm_food_declaration


def declaration(value, confidence=0.96):
    return Declaration(value=value, confidence=confidence, source_regions=["R09"])


def test_present_gm_passes():
    result = validate_gm_food_declaration(declaration("GM"))
    assert result.status == ComplianceStatus.PASS


def test_missing_declaration_fails():
    result = validate_gm_food_declaration(None)
    assert result.status == ComplianceStatus.FAIL


def test_low_confidence_requires_review():
    result = validate_gm_food_declaration(declaration("GM", 0.69))
    assert result.status == ComplianceStatus.REVIEW


def test_wrong_marking_requires_review():
    result = validate_gm_food_declaration(declaration("GMO"))
    assert result.status == ComplianceStatus.REVIEW


def test_explicit_absence_fails():
    result = validate_gm_food_declaration(declaration({"present": False}))
    assert result.status == ComplianceStatus.FAIL
