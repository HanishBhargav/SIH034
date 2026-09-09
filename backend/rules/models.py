from datetime import date
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field

class ComplianceStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    REVIEW = "REVIEW"

class OverallStatus(str, Enum):
    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    NOT_APPLICABLE = "NOT_APPLICABLE"

class DeclarationState(str, Enum):
    FOUND = "FOUND"
    MISSING = "MISSING"
    UNCERTAIN = "UNCERTAIN"
    CONFLICTING = "CONFLICTING"

class Declaration(BaseModel):
    value: Any | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    source_regions: list[str] = Field(default_factory=list)
    state: DeclarationState | None = None
    unit: str | None = None
    currency: str | None = None

class MoneyDeclaration(Declaration):
    currency: str = "INR"

class QuantityDeclaration(Declaration):
    unit: str

class Measurement(BaseModel):
    type: str
    value: float
    unit: str
    confidence: float = Field(ge=0.0, le=1.0)
    method: str
    source_regions: list[str] = Field(default_factory=list)

class M2Context(BaseModel):
    inspection_date: date | None = None
    commodity_category: str | None = None
    commodity_measure_type: str | None = None
    package_quantity: float | None = None
    package_quantity_unit: str | None = None
    package_type: str | None = None
    consumer_type: str | None = None
    is_imported: bool | None = None
    is_ecommerce: bool | None = None
    country_of_origin: str | None = None
    best_before_use_by_applicable: bool | None = None
    unit_sale_price_applicable: bool | None = None
    has_sticker_or_label: bool | None = None
    is_genetically_modified_food: bool | None = None
    veg_nonveg_dot_applicable: bool | None = None
    dimensions_applicable: bool | None = None

class M2Input(BaseModel):
    inspection_id: str
    image_id: str | None = None
    quality_status: str | None = None
    quality_score: float | None = Field(default=None, ge=0.0, le=1.0)
    text_blocks: list[dict[str, Any]] = Field(default_factory=list)
    declarations: dict[str, Declaration] = Field(default_factory=dict)
    measurements: list[Measurement] = Field(default_factory=list)
    context: M2Context

class RuleResult(BaseModel):
    rule_id: str
    field: str | None = None
    status: ComplianceStatus
    reason: str
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    evidence_regions: list[str] = Field(default_factory=list)
    legal_reference: str

class ComplianceResult(BaseModel):
    inspection_id: str
    overall_status: OverallStatus
    results: list[RuleResult] = Field(default_factory=list)
    applicable_rule_count: int = 0
    pass_count: int = 0
    fail_count: int = 0
    review_count: int = 0
