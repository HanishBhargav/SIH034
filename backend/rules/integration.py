from typing import Any

from .engine import evaluate
from .models import ComplianceResult, M2Context, M2Input


def build_m2_input(
    m1_output: dict[str, Any],
    *,
    inspection_id: str,
    context: M2Context | dict[str, Any],
) -> M2Input:
    """Adapt the frozen M1 observation contract into the M2 input contract.

    M1 supplies observations only. Inspection/context metadata belongs to M3,
    so M3 passes it separately rather than asking M1 to infer legal context.
    """
    quality = m1_output.get("quality") or {}
    if not isinstance(quality, dict):
        quality = {}

    return M2Input.model_validate(
        {
            "inspection_id": inspection_id,
            "image_id": m1_output.get("image_id"),
            "quality_status": quality.get("status"),
            "quality_score": quality.get("score"),
            "text_blocks": m1_output.get("text_blocks") or [],
            "declarations": m1_output.get("declarations") or {},
            "measurements": m1_output.get("measurements") or [],
            "context": context.model_dump() if isinstance(context, M2Context) else context,
        }
    )


def evaluate_m1_output(
    m1_output: dict[str, Any],
    *,
    inspection_id: str,
    context: M2Context | dict[str, Any],
    repo_root=None,
) -> ComplianceResult:
    """Single callable M3 integration entry point: M1 observations -> M2 result."""
    inspection = build_m2_input(
        m1_output,
        inspection_id=inspection_id,
        context=context,
    )
    return evaluate(inspection, repo_root=repo_root)
