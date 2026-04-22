#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from trading_platform.dev_harness.task_selector import load_tasks, select_task  # noqa: E402

SESSION_ARTIFACTS_DIR = ROOT / ".session-artifacts"
LOOP_STATE = SESSION_ARTIFACTS_DIR / "current_loop_state.json"

BACKLOG_OPEN_DIR = ROOT / "backlog" / "open"
BACKLOG_FIX_PLAN = ROOT / "backlog" / "fix_plan.md"
RECOVERY_PLAN = ROOT / "status" / "current_recovery_plan.json"


def run(cmd: list[str], allow_failure: bool = False) -> subprocess.CompletedProcess[str]:
    """Run a command from the repository root."""
    result = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    if not allow_failure and result.returncode != 0:
        stderr = result.stderr.strip()
        stdout = result.stdout.strip()
        detail = stderr or stdout or "no output"
        raise RuntimeError(f"Command failed: {' '.join(cmd)} :: {detail}")
    return result


def clear_session_artifacts() -> None:
    """Remove all session artifacts and recreate the directory."""
    if SESSION_ARTIFACTS_DIR.exists():
        shutil.rmtree(SESSION_ARTIFACTS_DIR)
    SESSION_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


def read_json(path: Path) -> Dict[str, Any]:
    """Read and decode a JSON file."""
    return json.loads(path.read_text(encoding="utf-8"))


def recovery_required() -> bool:
    """Return True if a durable recovery plan exists and requests recovery."""
    if not RECOVERY_PLAN.exists():
        return False
    try:
        plan = read_json(RECOVERY_PLAN)
    except Exception:
        return False
    return plan.get("recovery_required") is True


def selectable_task_exists() -> bool:
    """Return True if at least one implementation task is currently selectable."""
    try:
        tasks = load_tasks(BACKLOG_OPEN_DIR, BACKLOG_FIX_PLAN)
        result = select_task(tasks)
        return result.selected_task_id is not None
    except Exception:
        return False


def selected_task_id() -> Optional[str]:
    """Return the currently selected implementation task id, if any."""
    tasks = load_tasks(BACKLOG_OPEN_DIR, BACKLOG_FIX_PLAN)
    result = select_task(tasks)
    return result.selected_task_id


def write_loop_state(
    iteration: int,
    mode: str,
    status: str,
    selected_task: Optional[str] = None,
    stop_reason: str = "",
) -> None:
    """Write the current loop state for debugging and observability."""
    LOOP_STATE.write_text(
        json.dumps(
            {
                "iteration": iteration,
                "selected_mode": mode,
                "selected_task": selected_task,
                "status": status,
                "stop_reason": stop_reason,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def run_implementation(agent: str, task_id: Optional[str]) -> None:
    """Run one implementation iteration."""
    cmd = [
        "python",
        "scripts/run_agent_session.py",
        "--mode",
        "implementation",
        "--agent",
        agent,
        "--invoke",
    ]
    if task_id:
        cmd += ["--task", task_id]

    run(cmd)
    run(["python", "scripts/verify_session_outcome.py"])
    run(["python", "scripts/finalize_session.py"])


def run_planning(agent: str) -> None:
    """Run one planning iteration."""
    run(
        [
            "python",
            "scripts/run_agent_session.py",
            "--mode",
            "planning",
            "--agent",
            agent,
            "--invoke",
        ]
    )
    run(["python", "scripts/verify_session_outcome.py"])
    # Planning commits remain optional by policy.
    # Uncomment if you later decide planning sessions should auto-commit:
    # run(["python", "scripts/finalize_session.py", "--allow-planning-commit"])


def run_recovery() -> None:
    """Run one recovery iteration."""
    run(["python", "scripts/validate_recovery_plan.py"])
    run(["python", "scripts/execute_recovery.py"])
    run(["python", "scripts/verify_session_outcome.py"])
    run(["python", "scripts/finalize_session.py"])


def choose_mode() -> tuple[str, Optional[str]]:
    """Choose the next loop mode deterministically."""
    if recovery_required():
        return "recovery", None

    if selectable_task_exists():
        return "implementation", selected_task_id()

    return "planning", None


def main() -> int:
    """Run the unattended development loop conservatively."""
    parser = argparse.ArgumentParser(description="Run the unattended development loop.")
    parser.add_argument("--agent", default="claude-code")
    parser.add_argument("--max-iterations", type=int, default=1)
    args = parser.parse_args()

    try:
        for iteration in range(1, args.max_iterations + 1):
            clear_session_artifacts()

            mode, task_id = choose_mode()
            write_loop_state(iteration, mode, "running", selected_task=task_id)

            try:
                if mode == "recovery":
                    run_recovery()
                elif mode == "implementation":
                    run_implementation(args.agent, task_id)
                else:
                    run_planning(args.agent)
            except Exception as exc:
                write_loop_state(
                    iteration,
                    mode,
                    "stopped",
                    selected_task=task_id,
                    stop_reason=str(exc),
                )
                raise

            write_loop_state(iteration, mode, "completed", selected_task=task_id)

        return 0

    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
