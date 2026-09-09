from backend.rules.engine import evaluate
from backend.rules.models import ComplianceStatus, M2Input, OverallStatus


def test_actual_frozen_m1_observation_contract_runs_through_m2():
    """Use the exact frozen M1 observation example at the M2 boundary."""
    m1_output = {
        "image_id": "IMG001",
        "quality": {"status": "ACCEPTED", "score": 0.94},
        "text_blocks": [
            {
                "id": "R01",
                "text": "MRP ₹120",
                "confidence": 0.97,
                "bbox": [100, 200, 300, 240],
            }
        ],
        "declarations": {
            "mrp": {
                "value": 120,
                "currency": "INR",
                "confidence": 0.97,
                "source_regions": ["R01"],
            },
            "net_quantity": {
                "value": 500,
                "unit": "g",
                "confidence": 0.94,
                "source_regions": ["R03"],
            },
        },
        "measurements": [],
    }

    # M3's orchestration layer converts M1's quality object into the M2 quality
    # fields and supplies legal/applicability context that M1 intentionally does
    # not decide.
    m2_input = M2Input.model_validate(
        {
            "inspection_id": "M1-M2-E2E-001",
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
    )

    result = evaluate(m2_input)

    assert result.inspection_id == "M1-M2-E2E-001"
    assert result.overall_status == OverallStatus.NON_COMPLIANT

    # The two declarations supplied by M1 are consumed successfully.
    mrp = next(item for item in result.results if item.rule_id == "MRP_001")
    quantity = next(item for item in result.results if item.rule_id == "QTY_001")
    quantity_unit = next(item for item in result.results if item.rule_id == "QTY_002")

    assert mrp.status == ComplianceStatus.PASS
    assert quantity.status == ComplianceStatus.PASS
    assert quantity_unit.status == ComplianceStatus.PASS
    assert mrp.evidence_regions == ["R01"]
    assert quantity.evidence_regions == ["R03"]
    assert quantity_unit.evidence_regions == ["R03"]

    # The frozen M1 example intentionally contains only MRP and net quantity,
    # so M2 correctly identifies the missing mandatory declarations instead of
    # treating an incomplete observation as compliant.
    commodity_name = next(item for item in result.results if item.rule_id == "DECL_003")
    assert commodity_name.status == ComplianceStatus.FAIL
