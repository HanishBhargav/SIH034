from backend.rules.models import ComplianceStatus, Declaration, MoneyDeclaration, QuantityDeclaration
from backend.rules.validators.unit_sale_price import validate_unit_sale_price


def quantity(value, unit="g"):
    return QuantityDeclaration(value=value, unit=unit, confidence=0.96, source_regions=["Q1"])


def mrp(value):
    return MoneyDeclaration(value=value, currency="INR", confidence=0.96, source_regions=["M1"])


def test_unit_sale_price_passes_per_gram_for_sub_kg_package():
    result = validate_unit_sale_price(
        Declaration(value=0.24, unit="g", confidence=0.96, source_regions=["U1"]),
        net_quantity=quantity(500),
        mrp=mrp(120),
    )
    assert result.status == ComplianceStatus.PASS


def test_unit_sale_price_requires_per_kg_for_one_kg_package():
    result = validate_unit_sale_price(
        Declaration(value=120, unit="kg", confidence=0.96),
        net_quantity=quantity(1, "kg"),
        mrp=mrp(120),
    )
    assert result.status == ComplianceStatus.PASS


def test_unit_sale_price_fails_when_missing_and_not_exempt():
    result = validate_unit_sale_price(None, net_quantity=quantity(500), mrp=mrp(120))
    assert result.status == ComplianceStatus.FAIL


def test_unit_sale_price_passes_when_mrp_equals_unit_sale_price():
    result = validate_unit_sale_price(None, net_quantity=quantity(1, "kg"), mrp=mrp(120))
    assert result.status == ComplianceStatus.PASS


def test_unit_sale_price_passes_for_10g_exemption():
    result = validate_unit_sale_price(None, net_quantity=quantity(10), mrp=mrp(20))
    assert result.status == ComplianceStatus.PASS


def test_unit_sale_price_fails_on_wrong_unit():
    result = validate_unit_sale_price(
        Declaration(value=240, unit="kg", confidence=0.96),
        net_quantity=quantity(500),
        mrp=mrp(120),
    )
    assert result.status == ComplianceStatus.FAIL
