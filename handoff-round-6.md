# Handoff — end of Round 6

Written for a fresh session starting Round 7. Read `CLAUDE.md` first. It has
the standing rules, and a few were added this round: trying the program by
hand, writing files other than the data file, and reading exported CSV in
tests. Then read `problem.md` (requirements), `spec.md` (exact behavior; see
its "Round 6" section) and `docs/decisions/` (why things are the way they
are). `handoff-round-5.md` still has useful background on entry IDs (R13) and
the two saved settings (R11, R12).

## Current state

- Requirements R1-R14 are all implemented and tested. Round 6 added one:
  - R14: the user can export their data into a file that can be used in a
    spreadsheet (Google Sheets or Excel).
- **205 tests, all passing** (Python 3.13.7 on Windows 11). They take about
  80 s, because most tests run the CLI as a subprocess.
- The last commit is `4d24245`. Nothing has been pushed. This handoff file and
  this round's CLAUDE.md edits are not committed (the user will review them).
- The data file format did not change. `FILE_VERSION` is still 3.
- Files:
  - `lift.py` (about 735 lines): the whole program. Round 6 added an
    "export (R14)" section just before `parse_date()`: `DEFAULT_EXPORT`,
    `EXPORT_COLUMNS`, `export_weight()`, `export_rows()`, `same_file()`,
    `check_export_path()` and `write_csv()`. It also added the `export`
    subparser and a branch in `main()`.
  - `tests/test_round6.py`: R14, 33 tests (some parametrized). It imports
    `add`, `run`, `data_file` from `test_lift.py` and `ask` from
    `test_round5.py`, and defines `export()` (runs `export` with explicit
    stdin) and `read_csv()`.
  - `spec.md`: has a "Round 6" section, and `export` was added to the
    command list at the top.
  - `docs/decisions/0001-0011`. 0010 and 0011 are new this round.
  - `README.md`: new section "Export to a spreadsheet", before "Where data is
    stored".

## How to run

```
python lift.py add -e "Bench Press" -g chest -s 3 -r 8 -w 185 -d 7 [--date YYYY-MM-DD] [--unit lbs|kg]
python lift.py view [--group legs] [--units lbs|kg|both]
python lift.py edit 3 --reps 6                          # R13
python lift.py delete 3 [--yes|-y]                      # R13; asks [y/N]
python lift.py groups
python lift.py prs [--units ...]                        # R8
python lift.py improved [--units ...]                   # R9
python lift.py summary [--week YYYY-MM-DD] [--units ...]  # R10
python lift.py units [lbs|kg|both]                      # R11 display mode
python lift.py export [PATH] [--group G|-g G] [--yes|-y]  # R14; default PATH workouts.csv
python lift.py --file other.json view   # or set LIFT_LOG_FILE
python -m pytest
```

Data defaults to `workouts.json` next to `lift.py`. That file is gitignored and
holds the user's real data, so don't touch it. `export` writes into the
**current folder** by default, so run manual tries from a scratch folder
with `LIFT_LOG_FILE` set (see CLAUDE.md).

## What `export` does (short version; spec.md has the details)

- One header row, then one row per entry:
  `id,date,exercise,group,sets,reps,weight,unit,weight_lbs,weight_kg,difficulty`.
- `weight`/`unit` are exactly as stored. An entry with no `unit` (from a
  version 1 file) is `lbs`. `weight_lbs`/`weight_kg` are the stored number
  in its own unit, otherwise `fmt_num(weight_in(...))` (2 decimals).
- Rows go oldest date first. Entries on the same date keep their file order,
  not their ID order.
- `--group` is matched like `view --group` (strip, lowercase).
- The file is UTF-8 with a BOM (`utf-8-sig`) and uses `csv.writer` defaults
  (CRLF lines, minimal quoting). It is written to a temp file next to PATH,
  then moved into place with `os.replace`.
- If PATH exists: it prints `File PATH already exists.`, then
  `confirm("Overwrite it? [y/N] ")`. A no prints `Not exported.` and exits 1.
  `--yes` skips the question.
- Input errors (exit 2), checked before anything else, even with `--yes`:
  PATH is the data file (`same_file()`), or PATH is a folder.
- A write failure (`OSError`, e.g. a missing folder or the file is open in
  Excel) prints `error: could not write PATH: ...` and exits 1.
- It prints `Exported 1 entry to PATH` / `Exported N entries to PATH`. An
  empty result still writes the header and says `Exported 0 entries`.
- It only reads the data file and never creates or saves it, so
  `save(path, entries, settings)` is not involved.

## Round 6 commits

- `85e417c`: the spec for R14, written before any code.
- `bcb4379`: R14 code in `lift.py` and `tests/test_round6.py`.
- `06de6df`: README section.
- `4d24245`: decisions 0010 and 0011.

Every commit that touched code passed the full suite when it was made.

## Decisions made in Round 6, and why

The user chose these during clarification:
- **CSV, not `.xlsx`** (decision 0010). It opens in both Excel and Sheets and
  needs only the standard library. A hand-built `.xlsx` (zipped XML) would
  be a lot of fragile code.
- **Weights as logged plus `weight_lbs` and `weight_kg` columns** (0010).
  Nothing that was typed is lost, and a sheet can sort or chart a mixed
  lbs/kg log by real weight.
- **`export [PATH]`, default `workouts.csv`, asks before overwriting, with
  `--yes` to skip.** This follows the CLAUDE.md rule that a command that
  asks must have a skip flag.
