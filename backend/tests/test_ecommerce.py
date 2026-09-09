from backend.rules.models import ComplianceStatus, Declaration
from backend.rules.validators.ecommerce import validate_ecommerce_mandatory_declarations


def listing(**overrides):
    value = {
        "manufacturer_or_packer_details": "ABC Foods",
        "commodity_name": "Potato Chips",
        "net_quantity": "500 g",
        "mrp": "₹120 inclusive of all taxes",
        "consumer_care": "18001234567 / care@example.com",
    }
    value.update(overrides)
    return Declaration(value=value, confidence=0.96, source_regions=["LISTING"])


def test_ecommerce_rule_passes_for_complete_domestic_listing():
    result = validate_ecommerce_mandatory_declarations(
        listing(),
        is_imported=False,
        best_before_use_by_applicable=False,
        dimensions_applicable=False,
    )
    assert result.status == ComplianceStatus.PASS


def test_ecommerce_rule_requires_origin_for_imported_listing():
    result = validate_ecommerce_mandatory_declarations(
        listing(),
        is_imported=True,
        best_before_use_by_applicable=False,
        dimensions_applicable=False,
    )
    assert result.status == ComplianceStatus.FAIL
    assert "country_of_origin" in result.reason


def test_ecommerce_rule_requires_best_before_when_applicable():
    result = validate_ecommerce_mandatory_declarations(
        listing(),
        is_imported=False,
        best_before_use_by_applicable=True,
        dimensions_applicable=False,
    )
    assert result.status == ComplianceStatus.FAIL
    assert "best_before_use_by" in result.reason


def test_ecommerce_rule_requires_dimensions_when_applicable():
    result = validate_ecommerce_mandatory_declarations(
        listing(),
        is_imported=False,
        best_before_use_by_applicable=False,
        dimensions_applicable=True,
    )
    assert result.status == ComplianceStatus.FAIL
    assert "dimensions" in result.reason


def test_ecommerce_rule_does_not_require_manufacture_month_year():
    result = validate_ecommerce_mandatory_declarations(
        listing(),
        is_imported=False,
        best_before_use_by_applicable=False,
        dimensions_applicable=False,
    )
    assert result.status == ComplianceStatus.PASS
    assert "manufacture/packing month and year" in result.reason


def test_ecommerce_rule_reviews_unknown_context():
    result = validate_ecommerce_mandatory_declarations(
        listing(),
        is_imported=None,
        best_before_use_by_applicable=False,
        dimensions_applicable=False,
    )
    assert result.status == ComplianceStatus.REVIEW
