from backend.rules.models import ComplianceStatus, Declaration
from backend.rules.validators.party_declaration import validate_party_declaration


def test_party_declaration_missing_fails():
    result = validate_party_declaration(None)
    assert result.status == ComplianceStatus.FAIL


def test_party_declaration_empty_fails():
    result = validate_party_declaration(
        Declaration(value="", confidence=0.95, source_regions=["R02"])
    )
    assert result.status == ComplianceStatus.FAIL


def test_party_declaration_with_evidence_passes():
    result = validate_party_declaration(
        Declaration(
            value="ABC Foods Pvt Ltd, Mumbai, Maharashtra",
            confidence=0.94,
            source_regions=["R02"],
        )
    )
    assert result.status == ComplianceStatus.PASS
    assert result.evidence_regions == ["R02"]


def test_party_declaration_low_confidence_requires_review():
    result = validate_party_declaration(
        Declaration(value="ABC Foods", confidence=0.65, source_regions=["R02"])
    )
    assert result.status == ComplianceStatus.REVIEW


def test_party_declaration_structured_value_passes_when_nonempty():
    result = validate_party_declaration(
        Declaration(
            value={"name": "ABC Foods", "address": "Mumbai"},
            confidence=0.90,
            source_regions=["R02", "R03"],
        )
    )
    assert result.status == ComplianceStatus.PASS
