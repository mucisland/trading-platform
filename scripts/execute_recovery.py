#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = ROOT / ".session-artifacts"

RECOVERY_PLAN = ARTIFACTS_DIR / "current_recovery_plan.json"
RECOVERY_PLAN_VALIDATION = ARTIFACTS_DIR / "current_recovery_plan_validation.json"
RECOVERY_RESULT = ARTIFACTS_DIR / "current_recovery_result.json"

RECOVERY_HISTORY_DIR = ROOT / "status" / "recovery_history"
SESSION_HANDOFF = ROOT / "status" / "session_handoff.md"


@dataclass
class RecoveryExecutionResult:
    """Structured result of recovery execution."""

    recovery_executed: bool
    recovery_id: str
    rollback_target_type: str
    rollback_target_value: str
    validation_passed: bool
    commands_run: List[str]
    recovery_history_file: str
    handoff_updated: bool
    timestamp: str
    notes: List[str]


def read_text(path: Path) -> str:
    """Read a UTF-8 text file and fail clearly if missing."""
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> Dict[str, Any]:
    """Read and decode a JSON file."""
    return json.loads(read_text(path))


def run_command(cmd: str) -> None:
    """Run a shell command from the repository root and fail on non-zero exit."""
    result = subprocess.run(cmd, shell=True, cwd=ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd} (exit {result.returncode})")


def run_git(args: List[str], capture_output: bool = False) -> subprocess.CompletedProcess[str]:
    """Run a git command from the repository root."""
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=capture_output,
    )


def ensure_plan_is_valid() -> Dict[str, Any]:
    """Require that a validated recovery plan exists and has passed validation."""
    if not RECOVERY_PLAN.exists():
        raise FileNotFoundError(f"Missing recovery plan: {RECOVERY_PLAN}")

    if not RECOVERY_PLAN_VALIDATION.exists():
        raise FileNotFoundError(
            f"Missing recovery plan validation artifact: {RECOVERY_PLAN_VALIDATION}"
        )

    validation = read_json(RECOVERY_PLAN_VALIDATION)
    if not validation.get("passed", False):
        raise RuntimeError("Recovery plan validation did not pass. Refusing to execute recovery.")

    return read_json(RECOVERY_PLAN)


def ensure_clean_worktree() -> None:
    """Fail if the git working tree is not clean."""
    result = run_git(["status", "--porcelain"], capture_output=True)
    if result.stdout.strip():
        raise RuntimeError(
            "Working tree is not clean. Refusing to execute recovery with uncommitted changes present."
        )


def checkout_commit(commit_id: str) -> None:
    """Restore repository state to the target commit via hard reset."""
    run_git(["reset", "--hard", commit_id])


def restore_checkpoint(checkpoint_id: str) -> None:
    """Placeholder for future checkpoint-based restoration."""
    raise NotImplementedError(
        f"Checkpoint restore is not implemented yet. Requested checkpoint: {checkpoint_id}"
    )


def execute_restore(plan: Dict[str, Any]) -> Tuple[str, str]:
    """Execute the requested restore target and return its type and value."""
    target = plan["rollback_target"]
    target_type = target["target_type"]
    target_value = target["target_value"]

    if target_type == "commit":
        checkout_commit(target_value)
    elif target_type == "checkpoint":
        restore_checkpoint(target_value)
    else:
        raise RuntimeError(f"Unsupported rollback target type: {target_type}")

    return target_type, target_value


def run_post_restore_validation(commands: List[str]) -> None:
    """Run the post-restore validation command list in order."""
    for cmd in commands:
        run_command(cmd)


def ensure_recovery_history_dir() -> None:
    """Create the recovery history directory if it does not yet exist."""
    RECOVERY_HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def write_recovery_history(plan: Dict[str, Any], validation_passed: bool) -> Path:
    """Write a durable human-readable recovery history entry."""
    ensure_recovery_history_dir()

    recovery_id = plan["recovery_id"]
    target = plan["rollback_target"]
    decision_context = plan["decision_context"]
    timestamp = datetime.now(timezone.utc).isoformat()

    history_path = RECOVERY_HISTORY_DIR / f"{recovery_id}.md"

    affected_range = plan.get("affected_range")
    affected_range_text = ""
    if isinstance(affected_range, dict):
        from_value = affected_range.get("from", "")
        to_value = affected_range.get("to", "")
        if from_value or to_value:
            affected_range_text = f"- affected_range: {from_value}..{to_value}\n"

    notes = plan.get("notes", [])
    notes_block = ""
    if notes:
        notes_block = "\n## Notes\n\n" + "\n".join(f"- {item}" for item in notes) + "\n"

    content = (
        f"# {recovery_id}\n\n"
        f"- timestamp: {timestamp}\n"
        f"- recovery_type: {plan['recovery_type']}\n"
        f"- decision_session: {decision_context.get('decision_session', '')}\n"
        f"- execution_session: recovery-execution\n"
        f"- rollback_target: {target['target_type']}:{target['target_value']}\n"
        f"{affected_range_text}"
        f"- reason: {plan['reason']}\n\n"
        f"## Validation after restore\n\n"
        f"Commands:\n"
        + "\n".join(f"- {cmd}" for cmd in plan["post_restore_validation"])
        + "\n\n"
        f"Result:\n"
        f"- {'passed' if validation_passed else 'failed'}\n\n"
        f"## Next recommended task\n\n"
        f"- {plan['next_recommended_task']}\n"
        f"{notes_block}"
    )

    history_path.write_text(content, encoding="utf-8")
    return history_path


