from backend.rules.models import ComplianceStatus, Declaration
from backend.rules.validators.date_declaration import validate_manufacture_month_year


def declaration(value, confidence=0.96):
    return Declaration(value=value, confidence=confidence, source_regions=["R07"])


def test_valid_month_year_passes():
    result = validate_manufacture_month_year(declaration("09/2026"))
    assert result.status == ComplianceStatus.PASS


def test_month_name_and_year_passes():
    result = validate_manufacture_month_year(declaration("September 2026"))
    assert result.status == ComplianceStatus.PASS


def test_year_month_passes():
    result = validate_manufacture_month_year(declaration("2026-09"))
    assert result.status == ComplianceStatus.PASS


def test_missing_date_fails():
    result = validate_manufacture_month_year(None)
    assert result.status == ComplianceStatus.FAIL


def test_low_confidence_requires_review():
    result = validate_manufacture_month_year(declaration("09/2026", confidence=0.69))
    assert result.status == ComplianceStatus.REVIEW


def test_invalid_month_year_requires_review():
    result = validate_manufacture_month_year(declaration("2026-19"))
    assert result.status == ComplianceStatus.REVIEW


def test_food_category_requires_other_law_review():
    result = validate_manufacture_month_year(None, commodity_category="food")
    assert result.status == ComplianceStatus.REVIEW


def test_seeds_category_requires_other_law_review():
    result = validate_manufacture_month_year(None, commodity_category="seeds")
    assert result.status == ComplianceStatus.REVIEW


def test_cosmetics_category_requires_other_law_review():
    result = validate_manufacture_month_year(None, commodity_category="cosmetics")
    assert result.status == ComplianceStatus.REVIEW


def test_bidi_category_is_exempt():
    result = validate_manufacture_month_year(None, commodity_category="bidi")
    assert result.status == ComplianceStatus.PASS
