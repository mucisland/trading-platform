# Recovery Plan Artifact Schema

## Purpose

This document defines the machine-readable recovery plan artifact used by the harness to execute repository recovery deterministically.

Artifact location:

    .session-artifacts/current_recovery_plan.json

The planning/recovery agent produces this artifact.
The harness consumes and validates it before executing recovery.

---

## Required fields

A valid recovery plan must contain:

- `recovery_required`
- `recovery_id`
- `recovery_type`
- `reason`
- `decision_context`
- `rollback_target`
- `post_restore_validation`
- `next_recommended_task`

---

## Field definitions

### `recovery_required`
Type:
- boolean

Meaning:
- must be `true` for executable recovery plans

---

### `recovery_id`
Type:
- string

Format:
- `R-xxxxx`

Example:
- `R-00001`

Rules:
- must be unique
- must not reuse a previous recovery ID

---

### `recovery_type`
Type:
- string

Allowed values:
- `tactical`
- `strategic`

Meaning:
- `tactical` → limited rollback of a small recent change set
- `strategic` → broader rollback to restore a previously trusted direction

---

### `reason`
Type:
- string

Meaning:
- concise explanation of why recovery is required

Rules:
- must not be empty
- must be specific enough to justify rollback

---

### `decision_context`
Type:
- object

Required fields:
- `decision_mode`
- `decision_session`

Field meanings:
- `decision_mode` → usually `planning`
- `decision_session` → session or task reference that produced the decision

Example:
```json
{
  "decision_mode": "planning",
  "decision_session": "T-00042"
}
```

---

### `rollback_target`
Type:
- object

Required fields:
- `target_type`
- `target_value`

Allowed `target_type` values:
- `commit`
- `checkpoint`

Examples:
```json
{
  "target_type": "commit",
  "target_value": "abc1234"
}
```

```json
{
  "target_type": "checkpoint",
  "target_value": "CP-00003"
}
```

Rules:
- target must exist
- target must be restorable by the harness

---

### `affected_range`
Type:
- object or null

Optional but recommended.

Suggested fields:
- `from`
- `to`

Meaning:
- descriptive range of commits or states affected by the recovery

Example:
```json
{
  "from": "abc1234",
  "to": "def5678"
}
```

---

### `post_restore_validation`
Type:
- array of strings

Meaning:
- commands that must be run after rollback

Rules:
- must contain at least:
  - `./scripts/session_init.sh`
  - `./scripts/verify_env.sh`
  - `./scripts/run_fast_checks.sh`

Example:
```json
[
  "./scripts/session_init.sh",
  "./scripts/verify_env.sh",
  "./scripts/run_fast_checks.sh"
]
```

---

### `next_recommended_task`
Type:
- string

Meaning:
- the next task to continue with after successful recovery

Rules:
- must reference a valid task ID or a clearly defined planning action

---

## Optional fields

### `notes`
Type:
- array of strings

Meaning:
- additional context for humans or future automation

---

### `validation_rationale`
Type:
- string

Meaning:
- why the chosen validation commands are sufficient

---

## Example artifact

```json
{
  "recovery_required": true,
  "recovery_id": "R-00001",
  "recovery_type": "strategic",
  "reason": "Recent sessions degraded replay-correctness confidence and violated domain boundaries.",
  "decision_context": {
    "decision_mode": "planning",
    "decision_session": "T-00042"
  },
  "rollback_target": {
    "target_type": "commit",
    "target_value": "abc1234"
  },
  "affected_range": {
    "from": "abc1234",
    "to": "def5678"
  },
  "post_restore_validation": [
    "./scripts/session_init.sh",
    "./scripts/verify_env.sh",
    "./scripts/run_fast_checks.sh"
  ],
  "next_recommended_task": "T-00043",
  "notes": [
    "Restore to last state before interface contract drift."
  ]
}
```

---

## Validation rules

The harness must reject the recovery plan if:

- `recovery_required` is not `true`
- `recovery_id` is missing or malformed
- `recovery_type` is not one of the allowed values
- `reason` is empty
- `decision_context` is missing required fields
- `rollback_target` is missing or invalid
- `post_restore_validation` is empty
- required validation commands are missing
- `next_recommended_task` is empty

The harness must also reject the plan if:

- the rollback target does not exist
- the recovery ID already exists in `/status/recovery_history/`
- the target cannot be executed deterministically

---

## Execution contract

A recovery plan becomes executable only after validation succeeds.

The harness must:

1. validate the artifact
2. execute recovery
3. validate the restored state
4. write recovery history
5. create a recovery commit
