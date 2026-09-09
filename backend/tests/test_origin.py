from backend.rules.models import ComplianceStatus, Declaration
from backend.rules.validators.origin import validate_origin_declaration


def test_non_imported_package_does_not_require_origin():
    result = validate_origin_declaration(None, is_imported=False)
    assert result.status == ComplianceStatus.PASS


def test_unknown_import_status_requires_review():
    result = validate_origin_declaration(None, is_imported=None)
    assert result.status == ComplianceStatus.REVIEW


def test_imported_package_without_origin_fails():
    result = validate_origin_declaration(None, is_imported=True)
    assert result.status == ComplianceStatus.FAIL


def test_imported_package_with_origin_passes():
    result = validate_origin_declaration(
        Declaration(
            value="India",
            confidence=0.95,
            source_regions=["R05"],
        ),
        is_imported=True,
    )
    assert result.status == ComplianceStatus.PASS
    assert result.evidence_regions == ["R05"]


def test_imported_origin_low_confidence_requires_review():
    result = validate_origin_declaration(
        Declaration(value="China", confidence=0.65, source_regions=["R05"]),
        is_imported=True,
    )
    assert result.status == ComplianceStatus.REVIEW


def test_imported_empty_origin_fails():
    result = validate_origin_declaration(
        Declaration(value="   ", confidence=0.95, source_regions=["R05"]),
        is_imported=True,
    )
    assert result.status == ComplianceStatus.FAIL
