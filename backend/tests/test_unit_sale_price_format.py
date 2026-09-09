from backend.rules.models import ComplianceStatus, Declaration, DeclarationState, QuantityDeclaration
from backend.rules.validators.unit_sale_price_format import validate_unit_sale_price_format


def quantity(value, unit="g"):
    return QuantityDeclaration(value=value, unit=unit, confidence=0.96, source_regions=["Q1"])


def usp(value, unit="g"):
    return Declaration(value=value, unit=unit, confidence=0.96, source_regions=["U1"])


def test_unit_sale_price_format_accepts_whole_number():
    result = validate_unit_sale_price_format(usp(120, "kg"), net_quantity=quantity(1, "kg"))
    assert result.status == ComplianceStatus.PASS


def test_unit_sale_price_format_accepts_two_decimal_places():
    result = validate_unit_sale_price_format(usp(0.24, "g"), net_quantity=quantity(500))
    assert result.status == ComplianceStatus.PASS


def test_unit_sale_price_format_rejects_more_than_two_decimal_places():
    result = validate_unit_sale_price_format(usp(0.241, "g"), net_quantity=quantity(500))
    assert result.status == ComplianceStatus.FAIL


def test_unit_sale_price_format_rejects_wrong_unit():
    result = validate_unit_sale_price_format(usp(240, "kg"), net_quantity=quantity(500))
    assert result.status == ComplianceStatus.FAIL


def test_unit_sale_price_format_reviews_uncertain_declaration():
    declaration = usp(0.24, "g")
    declaration.state = DeclarationState.UNCERTAIN
    result = validate_unit_sale_price_format(declaration, net_quantity=quantity(500))
    assert result.status == ComplianceStatus.REVIEW


def test_unit_sale_price_format_passes_when_declaration_absent():
    result = validate_unit_sale_price_format(None, net_quantity=quantity(500))
    assert result.status == ComplianceStatus.PASS
