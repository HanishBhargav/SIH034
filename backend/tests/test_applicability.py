from backend.rules.applicability import ApplicabilityStatus, evaluate_chapter_ii
from backend.rules.models import M2Context


def test_retail_package_is_applicable():
    result = evaluate_chapter_ii(
        M2Context(package_type="retail", package_quantity=1, package_quantity_unit="kg")
    )
    assert result.status == ApplicabilityStatus.APPLICABLE
    assert result.pathway == "RETAIL"


def test_explicitly_not_prepackaged_is_not_applicable():
    result = evaluate_chapter_ii(
        M2Context(is_prepackaged=False, package_type="retail")
    )
    assert result.status == ApplicabilityStatus.NOT_APPLICABLE
    assert result.pathway == "NOT_PREPACKAGED"


def test_explicitly_prepackaged_retail_package_is_applicable():
    result = evaluate_chapter_ii(
        M2Context(is_prepackaged=True, package_type="retail")
    )
    assert result.status == ApplicabilityStatus.APPLICABLE
    assert result.pathway == "RETAIL"


def test_generic_package_over_25kg_is_not_applicable():
    result = evaluate_chapter_ii(
        M2Context(package_type="retail", commodity_category="snacks", package_quantity=30, package_quantity_unit="kg")
    )
    assert result.status == ApplicabilityStatus.NOT_APPLICABLE
    assert result.pathway == "SIZE_EXCLUSION"


def test_special_category_40kg_remains_in_chapter_ii():
    result = evaluate_chapter_ii(
        M2Context(package_type="retail", commodity_category="agricultural_farm_produce", package_quantity=40, package_quantity_unit="kg")
    )
    assert result.status == ApplicabilityStatus.APPLICABLE


def test_wholesale_is_not_chapter_ii():
    result = evaluate_chapter_ii(M2Context(package_type="wholesale"))
    assert result.status == ApplicabilityStatus.NOT_APPLICABLE
    assert result.pathway == "WHOLESALE"


def test_export_is_not_chapter_ii():
    result = evaluate_chapter_ii(M2Context(package_type="export"))
    assert result.status == ApplicabilityStatus.NOT_APPLICABLE
    assert result.pathway == "EXPORT"


def test_unknown_package_type_requires_review():
    result = evaluate_chapter_ii(M2Context())
    assert result.status == ApplicabilityStatus.REVIEW


def test_unknown_quantity_unit_requires_review():
    result = evaluate_chapter_ii(
        M2Context(package_type="retail", package_quantity=10, package_quantity_unit="piece")
    )
    assert result.status == ApplicabilityStatus.REVIEW


def test_medical_device_requires_specialist_routing():
    result = evaluate_chapter_ii(
        M2Context(package_type="retail", is_medical_device=True)
    )
    assert result.status == ApplicabilityStatus.REVIEW
    assert result.pathway == "MEDICAL_DEVICE"
    assert result.flags["specialist_routing_required"] is True
