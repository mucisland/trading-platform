#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[1]
SESSION_ARTIFACTS_DIR = ROOT / ".session-artifacts"

HANDOFF = ROOT / "status" / "session_handoff.md"
HANDOFF_HISTORY_DIR = ROOT / "status" / "handoff_history"
MANIFEST = SESSION_ARTIFACTS_DIR / "current_session_manifest.json"
VERIFICATION = SESSION_ARTIFACTS_DIR / "current_session_verification.json"
RECOVERY_RESULT = SESSION_ARTIFACTS_DIR / "current_recovery_result.json"
COMMIT_MESSAGE_ARTIFACT = SESSION_ARTIFACTS_DIR / "current_commit_message.txt"


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


def read_json(path: Path) -> Dict[str, Any]:
    """Read and decode a JSON file."""
    return json.loads(read_text(path))


def run_git(
    args: List[str],
    *,
    check: bool = True,
    capture_output: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Run a git command from the repository root."""
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=check,
        text=True,
        capture_output=capture_output,
    )


def require_clean_verification() -> dict:
    """Require that post-session verification passed and commit is allowed."""
    data = read_json(VERIFICATION)
    if not data.get("passed", False):
        raise RuntimeError(
            "Post-session verification did not pass. Refusing to finalize session."
        )
    if not data.get("eligible_for_commit", False):
        raise RuntimeError(
            "Session is not eligible for commit. Refusing to finalize session."
        )
    return data


def load_manifest() -> dict:
    """Load the current session manifest."""
    return read_json(MANIFEST)


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
        raise ValueError("Could not extract task status from status/session_handoff.md")
    return match.group(1).lower()


def extract_bullets(section_text: str) -> List[str]:
    """Extract bullet items from a markdown section."""
    items: List[str] = []
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
    return extract_bullets(section)[:6]


def extract_validation_lines(content: str) -> List[str]:
    """Extract validation summary lines from the handoff."""
    section = extract_section(content, "Validation run")
    return extract_bullets(section)[:6]


def extract_blockers(content: str) -> List[str]:
    """Extract blocker lines from the handoff."""
    section = extract_section(content, "Blockers")
    return extract_bullets(section)[:6]


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


def staged_files_exist() -> bool:
    """Return True if there are already staged changes."""
    result = run_git(["diff", "--cached", "--name-only"], capture_output=True)
    return bool(result.stdout.strip())


def working_tree_files() -> List[str]:
    """Return modified, added, deleted, or untracked files in the working tree."""
    result = run_git(["status", "--porcelain"], capture_output=True)
    files: List[str] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        path = line[3:].strip() if len(line) > 3 else line.strip()
        if path:
            files.append(path)
    return files


def ensure_nothing_staged() -> None:
    """Fail if there are already staged files, to keep finalization deterministic."""
    if staged_files_exist():
        raise RuntimeError(
            "There are already staged changes. Refusing to finalize ambiguous repository state."
        )


def ensure_handoff_history_dir() -> None:
    """Create the handoff history directory if needed."""
    HANDOFF_HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def next_handoff_history_id() -> str:
    """Allocate the next monotonic handoff-history identifier."""
    ensure_handoff_history_dir()

    max_id = 0
    for path in HANDOFF_HISTORY_DIR.glob("H-*.md"):
        match = re.fullmatch(r"H-(\d{5})", path.stem)
        if match:
            max_id = max(max_id, int(match.group(1)))

    return f"H-{max_id + 1:05d}"


def archive_current_handoff() -> Path:
    """Archive the current session handoff as an immutable history entry."""
    handoff_content = read_text(HANDOFF).rstrip()
    archive_id = next_handoff_history_id()
    timestamp = datetime.now(timezone.utc).isoformat()

    archive_path = HANDOFF_HISTORY_DIR / f"{archive_id}.md"
    archive_content = (
        f"# {archive_id}\n\n"
        f"- archived_from: /status/session_handoff.md\n"
        f"- timestamp: {timestamp}\n\n"
        f"{handoff_content}\n"
    )
    archive_path.write_text(archive_content, encoding="utf-8")
    return archive_path


def stage_all_session_changes() -> List[str]:
    """Stage all current repository changes for the session commit."""
    files = working_tree_files()
    if not files:
        raise RuntimeError("No repository changes detected. Nothing to finalize.")
    run_git(["add", "-A"])
    return files


def infer_standard_commit_header(manifest: dict) -> str:
    """Build the first-line commit summary from manifest task metadata."""
    task_id = manifest.get("task_id")
    task_title = manifest.get("task_title")

    if task_id and task_title:
        return f"{task_id}: {task_title[:72]}"
    if task_id:
        return f"{task_id}: session update"
    return "session: planning update"


def build_standard_commit_message(manifest: dict) -> str:
    """Construct a minimal task-oriented commit message aligned to version-control policy."""
    header = infer_standard_commit_header(manifest)
    return f"{header}\n"


def build_recovery_commit_message(recovery_result: dict) -> str:
    """Construct a minimal recovery-specific commit message aligned to version-control policy."""
    recovery_id = recovery_result.get("recovery_id", "R-UNKNOWN")
    target_value = recovery_result.get("rollback_target_value", "unknown")
    return f"{recovery_id}: recover repository to trusted state {target_value}\n"


def write_commit_message(message: str) -> Path:
    """Write the generated commit message to a session artifact file."""
    SESSION_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    COMMIT_MESSAGE_ARTIFACT.write_text(message, encoding="utf-8")
    return COMMIT_MESSAGE_ARTIFACT


def commit_session(message_file: Path) -> None:
    """Create the single session commit from the staged repository state."""
    run_git(["commit", "-F", str(message_file)])


def push_session() -> None:
    """Push the current branch to its default remote."""
    branch = current_branch()
    if not branch:
        raise RuntimeError("Could not determine current branch for push.")
    run_git(["push", "origin", branch])


def determine_session_kind(manifest: dict) -> str:
    """Determine whether the session is implementation, planning, or recovery."""
    if RECOVERY_RESULT.exists():
        return "recovery"
    return manifest.get("mode", "implementation")


def main() -> int:
    """Finalize a verified session into one structured git commit."""
    parser = argparse.ArgumentParser(
        description="Finalize a verified agent session into one git commit."
    )
    parser.add_argument("--push", action="store_true", help="Push after a successful commit")
    parser.add_argument(
        "--allow-planning-commit",
        action="store_true",
        help="Allow commit finalization for planning sessions as well",
    )
    args = parser.parse_args()

    try:
        require_clean_verification()
        manifest = load_manifest()

        session_kind = determine_session_kind(manifest)
        if session_kind == "planning" and not args.allow_planning_commit:
            raise RuntimeError(
                "Session mode is planning. Refusing to commit unless --allow-planning-commit is provided."
            )

        ensure_nothing_staged()
        parse_handoff_outcome()  # validates handoff shape enough for finalization flow

        archive_path = archive_current_handoff()
        print(f"Archived current handoff to: {archive_path}")

        changed_files = stage_all_session_changes()
        if not changed_files:
            raise RuntimeError("No changed files detected after staging.")

        if session_kind == "recovery":
            recovery_result = read_json(RECOVERY_RESULT)
            commit_message = build_recovery_commit_message(recovery_result)
        else:
            commit_message = build_standard_commit_message(manifest)

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
