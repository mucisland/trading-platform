# R-00001

- timestamp: <ISO-8601>
- recovery_type: tactical | strategic
- decision_session: <task id or planning session reference>
- execution_session: <session reference>
- rollback_target: <commit id or checkpoint id>
- affected_range: <optional commit range>
- reason: <concise explanation>

## Validation after restore

Commands:
- ./scripts/session_init.sh
- ./scripts/verify_env.sh
- ./scripts/run_fast_checks.sh

Result:
- passed | failed

## Next recommended task

- <task id>

## Notes

- additional context if needed
