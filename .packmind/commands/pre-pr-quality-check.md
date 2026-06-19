# Pre-PR Quality Check

Run all local code quality checks before opening a pull request. The AEFI project declares `black`, `flake8`, `mypy`, and `pytest` as dev dependencies but has no single command to run them all. This command chains them in the correct order.

## When to Use

- Before creating a pull request targeting `develop` or `main`
- After completing a feature to catch formatting, type, and test issues locally
- When a review is blocked on quality issues

## Checkpoints

- Is the `uv` virtual environment active or are you using `uv run`?
- Are all hardware drivers available (or are hardware tests skipped)?

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

### 5. Verify all green

All four steps must pass before opening the PR. If `mypy` reports errors in `infrastructure/`, address them or add targeted `# type: ignore` with a comment explaining why.
