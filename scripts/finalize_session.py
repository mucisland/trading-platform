#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = ROOT / ".artifacts"

HANDOFF = ROOT / "status" / "session_handoff.md"
BACKLOG = ROOT / "backlog" / "fix_plan.md"
MANIFEST = ARTIFACTS_DIR / "current_session_manifest.json"
VERIFICATION = ARTIFACTS_DIR / "current_session_verification.json"


@dataclass
class SessionOutcome:
    """Structured information extracted from the current session handoff."""

    status: str
    changes: List[str]
    validation_lines: List[str]
    blockers: List[str]
    next_task_lines: List[str]


def read_text(path: Path) -> str:
    """Read a UTF-8 text file and fail clearly if missing."""
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    return path.read_text(encoding="utf-8")


def run_git(args: List[str], check: bool = True, capture_output: bool = False) -> subprocess.CompletedProcess[str]:
    """Run a git command from the repository root."""
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=check,
        text=True,
        capture_output=capture_output,
    )


def require_clean_verification() -> dict:
    """Load verification artifact and require that the session is eligible for commit."""
    data = json.loads(read_text(VERIFICATION))
    if not data.get("passed", False):
        raise RuntimeError("Post-session verification did not pass. Refusing to finalize session.")
    if not data.get("eligible_for_commit", False):
        raise RuntimeError("Session is not eligible for commit. Refusing to finalize session.")
    return data


def load_manifest() -> dict:
    """Load the current session manifest."""
    return json.loads(read_text(MANIFEST))


def extract_section(content: str, heading: str) -> str:
    """Extract one markdown section body by heading title."""
    pattern = rf"^##\s+{re.escape(heading)}\s*(.*?)(?=^##\s+|\Z)"
    match = re.search(pattern, content, flags=re.MULTILINE | re.DOTALL)
    return match.group(1).strip() if match else ""


def extract_status(content: str) -> str:
    """Extract the normalized task result status from the handoff."""
    match = re.search(
        r"^\s*-\s*status:\s*(done|blocked|partial)\s*$",
        content,
        flags=re.MULTILINE | re.IGNORECASE,
    )
    if not match:
        raise ValueError("Could not extract task status from session_handoff.md")
    return match.group(1).lower()


def extract_bullets(section_text: str) -> List[str]:
    """Extract bullet items from a markdown section."""
    items = []
    for line in section_text.splitlines():
        match = re.match(r"^\s*-\s+(.*)$", line.rstrip())
        if match:
            item = match.group(1).strip()
            if item:
                items.append(item)
    return items


def extract_changes(content: str) -> List[str]:
    """Extract high-signal change summary lines from the handoff."""
    section = extract_section(content, "Changes made")
    bullets = extract_bullets(section)
    return bullets[:6]


def extract_validation_lines(content: str) -> List[str]:
    """Extract validation summary lines from the handoff."""
    section = extract_section(content, "Validation run")
    bullets = extract_bullets(section)
    return bullets[:6]


def extract_blockers(content: str) -> List[str]:
    """Extract blocker lines from the handoff."""
    section = extract_section(content, "Blockers")
    bullets = extract_bullets(section)
    return bullets[:6]


def extract_next_task_lines(content: str) -> List[str]:
    """Extract next-task guidance lines from the handoff."""
    section = extract_section(content, "Next recommended task")
    bullets = extract_bullets(section)
    if bullets:
        return bullets[:6]
    if section:
        return [line.strip() for line in section.splitlines() if line.strip()][:6]
    return []


def parse_handoff_outcome() -> SessionOutcome:
    """Parse the current session handoff into a commit-friendly summary."""
    content = read_text(HANDOFF)
    return SessionOutcome(
        status=extract_status(content),
        changes=extract_changes(content),
        validation_lines=extract_validation_lines(content),
        blockers=extract_blockers(content),
        next_task_lines=extract_next_task_lines(content),
    )


def current_branch() -> str:
    """Return the current git branch name."""
    result = run_git(["branch", "--show-current"], capture_output=True)
    return result.stdout.strip()


