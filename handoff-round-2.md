# Handoff — end of Round 2

Written for a fresh session starting Round 3. Read `CLAUDE.md` first (standing
rules), then `problem.md` (requirements), `spec.md` (exact behavior), and
`docs/decisions/` (why things are the way they are).

## Current state

- Requirements R1–R9 are all implemented and tested. Round 1 covered R1–R7
  (logging lifts, grouping by muscle, saving after every input, viewing). Round 2
  covered R8 (personal records) and R9 (most-improved exercises).
- **58 tests, all passing** (Python 3.13.7 on Windows 11). The suite takes about
  20 s because most tests run the CLI as a subprocess.
- The working tree is clean at commit `0031a4c`, and nothing has been pushed.
- Files:
  - `lift.py` (about 315 lines): the whole program, in sections: storage,
    validation, operations/view, personal records (R8), most improved (R9), CLI.
  - `tests/test_lift.py`: R1–R7.
  - `tests/test_round2.py`: R8–R9.
  - `spec.md`: has a "Round 2" section with exact rules and output formats.
  - `docs/decisions/0001–0003`: Y-statement decision records.
  - `README.md`: user-facing usage, updated for `prs` and `improved`.
- No handoff file existed from Round 1. This is the first one.

## How to run

```
python lift.py add -e "Bench Press" -g chest -s 3 -r 8 -w 185 -d 7 [--date YYYY-MM-DD]
python lift.py view [--group legs]
python lift.py groups
python lift.py prs          # R8
python lift.py improved     # R9
python lift.py --file other.json view   # or set LIFT_LOG_FILE
python -m pytest
```

Data defaults to `workouts.json` next to `lift.py`. That file is gitignored and
may hold the user's real data, so don't touch it.

## Decisions made in Round 2, and why

The user chose these when asked clarifying questions:
- **A PR is the heaviest weight per exercise (R8).** Ties go to more reps, then the
  earliest date.
- **Improvement = heaviest weight ever − heaviest weight on the exercise's
  earliest date, in lbs (R9).** It is easy to check by eye and always agrees with
  the PR. See `docs/decisions/0002`.
- **R9 shows only the top 5.** This is the `TOP_IMPROVED` constant, and there is
  no CLI flag to change it.
- **Exercise names are matched ignoring case.**

Made by Claude without being asked, and reported to the user:
- **Names are matched with `exercise_key()`** (spaces collapsed, then casefold),
  computed **when reading**. Stored names are never rewritten. The displayed
  name is the most recent spelling (latest date; on the same date, the one added
  last). See `docs/decisions/0003`.
- **Muscle group plays no part in exercise identity** for R8/R9.
- **R9 lists only gains above 0.** Single-date or never-heavier exercises are
  left out, and with none it prints `No improvement recorded yet.`
- **R9 ties are sorted by name, A–Z, ignoring case.** The best-weight date shown
  is the first date that weight was reached.
- **`prs` is one alphabetical list**, not split by muscle group.
- **Weights print with `fmt_lbs()`**, which gives at most 2 decimals with no
  trailing zeros, so floats like `2.2000000000000002` never show.
- **R9 output uses `->`, not `→`.** See the Windows warning below.

## Unresolved / possible follow-ups (none were requested)

- Abbreviations and typos ("OHP" vs "Overhead Press", "Bench" vs "Bench Press")
  still count as separate exercises. An alias feature was considered and not built
  (decision 0003).
- R9 ignores progress in reps at the same weight. An estimated-1RM measure was
  rejected (decision 0002) but could come back if the user wants it.
- There is no `--top N` option for `improved`, and no `--group` filter for `prs`
  or `improved`.
- `prs` and `improved` read every entry on each run. That is fine at personal-log
  scale.
- Bodyweight lifts logged at 0 lbs have a PR of 0 lbs and never show
  improvement.

## Warnings for the next session

- **Commit `9f088fc` (R8) contains R9 tests that fail at that commit.** They were
  written ahead of the implementation and pass from `3d04139` on. Keep this in
  mind if you use `git bisect`.
- **`tests/test_round2.py` imports `add`, `run` and the `data_file` fixture from
  `tests/test_lift.py`.** Renaming those helpers breaks both files. A shared
  `tests/conftest.py` would be cleaner if more test files are added.
- **Windows is the user's platform.** When stdout is piped (as the tests do),
  Python may encode as cp1252, and non-ASCII output can raise
  `UnicodeEncodeError`.
- **Editing Python source via a bash heredoc that runs a Python patch script**
  turned `"\\n"` into a real newline and broke `lift.py` once. Prefer the Edit
  tool for source changes.
- **Git prints "LF will be replaced by CRLF" warnings.** They are harmless, and
  there is no `.gitattributes`.
- **Tests were checked with mutations**: the code was deliberately broken to
  confirm each test can fail. CLAUDE.md requires that every test can fail, so
  repeat this for new tests.
- **Changing the data file format** means bumping `FILE_VERSION` and reading
  old files (decision 0001). Round 2 needed no format change.
