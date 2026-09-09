from collections.abc import Callable
from .applicability import ApplicabilityStatus, evaluate_chapter_ii
from .models import ComplianceResult, ComplianceStatus, M2Input, OverallStatus, RuleResult
from .rule_registry import RuleDefinition, load_rule_registry
from .validators.best_before import validate_best_before_use_by
from .validators.commodity_name import validate_commodity_name
from .validators.consumer_care import validate_consumer_care
from .validators.date_declaration import validate_manufacture_month_year
from .validators.gm_food import validate_gm_food_declaration
from .validators.mrp_format import validate_mrp_format
from .validators.mrp_presence import validate_mrp_presence
from .validators.origin import validate_origin_declaration
from .validators.party_declaration import validate_party_declaration
from .validators.quantity import validate_net_quantity
from .validators.quantity_unit import validate_quantity_unit
from .validators.sticker_declaration import validate_sticker_declaration
from .validators.veg_nonveg_dot import validate_veg_nonveg_dot
Validator = Callable[..., RuleResult]
_VALIDATORS: dict[str, Validator] = {"DECL_001": validate_party_declaration, "DECL_003": validate_commodity_name, "DECL_004": validate_consumer_care, "DECL_007": validate_gm_food_declaration, "DECL_008": validate_veg_nonveg_dot, "STICKER_001": validate_sticker_declaration, "MRP_001": validate_mrp_presence, "QTY_001": validate_net_quantity, "QTY_002": validate_quantity_unit}
def _legal_reference(rule: RuleDefinition) -> str:
    source = rule.source
    document = source.get("document", "Unknown legal source")
    rule_number = str(source.get("rule", "?"))
    sub_rule = source.get("sub_rule")
    if sub_rule and "(" not in rule_number: rule_number = f"{rule_number}({sub_rule})"
    return f"{document}, Rule {rule_number}"
def _review_result(rule: RuleDefinition, reason: str) -> RuleResult:
    return RuleResult(rule_id=rule.rule_id, field=rule.data.get("field"), status=ComplianceStatus.REVIEW, reason=reason, legal_reference=_legal_reference(rule))
def _select_applicable_rules(inspection: M2Input, registry: dict[str, RuleDefinition]) -> list[RuleDefinition]:
    decision = evaluate_chapter_ii(inspection.context)
    if decision.status != ApplicabilityStatus.APPLICABLE: return []
    selected: list[RuleDefinition] = []
    for rule in registry.values():
        applicability = rule.data.get("applicability") or {}
        when = applicability.get("when")
        if when == {"field": "chapter_ii_applicable", "equals": True}: selected.append(rule)
        elif rule.rule_id == "DECL_002" and when == {"field": "is_imported", "equals": True}: selected.append(rule)
        elif rule.rule_id == "DECL_007" and inspection.context.is_genetically_modified_food is True: selected.append(rule)
        elif rule.rule_id == "DECL_008" and inspection.context.veg_nonveg_dot_applicable is True: selected.append(rule)
    return selected
def evaluate(inspection: M2Input, repo_root=None) -> ComplianceResult:
    if inspection.quality_status == "REJECTED": return ComplianceResult(inspection_id=inspection.inspection_id, overall_status=OverallStatus.REVIEW_REQUIRED, results=[RuleResult(rule_id="APP_QUALITY", status=ComplianceStatus.REVIEW, reason="M1 rejected the image quality; compliance evaluation was stopped and manual review is required.", confidence=inspection.quality_score, legal_reference="M1 image-quality gate")], review_count=1)
    registry = load_rule_registry(repo_root)
    chapter_ii = evaluate_chapter_ii(inspection.context)
    if chapter_ii.status == ApplicabilityStatus.NOT_APPLICABLE: return ComplianceResult(inspection_id=inspection.inspection_id, overall_status=OverallStatus.NOT_APPLICABLE)
    if chapter_ii.status == ApplicabilityStatus.REVIEW: return ComplianceResult(inspection_id=inspection.inspection_id, overall_status=OverallStatus.REVIEW_REQUIRED, results=[RuleResult(rule_id="APP_001", status=ComplianceStatus.REVIEW, reason=chapter_ii.reason, legal_reference="Legal Metrology (Packaged Commodities) Rules, 2011, Rule 3")], review_count=1)
    results: list[RuleResult] = []
    for rule in _select_applicable_rules(inspection, registry):
        if rule.rule_id == "DECL_002": result = validate_origin_declaration(inspection.declarations.get(rule.data.get("field")), is_imported=inspection.context.is_imported)
        elif rule.rule_id == "QTY_002": result = validate_quantity_unit(inspection.declarations.get("net_quantity"), expected_measure_type=inspection.context.commodity_measure_type)
        elif rule.rule_id == "MRP_002": result = validate_mrp_format(inspection.declarations.get(rule.data.get("field")), text_blocks=inspection.text_blocks)
        elif rule.rule_id == "DATE_001": result = validate_manufacture_month_year(inspection.declarations.get(rule.data.get("field")), commodity_category=inspection.context.commodity_category)
        elif rule.rule_id == "DATE_002": result = validate_best_before_use_by(inspection.declarations.get(rule.data.get("field")), applicable=inspection.context.best_before_use_by_applicable)
        else:
            validator = _VALIDATORS.get(rule.rule_id)
            if validator is None:
                results.append(_review_result(rule, "Rule is applicable, but its validator has not yet been implemented in the current MVP engine.")); continue
            result = validator(inspection.declarations.get(rule.data.get("field")))
        result.field = rule.data.get("field")
        result.legal_reference = _legal_reference(rule)
        results.append(result)
    pass_count = sum(result.status == ComplianceStatus.PASS for result in results)
    fail_count = sum(result.status == ComplianceStatus.FAIL for result in results)
    review_count = sum(result.status == ComplianceStatus.REVIEW for result in results)
    if fail_count: overall_status = OverallStatus.NON_COMPLIANT
    elif review_count: overall_status = OverallStatus.REVIEW_REQUIRED
    else: overall_status = OverallStatus.COMPLIANT
    return ComplianceResult(inspection_id=inspection.inspection_id, overall_status=overall_status, results=results, applicable_rule_count=len(results), pass_count=pass_count, fail_count=fail_count, review_count=review_count)
