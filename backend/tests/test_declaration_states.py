from backend.rules.engine import evaluate
from backend.rules.models import ComplianceStatus, Declaration, DeclarationState, M2Context, M2Input, OverallStatus


def make_input(declaration_key: str, state: DeclarationState, *, value=None):
    return M2Input(
        inspection_id=f"STATE-{state.value}",
        declarations={
            declaration_key: Declaration(
                value=value,
                confidence=0.93,
                source_regions=["R-STATE"],
                state=state,
            )
        },
        context=M2Context(
            package_type="retail",
            commodity_category="snacks",
            package_quantity=1,
            package_quantity_unit="kg",
        ),
    )


def result_for(result, rule_id):
    return next(item for item in result.results if item.rule_id == rule_id)


def test_missing_state_for_mandatory_declaration_fails_even_when_value_is_present():
    result = evaluate(make_input("commodity_name", DeclarationState.MISSING, value="Potato Chips"))
    item = result_for(result, "DECL_003")

    assert item.status == ComplianceStatus.FAIL
    assert result.overall_status == OverallStatus.NON_COMPLIANT
    assert item.confidence == 0.93
    assert item.evidence_regions == ["R-STATE"]
    assert "MISSING" in item.reason


def test_uncertain_state_requires_review_even_when_value_is_present():
    result = evaluate(make_input("commodity_name", DeclarationState.UNCERTAIN, value="Potato Chips"))
    item = result_for(result, "DECL_003")

    assert item.status == ComplianceStatus.REVIEW
    assert item.confidence == 0.93
    assert item.evidence_regions == ["R-STATE"]
    assert "UNCERTAIN" in item.reason


def test_conflicting_state_requires_review_even_when_value_is_present():
    result = evaluate(make_input("mrp", DeclarationState.CONFLICTING, value=120))
    item = result_for(result, "MRP_001")

    assert item.status == ComplianceStatus.REVIEW
    assert item.confidence == 0.93
    assert item.evidence_regions == ["R-STATE"]
    assert "CONFLICTING" in item.reason


def test_found_state_runs_normal_validator():
    result = evaluate(make_input("commodity_name", DeclarationState.FOUND, value="Potato Chips"))
    item = result_for(result, "DECL_003")

    assert item.status == ComplianceStatus.PASS
    assert result.overall_status == OverallStatus.NON_COMPLIANT


def test_explicit_state_overrides_populated_value_for_quantity():
    result = evaluate(make_input("net_quantity", DeclarationState.MISSING, value=500))
    qty = result_for(result, "QTY_001")
    unit = result_for(result, "QTY_002")

    assert qty.status == ComplianceStatus.FAIL
    # QTY_002 validates the separate net_quantity_unit field, which is absent
    # in this fixture; it must not inherit net_quantity's declaration state.
    assert unit.status == ComplianceStatus.REVIEW
    assert result.overall_status == OverallStatus.NON_COMPLIANT


def test_state_result_keeps_rule_legal_reference():
    result = evaluate(make_input("mrp", DeclarationState.UNCERTAIN, value=120))
    item = result_for(result, "MRP_001")

    assert item.status == ComplianceStatus.REVIEW
    assert item.legal_reference.endswith("Rule 6(1)(e)")
