#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from trading_platform.dev_harness.task_selector import (  # noqa: E402
    SelectionResult,
    extract_task_markdown,
    load_tasks,
    select_task,
)

SESSION_ARTIFACTS_DIR = ROOT / ".session-artifacts"

DEFAULT_INSTRUCTION_FILES = [
    ROOT / "AGENT.md",
    ROOT / "agent" / "workflow.md",
    ROOT / "agent" / "project_rules.md",
    ROOT / "agent" / "patterns.md",
]

DEFAULT_HANDOFF = ROOT / "status" / "session_handoff.md"
DEFAULT_BACKLOG = ROOT / "backlog" / "fix_plan.md"
BACKLOG_OPEN_DIR = ROOT / "backlog" / "open"

IMPLEMENTATION_TEMPLATE = ROOT / "agent" / "templates" / "implementation_session_prompt.txt"
PLANNING_TEMPLATE = ROOT / "agent" / "templates" / "planning_session_prompt.txt"


def read_text(path: Path) -> str:
    """Read a UTF-8 text file and fail clearly if it is missing."""
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    return path.read_text(encoding="utf-8")


def run_script(path: Path) -> None:
    """Run a repository script and raise on non-zero exit."""
    if not path.exists():
        raise FileNotFoundError(f"Missing required script: {path}")
    result = subprocess.run([str(path)], cwd=ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Script failed: {path} (exit {result.returncode})")


def load_optional_files(paths: List[str]) -> Dict[str, str]:
    """Load optional repository files passed on the command line."""
    loaded: Dict[str, str] = {}
    for rel in paths:
        p = ROOT / rel
        loaded[rel] = read_text(p)
    return loaded


def render_template(template: str, replacements: Dict[str, str]) -> str:
    """Fill a text template by replacing placeholder tokens."""
    rendered = template
    for key, value in replacements.items():
        rendered = rendered.replace(f"<{key}>", value)
    return rendered


def ensure_session_artifacts_dir() -> None:
    """Create the session artifacts directory if needed."""
    SESSION_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


def join_named_sections(files: Dict[str, str], fallback: str) -> str:
    """Render loaded files into named markdown sections for prompt injection."""
    if not files:
        return fallback
    return "\n\n".join(f"## {path}\n\n{content}" for path, content in files.items())


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
    prompt_template: str,
) -> Dict[str, object]:
    """Build a machine-readable manifest describing the current session context."""
    manifest: Dict[str, object] = {
        "mode": mode,
        "agent": agent,
        "task_id": task_id,
        "task_title": task_title,
        "files_loaded": files_loaded,
        "specs_loaded": specs_loaded,
        "runbooks_loaded": runbooks_loaded,
        "extra_files_loaded": extra_files_loaded,
        "prompt_template": prompt_template,
    }
    if selection is not None:
        manifest["selection"] = {
            "selected_task_id": selection.selected_task_id,
            "reason": selection.reason,
            "skipped": selection.skipped,
        }
    return manifest


def invoke_agent(agent: str, prompt_path: Path) -> None:
    """Invoke the configured external agent CLI with the rendered prompt file."""
    if agent == "claude-code":
        subprocess.run(["claude", str(prompt_path)], check=True, cwd=ROOT)
    elif agent == "codex":
        subprocess.run(["codex", str(prompt_path)], check=True, cwd=ROOT)
    else:
        raise ValueError(f"Unknown agent: {agent}")


