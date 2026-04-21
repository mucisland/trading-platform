# Recovery Runbook

## Purpose

Defines the canonical procedure for restoring the repository to a previously trusted state.

This document is the authoritative source for how recovery is executed.

## Scope

This runbook is used when:

- recovery mode has been triggered (see `/agent/workflow.md`)
- a recovery plan artifact exists

This runbook defines how recovery is executed, not when it is chosen.

## Inputs

### Recovery plan artifact

Recovery execution requires a valid recovery plan artifact:

    .artifacts/current_recovery_plan.json

Its schema and validation rules are defined in:

    /docs/recovery_plan_schema.md

Recovery must not proceed if this artifact is missing or incomplete.

## Recovery plan validation

Before executing recovery, validate the recovery plan artifact against:

    /docs/recovery_plan_schema.md

Recovery must not proceed if:
- required fields are missing
- values are invalid
- rollback target is not restorable
- required validation commands are missing

Validation command:

    python scripts/validate_recovery_plan.py

This writes:

    .artifacts/current_recovery_plan_validation.json

Recovery must not proceed unless this validation passes.

## Recovery Procedure

### Step 1 — Confirm recovery plan

- verify recovery_required = true
- verify rollback_target exists
- verify artifact completeness

If validation fails:
- abort recovery
- record blocker in session handoff

### Step 2 — Stop forward work

- do not continue implementation tasks

### Step 3 — Prepare repository

- ensure working tree is clean or explicitly handled
- do not lose uncommitted changes silently

### Step 4 — Execute rollback

Run:

    python scripts/execute_recovery.py

This command:

1. validates the recovery plan
2. restores the repository to the rollback target
3. runs post-restore validation
4. writes recovery history
5. updates session handoff
6. writes `.artifacts/current_recovery_result.json`

Recovery execution must not proceed unless:

    python scripts/validate_recovery_plan.py

has passed.

### Step 5 — Reinitialize environment

    ./scripts/session_init.sh
    ./scripts/verify_env.sh

### Step 6 — Validate restored state

Run:

    ./scripts/run_fast_checks.sh

and any commands from:

    post_restore_validation

If validation fails:
- stop recovery
- record failure

### Step 7 — Create recovery commit / Finalizing recovery

After recovery execution succeeds and post-session verification passes, finalize the recovery event through the normal finalization path:

    python scripts/finalize_session.py

Recovery sessions are detected automatically by the presence of:

    .artifacts/current_recovery_result.json

### Step 8 — Resume workflow

Continue with:

    next_recommended_task

## Failure handling

If any step fails:

- stop recovery
- record failure in session handoff
- do not proceed to commit

## Constraints

- do not execute recovery without a valid plan artifact
- do not skip validation after rollback
- do not skip writing recovery history

## References

- Governance: `/agent/workflow.md`
- Version control: `/agent/version_control.md`