def staged_or_modified_files() -> List[str]:
    """Return modified, added, deleted, or untracked files in the working tree."""
    result = run_git(["status", "--porcelain"], capture_output=True)
    files: List[str] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        # porcelain lines look like "XY path"
        path = line[3:].strip() if len(line) > 3 else line.strip()
        if path:
            files.append(path)
    return files


def ensure_nothing_staged() -> None:
    """Fail if there are already staged files, to keep one finalize path deterministic."""
    result = run_git(["diff", "--cached", "--name-only"], capture_output=True)
    if result.stdout.strip():
        raise RuntimeError("There are already staged changes. Refusing to finalize ambiguous repository state.")


def stage_session_changes() -> List[str]:
    """Stage all current repository changes for the session commit."""
    files = staged_or_modified_files()
    if not files:
        raise RuntimeError("No repository changes detected. Nothing to finalize.")
    run_git(["add", "-A"])
    return files


def infer_task_summary(manifest: dict) -> str:
    """Build the first-line commit summary from manifest task metadata."""
    task_id = manifest.get("task_id")
    task_title = manifest.get("task_title")

    if task_id and task_title:
        return f"{task_id}: {task_title[:72]}"
    if task_id:
        return f"{task_id}: session update"
    return "session: planning update"


def build_commit_message(manifest: dict, outcome: SessionOutcome) -> str:
    """Construct a structured commit message for the completed session."""
    header = infer_task_summary(manifest)

    lines: List[str] = [header, ""]
    lines.append(f"Result: {outcome.status}")
    lines.append("")

    lines.append("Changes:")
    if outcome.changes:
        for item in outcome.changes:
            lines.append(f"- {item}")
    else:
        lines.append("- see session_handoff.md")

    lines.append("")
    lines.append("Validation:")
    if outcome.validation_lines:
        for item in outcome.validation_lines:
            lines.append(f"- {item}")
    else:
        lines.append("- see session_handoff.md")

    if outcome.blockers:
        lines.append("")
        lines.append("Blockers:")
        for item in outcome.blockers:
            lines.append(f"- {item}")

    if outcome.next_task_lines:
        lines.append("")
        lines.append("Next:")
        for item in outcome.next_task_lines:
            lines.append(f"- {item}")

    return "\n".join(lines).rstrip() + "\n"


def write_commit_message(message: str) -> Path:
    """Write the generated commit message to an artifact file."""
    path = ARTIFACTS_DIR / "current_commit_message.txt"
    path.write_text(message, encoding="utf-8")
    return path


def commit_session(message_file: Path) -> None:
    """Create the single session commit from the staged repository state."""
    run_git(["commit", "-F", str(message_file)])


def push_session() -> None:
    """Push the current branch to its default remote."""
    branch = current_branch()
    if not branch:
        raise RuntimeError("Could not determine current branch for push.")
    run_git(["push", "origin", branch])


def main() -> int:
    """Finalize a verified agent session into one structured git commit."""
    parser = argparse.ArgumentParser(description="Finalize a verified agent session into one git commit.")
    parser.add_argument("--push", action="store_true", help="Push after a successful commit")
    parser.add_argument(
        "--allow-planning-commit",
        action="store_true",
        help="Allow commit finalization for planning sessions as well",
    )
    args = parser.parse_args()

    try:
        verification = require_clean_verification()
        manifest = load_manifest()

        mode = manifest.get("mode")
        if mode == "planning" and not args.allow_planning_commit:
            raise RuntimeError(
                "Session mode is planning. Refusing to commit unless --allow-planning-commit is provided."
            )

        ensure_nothing_staged()
        outcome = parse_handoff_outcome()
        changed_files = stage_session_changes()
        if not changed_files:
            raise RuntimeError("No changed files detected after staging.")

        commit_message = build_commit_message(manifest, outcome)
        message_file = write_commit_message(commit_message)

        print(f"Prepared commit message at: {message_file}")
        print("Commit preview:\n")
        print(commit_message)

        commit_session(message_file)
        print("Commit created successfully.")

        if args.push:
            push_session()
            print("Push completed successfully.")

        return 0

    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
