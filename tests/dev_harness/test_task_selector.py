from pathlib import Path

import pytest

from trading_platform.dev_harness.task_selector import (
    Task,
    select_task,
    task_is_selectable,
)


def make_task(
    task_id: str,
    *,
    status: str = "open",
    priority: str = "medium",
    milestone: str = "M1",
    blocked_by=None,
    depends_on=None,
    acceptance_signal: str = "something",
    scope: str = "single-session",
):
    """Helper to construct Task objects concisely for testing."""
    return Task(
        task_id=task_id,
        title=f"title-{task_id}",
        task_type="implementation",
        priority=priority,
        status=status,
        milestone=milestone,
        blocked_by=blocked_by or [],
        depends_on=depends_on or [],
        scope=scope,
        acceptance_signal=acceptance_signal,
        files_likely_touched=[],
        notes=[],
        discovered_from="",
        next_if_done="",
        next_if_blocked="",
    )


# --- task_is_selectable tests ---


def test_task_selectable_basic():
    task = make_task("T-00001")
    ok, reason = task_is_selectable(task, done_task_ids=set())
    assert ok is True
    assert reason == "selectable"


def test_task_not_selectable_wrong_status():
    task = make_task("T-00001", status="done")
    ok, reason = task_is_selectable(task, done_task_ids=set())
    assert ok is False
    assert "status" in reason


def test_task_not_selectable_blocked():
    task = make_task("T-00001", blocked_by=["T-00000"])
    ok, reason = task_is_selectable(task, done_task_ids=set())
    assert ok is False
    assert "blocked_by" in reason


def test_task_not_selectable_missing_acceptance_signal():
    task = make_task("T-00001", acceptance_signal="")
    ok, reason = task_is_selectable(task, done_task_ids=set())
    assert ok is False
    assert "acceptance_signal" in reason


def test_task_not_selectable_missing_scope():
    task = make_task("T-00001", scope="")
    ok, reason = task_is_selectable(task, done_task_ids=set())
    assert ok is False
    assert "scope" in reason


def test_task_not_selectable_unmet_dependencies():
    task = make_task("T-00001", depends_on=["T-00000"])
    ok, reason = task_is_selectable(task, done_task_ids=set())
    assert ok is False
    assert "unmet dependencies" in reason


def test_task_selectable_with_satisfied_dependencies():
    task = make_task("T-00001", depends_on=["T-00000"])
    ok, _ = task_is_selectable(task, done_task_ids={"T-00000"})
    assert ok is True


# --- select_task tests ---


def test_select_highest_priority():
    t1 = make_task("T-00001", priority="low")
    t2 = make_task("T-00002", priority="high")
    result = select_task([t1, t2])

    assert result.selected_task_id == "T-00002"


def test_select_by_milestone_when_same_priority():
    t1 = make_task("T-00001", priority="high", milestone="M2")
    t2 = make_task("T-00002", priority="high", milestone="M1")
    result = select_task([t1, t2])

    assert result.selected_task_id == "T-00002"


def test_select_by_task_id_when_tied():
    t1 = make_task("T-00002", priority="high", milestone="M1")
    t2 = make_task("T-00001", priority="high", milestone="M1")
    result = select_task([t1, t2])

    assert result.selected_task_id == "T-00001"


def test_skips_non_selectable_tasks():
    t1 = make_task("T-00001", status="done")
    t2 = make_task("T-00002", priority="high")

    result = select_task([t1, t2])

    assert result.selected_task_id == "T-00002"
    assert any(s["id"] == "T-00001" for s in result.skipped)


def test_no_selectable_tasks_returns_none():
    t1 = make_task("T-00001", status="done")
    t2 = make_task("T-00002", blocked_by=["T-00001"])

    result = select_task([t1, t2])

    assert result.selected_task_id is None
    assert "No selectable" in result.reason


def test_dependency_chain_selection():
    t1 = make_task("T-00001", status="done")
    t2 = make_task("T-00002", depends_on=["T-00001"])
    t3 = make_task("T-00003", depends_on=["T-00002"])

    result = select_task([t1, t2, t3])

    assert result.selected_task_id == "T-00002"
