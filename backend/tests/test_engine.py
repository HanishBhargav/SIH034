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


def test_engine_valid_commodity_name_does_not_review_deferred_rules():
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
                "consumer_care": Declaration(
                    value={
                        "name": "ABC Foods Consumer Care",
                        "address": "Mumbai, Maharashtra",
                        "telephone": "18001234567",
                        "email": "care@abcfoods.example",
                    },
                    confidence=0.96,
                    source_regions=["R04"],
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
    expected_pass_rules = {"DECL_001", "DECL_003", "DECL_004", "QTY_001", "QTY_002", "MRP_001", "MRP_002", "DATE_001", "QR_001"}
    result_ids = {item.rule_id for item in result.results}
    assert expected_pass_rules.issubset(result_ids)
    assert all(
        next(item for item in result.results if item.rule_id == rule_id).status == ComplianceStatus.PASS
        for rule_id in expected_pass_rules
    )
    deferred_rules = {"MRP_003", "PDP_001", "FONT_001", "FONT_002", "READ_001", "READ_002", "READ_003", "PACK_001", "PACK_002", "DECL_009"}
    assert result_ids.isdisjoint(deferred_rules)
    assert result.overall_status == OverallStatus.REVIEW_REQUIRED
    assert result.pass_count >= len(expected_pass_rules)
    assert result.review_count == 1
    assert any(item.rule_id == "USP_001" and item.status == ComplianceStatus.REVIEW for item in result.results)


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


def test_date_002_only_runs_when_best_before_is_applicable():
    declarations = {
        "best_before_use_by": Declaration(
            value="12 months",
            confidence=0.96,
            source_regions=["R07"],
        )
    }

    not_applicable = evaluate(
        make_input(
            declarations=declarations,
            context_overrides={"best_before_use_by_applicable": False},
        )
    )
    assert not any(item.rule_id == "DATE_002" for item in not_applicable.results)

    applicable = evaluate(
        make_input(
            declarations=declarations,
            context_overrides={"best_before_use_by_applicable": True},
        )
    )
    date_002 = next(item for item in applicable.results if item.rule_id == "DATE_002")
    assert date_002.status == ComplianceStatus.PASS


def test_imported_and_ecommerce_rules_route_only_when_context_applies():
    base = evaluate(make_input())
    assert not any(item.rule_id in {"DECL_002", "ECOM_001", "ECOM_002"} for item in base.results)

    imported = evaluate(make_input(context_overrides={"is_imported": True}))
    assert any(item.rule_id == "DECL_002" for item in imported.results)
    assert not any(item.rule_id in {"ECOM_001", "ECOM_002"} for item in imported.results)

    ecommerce = evaluate(make_input(context_overrides={"is_ecommerce": True}))
    assert any(item.rule_id == "ECOM_001" for item in ecommerce.results)
    assert not any(item.rule_id == "ECOM_002" for item in ecommerce.results)

    ecommerce_imported = evaluate(
        make_input(context_overrides={"is_ecommerce": True, "is_imported": True})
    )
    assert any(item.rule_id == "ECOM_001" for item in ecommerce_imported.results)
    assert any(item.rule_id == "ECOM_002" for item in ecommerce_imported.results)


def test_special_conditional_rules_are_not_run_when_irrelevant():
    result = evaluate(make_input())
    conditional_rules = {"DECL_005", "DECL_007", "DECL_008", "STICKER_001", "USP_002"}
    assert not any(item.rule_id in conditional_rules for item in result.results)


def test_special_conditional_rules_route_when_context_applies():
    result = evaluate(
        make_input(
            context_overrides={
                "dimensions_applicable": True,
                "is_genetically_modified_food": True,
                "veg_nonveg_dot_applicable": True,
                "has_sticker_or_label": True,
                "unit_sale_price_applicable": True,
            }
        )
    )
    result_ids = {item.rule_id for item in result.results}
    assert {"DECL_005", "DECL_007", "DECL_008", "STICKER_001", "USP_002"}.issubset(result_ids)
