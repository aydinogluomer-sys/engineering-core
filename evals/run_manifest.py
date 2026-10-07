from __future__ import annotations

from harness_core import finite_number

MODELS = ["haiku", "sonnet", "opus", "fable"]
CELLS = ["activation", "mode_selection", "core_l4", "team_l4", "long_horizon"]


def validate_run_manifest(manifest: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        return ["unsupported run manifest"]
    if manifest.get("models") != MODELS or len(set(manifest.get("models", []))) != 4:
        errors.append("model cells must be four distinct stable aliases")
    if manifest.get("cells") != CELLS:
        errors.append("evaluation cells differ from the frozen plan")
    for field in ("per_call_budget_usd", "total_budget_usd"):
        if not finite_number(manifest.get(field), positive=True):
            errors.append(f"{field} must be finite and positive")
    if type(manifest.get("timeout_seconds")) is not int or manifest["timeout_seconds"] <= 0:
        errors.append("timeout_seconds must be a positive integer")
    if type(manifest.get("estimated_max_invocations")) is not int or manifest["estimated_max_invocations"] <= 0:
        errors.append("estimated_max_invocations must be a positive integer")
    if manifest.get("status") == "AUTHORIZED":
        if manifest.get("execution_permitted") is not True or not manifest.get("authorized_by") or not manifest.get("authorization_evidence"):
            errors.append("authorized execution requires explicit actor/evidence and execution_permitted=true")
    elif manifest.get("execution_permitted") is not False:
        errors.append("non-authorized manifest must prohibit execution")
    if manifest.get("critical_positive_prompts_per_model_category", 0) < 20:
        errors.append("critical category sample target is below 20")
    if manifest.get("representative_run_repetitions", 0) < 3:
        errors.append("representative repetitions are below 3")
    return errors
