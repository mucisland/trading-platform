# T-00000 Harness Preflight

## Purpose

Verify that the agentic harness workflow executes end-to-end without manual intervention.

This task does not implement product functionality. It validates the harness itself.

---

## Scope

In scope:

- task selection
- prompt generation
- session execution
- artifact generation
- session verification
- session finalization
- version control integration
- handoff history archiving

Out of scope:

- business logic
- feature development
- non-harness refactoring

---

## Preconditions

- repository is clean
- `.session-artifacts/` is empty or absent
- all scripts are executable
- at least one valid task exists (this task)

---

## Execution steps

1. Run session initialization:

    ./scripts/session_init.sh
    ./scripts/verify_env.sh

2. Run agent session:

    python scripts/run_agent_session.py --mode implementation

3. Verify session outcome:

    python scripts/verify_session_outcome.py

4. Finalize session:

    python scripts/finalize_session.py

---

## Expected behavior

The workflow must:

- select this task deterministically
- generate a valid session prompt
- produce a valid `/status/session_handoff.md`
- generate session artifacts in `.session-artifacts/`
- pass verification without manual fixes
- archive handoff to `/status/handoff_history/H-xxxxx.md`
- create exactly one commit
- include all relevant non-ignored changes
- produce a valid commit message

---

## Acceptance criteria

All of the following must be true:

- `verify_session_outcome.py` exits successfully
- `finalize_session.py` exits successfully
- exactly one new commit exists
- commit message follows version control rules
- `/status/session_handoff.md` is updated
- a new `/status/handoff_history/H-xxxxx.md` exists
- `.session-artifacts/` contains only session artifacts
- no unexpected files are created
- no manual intervention was required

---

## Failure handling

If any step fails:

- do not modify scripts ad hoc
- record the failure in `/status/session_handoff.md`
- create a follow-up task describing the issue
- do not proceed with further tasks

---

## Notes

- This task may result in no meaningful code changes.
- Minimal or no code changes are acceptable if the harness is already correct.
- The purpose is validation, not feature implementation.

---

## Next task (if successful)

Proceed with first real implementation task (e.g. T-00001).
