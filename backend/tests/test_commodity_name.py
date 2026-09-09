from backend.rules.models import ComplianceStatus, Declaration
from backend.rules.validators.commodity_name import validate_commodity_name


def test_commodity_name_passes_when_present_and_confident():
    result = validate_commodity_name(
        Declaration(value="Bath Soap", confidence=0.95, source_regions=["R02"])
    )
    assert result.status == ComplianceStatus.PASS
    assert result.evidence_regions == ["R02"]


def test_commodity_name_fails_when_missing():
    result = validate_commodity_name(None)
    assert result.status == ComplianceStatus.FAIL


def test_commodity_name_fails_when_empty():
    result = validate_commodity_name(
        Declaration(value="   ", confidence=0.95, source_regions=["R02"])
    )
    assert result.status == ComplianceStatus.FAIL


def test_commodity_name_requires_review_at_low_confidence():
    result = validate_commodity_name(
        Declaration(value="Bath Soap", confidence=0.69, source_regions=["R02"])
    )
    assert result.status == ComplianceStatus.REVIEW