def write_session_handoff(plan: Dict[str, Any], validation_passed: bool) -> None:
    """Overwrite the current session handoff with recovery execution state."""
    target = plan["rollback_target"]
    timestamp = datetime.now(timezone.utc).isoformat()

    content = f"""# Session Handoff

## Session metadata
- Date: {timestamp}
- Session type: recovery
- Task ID:
- Task title: Execute recovery {plan["recovery_id"]}

## Goal
Restore the repository to a previously trusted state defined by the recovery plan artifact.

## Scope boundary
In scope:
- recovery plan execution
- repository restore
- post-restore validation
- recovery history update
- session handoff update

Out of scope:
- new implementation work
- backlog reprioritization beyond recovery follow-up

## Inputs used
- recovery plan artifact: `.session-artifacts/current_recovery_plan.json`
- recovery plan validation: `.session-artifacts/current_recovery_plan_validation.json`

## Changes made
- files changed:
  - status/recovery_history/{plan["recovery_id"]}.md
  - status/session_handoff.md
- behavior changed:
  - repository restored to trusted prior state
- docs updated:
  - recovery history entry written
- tests added/updated:

## Validation run
- commands:
  - {"; ".join(plan["post_restore_validation"])}
- result:
  - {"passed" if validation_passed else "failed"}
- failures:

## Outcome
- status: {"done" if validation_passed else "blocked"}
- summary:
  - recovery executed for {plan["recovery_id"]}
  - rollback target: {target["target_type"]}:{target["target_value"]}
  - reason: {plan["reason"]}

## Blockers
{"- post-restore validation failed" if not validation_passed else ""}

## New backlog items discovered

## Next recommended task
- {plan["next_recommended_task"]}
"""
    SESSION_HANDOFF.write_text(content, encoding="utf-8")


def write_recovery_result(
    plan: Dict[str, Any],
    target_type: str,
    target_value: str,
    history_path: Path,
    commands_run: List[str],
    validation_passed: bool,
) -> None:
    """Write a machine-readable recovery execution result artifact."""
    result = RecoveryExecutionResult(
        recovery_executed=True,
        recovery_id=plan["recovery_id"],
        rollback_target_type=target_type,
        rollback_target_value=target_value,
        validation_passed=validation_passed,
        commands_run=commands_run,
        recovery_history_file=str(history_path.relative_to(ROOT)),
        handoff_updated=True,
        timestamp=datetime.now(timezone.utc).isoformat(),
        notes=plan.get("notes", []),
    )
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    RECOVERY_RESULT.write_text(json.dumps(asdict(result), indent=2), encoding="utf-8")


def main() -> int:
    """Execute repository recovery from a validated recovery plan artifact."""
    try:
        plan = ensure_plan_is_valid()
        ensure_clean_worktree()

        commands_run: List[str] = []
        target_type, target_value = execute_restore(plan)

        for cmd in plan["post_restore_validation"]:
            run_command(cmd)
            commands_run.append(cmd)

        history_path = write_recovery_history(plan, validation_passed=True)
        write_session_handoff(plan, validation_passed=True)
        write_recovery_result(
            plan=plan,
            target_type=target_type,
            target_value=target_value,
            history_path=history_path,
            commands_run=commands_run,
            validation_passed=True,
        )

        print(f"Recovery executed successfully.")
        print(f"Recovery history written to: {history_path}")
        print(f"Recovery result written to: {RECOVERY_RESULT}")
        return 0

    except Exception as exc:
        try:
            if RECOVERY_PLAN.exists():
                plan = read_json(RECOVERY_PLAN)
                write_session_handoff(plan, validation_passed=False)
        except Exception:
            pass

        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
