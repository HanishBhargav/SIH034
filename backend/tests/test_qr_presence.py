from backend.rules.models import ComplianceStatus, Declaration
from backend.rules.validators.qr_presence import validate_qr_presence


def declaration(value, confidence=0.96):
    return Declaration(value=value, confidence=confidence, source_regions=["R12"])


def test_absent_optional_code_passes():
    assert validate_qr_presence(None).status == ComplianceStatus.PASS


def test_qr_passes():
    result = validate_qr_presence(declaration({"type": "qr", "value": "https://example.test/item/1"}))
    assert result.status == ComplianceStatus.PASS


def test_gtin_passes():
    result = validate_qr_presence(declaration({"type": "gtin", "value": "08912345678901"}))
    assert result.status == ComplianceStatus.PASS


def test_unknown_code_requires_review():
    result = validate_qr_presence(declaration({"type": "unknown", "value": "123"}))
    assert result.status == ComplianceStatus.REVIEW


def test_low_confidence_requires_review():
    result = validate_qr_presence(declaration({"type": "qr", "value": "abc"}, 0.69))
    assert result.status == ComplianceStatus.REVIEW
