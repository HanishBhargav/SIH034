from backend.rules.models import ComplianceStatus, MoneyDeclaration
from backend.rules.validators.mrp_format import validate_mrp_format


def mrp(value=120, currency="INR", confidence=0.96, regions=None):
    return MoneyDeclaration(
        value=value,
        currency=currency,
        confidence=confidence,
        source_regions=regions or ["R05"],
    )


def tax_text(text="MRP ₹120 (inclusive of all taxes)"):
    return [{"id": "R05", "text": text}]


def test_valid_mrp_format_passes():
    result = validate_mrp_format(mrp(), text_blocks=tax_text())
    assert result.status == ComplianceStatus.PASS


def test_missing_mrp_fails():
    result = validate_mrp_format(None, text_blocks=tax_text())
    assert result.status == ComplianceStatus.FAIL


def test_non_inr_currency_fails():
    result = validate_mrp_format(mrp(currency="USD"), text_blocks=tax_text())
    assert result.status == ComplianceStatus.FAIL


def test_missing_currency_requires_review():
    declaration = MoneyDeclaration(value=120, confidence=0.96, source_regions=["R05"])
    result = validate_mrp_format(declaration, text_blocks=tax_text())
    assert result.status == ComplianceStatus.REVIEW


def test_low_confidence_requires_review():
    result = validate_mrp_format(mrp(confidence=0.69), text_blocks=tax_text())
    assert result.status == ComplianceStatus.REVIEW


def test_non_numeric_mrp_requires_review():
    result = validate_mrp_format(mrp(value="one hundred"), text_blocks=tax_text())
    assert result.status == ComplianceStatus.REVIEW


def test_missing_tax_inclusive_wording_fails():
    result = validate_mrp_format(mrp(), text_blocks=tax_text("MRP ₹120"))
    assert result.status == ComplianceStatus.FAIL


def test_tax_wording_can_be_in_same_source_region():
    result = validate_mrp_format(
        mrp(regions=["R05"]),
        text_blocks=[{"id": "R05", "text": "MRP ₹120 incl. of all taxes"}],
    )
    assert result.status == ComplianceStatus.PASS


def test_tax_wording_in_unrelated_region_is_not_used():
    result = validate_mrp_format(
        mrp(regions=["R05"]),
        text_blocks=[
            {"id": "R05", "text": "MRP ₹120"},
            {"id": "R99", "text": "inclusive of all taxes"},
        ],
    )
    assert result.status == ComplianceStatus.FAIL


def test_missing_text_evidence_requires_review():
    result = validate_mrp_format(mrp(), text_blocks=None)
    assert result.status == ComplianceStatus.REVIEW
