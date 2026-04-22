#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict


ROOT = Path(__file__).resolve().parents[1]
SESSION_ARTIFACTS = ROOT / ".session-artifacts"
RECOVERY_PLAN = SESSION_ARTIFACTS / "current_recovery_plan.json"
RECOVERY_PLAN_VALIDATION = SESSION_ARTIFACTS / "current_recovery_plan_validation.json"
SESSION_MANIFEST = SESSION_ARTIFACTS / "current_session_manifest.json"
SESSION_VERIFICATION = SESSION_ARTIFACTS / "current_session_verification.json"
LOOP_STATE = SESSION_ARTIFACTS / "current_loop_state.json"


def run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}")


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def clear_session_artifacts() -> None:
    if SESSION_ARTIFACTS.exists():
        shutil.rmtree(SESSION_ARTIFACTS)
    SESSION_ARTIFACTS.mkdir(parents=True, exist_ok=True)


def recovery_required() -> bool:
    if not RECOVERY_PLAN.exists():
        return False
    try:
        plan = read_json(RECOVERY_PLAN)
    except Exception:
        return False
    return plan.get("recovery_required") is True


def selectable_task_exists() -> bool:
    # Conservative v1 approach:
    # let run_agent_session.py be the selector; here we only choose planning
    # if recovery is not active. We assume implementation first and let failure
    # fall back to planning when needed.
    return True


def write_loop_state(iteration: int, mode: str, status: str, stop_reason: str = "") -> None:
    LOOP_STATE.write_text(
        json.dumps(
            {
                "iteration": iteration,
                "selected_mode": mode,
                "status": status,
                "stop_reason": stop_reason,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def run_implementation(agent: str) -> None:
    run(["python", "scripts/run_agent_session.py", "--mode", "implementation", "--agent", agent, "--invoke"])
    run(["python", "scripts/verify_session_outcome.py"])
    run(["python", "scripts/finalize_session.py"])


def run_planning(agent: str) -> None:
    run(["python", "scripts/run_agent_session.py", "--mode", "planning", "--agent", agent, "--invoke"])
    run(["python", "scripts/verify_session_outcome.py"])
    # Optional by policy; keep disabled by default
    # run(["python", "scripts/finalize_session.py", "--allow-planning-commit"])


def run_recovery() -> None:
    run(["python", "scripts/validate_recovery_plan.py"])
    run(["python", "scripts/execute_recovery.py"])
    run(["python", "scripts/verify_session_outcome.py"])
    run(["python", "scripts/finalize_session.py"])


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the unattended development loop.")
    parser.add_argument("--agent", default="claude-code")
    parser.add_argument("--max-iterations", type=int, default=1)
    args = parser.parse_args()

    try:
        for iteration in range(1, args.max_iterations + 1):
            clear_session_artifacts()

            if recovery_required():
                mode = "recovery"
            elif selectable_task_exists():
                mode = "implementation"
            else:
                mode = "planning"

            write_loop_state(iteration, mode, "running")

            try:
                if mode == "recovery":
                    run_recovery()
                elif mode == "implementation":
                    run_implementation(args.agent)
                else:
                    run_planning(args.agent)
            except Exception as exc:
                write_loop_state(iteration, mode, "stopped", str(exc))
                raise

            write_loop_state(iteration, mode, "completed")

        return 0

    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
