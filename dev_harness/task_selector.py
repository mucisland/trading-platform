from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class Task:
    """Normalized backlog task metadata used by the selector."""

    task_id: str
    title: str
    task_type: str
    priority: str
    status: str
    milestone: str
    blocked_by: List[str]
    depends_on: List[str]
    scope: str
    acceptance_signal: str
    files_likely_touched: List[str]
    notes: List[str]
    discovered_from: str
    next_if_done: str
    next_if_blocked: str


@dataclass
class SelectionResult:
    """Result of deterministic task selection."""

    selected_task_id: Optional[str]
    reason: str
    skipped: List[Dict[str, str]]


def read_text(path: Path) -> str:
    """Read a UTF-8 text file and fail clearly if missing."""
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    return path.read_text(encoding="utf-8")


def parse_bullet_list(value: str) -> List[str]:
    """Parse a comma-separated inline metadata list into normalized items."""
    value = value.strip()
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def normalize_priority(value: str) -> int:
    """Map textual priorities to a stable sortable rank."""
    mapping = {"high": 0, "medium": 1, "low": 2}
    return mapping.get(value.strip().lower(), 99)


def _parse_task_lines(lines: List[str], task_id: str) -> Task:
    """Parse task metadata from markdown lines using the shared task schema."""
    data: Dict[str, str] = {
        "title": "",
        "type": "",
        "priority": "",
        "status": "",
        "milestone": "",
        "blocked_by": "",
        "depends_on": "",
        "scope": "",
        "acceptance_signal": "",
        "discovered_from": "",
        "next_if_done": "",
        "next_if_blocked": "",
    }
    files_likely_touched: List[str] = []
    notes: List[str] = []
    current_list_field: Optional[str] = None

    for line in lines:
        stripped = line.rstrip()

        field_match = re.match(r"^\s*-\s+([a-zA-Z0-9_]+):\s*(.*)$", stripped)
        if field_match:
            key = field_match.group(1)
            value = field_match.group(2).strip()
            current_list_field = None

            if key in ("files_likely_touched", "notes"):
                current_list_field = key
                if value:
                    if key == "files_likely_touched":
                        files_likely_touched.append(value)
                    else:
                        notes.append(value)
            elif key in data:
                data[key] = value
            continue

        list_item_match = re.match(r"^\s*-\s+(.*)$", stripped)
        if list_item_match and current_list_field:
            item = list_item_match.group(1).strip()
            if current_list_field == "files_likely_touched":
                files_likely_touched.append(item)
            elif current_list_field == "notes":
                notes.append(item)

    return Task(
        task_id=task_id,
        title=data["title"],
        task_type=data["type"],
        priority=data["priority"],
        status=data["status"],
        milestone=data["milestone"],
        blocked_by=parse_bullet_list(data["blocked_by"]),
        depends_on=parse_bullet_list(data["depends_on"]),
        scope=data["scope"],
        acceptance_signal=data["acceptance_signal"],
        files_likely_touched=files_likely_touched,
        notes=notes,
        discovered_from=data["discovered_from"],
        next_if_done=data["next_if_done"],
        next_if_blocked=data["next_if_blocked"],
    )


def parse_task_file(path: Path) -> Task:
    """Parse one task file from backlog/open using the shared task schema."""
    match = re.match(r"^(T-\d{5})", path.stem)
    if not match:
        raise ValueError(f"Invalid task filename: {path.name}")
    task_id = match.group(1)
    content = read_text(path)
    return _parse_task_lines(content.splitlines(), task_id)


def parse_tasks_from_fix_plan(content: str) -> List[Task]:
    """Parse embedded task entries from backlog/fix_plan.md."""
    lines = content.splitlines()
    tasks: List[Task] = []

    task_indices = [i for i, line in enumerate(lines) if re.match(r"^###\s+T-\d{5}\s*$", line.strip())]
    task_indices.append(len(lines))

    for idx in range(len(task_indices) - 1):
        start = task_indices[idx]
        end = task_indices[idx + 1]
        block = lines[start:end]
        task_id = block[0].strip().replace("###", "").strip()
        tasks.append(_parse_task_lines(block[1:], task_id))

    return tasks


def load_tasks(backlog_open_dir: Path, fallback_fix_plan: Path) -> List[Task]:
    """Load tasks from task files if present, otherwise fall back to fix_plan.md."""
    if backlog_open_dir.exists():
        tasks = [parse_task_file(path) for path in sorted(backlog_open_dir.glob("T-*.md"))]
        if tasks:
            return tasks

    if fallback_fix_plan.exists():
        return parse_tasks_from_fix_plan(read_text(fallback_fix_plan))

    raise FileNotFoundError(
        f"No task files found in {backlog_open_dir} and fallback backlog missing: {fallback_fix_plan}"
    )


def task_is_selectable(task: Task, done_task_ids: set[str]) -> Tuple[bool, str]:
    """Check whether a task satisfies the deterministic selection contract."""
    if task.status.strip().lower() != "open":
        return False, f"status is {task.status or 'missing'}"
    if task.blocked_by:
        return False, "blocked_by is not empty"
    unmet = [dep for dep in task.depends_on if dep not in done_task_ids]
    if unmet:
        return False, f"unmet dependencies: {', '.join(unmet)}"
    if not task.acceptance_signal.strip():
        return False, "missing acceptance_signal"
    if not task.scope.strip():
        return False, "missing scope"
    return True, "selectable"


def select_task(tasks: List[Task]) -> SelectionResult:
    """Select the next implementation task using deterministic ranking rules."""
    done_task_ids = {t.task_id for t in tasks if t.status.strip().lower() == "done"}
    skipped: List[Dict[str, str]] = []
    selectable: List[Task] = []

    for task in tasks:
        ok, reason = task_is_selectable(task, done_task_ids)
        if ok:
            selectable.append(task)
        else:
            skipped.append({"id": task.task_id, "reason": reason})

    if not selectable:
        return SelectionResult(
            selected_task_id=None,
            reason="No selectable implementation task found; planning mode should be used.",
            skipped=skipped,
        )

    selectable.sort(
        key=lambda t: (
            normalize_priority(t.priority),
            t.milestone or "ZZZ",
            t.task_id,
        )
    )
    selected = selectable[0]

    return SelectionResult(
        selected_task_id=selected.task_id,
        reason="Selected highest-priority open task with satisfied dependencies and defined acceptance signal.",
        skipped=skipped,
    )


def extract_task_block_from_fix_plan(content: str, task_id: str) -> str:
    """Extract one embedded task block from fix_plan.md by task id."""
    pattern = rf"(^###\s+{re.escape(task_id)}\s*$)(.*?)(?=^###\s+T-\d{{5}}\s*$|\Z)"
    match = re.search(pattern, content, flags=re.MULTILINE | re.DOTALL)
    if not match:
        raise ValueError(f"Task not found in fix_plan.md: {task_id}")
    return match.group(0).strip()


def extract_task_markdown(backlog_open_dir: Path, fallback_fix_plan: Path, task_id: str) -> str:
    """Load the full markdown for one task from task files or fix_plan fallback."""
    for path in sorted(backlog_open_dir.glob(f"{task_id}*.md")):
        return read_text(path)

    if fallback_fix_plan.exists():
        return extract_task_block_from_fix_plan(read_text(fallback_fix_plan), task_id)

    raise FileNotFoundError(f"Task markdown not found for task: {task_id}")
