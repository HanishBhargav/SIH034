from backend.rules.engine import evaluate
from backend.rules.models import ComplianceStatus, Declaration, M2Context, M2Input, OverallStatus


def make_input(**kwargs):
    context_values = {
        "package_type": "retail",
        "commodity_category": "snacks",
        "package_quantity": 1,
        "package_quantity_unit": "kg",
    }
    context_values.update(kwargs.pop("context_overrides", {}))
    context = M2Context(**context_values)

    return M2Input(
        inspection_id="TEST-001",
        declarations=kwargs.pop("declarations", {}),
        context=context,
        **kwargs,
    )


def test_engine_missing_commodity_name_is_non_compliant():
    result = evaluate(make_input())
    decl_003 = next(item for item in result.results if item.rule_id == "DECL_003")
    assert decl_003.status == ComplianceStatus.FAIL
    assert result.overall_status == OverallStatus.NON_COMPLIANT
    assert result.fail_count >= 1


def test_engine_valid_commodity_name_still_reviews_unimplemented_rules():
    result = evaluate(
        make_input(
            declarations={
                "commodity_name": Declaration(
                    value="Potato Chips",
                    confidence=0.96,
                    source_regions=["R01"],
                )
            }
        )
    )
    decl_003 = next(item for item in result.results if item.rule_id == "DECL_003")
    assert decl_003.status == ComplianceStatus.PASS
    assert result.overall_status == OverallStatus.REVIEW_REQUIRED
    assert result.pass_count >= 1
    assert result.review_count >= 1


def test_engine_unknown_applicability_requires_review():
    result = evaluate(make_input(context_overrides={"package_type": None}))
    assert result.overall_status == OverallStatus.REVIEW_REQUIRED
    assert result.results[0].rule_id == "APP_001"
    assert result.results[0].status == ComplianceStatus.REVIEW


def test_engine_wholesale_is_not_applicable():
    result = evaluate(make_input(context_overrides={"package_type": "wholesale"}))
    assert result.overall_status == OverallStatus.NOT_APPLICABLE
    assert result.results == []


def test_engine_generic_over_25kg_is_not_applicable():
    result = evaluate(
        make_input(
            context_overrides={
                "package_quantity": 30,
                "package_quantity_unit": "kg",
            }
        )
    )
    assert result.overall_status == OverallStatus.NOT_APPLICABLE


def test_engine_special_category_40kg_is_still_applicable():
    result = evaluate(
        make_input(
            context_overrides={
                "commodity_category": "agricultural_farm_produce",
                "package_quantity": 40,
                "package_quantity_unit": "kg",
            }
        )
    )
    assert result.overall_status == OverallStatus.NON_COMPLIANT
    assert any(item.rule_id == "DECL_003" for item in result.results)
