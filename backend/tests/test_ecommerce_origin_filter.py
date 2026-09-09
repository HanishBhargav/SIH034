from backend.rules.models import ComplianceStatus, Declaration
from backend.rules.validators.ecommerce_origin_filter import validate_ecommerce_country_origin_filter


def test_ecommerce_origin_filter_passes_when_complete():
    result = validate_ecommerce_country_origin_filter(
        Declaration(
            value={"filter_present": True, "searchable": True, "sortable": True, "country_of_origin": True},
            confidence=0.96,
            source_regions=["FILTER"],
        )
    )
    assert result.status == ComplianceStatus.PASS


def test_ecommerce_origin_filter_fails_when_missing():
    result = validate_ecommerce_country_origin_filter(None)
    assert result.status == ComplianceStatus.FAIL


def test_ecommerce_origin_filter_fails_when_not_sortable():
    result = validate_ecommerce_country_origin_filter(
        Declaration(
            value={"filter_present": True, "searchable": True, "sortable": False, "country_of_origin": True},
            confidence=0.96,
        )
    )
    assert result.status == ComplianceStatus.FAIL
    assert "sortable" in result.reason


def test_ecommerce_origin_filter_reviews_low_confidence():
    result = validate_ecommerce_country_origin_filter(
        Declaration(value=True, confidence=0.50)
    )
    assert result.status == ComplianceStatus.REVIEW
