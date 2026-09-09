from backend.rules.models import ComplianceStatus, Declaration
from backend.rules.validators.veg_nonveg_dot import validate_veg_nonveg_dot


def declaration(value, confidence=0.96):
    return Declaration(value=value, confidence=confidence, source_regions=["R10"])


def test_valid_veg_marking_passes():
    assert validate_veg_nonveg_dot(declaration("veg")).status == ComplianceStatus.PASS


def test_valid_nonveg_marking_passes():
    assert validate_veg_nonveg_dot(declaration("non-veg")).status == ComplianceStatus.PASS


def test_missing_declaration_fails():
    assert validate_veg_nonveg_dot(None).status == ComplianceStatus.FAIL


def test_low_confidence_requires_review():
    assert validate_veg_nonveg_dot(declaration("veg", 0.69)).status == ComplianceStatus.REVIEW


def test_unknown_marking_requires_review():
    assert validate_veg_nonveg_dot(declaration("symbol")).status == ComplianceStatus.REVIEW
