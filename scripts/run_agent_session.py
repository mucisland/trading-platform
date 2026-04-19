"""
# Example usage

## Implementation mode with auto-selection:

```
python scripts/run_agent_session.py \
  --mode implementation \
  --spec specs/architecture.md \
  --spec specs/trader-runtime.md \
  --runbook runbooks/setup.md \
  --file scripts/session_init.sh \
  --file scripts/verify_env.sh
```

## Implementation mode with explicit task override:

```
python scripts/run_agent_session.py \
  --mode implementation \
  --task FP-001 \
  --spec specs/architecture.md \
  --runbook runbooks/setup.md
```

Planning mode:

```
python scripts/run_agent_session.py \
  --mode planning \
  --planning-goal "Refine Milestone 0 tasks for selector-readiness." \
  --spec specs/architecture.md
```

"""
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = ROOT / ".artifacts"

DEFAULT_INSTRUCTION_FILES = [
    ROOT / "AGENT.md",
    ROOT / "agent" / "workflow.md",
    ROOT / "agent" / "project_rules.md",
    ROOT / "agent" / "patterns.md",
]

DEFAULT_HANDOFF = ROOT / "status" / "session_handoff.md"
DEFAULT_BACKLOG = ROOT / "backlog" / "fix_plan.md"

IMPLEMENTATION_TEMPLATE = ROOT / "agent" / "templates" / "implementation_session_prompt.txt"
PLANNING_TEMPLATE = ROOT / "agent" / "templates" / "planning_session_prompt.txt"


@dataclass
class Task:
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
    selected_task_id: Optional[str]
    reason: str
    skipped: List[Dict[str, str]]


def read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    return path.read_text(encoding="utf-8")


