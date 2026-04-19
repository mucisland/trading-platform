#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = ROOT / ".artifacts"
HANDOFF = ROOT / "status" / "session_handoff.md"
MANIFEST = ARTIFACTS_DIR / "current_session_manifest.json"
PROMPT = ARTIFACTS_DIR / "current_session_prompt.txt"
VERIFICATION = ARTIFACTS_DIR / "current_session_verification.json"
BACKLOG = ROOT / "backlog" / "fix_plan.md"


@dataclass
class VerificationResult:
    """Structured result of post-session verification."""
    passed: bool
    eligible_for_commit: bool
    hard_failures: List[str]
    warnings: List[str]


def read_text(path: Path) -> str:
    """Read a UTF-8 text file and fail clearly if missing."""
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    return path.read_text(encoding="utf-8")


def git_changed(path: Path) -> bool:
    """Return True if the given path differs from HEAD."""
    result = subprocess.run(
        ["git", "diff", "--quiet", "HEAD", "--", str(path)],
        cwd=ROOT,
    )
    return result.returncode != 0


def git_changed_any(paths: List[Path]) -> bool:
    """Return True if any path in the list differs from HEAD."""
    return any(git_changed(path) for path in paths if path.exists())


def extract_handoff_status(content: str) -> Optional[str]:
    """Extract status from the handoff outcome section."""
    match = re.search(r"^\s*-\s*status:\s*(done|blocked|partial)\s*$", content, flags=re.MULTILINE | re.IGNORECASE)
    return match.group(1).lower() if match else None


def validation_passed(content: str) -> Optional[bool]:
    """Infer whether validation passed from handoff text."""
    if re.search(r"pass(ed)?", content, flags=re.IGNORECASE):
        return True
    if re.search(r"fail(ed|ure)?", content, flags=re.IGNORECASE):
        return False
    return None


def blockers_present(content: str) -> bool:
    """Heuristically detect whether blockers are recorded in handoff."""
    block = re.search(r"## Blockers(.*?)(?=^## |\Z)", content, flags=re.MULTILINE | re.DOTALL)
    if not block:
        return False
    return bool(re.search(r"\S", block.group(1)))


def next_task_present(content: str) -> bool:
    """Heuristically detect whether a next recommended task is present."""
    block = re.search(r"## Next recommended task(.*?)(?=^## |\Z)", content, flags=re.MULTILINE | re.DOTALL)
    if not block:
        return False
    return bool(re.search(r"\S", block.group(1)))


def validation_section_present(content: str) -> bool:
    """Check whether handoff includes a validation section."""
    return "## Validation" in content or "## Validation run" in content


def outcome_section_present(content: str) -> bool:
    """Check whether handoff includes an outcome section."""
    return "## Outcome" in content


def backlog_changed() -> bool:
    """Return True if the backlog changed relative to HEAD."""
    if not BACKLOG.exists():
        return False
    return git_changed(BACKLOG)


def verify() -> VerificationResult:
    """Run post-session checks and return a structured verification result."""
    hard_failures: List[str] = []
    warnings: List[str] = []

    # Required artifact existence
    for required in (PROMPT, MANIFEST, HANDOFF):
        if not required.exists():
            hard_failures.append(f"Missing required artifact: {required.relative_to(ROOT)}")

    if hard_failures:
        return VerificationResult(
            passed=False,
            eligible_for_commit=False,
            hard_failures=hard_failures,
            warnings=warnings,
        )

    handoff_content = read_text(HANDOFF)
    manifest_content = read_text(MANIFEST)
    manifest = json.loads(manifest_content)

    # Handoff changed
    if not git_changed(HANDOFF):
        hard_failures.append("status/session_handoff.md was not updated during the session.")

    # Handoff structure
    if not validation_section_present(handoff_content):
        hard_failures.append("session_handoff.md is missing a validation section.")
    if not outcome_section_present(handoff_content):
        hard_failures.append("session_handoff.md is missing an outcome section.")

    status = extract_handoff_status(handoff_content)
    if status not in {"done", "partial", "blocked"}:
        hard_failures.append("session_handoff.md is missing a valid task status (done | partial | blocked).")

    val = validation_passed(handoff_content)

    if status == "done":
        if val is not True:
            hard_failures.append("Task is marked done but validation is not clearly recorded as passed.")

    if status == "blocked":
        if not blockers_present(handoff_content):
            hard_failures.append("Task is marked blocked but no blocker is recorded.")

    if status == "partial":
        if not next_task_present(handoff_content):
            hard_failures.append("Task is marked partial but no next recommended task is recorded.")

    # Backlog warning heuristic
    if status in {"done", "blocked"} and not backlog_changed():
        warnings.append(
            "Task is marked done/blocked but backlog/fix_plan.md does not appear to have changed."
        )

    # Manifest sanity
    if not manifest.get("mode"):
        hard_failures.append("Session manifest is missing mode.")
    if manifest.get("mode") == "implementation" and not manifest.get("task_id"):
        hard_failures.append("Implementation session manifest is missing task_id.")

    passed = len(hard_failures) == 0
    eligible_for_commit = passed

    return VerificationResult(
        passed=passed,
        eligible_for_commit=eligible_for_commit,
        hard_failures=hard_failures,
        warnings=warnings,
    )


def main() -> int:
    """Run verification and write the result artifact."""
    parser = argparse.ArgumentParser(description="Verify outcome of an agent session.")
    parser.parse_args()

    try:
        result = verify()
        VERIFICATION.parent.mkdir(parents=True, exist_ok=True)
        VERIFICATION.write_text(json.dumps(asdict(result), indent=2), encoding="utf-8")

        print(f"Verification written to: {VERIFICATION}")
        print(f"Passed: {result.passed}")
        print(f"Eligible for commit: {result.eligible_for_commit}")

        if result.hard_failures:
            print("\nHard failures:")
            for item in result.hard_failures:
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
