from backend.rules.models import ComplianceStatus, Declaration
from backend.rules.validators.mrp_presence import validate_mrp_presence


def test_mrp_presence_passes_for_non_empty_declaration():
    result = validate_mrp_presence(
        Declaration(value=120, confidence=0.95, source_regions=["R05"])
    )
    assert result.rule_id == "MRP_001"
    assert result.status == ComplianceStatus.PASS
    assert result.evidence_regions == ["R05"]


def test_mrp_presence_fails_when_missing():
    result = validate_mrp_presence(None)
    assert result.status == ComplianceStatus.FAIL


def test_mrp_presence_fails_when_empty():
    result = validate_mrp_presence(
        Declaration(value="   ", confidence=0.95, source_regions=["R05"])
    )
    assert result.status == ComplianceStatus.FAIL


def test_mrp_presence_reviews_low_confidence():
    result = validate_mrp_presence(
        Declaration(value=120, confidence=0.69, source_regions=["R05"])
    )
    assert result.status == ComplianceStatus.REVIEW
    assert result.confidence == 0.69


def test_mrp_presence_preserves_evidence():
    result = validate_mrp_presence(
        Declaration(value="₹120", confidence=0.91, source_regions=["R01", "R05"])
    )
    assert result.status == ComplianceStatus.PASS
    assert result.evidence_regions == ["R01", "R05"]
