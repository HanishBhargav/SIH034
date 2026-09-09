import re
from typing import Any

from ..models import ComplianceStatus, Declaration, DeclarationState, RuleResult

RULE_ID = "DATE_002"
LEGAL_REFERENCE = "Legal Metrology (Packaged Commodities) Rules, 2011, Rule 6(1)(da)"
MIN_CONFIDENCE = 0.70

_DATE_PATTERN = re.compile(
    r"(?:0?[1-9]|[12]\d|3[01])\s*[-/. ]\s*(?:0?[1-9]|1[0-2]|"
    r"jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|"
    r"nov(?:ember)?|dec(?:ember)?)\s*[-/. ]\s*(?:19|20)\d{2}",
    re.IGNORECASE,
)
_MONTH_YEAR_PATTERN = re.compile(
    r"(?:0?[1-9]|1[0-2]|jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|"
    r"may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|"
    r"oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s*[-/. ]\s*(?:19|20)\d{2}",
    re.IGNORECASE,
)
_DURATION_PATTERN = re.compile(
    r"\b(?:\d+(?:\.\d+)?)\s+(?:day|days|month|months|year|years)\b"
    r"(?:\s+from\s+(?:date\s+of\s+)?manufacture)?",
    re.IGNORECASE,
)


def _meaningful(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return True


def _parseable(value: Any) -> bool:
    if isinstance(value, dict):
        candidate = value.get("value") or value.get("date") or value.get("period")
        if candidate is None:
            return False
        return _parseable(candidate)

    text = str(value).strip()
    if not text:
        return False
    return bool(
        _DATE_PATTERN.search(text)
        or _MONTH_YEAR_PATTERN.search(text)
        or _DURATION_PATTERN.search(text)
    )


def validate_best_before_use_by(
    declaration: Declaration | None,
    *,
    applicable: bool | None,
) -> RuleResult:
    """Validate best-before/use-by only when applicability is explicitly known."""
    evidence = list(declaration.source_regions) if declaration else []
    confidence = declaration.confidence if declaration else None

    if applicable is False:
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.PASS,
            reason="Best-before/use-by declaration is not applicable for the supplied commodity context.",
            confidence=confidence,
            evidence_regions=evidence,
            legal_reference=LEGAL_REFERENCE,
        )

    if applicable is None:
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.REVIEW,
            reason="Applicability of the best-before/use-by declaration is not established from the supplied commodity context.",
            confidence=confidence,
            evidence_regions=evidence,
            legal_reference=LEGAL_REFERENCE,
        )

    if declaration is None or not _meaningful(declaration.value):
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.FAIL,
            reason="Required best-before/use-by declaration is missing.",
            confidence=confidence,
            evidence_regions=evidence,
            legal_reference=LEGAL_REFERENCE,
        )

    if declaration.state in {DeclarationState.UNCERTAIN, DeclarationState.CONFLICTING}:
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.REVIEW,
            reason="Best-before/use-by declaration was detected with uncertain or conflicting extraction state.",
            confidence=confidence,
            evidence_regions=evidence,
            legal_reference=LEGAL_REFERENCE,
        )

    if confidence < MIN_CONFIDENCE:
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.REVIEW,
            reason="Best-before/use-by declaration was detected, but extraction confidence is below the review threshold.",
            confidence=confidence,
            evidence_regions=evidence,
            legal_reference=LEGAL_REFERENCE,
        )

    if not _parseable(declaration.value):
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.REVIEW,
            reason="The extracted best-before/use-by value cannot be reliably classified as a date or stated validity period.",
            confidence=confidence,
            evidence_regions=evidence,
            legal_reference=LEGAL_REFERENCE,
        )

    return RuleResult(
        rule_id=RULE_ID,
        status=ComplianceStatus.PASS,
        reason="Best-before/use-by declaration is present and has a recognizable date or validity-period representation.",
        confidence=confidence,
        evidence_regions=evidence,
        legal_reference=LEGAL_REFERENCE,
    )
