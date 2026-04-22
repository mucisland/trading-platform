# Trading Platform (Agentic Development Harness)

This repository contains:

- a trading platform (project domain)
- an agentic development harness (task-driven workflow)

---

## Requirements

- Python 3.10+
- Git
- `uv` (recommended)

---

## Setup

```bash
git clone <repo-url>
cd trading-platform

uv venv
source .venv/bin/activate

uv sync --extra dev
```

---

## Run tests

```bash
pytest
```

Run only harness tests:

```bash
pytest tests/dev_harness
```

---

## Run one agent session

```bash
python scripts/run_agent_session.py --mode implementation
```

---

## Run development loop (experimental)

```bash
python scripts/run_dev_loop.py --max-iterations 1
```

Start with one iteration.

---

## Structure

```text
src/trading_platform/
  dev_harness/

scripts/
backlog/
status/
tests/
.session-artifacts/
```

---

## Notes

- `.session-artifacts/` is disposable
- `status/` contains durable workflow state
- all work must come from backlog tasks
