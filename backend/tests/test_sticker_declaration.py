from backend.rules.models import ComplianceStatus, Declaration
from backend.rules.validators.sticker_declaration import validate_sticker_declaration


def declaration(value, confidence=0.96):
    return Declaration(value=value, confidence=confidence, source_regions=["R11"])


def test_mandatory_declaration_alteration_fails():
    result = validate_sticker_declaration(declaration({"alters_mandatory_declaration": True}))
    assert result.status == ComplianceStatus.FAIL


def test_reduced_mrp_without_covering_original_passes():
    result = validate_sticker_declaration(declaration({"type": "mrp_reduction", "covers_original_mrp": False}))
    assert result.status == ComplianceStatus.PASS


def test_reduced_mrp_covering_original_fails():
    result = validate_sticker_declaration(declaration({"type": "mrp_reduction", "covers_original_mrp": True}))
    assert result.status == ComplianceStatus.FAIL


def test_additional_information_passes():
    result = validate_sticker_declaration(declaration({"type": "non_mandatory"}))
    assert result.status == ComplianceStatus.PASS


def test_unknown_sticker_requires_review():
    result = validate_sticker_declaration(declaration({"type": "unknown"}))
    assert result.status == ComplianceStatus.REVIEW