def run_script(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Missing required script: {path}")
    result = subprocess.run([str(path)], cwd=ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Script failed: {path} (exit {result.returncode})")


def parse_bullet_list(value: str) -> List[str]:
    value = value.strip()
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def normalize_priority(value: str) -> int:
    mapping = {"high": 0, "medium": 1, "low": 2}
    return mapping.get(value.strip().lower(), 99)


def parse_tasks_from_fix_plan(content: str) -> List[Task]:
    """
    Expects tasks in this approximate form:

    ### FP-001
    - title: ...
    - type: ...
    - priority: ...
    - status: ...
    - milestone: ...
    - blocked_by:
    - depends_on:
    - scope: ...
    - acceptance_signal: ...
    - files_likely_touched:
      - file1
      - file2
    - notes:
      - note
    - discovered_from:
    - next_if_done:
    - next_if_blocked:
    """
    lines = content.splitlines()
    tasks: List[Task] = []

    task_indices = [i for i, line in enumerate(lines) if re.match(r"^###\s+FP-\d+\s*$", line.strip())]
    task_indices.append(len(lines))

    for idx in range(len(task_indices) - 1):
        start = task_indices[idx]
        end = task_indices[idx + 1]
        block = lines[start:end]
        task_id = block[0].strip().replace("###", "").strip()

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

        for line in block[1:]:
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

        tasks.append(
            Task(
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
        )

    return tasks


def task_is_selectable(task: Task, done_task_ids: set[str]) -> Tuple[bool, str]:
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


def extract_task_block(content: str, task_id: str) -> str:
    pattern = rf"(^###\s+{re.escape(task_id)}\s*$)(.*?)(?=^###\s+FP-\d+\s*$|\Z)"
    match = re.search(pattern, content, flags=re.MULTILINE | re.DOTALL)
    if not match:
        raise ValueError(f"Task not found in fix_plan.md: {task_id}")
    return match.group(0).strip()


def load_optional_files(paths: List[str]) -> Dict[str, str]:
    loaded: Dict[str, str] = {}
    for rel in paths:
        p = ROOT / rel
        loaded[rel] = read_text(p)
    return loaded


def render_template(template: str, replacements: Dict[str, str]) -> str:
    rendered = template
    for key, value in replacements.items():
        rendered = rendered.replace(f"<{key}>", value)
    return rendered


def ensure_artifacts_dir() -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


def build_manifest(
    mode: str,
    agent: str,
    task_id: Optional[str],
    task_title: Optional[str],
    selection: Optional[SelectionResult],
    files_loaded: List[str],
    specs_loaded: List[str],
    runbooks_loaded: List[str],
    extra_files_loaded: List[str],
) -> Dict[str, object]:
    manifest: Dict[str, object] = {
        "mode": mode,
        "agent": agent,
        "task_id": task_id,
        "task_title": task_title,
        "files_loaded": files_loaded,
        "specs_loaded": specs_loaded,
        "runbooks_loaded": runbooks_loaded,
        "extra_files_loaded": extra_files_loaded,
    }
    if selection is not None:
        manifest["selection"] = {
            "selected_task_id": selection.selected_task_id,
            "reason": selection.reason,
            "skipped": selection.skipped,
        }
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare one agent session prompt and manifest.")
    parser.add_argument("--mode", choices=["implementation", "planning"], required=True)
    parser.add_argument("--agent", default="claude-code")
    parser.add_argument("--task", help="Optional explicit task id, e.g. FP-001")
    parser.add_argument("--planning-goal", default="Improve backlog clarity and selector-readiness.")
    parser.add_argument("--spec", action="append", default=[], help="Relative path to a spec file")
    parser.add_argument("--runbook", action="append", default=[], help="Relative path to a runbook file")
    parser.add_argument("--file", action="append", default=[], help="Relative path to an extra source/test file")
    parser.add_argument("--skip-init", action="store_true", help="Skip session_init.sh and verify_env.sh")
    args = parser.parse_args()

    try:
        if not args.skip_init:
            run_script(ROOT / "scripts" / "session_init.sh")
            run_script(ROOT / "scripts" / "verify_env.sh")

        ensure_artifacts_dir()

        instruction_contents = {str(path.relative_to(ROOT)): read_text(path) for path in DEFAULT_INSTRUCTION_FILES}
        handoff_content = read_text(DEFAULT_HANDOFF)
        backlog_content = read_text(DEFAULT_BACKLOG)

        specs_contents = load_optional_files(args.spec)
        runbook_contents = load_optional_files(args.runbook)
        extra_contents = load_optional_files(args.file)

        selected_task_block = ""
        selected_task_id: Optional[str] = None
        selected_task_title: Optional[str] = None
        selection_result: Optional[SelectionResult] = None

        if args.mode == "implementation":
            tasks = parse_tasks_from_fix_plan(backlog_content)

            if args.task:
                selected_task_id = args.task
                selected_task_block = extract_task_block(backlog_content, args.task)
                task_lookup = {t.task_id: t for t in tasks}
                if args.task not in task_lookup:
                    raise ValueError(f"Explicit task not found: {args.task}")
                selected_task_title = task_lookup[args.task].title
                selection_result = SelectionResult(
                    selected_task_id=args.task,
                    reason="Task explicitly provided by CLI.",
                    skipped=[],
                )
            else:
                selection_result = select_task(tasks)
                if not selection_result.selected_task_id:
                    raise RuntimeError(
                        "No selectable implementation task found. Use planning mode to repair or refine the backlog."
                    )
                selected_task_id = selection_result.selected_task_id
                selected_task_block = extract_task_block(backlog_content, selected_task_id)
                task_lookup = {t.task_id: t for t in tasks}
                selected_task_title = task_lookup[selected_task_id].title

            template = read_text(IMPLEMENTATION_TEMPLATE)
            prompt = render_template(
                template,
                {
                    "TASK_CONTENT": selected_task_block,
                    "HANDOFF_CONTENT": handoff_content,
                    "SPEC_CONTENTS": "\n\n".join(
                        f"## {path}\n\n{content}" for path, content in specs_contents.items()
                    )
                    or "(no additional spec files provided)",
                    "RUNBOOK_CONTENT": "\n\n".join(
                        f"## {path}\n\n{content}" for path, content in runbook_contents.items()
                    )
                    or "(no additional runbook provided)",
                    "CODE_CONTEXT": "\n\n".join(
                        f"## {path}\n\n{content}" for path, content in extra_contents.items()
                    )
                    or "(no additional source/test context provided)",
                },
            )

        else:
            template = read_text(PLANNING_TEMPLATE)
            prompt = render_template(
                template,
                {
                    "PLANNING_GOAL": args.planning_goal,
                    "BACKLOG_CONTENT": backlog_content,
                    "HANDOFF_CONTENT": handoff_content,
                    "SPEC_CONTENTS": "\n\n".join(
                        f"## {path}\n\n{content}" for path, content in specs_contents.items()
                    )
                    or "(no additional spec files provided)",
                },
            )

        prompt_path = ARTIFACTS_DIR / "current_session_prompt.txt"
        manifest_path = ARTIFACTS_DIR / "current_session_manifest.json"

        prompt_path.write_text(prompt, encoding="utf-8")

        manifest = build_manifest(
            mode=args.mode,
            agent=args.agent,
            task_id=selected_task_id,
            task_title=selected_task_title,
            selection=selection_result,
            files_loaded=[str(p.relative_to(ROOT)) for p in DEFAULT_INSTRUCTION_FILES]
            + [str(DEFAULT_BACKLOG.relative_to(ROOT)), str(DEFAULT_HANDOFF.relative_to(ROOT))],
            specs_loaded=args.spec,
            runbooks_loaded=args.runbook,
            extra_files_loaded=args.file,
        )
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        print(f"Prompt written to: {prompt_path}")
        print(f"Manifest written to: {manifest_path}")
        if selection_result is not None:
            print(f"Selection: {selection_result.reason}")
            if selection_result.selected_task_id:
                print(f"Selected task: {selection_result.selected_task_id}")

        return 0

    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
