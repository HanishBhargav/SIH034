from backend.rules.models import ComplianceStatus, Declaration, DeclarationState
from backend.rules.validators.consumer_care import validate_consumer_care


def _valid_declaration(**overrides):
    value = {
        "name": "ABC Consumer Care Office",
        "address": "12 Market Road, Mumbai, Maharashtra",
        "telephone": "+91 9876543210",
        "email": "care@example.com",
    }
    value.update(overrides)
    return Declaration(value=value, confidence=0.94, source_regions=["R05"])


def test_consumer_care_missing_fails():
    result = validate_consumer_care(None)
    assert result.status == ComplianceStatus.FAIL


def test_consumer_care_complete_structured_declaration_passes():
    result = validate_consumer_care(_valid_declaration())
    assert result.status == ComplianceStatus.PASS
    assert result.evidence_regions == ["R05"]
    assert result.legal_reference.endswith("Rule 6(2)")


def test_consumer_care_missing_required_field_fails():
    result = validate_consumer_care(_valid_declaration(email=""))
    assert result.status == ComplianceStatus.FAIL
    assert "e-mail" in result.reason


def test_consumer_care_low_confidence_requires_review():
    declaration = _valid_declaration()
    declaration.confidence = 0.65
    result = validate_consumer_care(declaration)
    assert result.status == ComplianceStatus.REVIEW


def test_consumer_care_unclassified_text_requires_review():
    result = validate_consumer_care(
        Declaration(
            value="ABC Consumer Care Office, Mumbai, 9876543210, care@example.com",
            confidence=0.94,
            source_regions=["R05"],
        )
    )
    assert result.status == ComplianceStatus.REVIEW


def test_consumer_care_invalid_email_requires_review():
    result = validate_consumer_care(_valid_declaration(email="not-an-email"))
    assert result.status == ComplianceStatus.REVIEW


def test_consumer_care_invalid_phone_requires_review():
    result = validate_consumer_care(_valid_declaration(telephone="12"))
    assert result.status == ComplianceStatus.REVIEW


def test_consumer_care_uncertain_state_requires_review():
    declaration = _valid_declaration()
    declaration.state = DeclarationState.UNCERTAIN
    result = validate_consumer_care(declaration)
    assert result.status == ComplianceStatus.REVIEW


def test_consumer_care_supports_phone_alias_and_email_alias():
    result = validate_consumer_care(
        Declaration(
            value={
                "office": "ABC Consumer Care Office",
                "address": "12 Market Road, Mumbai",
                "phone": "+91 9876543210",
                "email_address": "care@example.com",
            },
            confidence=0.90,
            source_regions=["R05"],
        )
    )
    assert result.status == ComplianceStatus.PASS
