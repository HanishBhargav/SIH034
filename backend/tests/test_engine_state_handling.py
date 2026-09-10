from backend.rules.engine import evaluate
from backend.rules.models import ComplianceStatus, Declaration, DeclarationState, M2Context, M2Input, OverallStatus


def make_input(declarations, **context_overrides):
    context = {
        "package_type": "retail",
        "commodity_category": "snacks",
        "package_quantity": 1,
        "package_quantity_unit": "kg",
    }
    context.update(context_overrides)
    return M2Input(
        inspection_id="STATE-001",
        declarations=declarations,
        context=M2Context(**context),
    )


def test_uncertain_declaration_forces_review_even_with_value():
    result = evaluate(make_input({
        "commodity_name": Declaration(
            value="Potato Chips",
            confidence=0.99,
            source_regions=["R01"],
            state=DeclarationState.UNCERTAIN,
        )
    }))
    item = next(item for item in result.results if item.rule_id == "DECL_003")
    assert item.status == ComplianceStatus.REVIEW
    assert "UNCERTAIN" in item.reason
    assert item.evidence_regions == ["R01"]
    assert result.overall_status == OverallStatus.NON_COMPLIANT


def test_conflicting_declaration_forces_review_even_with_value():
    result = evaluate(make_input({
        "mrp": Declaration(
            value=120,
            confidence=0.99,
            source_regions=["R05"],
            state=DeclarationState.CONFLICTING,
        )
    }))
    item = next(item for item in result.results if item.rule_id == "MRP_001")
    assert item.status == ComplianceStatus.REVIEW
    assert "CONFLICTING" in item.reason
    assert result.overall_status == OverallStatus.NON_COMPLIANT


def test_missing_state_forces_fail_even_if_parser_supplied_value():
    result = evaluate(make_input({
        "commodity_name": Declaration(
            value="Potato Chips",
            confidence=0.99,
            source_regions=["R01"],
            state=DeclarationState.MISSING,
        )
    }))
    item = next(item for item in result.results if item.rule_id == "DECL_003")
    assert item.status == ComplianceStatus.FAIL
    assert "MISSING" in item.reason
    assert result.overall_status == OverallStatus.NON_COMPLIANT


def test_found_state_keeps_normal_validator_behavior():
    result = evaluate(make_input({
        "commodity_name": Declaration(
            value="Potato Chips",
            confidence=0.99,
            source_regions=["R01"],
            state=DeclarationState.FOUND,
        )
    }))
    item = next(item for item in result.results if item.rule_id == "DECL_003")
    assert item.status == ComplianceStatus.PASS
