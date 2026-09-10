# API / Module Contract

## M1 → M3

M1 returns image quality, OCR `text_blocks`, declarations, and measurements. Each text block has a canonical ID used for evidence traceability.

## M3 → M2

M3 passes `inspection_id`, image/quality information, `text_blocks`, `declarations`, `measurements`, and `M2Context` to the rules engine.

## M2 → M3

M2 returns `ComplianceResult` containing `inspection_id`, `overall_status`, counts, and rule results. Each rule result contains:

- `rule_id`
- `field`
- `status`: `PASS | FAIL | REVIEW`
- `reason`
- `confidence`
- `evidence_regions`
- `legal_reference`

Overall compliance status is `COMPLIANT | NON_COMPLIANT | REVIEW_REQUIRED | NOT_APPLICABLE`.

## Processing status

Processing lifecycle is separate from compliance status: `CREATED | PROCESSING | COMPLETED | FAILED`.

## M3 ↔ M4

M3 uses a repository/service boundary for inspection creation, retrieval/listing, declaration persistence, compliance-result persistence, violations and reports. M4 does not reinterpret M2 decisions.

## Compatibility rule

Do not silently rename or change shared fields during integration. If the interface must evolve, update this document and the corresponding tests together.
