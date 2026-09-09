from backend.rules.models import ComplianceStatus, Declaration
from backend.rules.validators.quantity import validate_net_quantity


def test_missing_quantity_fails():
    result = validate_net_quantity(None)
    assert result.rule_id == "QTY_001"
    assert result.status == ComplianceStatus.FAIL


def test_numeric_quantity_passes():
    result = validate_net_quantity(
        Declaration(value=500, confidence=0.95, source_regions=["R03"])
    )
    assert result.status == ComplianceStatus.PASS
    assert result.confidence == 0.95
    assert result.evidence_regions == ["R03"]


def test_numeric_string_quantity_passes():
    result = validate_net_quantity(
        Declaration(value="1,250", confidence=0.90, source_regions=["R03"])
    )
    assert result.status == ComplianceStatus.PASS


def test_unparseable_quantity_fails():
    result = validate_net_quantity(
        Declaration(value="five hundred", confidence=0.92, source_regions=["R03"])
    )
    assert result.status == ComplianceStatus.FAIL


def test_zero_quantity_fails():
    result = validate_net_quantity(
        Declaration(value=0, confidence=0.95, source_regions=["R03"])
    )
    assert result.status == ComplianceStatus.FAIL


def test_negative_quantity_fails():
    result = validate_net_quantity(
        Declaration(value=-10, confidence=0.95, source_regions=["R03"])
    )
    assert result.status == ComplianceStatus.FAIL


def test_low_confidence_quantity_requires_review():
    result = validate_net_quantity(
        Declaration(value=500, confidence=0.60, source_regions=["R03"])
    )
    assert result.status == ComplianceStatus.REVIEW
