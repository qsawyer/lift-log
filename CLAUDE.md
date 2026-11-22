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
- Never let a test read the terminal. Run any command that can ask a
  question (e.g. `delete` without `--yes`, or `export` onto an existing
  file) with explicit stdin, as the `ask()` helper in `tests/test_round5.py`
  does. Otherwise the test can hang.
- Run the CLI in tests with `cwd` set to `tmp_path` (as `run()`/`ask()` do):
  `export` writes `workouts.csv` into the current folder by default.
- Read exported CSV with `encoding="utf-8-sig", newline=""` (the file
  starts with a byte-order mark).
- R12 makes `--unit` stick: once a test logs with `unit="kg"`, later adds
  without `unit=` in that same file also log kg. Pass `unit="lbs"` when a
  test needs lbs after a kg entry.

## Code rules
- Program output must be plain ASCII (e.g. `->`, not `→`). The user is on
  Windows, where piped output may use cp1252 and crash on other characters.
- Compare exercise names only through `exercise_key()` in `lift.py` (case- and
  space-insensitive). Never rewrite the names stored in the data file.
- Changing the data file format requires bumping `FILE_VERSION` and still
  reading older files (see decision 0001).
- Never read or modify the real `workouts.json`; it holds the user's data.
  To try the program by hand, set `LIFT_LOG_FILE` to a scratch file and run
  from a scratch folder (otherwise `view` reads the real data and `export`
  copies it into the repo folder).
- Code that writes any file other than the data file (like `export`) must
  refuse to write onto the data file (`same_file()`), even with `--yes`,
  and write through a temp file plus `os.replace`, like `save()`.
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
  `save(path, entries)` alone drops both saved settings: `units` (the R11
  display mode) and `log_unit` (the R12 logging default). Keep these two
  settings separate; neither one changes the other.
- Entries are identified by their stable `id` (R13), never by list position
  or `view` order. Parse user-typed IDs with `parse_id()` and look them up
  with `find_entry()`. Create entries only through `add_entry()`, which gives
  out the ID. `load_file()` gives IDs to entries that lack them.
- When printing a single entry with its weight as typed (`Saved:`,
  `edit`, `delete`), use `describe(e)`.
- Questions to the user go through `confirm()`, where end of input means
  "no". A command that asks must also have a flag (like `--yes`) that skips
  the question.
- Shared test helpers (`add`, `run`, `data_file`) live in `tests/test_lift.py`
  and are imported by later test files; don't rename them without updating
  every importer. `add()` takes an optional `unit=` (omit it to use the
  saved default unit, which is lbs until a unit has been given).

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