- **All entries, with an optional `--group`.** There are no PR or summary
  sheets.

Claude made these without being asked, and reported them to the user:
- **Column names and order** as listed above, including `id` and a header
  row.
- **Row order:** by date, then file order. This matches how `view` orders
  entries within a group.
- **Converted weights rounded to 2 decimals; the logged weight never
  rounded** (1.125 stays 1.125).
- **Names written as stored,** with no `exercise_key()` merging. Export is a
  copy of the log, not a report.
- **UTF-8 with BOM, CRLF, standard quoting** (decision 0011). Without a BOM,
  Excel on Windows shows `é` as `Ã©`.
- **Default path is relative to the current folder,** not next to `lift.py`.
  A missing folder is not created; that is a write error, exit 1.
- **An empty export writes a header-only file,** not an error.
- **The exact messages,** including singular `entry`.
- **Declining to overwrite exits 1,** the same as `delete`.
- **Exporting onto the data file is refused even with `--yes`,** because
  `export workouts.json -y` would destroy the log. The same check refuses a
  folder.
- **Temp file then `os.replace`,** the same pattern as `save()`.
- **`export` takes no `--units`.** It doesn't print weights to the screen,
  and the file always has both units. CLAUDE.md's "a new command that shows
  weights takes the `show` parent parser" rule was judged not to apply.
- **Formula-looking names (`=...`, `+...`) are not escaped.** Escaping would
  change stored names, and the data is the user's own. See "Unresolved".
- **Two decision records, 0010 and 0011,** where one was required.

## Unresolved / possible follow-ups (none were requested)

- **`workouts.csv` is not in `.gitignore`.** Running `python lift.py export`
  in the repo folder creates an untracked file holding the user's real data,
  and a careless `git add .` would commit it. Adding `*.csv` or
  `workouts.csv` to `.gitignore` is a one-line fix, but ask the user first.
- **CSV formula injection.** A name starting with `=`, `+`, `-` or `@` is
  run as a formula by Excel or Sheets. The usual fix is to prefix such cells
  with `'`, but that changes the exported name. The data is the user's own,
  so the risk is low.
- **No import.** There is no way to read a CSV back in (e.g. after editing
  it in a sheet).
- **Export has no date range** (`--from`/`--to`) and no `--exercise` filter.
- **No export of reports** (PRs, most improved, weekly summary). A CSV holds
  only one table, so this would mean several files or a different format.
- **Different spellings of one exercise are separate in the sheet.**
  "bench  press" and "Bench Press" stay as typed. A `key` column could group
  them.
- **The temp file is named `.lift-*.tmp`,** the same prefix `save()` uses.
  That is harmless, but a crash could leave one next to the CSV.
- Left over from Rounds 2-5 (see `handoff-round-5.md` for details):
  - There is no command that shows only the R12 logging default.
  - A one-off `--unit` changes the default.
  - There is no undo or edit history.
  - The highest deleted ID can be reused.
  - There is no bulk edit or delete.
  - `load()` ignores `version`.
  - There is no "as logged" display mode.
  - There is no multi-week history.
  - `summary` has no `--group`.
  - There are no exercise aliases.
  - R9 ignores progress in reps alone.
  - There is no `improved --top N`.
  - The shared test helpers are not in `tests/conftest.py`.

## Warnings for the next session

- **`export` with no PATH writes to the current folder.** Tests rely on
  `run()`/`ask()` setting `cwd` to `tmp_path`. Any new helper that runs the
  CLI must do the same, or tests will drop `workouts.csv` into the repo.
- **Tests that run `export` onto an existing file must pass stdin.** Use
  `export(data_file, ..., answer=...)` from `test_round6.py`, or
  `ask(data_file, answer, ...)` from `test_round5.py`.
- **Read exported CSV with `encoding="utf-8-sig", newline=""`.** Plain
  `utf-8` leaves a `﻿` on the first header cell.
- **`same_file()` uses `os.path.samefile` only when both paths exist.**
  Otherwise it compares `normcase(resolve())`. Case-insensitive matching is
  Windows-only; on other systems `WORKOUTS.JSON` is a different file, which
  is correct.
- **`export_rows()` takes `group` but no other filters.** If a later round
  adds filters, keep the date-then-file-order sort. `test_R14_same_date_uses_file_order_not_id`
  pins it.
- **Mutation check, Round 6:** 30 mutants of the export code, all caught,
  run against `tests/test_round6.py` with `-x`.
  - The first pass left 3 uncaught: rounding the logged weight, sorting by
    ID on ties, and skipping temp-file cleanup. A test was added for each.
  - The script lived in the session scratchpad and is probably gone. It
    used the same approach as Round 5: normalize to LF, swap one snippet
    that matches exactly once, write CRLF back, run pytest, restore the
    original bytes, and check the md5.
- **Line endings are unchanged:**
  - `lift.py` and `README.md` are CRLF. Both were edited this round with
    byte-level scripts.
  - Everything else is LF, including the new `tests/test_round6.py`,
    decisions 0010-0011 and this file.
  - Git prints "LF will be replaced by CRLF" warnings on `git add` for LF
    files. They are expected with `core.autocrlf=true` and harmless.
- **Carried over:**
  - `test_R10_defaults_to_current_week` uses the real clock, so it can fail
    across a Sunday-to-Monday midnight.
  - Commit `9f088fc` has R9 tests that fail at that commit, which matters
    for `git bisect`.
  - R12 makes `--unit` sticky within a test's data file.
