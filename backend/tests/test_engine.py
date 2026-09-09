from backend.rules.engine import evaluate
from backend.rules.models import ComplianceStatus, Declaration, DeclarationState, M2Context, M2Input, MoneyDeclaration, OverallStatus


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
            text_blocks=[{"id": "R05", "text": "MRP ₹120 (inclusive of all taxes)"}],
            declarations={
                "manufacturer_or_packer_details": Declaration(
                    value="ABC Foods Pvt Ltd, Mumbai, Maharashtra",
                    confidence=0.96,
                    source_regions=["R02"],
                ),
                "commodity_name": Declaration(
                    value="Potato Chips",
                    confidence=0.96,
                    source_regions=["R01"],
                ),
                "net_quantity": Declaration(
                    value=1,
                    unit="kg",
                    confidence=0.96,
                    source_regions=["R03"],
                ),
                "mrp": MoneyDeclaration(
                    value=120,
                    currency="INR",
                    confidence=0.96,
                    source_regions=["R05"],
                ),
                "manufacture_month_year": Declaration(
                    value="09/2026",
                    confidence=0.96,
                    source_regions=["R06"],
                ),
            },
            context_overrides={"commodity_measure_type": "mass"},
        )
    )
    decl_003 = next(item for item in result.results if item.rule_id == "DECL_003")
    qty_001 = next(item for item in result.results if item.rule_id == "QTY_001")
    qty_002 = next(item for item in result.results if item.rule_id == "QTY_002")
    mrp_001 = next(item for item in result.results if item.rule_id == "MRP_001")
    mrp_002 = next(item for item in result.results if item.rule_id == "MRP_002")
    date_001 = next(item for item in result.results if item.rule_id == "DATE_001")
    assert decl_003.status == ComplianceStatus.PASS
    assert qty_001.status == ComplianceStatus.PASS
    assert qty_002.status == ComplianceStatus.PASS
    assert mrp_001.status == ComplianceStatus.PASS
    assert mrp_002.status == ComplianceStatus.PASS
    assert date_001.status == ComplianceStatus.PASS
    assert result.overall_status == OverallStatus.REVIEW_REQUIRED
    assert result.pass_count >= 6
    assert result.review_count >= 1


def test_engine_valid_mrp_presence_passes():
    result = evaluate(
        make_input(
            declarations={
                "mrp": Declaration(
                    value=120,
                    confidence=0.96,
                    source_regions=["R05"],
                )
            }
        )
    )
    mrp_001 = next(item for item in result.results if item.rule_id == "MRP_001")
    assert mrp_001.status == ComplianceStatus.PASS
    assert mrp_001.legal_reference.endswith("Rule 6(1)(e)")


def test_engine_valid_mrp_format_passes():
    result = evaluate(
        make_input(
            text_blocks=[{"id": "R05", "text": "MRP ₹120 (inclusive of all taxes)"}],
            declarations={
                "mrp": MoneyDeclaration(
                    value=120,
                    currency="INR",
                    confidence=0.96,
                    source_regions=["R05"],
                )
            },
        )
    )
    mrp_002 = next(item for item in result.results if item.rule_id == "MRP_002")
    assert mrp_002.status == ComplianceStatus.PASS
    assert mrp_002.legal_reference.endswith("Rule 6(1)(e)")


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


def test_m1_style_quantity_json_preserves_unit_and_state():
    """Exercise the actual JSON shape M1 sends instead of a Python subclass."""
    m1_payload = {
        "value": 500,
        "unit": "g",
        "confidence": 0.94,
        "source_regions": ["R03"],
        "state": "FOUND",
    }

    inspection = M2Input.model_validate(
        {
            "inspection_id": "M1-CONTRACT-001",
            "image_id": "IMG001",
            "quality_status": "ACCEPTED",
            "quality_score": 0.94,
            "text_blocks": [
                {
                    "id": "R03",
                    "text": "Net Qty 500 g",
                    "confidence": 0.94,
                    "bbox": [100, 200, 300, 240],
                }
            ],
            "declarations": {"net_quantity": m1_payload},
            "context": {
                "package_type": "retail",
                "commodity_category": "snacks",
                "commodity_measure_type": "mass",
                "package_quantity": 0.5,
                "package_quantity_unit": "kg",
            },
        }
    )

    quantity = inspection.declarations["net_quantity"]
    assert quantity.unit == "g"
    assert quantity.state == DeclarationState.FOUND
    assert quantity.source_regions == ["R03"]

    result = evaluate(inspection)
    qty_002 = next(item for item in result.results if item.rule_id == "QTY_002")
    assert qty_002.status == ComplianceStatus.PASS
    assert qty_002.evidence_regions == ["R03"]


def test_rejected_m1_quality_stops_compliance_evaluation():
    result = evaluate(
        make_input(
            quality_status="REJECTED",
            quality_score=0.22,
            declarations={
                "commodity_name": Declaration(
                    value="Potato Chips",
                    confidence=0.96,
                    source_regions=["R01"],
                )
            },
        )
    )
    assert result.overall_status == OverallStatus.REVIEW_REQUIRED
    assert result.results[0].rule_id == "APP_QUALITY"
    assert result.results[0].status == ComplianceStatus.REVIEW
    assert result.applicable_rule_count == 0
