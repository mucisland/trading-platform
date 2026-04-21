#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = ROOT / ".artifacts"

RECOVERY_PLAN = ARTIFACTS_DIR / "current_recovery_plan.json"
RECOVERY_PLAN_VALIDATION = ARTIFACTS_DIR / "current_recovery_plan_validation.json"
RECOVERY_HISTORY_DIR = ROOT / "status" / "recovery_history"
CHECKPOINTS_FILE = ROOT / "status" / "checkpoints.md"

REQUIRED_VALIDATION_COMMANDS = [
    "./scripts/session_init.sh",
    "./scripts/verify_env.sh",
    "./scripts/run_fast_checks.sh",
]


@dataclass
class RecoveryPlanValidationResult:
    """Structured result of recovery plan validation."""

    passed: bool
    errors: List[str]
    warnings: List[str]


def read_text(path: Path) -> str:
    """Read a UTF-8 file and fail clearly if it is missing."""
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> Dict[str, Any]:
    """Read and decode a JSON file."""
    return json.loads(read_text(path))


def git_commit_exists(commit_id: str) -> bool:
    """Return True if the given Git commit exists in the repository."""
    result = subprocess.run(
        ["git", "cat-file", "-e", f"{commit_id}^{{commit}}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def checkpoint_exists(checkpoint_id: str) -> bool:
    """Return True if the checkpoint id appears in status/checkpoints.md."""
    if not CHECKPOINTS_FILE.exists():
        return False
    content = read_text(CHECKPOINTS_FILE)
    pattern = rf"^###\s+{re.escape(checkpoint_id)}\s*$"
    return re.search(pattern, content, flags=re.MULTILINE) is not None


def recovery_id_exists(recovery_id: str) -> bool:
    """Return True if a recovery history entry with this id already exists."""
    if not RECOVERY_HISTORY_DIR.exists():
        return False
    return any(path.stem == recovery_id for path in RECOVERY_HISTORY_DIR.glob("R-*.md"))


def require_type(obj: Dict[str, Any], key: str, expected_type: type, errors: List[str]) -> None:
    """Append an error if the field is missing or has the wrong type."""
    if key not in obj:
        errors.append(f"Missing required field: {key}")
        return
    if not isinstance(obj[key], expected_type):
        errors.append(f"Field '{key}' must be of type {expected_type.__name__}")


def validate_required_fields(plan: Dict[str, Any], errors: List[str]) -> None:
    """Validate presence and basic types of top-level required fields."""
    require_type(plan, "recovery_required", bool, errors)
    require_type(plan, "recovery_id", str, errors)
    require_type(plan, "recovery_type", str, errors)
    require_type(plan, "reason", str, errors)
    require_type(plan, "decision_context", dict, errors)
    require_type(plan, "rollback_target", dict, errors)
    require_type(plan, "post_restore_validation", list, errors)
    require_type(plan, "next_recommended_task", str, errors)


def validate_recovery_id(plan: Dict[str, Any], errors: List[str]) -> None:
    """Validate recovery id format and uniqueness."""
    recovery_id = plan.get("recovery_id")
    if not isinstance(recovery_id, str):
        return
    if not re.fullmatch(r"R-\d{5}", recovery_id):
        errors.append("Field 'recovery_id' must match format R-xxxxx")
        return
    if recovery_id_exists(recovery_id):
        errors.append(f"Recovery id already exists in history: {recovery_id}")


def validate_recovery_type(plan: Dict[str, Any], errors: List[str]) -> None:
    """Validate allowed recovery type values."""
    recovery_type = plan.get("recovery_type")
    if isinstance(recovery_type, str) and recovery_type not in {"tactical", "strategic"}:
        errors.append("Field 'recovery_type' must be 'tactical' or 'strategic'")


def validate_reason(plan: Dict[str, Any], errors: List[str]) -> None:
    """Ensure the reason field is not empty."""
    reason = plan.get("reason")
    if isinstance(reason, str) and not reason.strip():
        errors.append("Field 'reason' must not be empty")


def validate_recovery_required(plan: Dict[str, Any], errors: List[str]) -> None:
    """Ensure the artifact is executable as a recovery plan."""
    value = plan.get("recovery_required")
    if value is not True:
        errors.append("Field 'recovery_required' must be true")


def validate_decision_context(plan: Dict[str, Any], errors: List[str]) -> None:
    """Validate required structure of decision_context."""
    ctx = plan.get("decision_context")
    if not isinstance(ctx, dict):
        return
    for key in ("decision_mode", "decision_session"):
        if key not in ctx or not isinstance(ctx[key], str) or not ctx[key].strip():
            errors.append(f"decision_context.{key} is required and must be a non-empty string")


def validate_rollback_target(plan: Dict[str, Any], errors: List[str], warnings: List[str]) -> None:
    """Validate rollback target structure and existence."""
    target = plan.get("rollback_target")
    if not isinstance(target, dict):
        return

    target_type = target.get("target_type")
    target_value = target.get("target_value")

    if not isinstance(target_type, str) or target_type not in {"commit", "checkpoint"}:
        errors.append("rollback_target.target_type must be 'commit' or 'checkpoint'")
        return

    if not isinstance(target_value, str) or not target_value.strip():
        errors.append("rollback_target.target_value must be a non-empty string")
        return

    if target_type == "commit":
        if not git_commit_exists(target_value):
            errors.append(f"Rollback target commit does not exist: {target_value}")
    elif target_type == "checkpoint":
        if not CHECKPOINTS_FILE.exists():
            errors.append(
                f"Checkpoint target specified but {CHECKPOINTS_FILE.relative_to(ROOT)} does not exist"
            )
        elif not checkpoint_exists(target_value):
            errors.append(f"Rollback target checkpoint does not exist: {target_value}")
        else:
            warnings.append(
                "Checkpoint existence was validated by name only; restore mechanism must still support it."
            )


def validate_post_restore_validation(plan: Dict[str, Any], errors: List[str]) -> None:
    """Validate the post-restore validation command list."""
    commands = plan.get("post_restore_validation")
    if not isinstance(commands, list):
        return
    if not commands:
        errors.append("Field 'post_restore_validation' must not be empty")
        return
    if not all(isinstance(cmd, str) and cmd.strip() for cmd in commands):
        errors.append("All post_restore_validation entries must be non-empty strings")
        return

    missing = [cmd for cmd in REQUIRED_VALIDATION_COMMANDS if cmd not in commands]
    if missing:
        errors.append(
            "post_restore_validation is missing required commands: " + ", ".join(missing)
        )


def validate_next_recommended_task(plan: Dict[str, Any], errors: List[str]) -> None:
    """Validate the next_recommended_task field is present and non-empty."""
    value = plan.get("next_recommended_task")
    if isinstance(value, str) and not value.strip():
        errors.append("Field 'next_recommended_task' must not be empty")


def validate_plan(plan: Dict[str, Any]) -> RecoveryPlanValidationResult:
    """Validate the recovery plan artifact and return a structured result."""
    errors: List[str] = []
    warnings: List[str] = []

    validate_required_fields(plan, errors)
    validate_recovery_required(plan, errors)
    validate_recovery_id(plan, errors)
    validate_recovery_type(plan, errors)
    validate_reason(plan, errors)
    validate_decision_context(plan, errors)
    validate_rollback_target(plan, errors, warnings)
    validate_post_restore_validation(plan, errors)
    validate_next_recommended_task(plan, errors)

    return RecoveryPlanValidationResult(
        passed=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


def main() -> int:
    """Validate the current recovery plan and write a machine-readable result artifact."""
    try:
        plan = read_json(RECOVERY_PLAN)
        result = validate_plan(plan)

        ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        RECOVERY_PLAN_VALIDATION.write_text(
            json.dumps(asdict(result), indent=2),
            encoding="utf-8",
        )

        print(f"Validation written to: {RECOVERY_PLAN_VALIDATION}")
        print(f"Passed: {result.passed}")

        if result.errors:
            print("\nErrors:")
            for item in result.errors:
                print(f"- {item}")

        if result.warnings:
            print("\nWarnings:")
            for item in result.warnings:
                print(f"- {item}")

        return 0 if result.passed else 1

    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
