from backend.rules.integration import build_m2_input, evaluate_m1_output
from backend.rules.models import ComplianceStatus, DeclarationState, M2Context, OverallStatus


def m1_output():
    return {
        "image_id": "IMG001",
        "quality": {"status": "ACCEPTED", "score": 0.94},
        "text_blocks": [
            {"id": "R01", "text": "Potato Chips", "confidence": 0.97, "bbox": [100, 100, 300, 140]},
            {"id": "R02", "text": "ABC Foods Pvt Ltd, Mumbai", "confidence": 0.96, "bbox": [100, 150, 400, 190]},
            {"id": "R03", "text": "Net Qty 500 g", "confidence": 0.94, "bbox": [100, 200, 300, 240]},
            {"id": "R04", "text": "MRP ₹120 (inclusive of all taxes)", "confidence": 0.97, "bbox": [100, 250, 400, 290]},
            {"id": "R05", "text": "Consumer Care 18001234567", "confidence": 0.95, "bbox": [100, 300, 400, 340]},
            {"id": "R06", "text": "09/2026", "confidence": 0.95, "bbox": [100, 350, 250, 390]},
        ],
        "declarations": {
            "commodity_name": {"value": "Potato Chips", "confidence": 0.97, "source_regions": ["R01"], "state": "FOUND"},
            "manufacturer_or_packer_details": {"value": "ABC Foods Pvt Ltd, Mumbai", "confidence": 0.96, "source_regions": ["R02"], "state": "FOUND"},
            "net_quantity": {"value": 500, "unit": "g", "confidence": 0.94, "source_regions": ["R03"], "state": "FOUND"},
            "mrp": {"value": 120, "currency": "INR", "confidence": 0.97, "source_regions": ["R04"], "state": "FOUND"},
            "consumer_care": {"value": {"telephone": "18001234567"}, "confidence": 0.95, "source_regions": ["R05"], "state": "FOUND"},
            "manufacture_month_year": {"value": "09/2026", "confidence": 0.95, "source_regions": ["R06"], "state": "FOUND"},
        },
        "measurements": [],
    }


def context(**overrides):
    values = {
        "package_type": "retail",
        "commodity_category": "snacks",
        "commodity_measure_type": "mass",
        "package_quantity": 0.5,
        "package_quantity_unit": "kg",
    }
    values.update(overrides)
    return M2Context(**values)


def test_m1_output_can_flow_directly_into_m2_and_preserve_evidence():
    inspection = build_m2_input(m1_output(), inspection_id="M1-M2-001", context=context())
    assert inspection.declarations["net_quantity"].state == DeclarationState.FOUND
    assert inspection.text_blocks[2]["id"] == "R03"

    result = evaluate_m1_output(m1_output(), inspection_id="M1-M2-001", context=context())
    qty = next(item for item in result.results if item.rule_id == "QTY_001")
    mrp = next(item for item in result.results if item.rule_id == "MRP_001")
    assert qty.status == ComplianceStatus.PASS
    assert qty.evidence_regions == ["R03"]
    assert mrp.status == ComplianceStatus.PASS
    assert mrp.evidence_regions == ["R04"]
    assert result.inspection_id == "M1-M2-001"


def test_m1_rejected_quality_reaches_m2_as_review_required():
    output = m1_output()
    output["quality"] = {"status": "REJECTED", "score": 0.22}
    result = evaluate_m1_output(output, inspection_id="QUALITY-001", context=context())
    assert result.overall_status == OverallStatus.REVIEW_REQUIRED
    assert result.results[0].rule_id == "APP_QUALITY"
    assert result.results[0].status == ComplianceStatus.REVIEW


def test_m1_missing_physical_measurements_produce_rule_review():
    result = evaluate_m1_output(m1_output(), inspection_id="PHYSICAL-001", context=context())
    font = next(item for item in result.results if item.rule_id == "FONT_001")
    numeral = next(item for item in result.results if item.rule_id == "MRP_003")
    assert font.status == ComplianceStatus.REVIEW
    assert numeral.status == ComplianceStatus.REVIEW
    assert "M1" in font.reason
    assert "M1" in numeral.reason
    # Physical checks remain REVIEW, while missing mandatory declarations make
    # the overall inspection NON_COMPLIANT.
    assert result.overall_status == OverallStatus.NON_COMPLIANT
