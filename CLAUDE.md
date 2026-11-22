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
- Each test must be able to fail if the code it checks is wrong. Check this by
  temporarily breaking the code (a mutation) and confirming a test fails.
- Run the full suite, earlier rounds included, before every commit that touches code.

## Code rules
- Program output must be plain ASCII (e.g. `->`, not `→`). The user is on
  Windows, where piped output may use cp1252 and crash on other characters.
- Compare exercise names only through `exercise_key()` in `lift.py` (case- and
  space-insensitive). Never rewrite the names stored in the data file.
- Changing the data file format requires bumping `FILE_VERSION` and still
  reading older files (see decision 0001).
- Never read or modify the real `workouts.json`; it holds the user's data.
- Pick an exercise's best entry only through `best_entry()` in `lift.py` (the
  R8 rule: heaviest weight, then more reps, then earlier date), so `prs` and
  other commands never disagree.
- Working-copy line endings are mixed (`core.autocrlf=true`; git stores LF).
  `lift.py` and `README.md` are CRLF; the other tracked files are LF. Check a
  file's bytes before rewriting it with a script, and preserve whatever it
  has (use bytes, not `read_text`/`write_text`). Restore the file exactly
  after a mutation check.
- Weights have a unit (R6): every entry stores `weight` as typed plus `unit`
  (`lbs` or `kg`; a missing `unit` means lbs). Never compare raw
  `e["weight"]` values across entries; compare with `weight_lbs()` (or go
  through `best_entry()`). Never convert weights in the stored data.
- Print weights only through `fmt_weight(e, mode)` (and `fmt_gain()` for R9
  gains), so the R11 display mode (`lbs`, `kg`, `both`) applies everywhere.
  A new command that shows weights takes the `show` parent parser (`--units`)
  and defaults to the saved mode.
- Any code that saves the data file must carry the saved settings forward:
  read with `load_file()` and call `save(path, entries, settings)`.
  `save(path, entries)` alone drops the R11 display setting.
- Shared test helpers (`add`, `run`, `data_file`) live in `tests/test_lift.py`
  and are imported by later test files; don't rename them without updating
  every importer. `add()` takes an optional `unit=` (omit for lbs).

## Git
- Never undo or amend a commit (no `--amend`, `reset`, `revert` of pushed work,
  or force-push). Fix mistakes with a new commit.
- Make small commits. Each message says what changed and why.
- Do not push unless asked.

## Docs
- Requirements live in `problem.md`; design in `spec.md`.
- Significant decisions go in `docs/decisions/NNNN-<name>.md` as Y-statements.
- When a round's requirements change behavior, update `spec.md` and `README.md`.
- At the start of a session, read the latest `handoff-round-N.md` if one exists.
  Don't commit handoff files or CLAUDE.md edits unless the user says to.
