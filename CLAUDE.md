# CLAUDE.md — standing rules for this project

## Stack
- Python 3, **standard library only**. The only third-party package allowed is
  `pytest` (for tests). Do not add other dependencies.

## Running
- Program: `python lift.py <command> [args]` (e.g. `python lift.py view`).
- Tests: `python -m pytest`

## Tests
- Every test names the requirement ID it checks (e.g. `R3`) in its function
  name or docstring.
- Tests must use a temporary data file (pytest `tmp_path`), never the real
  `workouts.json`.
- Each test must be able to fail if the code it checks is wrong.

## Git
- Never undo or amend a commit (no `--amend`, `reset`, `revert` of pushed work,
  or force-push). Fix mistakes with a new commit.
- Make small commits. Each message says what changed and why.
- Do not push unless asked.

## Docs
- Requirements live in `problem.md`; design in `spec.md`.
- Significant decisions go in `docs/decisions/NNNN-<name>.md` as Y-statements.
