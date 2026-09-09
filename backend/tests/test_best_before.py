from backend.rules.models import ComplianceStatus, Declaration, DeclarationState
from backend.rules.validators.best_before import validate_best_before_use_by


def declaration(value, confidence=0.96, state=None):
    return Declaration(value=value, confidence=confidence, source_regions=["R08"], state=state)


def test_not_applicable_passes():
    result = validate_best_before_use_by(None, applicable=False)
    assert result.status == ComplianceStatus.PASS


def test_unknown_applicability_requires_review():
    result = validate_best_before_use_by(None, applicable=None)
    assert result.status == ComplianceStatus.REVIEW


def test_missing_required_declaration_fails():
    result = validate_best_before_use_by(None, applicable=True)
    assert result.status == ComplianceStatus.FAIL


def test_date_declaration_passes():
    result = validate_best_before_use_by(declaration("Best Before 30/09/2027"), applicable=True)
    assert result.status == ComplianceStatus.PASS


def test_month_year_declaration_passes():
    result = validate_best_before_use_by(declaration("Use By 09/2027"), applicable=True)
    assert result.status == ComplianceStatus.PASS


def test_validity_period_passes():
    result = validate_best_before_use_by(
        declaration("Best Before 12 months from manufacture"), applicable=True
    )
    assert result.status == ComplianceStatus.PASS


def test_low_confidence_requires_review():
    result = validate_best_before_use_by(declaration("Best Before 09/2027", 0.69), applicable=True)
    assert result.status == ComplianceStatus.REVIEW


def test_uncertain_state_requires_review():
    result = validate_best_before_use_by(
        declaration("Best Before 09/2027", state=DeclarationState.UNCERTAIN), applicable=True
    )
    assert result.status == ComplianceStatus.REVIEW


def test_unparseable_value_requires_review():
    result = validate_best_before_use_by(declaration("Best Before whenever"), applicable=True)
    assert result.status == ComplianceStatus.REVIEW
