from backend.rules.engine import evaluate
from backend.rules.models import ComplianceStatus, DeclarationState, M2Input, OverallStatus


def test_m1_output_can_flow_directly_into_m2_and_preserve_evidence():
    m1_output = {
        "image_id": "IMG001",
        "quality": {"status": "ACCEPTED", "score": 0.94},
        "text_blocks": [
            {
                "id": "R01",
                "text": "Potato Chips",
                "confidence": 0.97,
                "bbox": [100, 100, 300, 140],
            },
            {
                "id": "R02",
                "text": "ABC Foods Pvt Ltd, Mumbai",
                "confidence": 0.96,
                "bbox": [100, 150, 400, 190],
            },
            {
                "id": "R03",
                "text": "Net Qty 500 g",
                "confidence": 0.94,
                "bbox": [100, 200, 300, 240],
            },
            {
                "id": "R04",
                "text": "MRP ₹120 (inclusive of all taxes)",
                "confidence": 0.97,
                "bbox": [100, 250, 400, 290],
            },
            {
                "id": "R05",
                "text": "Consumer Care 18001234567",
                "confidence": 0.95,
                "bbox": [100, 300, 400, 340],
            },
            {
                "id": "R06",
                "text": "09/2026",
                "confidence": 0.95,
                "bbox": [100, 350, 250, 390],
            },
        ],
        "declarations": {
            "commodity_name": {
                "value": "Potato Chips",
                "confidence": 0.97,
                "source_regions": ["R01"],
                "state": "FOUND",
            },
            "manufacturer_or_packer_details": {
                "value": "ABC Foods Pvt Ltd, Mumbai",
                "confidence": 0.96,
                "source_regions": ["R02"],
                "state": "FOUND",
            },
            "net_quantity": {
                "value": 500,
                "unit": "g",
                "confidence": 0.94,
                "source_regions": ["R03"],
                "state": "FOUND",
            },
            "mrp": {
                "value": 120,
                "currency": "INR",
                "confidence": 0.97,
                "source_regions": ["R04"],
                "state": "FOUND",
            },
            "consumer_care": {
                "value": {"telephone": "18001234567"},
                "confidence": 0.95,
                "source_regions": ["R05"],
                "state": "FOUND",
            },
            "manufacture_month_year": {
                "value": "09/2026",
                "confidence": 0.95,
                "source_regions": ["R06"],
                "state": "FOUND",
            },
        },
        "measurements": [],
    }

    observation = {
        "inspection_id": "M1-M2-001",
        "image_id": m1_output["image_id"],
        "quality_status": m1_output["quality"]["status"],
        "quality_score": m1_output["quality"]["score"],
        "text_blocks": m1_output["text_blocks"],
        "declarations": m1_output["declarations"],
        "measurements": m1_output["measurements"],
        "context": {
            "package_type": "retail",
            "commodity_category": "snacks",
            "commodity_measure_type": "mass",
            "package_quantity": 0.5,
            "package_quantity_unit": "kg",
        },
    }

    inspection = M2Input.model_validate(observation)
    assert inspection.declarations["net_quantity"].state == DeclarationState.FOUND
    assert inspection.text_blocks[2]["id"] == "R03"

    result = evaluate(inspection)

    qty = next(item for item in result.results if item.rule_id == "QTY_001")
    assert qty.status == ComplianceStatus.PASS
    assert qty.evidence_regions == ["R03"]

    mrp = next(item for item in result.results if item.rule_id == "MRP_001")
    assert mrp.status == ComplianceStatus.PASS
    assert mrp.evidence_regions == ["R04"]

    assert result.inspection_id == "M1-M2-001"
    assert result.overall_status in {
        OverallStatus.COMPLIANT,
        OverallStatus.REVIEW_REQUIRED,
        OverallStatus.NON_COMPLIANT,
    }
