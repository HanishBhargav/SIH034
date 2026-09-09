import re
from typing import Any

from ..models import ComplianceStatus, Declaration, RuleResult

RULE_ID = "DATE_001"
LEGAL_REFERENCE = "Legal Metrology (Packaged Commodities) Rules, 2011, Rule 6(1)(d)"
MIN_CONFIDENCE = 0.70

# Month names/numbers are intentionally accepted in common OCR forms because
# Rule 6 permits the month and year to be expressed in words or numerals.
_MONTH_PATTERN = re.compile(
    r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|sept|oct(?:ober)?|nov(?:ember)?|"
    r"dec(?:ember)?|0?[1-9]|1[0-2])"
    r"\s*[-/. ]\s*(?:19|20)\d{2}",
    re.IGNORECASE,
)
_YEAR_MONTH_PATTERN = re.compile(
    r"(?:19|20)\d{2}\s*[-/. ]\s*(?:0?[1-9]|1[0-2])",
    re.IGNORECASE,
)
_YEAR_PATTERN = re.compile(r"(?:19|20)\d{2}")


def _meaningful(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return True


def _looks_like_month_year(value: Any) -> bool:
    text = str(value).strip()
    if _MONTH_PATTERN.search(text) or _YEAR_MONTH_PATTERN.search(text):
        return True
    # Numeric forms such as 09/2026 or 092026 are common OCR outputs.
    if re.fullmatch(r"(?:0?[1-9]|1[0-2])[/.-](?:19|20)\d{2}", text):
        return True
    if re.fullmatch(r"(?:0?[1-9]|1[0-2])(?:19|20)\d{2}", text):
        return True
    return False


def _special_pathway(commodity_category: str | None) -> str | None:
    category = (commodity_category or "").strip().lower().replace("-", "_")
    if category in {"food", "food_article", "food_articles", "seeds", "cosmetics", "cosmetic"}:
        return category
    if category in {"bidi", "incense", "incense_sticks", "incense_stick"}:
        return category
    return None


def validate_manufacture_month_year(
    declaration: Declaration | None,
    *,
    commodity_category: str | None = None,
) -> RuleResult:
    """Validate presence and basic parseability of the manufacture month/year.

    The current MVP does not adjudicate declarations governed by another law.
    For food, seeds and cosmetics it therefore returns REVIEW rather than
    incorrectly applying the Packaged Commodities Rules. Bidi/incense and the
    specified LPG pathway are treated as explicit date exceptions when the
    context identifies them.
    """
    evidence = list(declaration.source_regions) if declaration else []
    confidence = declaration.confidence if declaration else None
    pathway = _special_pathway(commodity_category)

    if pathway in {"bidi", "incense", "incense_sticks", "incense_stick"}:
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.PASS,
            reason="Manufacture month/year declaration is exempt for the identified bidi/incense category.",
            confidence=confidence,
            evidence_regions=evidence,
            legal_reference=LEGAL_REFERENCE,
        )

    if pathway in {"food", "food_article", "food_articles", "seeds", "cosmetics", "cosmetic"}:
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.REVIEW,
            reason="Date declaration is governed by another applicable law for the identified commodity category; specialist verification is required.",
            confidence=confidence,
            evidence_regions=evidence,
            legal_reference=LEGAL_REFERENCE,
        )

    if declaration is None or not _meaningful(declaration.value):
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.FAIL,
            reason="Manufacture month/year declaration is missing.",
            confidence=confidence,
            evidence_regions=evidence,
            legal_reference=LEGAL_REFERENCE,
        )

    if confidence < MIN_CONFIDENCE:
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.REVIEW,
            reason="Manufacture month/year was detected, but extraction confidence is below the review threshold.",
            confidence=confidence,
            evidence_regions=evidence,
            legal_reference=LEGAL_REFERENCE,
        )

    if not _looks_like_month_year(declaration.value):
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.REVIEW,
            reason="The extracted date does not reliably match an accepted month/year representation.",
            confidence=confidence,
            evidence_regions=evidence,
            legal_reference=LEGAL_REFERENCE,
        )

    return RuleResult(
        rule_id=RULE_ID,
        status=ComplianceStatus.PASS,
        reason="Manufacture month/year declaration is present and matches an accepted month/year representation.",
        confidence=confidence,
        evidence_regions=evidence,
        legal_reference=LEGAL_REFERENCE,
    )
