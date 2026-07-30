---
description: 'Pre pr quality check'
---

# Pre-PR Quality Check

Run all local code quality checks before opening a pull request. The AEFI project declares `black`, `flake8`, `mypy`, and `pytest` as dev dependencies but has no single command to run them all. This command chains them in the correct order.

## When to Use

- Before creating a pull request targeting `develop` or `main`
- After completing a feature to catch formatting, type, and test issues locally
- When a review is blocked on quality issues

## Checkpoints

- Is the `uv` virtual environment active or are you using `uv run`?
- Are all hardware drivers available (or are hardware tests skipped)?
- Does the diff introduce any `Result[T, Exception]` or `Result[T, Any]` at a layer boundary?
- Does any Application service method raise for a business-refused outcome instead of returning `Result`?
- Does any third-party exception escape an infrastructure adapter without translation?
- Does the Fake reproduce every failure-mode variant of its Real counterpart?

## Steps

### 1. Format check

Verify code formatting without modifying files:

```bash
uv run black --check src/
```

If formatting issues are found, auto-fix with `uv run black src/` then re-check.

### 2. Lint

Run static analysis:

```bash
uv run flake8 src/ --max-line-length=120 --exclude=src/_tests,__pycache__
```

Fix any reported issues before proceeding.

### 3. Type check

Run type checking (strict on application and domain layers):

```bash
uv run mypy src/domain/ src/application/ --ignore-missing-imports
```

### 4. Run tests

Run the full test suite (excluding hardware integration tests that require physical devices):

```bash
uv run pytest src/ -v --ignore=src/infrastructure/hardware
```

### 4.5. Error-taxonomy static checks

Enforce the `solidai-error-taxonomy-and-layer-contracts` standard by running four grep-based checks. Any hit is a violation.

**Check A — no generic error slot at layer boundaries:**

```bash
rg 'Result\[.*,\s*(Exception|Any)\s*\]' src/
```
Expected: 0 matches. Any hit means a `Result` boundary is typed with a non-layer-specific error slot.

**Check B — no `raise` for expected failure inside application services:**

```bash
rg -n '^\s*raise\b' src/application/services/
```
Every hit must be inspected and commented as a programmer error (bug, precondition violated by caller code). Expected business refusals must be returned as `Result`, not raised.

**Check C — no third-party exception past adapter boundary:**

For each `src/infrastructure/<adapter>/` folder, verify there is exactly one translation site. Locate `except` blocks catching third-party exceptions and confirm each returns a `<Adapter>Error` variant. Any `raise` inside `except` that re-raises a third-party exception past the adapter boundary is a violation.

```bash
rg -n 'except\s+\w+.*:' src/infrastructure/ -A 3 | rg -B 1 'raise\s+'
```

**Check D — Fake reproduces every Real failure-mode variant:**

For each `infrastructure/<adapter>/fake/`, verify its `_tests/` file exercises the same `<Adapter>Error` variants declared by the Real adapter. Structural symmetry test:

```bash
# Enumerate Real variants
rg -o '<Adapter>Error\.\w+' src/infrastructure/<adapter>/<adapter>.py | sort -u
# Enumerate Fake test coverage
rg -o '<Adapter>Error\.\w+' src/infrastructure/<adapter>/fake/_tests/ | sort -u
# Both sets must be equal
```

### 5. Verify all green

All five steps must pass before opening the PR — including the four taxonomy checks (A/B/C/D) whenever the diff touches `application/`, `infrastructure/`, or `domain/`. If `mypy` reports errors in `infrastructure/`, address them or add targeted `# type: ignore` with a comment explaining why.