def main() -> int:
    """Prepare one agent session by initializing the environment, selecting work, and rendering prompt artifacts."""
    parser = argparse.ArgumentParser(description="Prepare one agent session prompt and manifest.")
    parser.add_argument("--mode", choices=["implementation", "planning"], required=True)
    parser.add_argument("--agent", default="claude-code")
    parser.add_argument("--task", help="Optional explicit task id, e.g. T-00001")
    parser.add_argument("--planning-goal", default="Improve backlog clarity and selector-readiness.")
    parser.add_argument("--spec", action="append", default=[], help="Relative path to a spec file")
    parser.add_argument("--runbook", action="append", default=[], help="Relative path to a runbook file")
    parser.add_argument("--file", action="append", default=[], help="Relative path to an extra source/test file")
    parser.add_argument("--skip-init", action="store_true", help="Skip session_init.sh and verify_env.sh")
    parser.add_argument("--invoke", action="store_true", help="Invoke the selected agent directly")
    parser.add_argument("--force-recovery", action="store_true", help="Force recovery evaluation in planning mode")
    args = parser.parse_args()

    try:
        if not args.skip_init:
            run_script(ROOT / "scripts" / "session_init.sh")
            run_script(ROOT / "scripts" / "verify_env.sh")

        ensure_session_artifacts_dir()

        handoff_content = read_text(DEFAULT_HANDOFF)
        backlog_content = read_text(DEFAULT_BACKLOG) if DEFAULT_BACKLOG.exists() else ""

        specs_contents = load_optional_files(args.spec)
        runbook_contents = load_optional_files(args.runbook)
        extra_contents = load_optional_files(args.file)

        selected_task_markdown = ""
        selected_task_id: Optional[str] = None
        selected_task_title: Optional[str] = None
        selection_result: Optional[SelectionResult] = None
        prompt_template_path: Path

        if args.mode == "implementation":
            tasks = load_tasks(BACKLOG_OPEN_DIR, DEFAULT_BACKLOG)
            task_lookup = {t.task_id: t for t in tasks}

            if args.task:
                if args.task not in task_lookup:
                    raise ValueError(f"Explicit task not found: {args.task}")
                selected_task_id = args.task
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
                selected_task_title = task_lookup[selected_task_id].title

            selected_task_markdown = extract_task_markdown(BACKLOG_OPEN_DIR, DEFAULT_BACKLOG, selected_task_id)

            prompt_template_path = IMPLEMENTATION_TEMPLATE
            prompt = render_template(
                read_text(prompt_template_path),
                {
                    "TASK_CONTENT": selected_task_markdown,
                    "HANDOFF_CONTENT": handoff_content,
                    "SPEC_CONTENTS": join_named_sections(
                        specs_contents,
                        "(no additional spec files provided)",
                    ),
                    "RUNBOOK_CONTENT": join_named_sections(
                        runbook_contents,
                        "(no additional runbook provided)",
                    ),
                    "CODE_CONTEXT": join_named_sections(
                        extra_contents,
                        "(no additional source/test context provided)",
                    ),
                },
            )
        else:
            prompt_template_path = PLANNING_TEMPLATE
            planning_goal = args.planning_goal
            if args.force_recovery:
                planning_goal += "\n\n## Recovery override\nRecovery mode is explicitly requested."

            prompt = render_template(
                read_text(prompt_template_path),
                {
                    "PLANNING_GOAL": planning_goal,
                    "BACKLOG_CONTENT": backlog_content or "(no backlog fallback file provided)",
                    "HANDOFF_CONTENT": handoff_content,
                    "SPEC_CONTENTS": join_named_sections(
                        specs_contents,
                        "(no additional spec files provided)",
                    ),
                },
            )

        prompt_path = SESSION_ARTIFACTS_DIR / "current_session_prompt.txt"
        manifest_path = SESSION_ARTIFACTS_DIR / "current_session_manifest.json"

        prompt_path.write_text(prompt, encoding="utf-8")

        files_loaded = [str(p.relative_to(ROOT)) for p in DEFAULT_INSTRUCTION_FILES if p.exists()]
        if DEFAULT_BACKLOG.exists():
            files_loaded.append(str(DEFAULT_BACKLOG.relative_to(ROOT)))
        files_loaded.append(str(DEFAULT_HANDOFF.relative_to(ROOT)))

        manifest = build_manifest(
            mode=args.mode,
            agent=args.agent,
            task_id=selected_task_id,
            task_title=selected_task_title,
            selection=selection_result,
            files_loaded=files_loaded,
            specs_loaded=args.spec,
            runbooks_loaded=args.runbook,
            extra_files_loaded=args.file,
            prompt_template=str(prompt_template_path.relative_to(ROOT)),
        )
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        print(f"Prompt written to: {prompt_path}")
        print(f"Manifest written to: {manifest_path}")

        if selection_result is not None:
            print(f"Selection: {selection_result.reason}")
            if selection_result.selected_task_id:
                print(f"Selected task: {selection_result.selected_task_id}")

        if args.invoke:
            invoke_agent(args.agent, prompt_path)

        return 0

    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
