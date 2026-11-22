# Handoff — end of Round 3

Written for a fresh session starting Round 4. Read `CLAUDE.md` first (standing
rules), then `problem.md` (requirements), `spec.md` (exact behavior), and
`docs/decisions/` (why things are the way they are). `handoff-round-2.md` still
has useful background on R8/R9.

## Current state

- Requirements R1–R10 are all implemented and tested. Round 1 covered R1–R7
  (logging, grouping by muscle, saving after every input, viewing), Round 2
  covered R8 (personal records) and R9 (most improved), and Round 3 covered R10
  (weekly summary).
- **71 tests, all passing** (Python 3.13.7 on Windows 11). The suite takes about
  25 s because most tests run the CLI as a subprocess.
- Last commit is `dfd9fcf`. Nothing has been pushed. The handoff files and this
  round's CLAUDE.md edits are not committed.
- Files:
  - `lift.py` (about 370 lines): the whole program, in sections: storage,
    validation, operations/view, personal records (R8), most improved (R9),
    weekly summary (R10), CLI.
  - `tests/test_lift.py`: R1–R7. `tests/test_round2.py`: R8–R9.
    `tests/test_round3.py`: R10.
  - `spec.md`: has "Round 2" and "Round 3" sections with exact rules and
    output formats.
  - `docs/decisions/0001–0005`: Y-statement decision records.
  - `README.md`: user-facing usage, updated for `summary`.

## How to run

```
python lift.py add -e "Bench Press" -g chest -s 3 -r 8 -w 185 -d 7 [--date YYYY-MM-DD]
python lift.py view [--group legs]
python lift.py groups
python lift.py prs                          # R8
python lift.py improved                     # R9
python lift.py summary [--week YYYY-MM-DD]  # R10
python lift.py --file other.json view       # or set LIFT_LOG_FILE
python -m pytest
```

Data defaults to `workouts.json` next to `lift.py`. That file is gitignored and
holds the user's real data, so don't touch it.

## Round 3 commits

- `d3e3c44`: spec for R10, written before any code.
- `d54dde3`: `summary` command plus `tests/test_round3.py` (one commit, so no
  commit has failing tests this round).
- `f9b86a1`: README section.
- `dfd9fcf`: decisions 0004 and 0005.

## Decisions made in Round 3, and why

The user chose these when asked clarifying questions:
- **A week is Monday–Sunday.** `summary` shows the week containing today, and
  `--week DATE` shows the week containing DATE. Stable weeks can be checked
  against `view` and give the same answer each time. See `docs/decisions/0004`.
- **Workouts = distinct dates with at least one entry.** Three exercises on one
  day count as one workout.
- **"PRs for the week" = the best lift of each exercise trained that week**, even
  if it is lighter than an earlier week. It is *not* "new all-time records". See
  `docs/decisions/0005`.

Made by Claude without being asked, and reported to the user:
- **The R8 rule moved into `best_entry()`** (heaviest, then more reps, then
  earlier date). `personal_records()` and `weekly_summary()` both use it, so
  `prs` and `summary` can't disagree. This was a small refactor of Round 2 code,
  and the R8 tests still pass.
- **Names in `summary` use the latest spelling from the whole log**, not just the
  week, so they match `prs`. Matching uses `exercise_key()` as in Round 2.
- **Exercises are listed A–Z, ignoring case.** Lines use the same format as `prs`.
- **An empty week (or an empty log) is not an error.** It prints the heading,
  `Workouts: 0` and `No lifts logged this week.` This differs from other commands,
  which print `No workouts logged yet.` for an empty log.
- **An invalid `--week` date is an input error (exit 2).** It goes through the new
  `parse_date()` helper. `make_entry()` still has its own date check, which was
  not merged.
- **Output text:** `Week of <Mon> to <Sun>`, `Workouts: N` (which avoids
  singular/plural wording), and `PRs this week (best lift per exercise):`.

## Unresolved / possible follow-ups (none were requested)

- There is no way to see only *new all-time* PRs set in a week. This was the
  rejected alternative in 0005 and is easy to add with `best_entry()` over
  entries before the week's Monday.
- `summary` shows one week only. There is no multi-week history or "last week"
  shortcut. On a Monday, the user needs `--week` to see the week that just ended.
- `summary` has no `--group` filter, and it doesn't show volume, sets or average
  difficulty.
- Items still open from Round 2: no alias for abbreviations ("OHP"), R9 ignores
  rep-only progress, no `--top N` for `improved`, and bodyweight lifts at 0 lbs
  never show improvement.
- `make_entry()` and `parse_date()` both parse ISO dates. They could share code,
  but the error messages are the same, so it's harmless.

## Warnings for the next session

- **Working-copy files are CRLF.** `core.autocrlf=true`, and git stores LF. Git
  Bash's `grep -c $'\r'` reported 0 on a CRLF file, which was misleading. Python
  `read_text()`/`write_text()` translate newlines on Windows, so a script that
  rewrites a source file can silently change its line endings, and a multi-line
  `str.replace` pattern written with `\n` won't match. For byte checks, use
  Python `read_bytes()`. Git's "LF will be replaced by CRLF" warnings are
  harmless.
- **Mutation checks were done with a throwaway script**, kept outside the repo,
  that swaps one snippet, runs `tests/test_round3.py`, and restores the file from
  bytes (checksum verified afterwards). All 13 mutations made at least one test
  fail. Repeat this for new tests, as CLAUDE.md requires, and check that
  `lift.py` is byte-identical afterwards (`md5sum lift.py` before and after).
- **`tests/test_round2.py` and `tests/test_round3.py` both import `add`, `run` and
  the `data_file` fixture from `tests/test_lift.py`.** Renaming those breaks three
  files. Moving them to `tests/conftest.py` would now be worth doing.
- **`test_R10_defaults_to_current_week` uses the real clock.** It adds an entry
  dated today and then runs `summary` without `--week`. It could fail if run
  exactly across midnight from Sunday to Monday. There is deliberately no "fake
  today" setting, since none was requested.
- **Changing `best_entry()` changes both `prs` (R8) and `summary` (R10).** That
  is intended, but run both test files.
- **Commit `9f088fc` (Round 2) still has R9 tests that fail at that commit.**
  Keep this in mind for `git bisect`.
- **The data file format did not change in Round 3** (`FILE_VERSION` is still 1).
