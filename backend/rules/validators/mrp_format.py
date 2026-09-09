import re
from typing import Any

from ..models import ComplianceStatus, Declaration, RuleResult

RULE_ID = "MRP_002"
LEGAL_REFERENCE = "Legal Metrology (Packaged Commodities) Rules, 2011, Rule 6(1)(e), read with Rule 2(m)"
MIN_CONFIDENCE = 0.70

_TAX_INCLUSIVE_PATTERNS = (
    re.compile(r"inclusive\s+of\s+all\s+tax(?:es)?", re.IGNORECASE),
    re.compile(r"incl\.?\s*(?:of\s*)?all\s+tax(?:es)?", re.IGNORECASE),
)


def _is_meaningful(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return True


def _is_positive_numeric(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return value > 0
    if isinstance(value, str):
        try:
            return float(value.replace(",", "").strip()) > 0
        except ValueError:
            return False
    return False


def _has_tax_inclusive_wording(declaration: Declaration, text_blocks: list[dict[str, Any]]) -> bool:
    region_ids = set(declaration.source_regions)
    candidate_text = " ".join(
        str(block.get("text", ""))
        for block in text_blocks
        if not region_ids or block.get("id") in region_ids
    )
    return any(pattern.search(candidate_text) for pattern in _TAX_INCLUSIVE_PATTERNS)


def validate_mrp_format(
    declaration: Declaration | None,
    *,
    text_blocks: list[dict[str, Any]] | None = None,
) -> RuleResult:
    """Validate the current MVP requirements for MRP representation.

    Checks the parseable price, Indian-currency declaration, and explicit
    tax-inclusive wording. If OCR evidence needed for the wording check is
    unavailable, the result is REVIEW rather than an inferred PASS/FAIL.
    """
    if declaration is None:
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.FAIL,
            reason="MRP declaration is missing.",
            legal_reference=LEGAL_REFERENCE,
        )

    evidence = list(declaration.source_regions)
    confidence = declaration.confidence

    if not _is_meaningful(declaration.value):
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.FAIL,
            reason="MRP declaration is missing or empty.",
            confidence=confidence,
            evidence_regions=evidence,
            legal_reference=LEGAL_REFERENCE,
        )

    if confidence < MIN_CONFIDENCE:
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.REVIEW,
            reason="MRP was detected, but extraction confidence is below the review threshold.",
            confidence=confidence,
            evidence_regions=evidence,
            legal_reference=LEGAL_REFERENCE,
        )

    if not _is_positive_numeric(declaration.value):
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.REVIEW,
            reason="MRP value could not be reliably parsed as a positive price.",
            confidence=confidence,
            evidence_regions=evidence,
            legal_reference=LEGAL_REFERENCE,
        )

    currency = getattr(declaration, "currency", None)
    if currency is not None and str(currency).upper() != "INR":
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.FAIL,
            reason="MRP is declared in a currency other than Indian currency (INR).",
            confidence=confidence,
            evidence_regions=evidence,
            legal_reference=LEGAL_REFERENCE,
        )

    if currency is None:
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.REVIEW,
            reason="Indian currency could not be established from the extracted MRP declaration.",
            confidence=confidence,
            evidence_regions=evidence,
            legal_reference=LEGAL_REFERENCE,
        )

    if text_blocks is None:
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.REVIEW,
            reason="Tax-inclusive MRP wording cannot be verified because OCR text evidence is unavailable.",
            confidence=confidence,
            evidence_regions=evidence,
            legal_reference=LEGAL_REFERENCE,
        )

    if not _has_tax_inclusive_wording(declaration, text_blocks):
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.FAIL,
            reason="MRP does not contain detectable wording indicating that it is inclusive of all taxes.",
            confidence=confidence,
            evidence_regions=evidence,
            legal_reference=LEGAL_REFERENCE,
        )

    return RuleResult(
        rule_id=RULE_ID,
        status=ComplianceStatus.PASS,
        reason="MRP is a positive parseable value in Indian currency and the OCR evidence indicates that it is inclusive of all taxes.",
        confidence=confidence,
        evidence_regions=evidence,
        legal_reference=LEGAL_REFERENCE,
    )
