from enum import Enum
from typing import Any

from pydantic import BaseModel

from .models import M2Context


class ApplicabilityStatus(str, Enum):
    APPLICABLE = "APPLICABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    REVIEW = "REVIEW"


class ApplicabilityDecision(BaseModel):
    status: ApplicabilityStatus
    reason: str
    pathway: str | None = None
    flags: dict[str, Any] = {}


_GENERIC_LIMITS_KG = 25.0
_GENERIC_LIMITS_L = 25.0
_SPECIAL_LIMIT_KG = 50.0
_SPECIAL_CATEGORIES = {
    "cement",
    "fertilizer",
    "agricultural_farm_produce",
}


def _normalize(value: str | None) -> str | None:
    if value is None:
        return None
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def _quantity_exceeds_chapter_ii_limit(context: M2Context) -> bool | None:
    quantity = context.package_quantity
    unit = _normalize(context.package_quantity_unit)
    category = _normalize(context.commodity_category)

    if quantity is None or unit is None:
        return None

    if unit in {"kg", "kilogram", "kilograms"}:
        limit = _SPECIAL_LIMIT_KG if category in _SPECIAL_CATEGORIES else _GENERIC_LIMITS_KG
        return quantity > limit

    if unit in {"l", "liter", "litre", "liters", "litres"}:
        return quantity > _GENERIC_LIMITS_L

    # Other units cannot be compared reliably with the Rule 3 thresholds.
    return None


def evaluate_chapter_ii(context: M2Context) -> ApplicabilityDecision:
    """Determine whether the Chapter II packaged-commodity rules are in scope.

    This is intentionally conservative: missing or contradictory context produces
    REVIEW rather than silently assuming a legal pathway.
    """
    package_type = _normalize(context.package_type)
    consumer_type = _normalize(context.consumer_type)
    category = _normalize(context.commodity_category)

    if package_type in {"export", "export_package"}:
        return ApplicabilityDecision(
            status=ApplicabilityStatus.NOT_APPLICABLE,
            reason="Export packages follow the export-package pathway rather than Chapter II.",
            pathway="EXPORT",
        )

    if package_type in {"wholesale", "wholesale_package"}:
        return ApplicabilityDecision(
            status=ApplicabilityStatus.NOT_APPLICABLE,
            reason="Wholesale packages follow the Chapter III pathway rather than Chapter II.",
            pathway="WHOLESALE",
        )

    if consumer_type in {"industrial", "institutional"}:
        return ApplicabilityDecision(
            status=ApplicabilityStatus.NOT_APPLICABLE,
            reason="Industrial/institutional supply is outside the ordinary Chapter II retail pathway.",
            pathway="INDUSTRIAL_INSTITUTIONAL",
        )

    if package_type in {"industrial", "institutional"}:
        return ApplicabilityDecision(
            status=ApplicabilityStatus.NOT_APPLICABLE,
            reason="Industrial/institutional package pathway is outside ordinary Chapter II retail checks.",
            pathway="INDUSTRIAL_INSTITUTIONAL",
        )

    if category == "medical_device":
        return ApplicabilityDecision(
            status=ApplicabilityStatus.REVIEW,
            reason="Medical devices require routing against the Medical Devices Rules pathway; do not treat this as a blanket PCR exemption.",
            pathway="MEDICAL_DEVICE",
            flags={"specialist_routing_required": True},
        )

    if package_type is None:
        return ApplicabilityDecision(
            status=ApplicabilityStatus.REVIEW,
            reason="Package pathway is unknown; Chapter II applicability cannot be established safely.",
        )

    if package_type not in {"retail", "retail_prepackaged", "prepackaged"}:
        return ApplicabilityDecision(
            status=ApplicabilityStatus.REVIEW,
            reason=f"Unrecognized package pathway '{context.package_type}'; legal applicability requires review.",
        )

    exceeds_limit = _quantity_exceeds_chapter_ii_limit(context)
    if exceeds_limit is True:
        return ApplicabilityDecision(
            status=ApplicabilityStatus.NOT_APPLICABLE,
            reason="Package quantity exceeds the applicable Rule 3 Chapter II threshold for the identified commodity category.",
            pathway="SIZE_EXCLUSION",
        )

    if exceeds_limit is None and context.package_quantity is not None:
        return ApplicabilityDecision(
            status=ApplicabilityStatus.REVIEW,
            reason="Package quantity is present but its unit cannot be reliably evaluated against the Rule 3 threshold.",
            pathway="RETAIL",
        )

    return ApplicabilityDecision(
        status=ApplicabilityStatus.APPLICABLE,
        reason="Package is in the retail/pre-packaged pathway and no Rule 3 size exclusion has been established.",
        pathway="RETAIL",
    )
