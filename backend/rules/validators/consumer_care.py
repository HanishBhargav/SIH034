import re
from typing import Any

from ..models import ComplianceStatus, Declaration, DeclarationState, RuleResult

RULE_ID = "DECL_004"
LEGAL_REFERENCE = "Legal Metrology (Packaged Commodities) Rules, 2011, Rule 6(2)"
_REVIEW_THRESHOLD = 0.70
_EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _meaningful(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return bool(str(value).strip())


def _pick(data: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in data and _meaningful(data[key]):
            return data[key]
    return None


def _phone_looks_valid(value: Any) -> bool:
    if not _meaningful(value):
        return False
    digits = re.sub(r"\D", "", str(value))
    return 7 <= len(digits) <= 15


def validate_consumer_care(declaration: Declaration | None) -> RuleResult:
    """Validate the consumer-care contact declaration under Rule 6(2).

    The validator expects M1/parser output to classify the contact details into
    a structured mapping containing name, address, telephone and e-mail. It
    does not decide whether an address is legally sufficient or whether the
    named person/office is substantively responsible for complaints.
    """
    if declaration is None:
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.FAIL,
            reason="Consumer-care contact declaration is missing.",
            legal_reference=LEGAL_REFERENCE,
        )

    evidence = list(declaration.source_regions)
    confidence = declaration.confidence

    if declaration.state in {DeclarationState.UNCERTAIN, DeclarationState.CONFLICTING}:
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.REVIEW,
            reason="Consumer-care contact information was detected but its extraction state is uncertain or conflicting.",
            confidence=confidence,
            evidence_regions=evidence,
            legal_reference=LEGAL_REFERENCE,
        )

    if not _meaningful(declaration.value):
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.FAIL,
            reason="Consumer-care contact declaration is missing or empty.",
            confidence=confidence,
            evidence_regions=evidence,
            legal_reference=LEGAL_REFERENCE,
        )

    if confidence < _REVIEW_THRESHOLD:
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.REVIEW,
            reason="Consumer-care contact information was detected, but extraction confidence is below the review threshold.",
            confidence=confidence,
            evidence_regions=evidence,
            legal_reference=LEGAL_REFERENCE,
        )

    if not isinstance(declaration.value, dict):
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.REVIEW,
            reason="Consumer-care contact information is present but could not be reliably classified into name, address, telephone and e-mail fields.",
            confidence=confidence,
            evidence_regions=evidence,
            legal_reference=LEGAL_REFERENCE,
        )

    data = declaration.value
    name = _pick(data, "name", "person", "office")
    address = _pick(data, "address")
    telephone = _pick(data, "telephone", "phone", "telephone_number", "phone_number")
    email = _pick(data, "email", "email_address", "e_mail")

    missing = []
    if name is None:
        missing.append("name/office")
    if address is None:
        missing.append("address")
    if telephone is None:
        missing.append("telephone")
    if email is None:
        missing.append("e-mail")

    if missing:
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.FAIL,
            reason=f"Consumer-care declaration is incomplete; missing {', '.join(missing)}.",
            confidence=confidence,
            evidence_regions=evidence,
            legal_reference=LEGAL_REFERENCE,
        )

    if not _phone_looks_valid(telephone):
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.REVIEW,
            reason="Consumer-care telephone number is present but could not be reliably classified as a valid contact number.",
            confidence=confidence,
            evidence_regions=evidence,
            legal_reference=LEGAL_REFERENCE,
        )

    if not _EMAIL_PATTERN.fullmatch(str(email).strip()):
        return RuleResult(
            rule_id=RULE_ID,
            status=ComplianceStatus.REVIEW,
            reason="Consumer-care e-mail address is present but does not have a reliably parseable e-mail format.",
            confidence=confidence,
            evidence_regions=evidence,
            legal_reference=LEGAL_REFERENCE,
        )

    return RuleResult(
        rule_id=RULE_ID,
        status=ComplianceStatus.PASS,
        reason="Consumer-care name, address, telephone and e-mail declaration evidence was detected.",
        confidence=confidence,
        evidence_regions=evidence,
        legal_reference=LEGAL_REFERENCE,
    )
