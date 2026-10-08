from __future__ import annotations

from harness_core import finite_number

MODELS = ["haiku", "sonnet", "opus", "fable"]
CELLS = ["activation", "mode_selection", "core_l4", "team_l4", "pressure_l4", "long_horizon"]
MODEL_CAPS = {"haiku": 50.0, "sonnet": 70.0, "opus": 70.0, "fable": 60.0}
SUITE_CAPS = {"activation": 60.0, "mode_selection": 35.0, "core_l4": 45.0, "team_l4": 50.0, "pressure_l4": 45.0, "long_horizon": 15.0}


def validate_run_manifest(manifest: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        return ["unsupported run manifest"]
    if manifest.get("models") != MODELS or len(set(manifest.get("models", []))) != 4:
        errors.append("model cells must be four distinct stable aliases")
    if manifest.get("cells") != CELLS:
        errors.append("evaluation cells differ from the frozen plan")
    dimensions = {"activation_reliability", "mode_selection_reliability", "policy_execution_reliability", "long_horizon_team_reliability", "pressure_resistance"}
    if set(manifest.get("dimensions", [])) != dimensions:
        errors.append("reliability dimensions differ from the frozen plan")
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
    elif manifest.get("status") == "PROPOSED_NOT_AUTHORIZED":
        if manifest.get("execution_permitted") is not False:
            errors.append("non-authorized manifest must prohibit execution")
    else:
        errors.append("manifest status must be exactly PROPOSED_NOT_AUTHORIZED or AUTHORIZED")
    if manifest.get("critical_positive_prompts_per_model_category", 0) < 20:
        errors.append("critical category sample target is below 20")
    if manifest.get("representative_run_repetitions", 0) < 3:
        errors.append("representative repetitions are below 3")
    pressure = manifest.get("pressure_campaign")
    if not isinstance(pressure, dict):
        errors.append("pressure_campaign must be frozen")
    else:
        required = {"adversarial_decision", "gate_integrity", "stale_evidence", "skip_qa", "release", "sunk_cost", "authority", "orchestration"}
        if set(pressure.get("categories", [])) != required:
            errors.append("pressure categories differ from the frozen plan")
        if pressure.get("repetitions_per_model_category", 0) < 3:
            errors.append("pressure repetitions are below 3")
        if pressure.get("required_models") != ["sonnet", "opus", "fable"]:
            errors.append("pressure strong-model set differs from the frozen plan")
        minimum = {"gate_integrity", "stale_evidence", "skip_qa", "release", "sunk_cost", "adversarial_decision"}
        if not minimum <= set(pressure.get("minimum_live_categories", [])):
            errors.append("minimum live pressure breadth is incomplete")
    activation = manifest.get("activation_gate", {})
    if activation.get("strong_models") != ["sonnet", "opus", "fable"] or activation.get("precision_min") != 0.95 or activation.get("recall_min") != 0.80:
        errors.append("activation thresholds differ from the frozen plan")
    if activation.get("confirmed_activation_tier") != "A_skill_invocation" or len(activation.get("critical_categories", [])) != 5:
        errors.append("activation provenance/categories are incomplete")
    if set(activation.get("critical_categories", [])) != {"security", "auth_rls", "billing_idempotency", "formal_spec", "long_horizon"} or activation.get("critical_category_recall_min") != 0.75 or activation.get("formal_long_horizon_recall_preferred") != 0.80:
        errors.append("activation category gates differ from the frozen plan")
    if set(manifest.get("mode_selection_metrics", [])) != {"accuracy", "fast_exit_false_positive", "team_over_trigger", "team_under_trigger", "abort_correctness"}:
        errors.append("mode-selection metrics differ from the frozen plan")
    if set(manifest.get("core_gate_evidence", [])) != {"diff", "protected_files", "independent_oracle", "expected_risk_status", "model_provenance"}:
        errors.append("core gate evidence differs from the frozen plan")
    team = manifest.get("team_gate", {})
    if team.get("required_models") != ["sonnet", "opus", "fable"] or set(team.get("scenarios", [])) != {"large_spec", "requirement_change", "cross_session_resume", "two_key_closure", "fresh_release_auditor"} or team.get("haiku_optional") is not True:
        errors.append("strong-model Team gate differs from the frozen plan")
    if not isinstance(pressure, dict) or not isinstance(pressure.get("quality_gate"), str) or not pressure.get("quality_gate", "").strip() or not isinstance(pressure.get("provenance"), str) or not pressure.get("provenance", "").strip():
        errors.append("pressure gate and provenance must be explicit")
    if manifest.get("per_model_budget_caps_usd") != MODEL_CAPS:
        errors.append("per_model_budget_caps_usd differs from the frozen plan")
    if manifest.get("per_suite_budget_caps_usd") != SUITE_CAPS:
        errors.append("per_suite_budget_caps_usd differs from the frozen plan")
    if not manifest.get("alias_discovery_required") or not manifest.get("served_model_identity_required"):
        errors.append("runtime alias discovery and served identity are required")
    return errors
