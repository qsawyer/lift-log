# Handoff — end of Round 5

Written for a fresh session starting Round 6. Read `CLAUDE.md` first. It has
the standing rules, and several were added this round: entry IDs, `describe()`,
`confirm()`, tests that ask questions, and the two settings. Then read
`problem.md` (requirements), `spec.md` (exact behavior; see its "Round 5"
section) and `docs/decisions/` (why things are the way they are).
`handoff-round-4.md` still has useful background on units (R6, R11).

## Current state

- Requirements R1-R13 are all implemented and tested. Round 5 added two:
  - R12: once a unit is set, it is saved as the default, and the user isn't
    asked again unless they ask.
  - R13: the user can edit or delete an entry.
- **172 tests, all passing** (Python 3.13.7 on Windows 11). They take about
  70 s, because most tests run the CLI as a subprocess.
- The last commit is `2f806cb`. Nothing has been pushed. This handoff file and
  this round's CLAUDE.md edits are not committed (the user will review them).
- Files:
  - `lift.py` (about 645 lines): the whole program. Its sections are storage
    (including `assign_ids`), validation, operations (`add_entry`), edit and
    delete (R13), units (R6, R11, R12), view, personal records (R8), most
    improved (R9), weekly summary (R10), and CLI (including `confirm()`).
  - `tests/test_lift.py`: R1-R7. `tests/test_round2.py`: R8-R9.
    `tests/test_round3.py`: R10. `tests/test_round4.py`: R6 (changed) and
    R11 (six of its tests were adjusted this round; see below).
    `tests/test_round5.py`: R12 and R13, 59 tests (40 test functions, some
    parametrized).
  - `spec.md`: has a "Round 5" section, including file format version 3. Its
    data-model table and command list at the top were also updated.
  - `docs/decisions/0001-0009`: decision records written as Y-statements.
    0008 and 0009 are new this round.
  - `README.md`: user-facing usage. New this round: how the remembered unit
    works, entry IDs in `view`, and a "Fix or remove an entry" section.

## How to run

```
python lift.py add -e "Bench Press" -g chest -s 3 -r 8 -w 185 -d 7 [--date YYYY-MM-DD]
python lift.py add -e Squat -g legs -s 5 -r 5 -w 100 --unit kg -d 8   # kg is now the default (R12)
python lift.py add -e Squat -g legs -s 5 -r 5 -w 105 -d 8             # logged in kg, no question
python lift.py view [--group legs] [--units lbs|kg|both]              # shows #ID per entry
python lift.py edit 3 --reps 6 [-e -g -s -r -w --unit -d --date]      # R13; also "#3"
python lift.py delete 3 [--yes|-y]                                    # R13; asks [y/N]
python lift.py groups
python lift.py prs [--units ...]                          # R8
python lift.py improved [--units ...]                     # R9
python lift.py summary [--week YYYY-MM-DD] [--units ...]  # R10
python lift.py units [lbs|kg|both]                        # R11 display mode
python lift.py --file other.json view   # or set LIFT_LOG_FILE
python -m pytest
```

Data defaults to `workouts.json` next to `lift.py`. That file is gitignored and
holds the user's real data, so don't touch it.

## Round 5 commits

- `e88f467`: the spec for R12 and R13, written before any code.
- `134d47c`: R13. It adds stable entry IDs (`FILE_VERSION` 3), the `edit` and
  `delete` commands, `#N` in `view` and in the `Saved:` line, and the R13
  tests. It also updates two Round 4 tests that pinned version 2 and an
  unchanged old entry.
- `a380b1b`: R12. It adds `settings.log_unit`, the remembered `--unit`, and
  the R12 tests. It also updates four Round 4 tests that assumed a later
  `add` without `--unit` would log lbs.
- `a75bfab`: README.
- `2f806cb`: decisions 0008 (stable IDs) and 0009 (remembered logging unit).

Every commit that touched code passed the full suite when it was made. R13
was committed before R12 by staging an R13-only version of `lift.py` and of
the test file.

## Decisions made in Round 5, and why

The user chose these during clarification:
- **The last `--unit` given to `add` becomes the default** (decision 0009).
  R12 says "once a unit is set it is saved", and this way setting it is part
  of a normal add.
- **With no saved default, `add` logs lbs and never asks.** Nothing in the
  program is interactive except `delete`. All Round 1-4 behavior is
  unchanged until a `--unit` is given.
- **Entries get a stable ID, not a position in `view`** (decision 0008).
  Positions shift after a delete, after a back-dated add, and under
  `view --group`, so `delete 3` run twice could remove two different
  entries.
- **`delete` asks `Delete this entry? [y/N]`.** `--yes`/`-y` skips the
  question.

Claude made these without being asked, and reported them to the user:
- **Where the default is saved:** `settings.log_unit` in the data file, next
  to the R11 `units` key. It is kept separate from the display mode, so
  `units kg` doesn't change logging and `add --unit kg` doesn't change
  display. A display mode of `both` has no single logging unit.
- **`add` prints `Default unit for new entries is now: X`, only when the
  default actually changes.** A one-off `--unit` silently changing every
  later entry would otherwise go unnoticed.
- **Any `--unit` saves the default,** even when it matches the current one.
  So `settings` appears after `add --unit lbs`.
- **`edit --unit` doesn't change the default.**
- **An unknown `log_unit` from a hand edit is read as lbs,** the same rule
  as for an unknown display mode in R11.
- **How IDs are given out:**
  - A new entry gets one more than the highest ID in the file.
  - Entries from version 1-2 files get 1, 2, 3... in file order when the
    file is read. The IDs are written on the next save.
  - Missing, non-integer, boolean, zero or duplicate IDs are renumbered
    after the highest valid one. For duplicates, the first keeps its ID.
  - The highest ID can be given out again after that entry is deleted.
    There is no "next id" counter.
- **Where IDs are shown:** in `view`, in the `Saved:` line (now
  `Saved: #N  date ...`) and in the `edit`/`delete` output. `prs`,
  `improved` and `summary` don't show them.
- **ID format:** IDs are accepted as `7` or `#7`. Anything else, or an ID
  that doesn't exist, is an input error (exit 2), and nothing is written.
  `delete` on a missing data file doesn't create one.
- **What `delete` accepts:**
  - Only `y` or `yes` deletes. Case and surrounding spaces are ignored.
  - Any other answer, or end of input, prints `Not deleted.` and exits with
    **status 1**. That status lets a script tell that nothing was deleted.
  - The entry is shown before the question, with its weight as typed and
    its group.
- **How `edit` works:**
  - It takes `add`'s options, all optional, and at least one is required.
  - Values are checked by `make_entry()`, the same function `add` uses. If
    any value is invalid, nothing is saved.
  - The entry keeps its ID and its position in the file.
  - `--weight` keeps the entry's unit, not the saved default.
  - `--unit` alone relabels the stored number without converting it
    (100 lbs becomes 100 kg).
  - It doesn't ask for confirmation, and it prints `Was:` / `Now:` lines.
  - Editing a version 1 entry (one with no `unit`) adds `"unit": "lbs"` to it.
- **There is no command that shows only the logging default.** Adding a line
  to `units` would have changed output that Round 4 tests check exactly.
- **Six Round 4 tests were changed, not left to fail.** Their docstrings say
  "Round 5" and why.
  - Two tests pinned `version == 2` and an old entry staying byte-identical.
    They now accept `FILE_VERSION` and the added `id`.
  - Two tests now pass `unit="lbs"` explicitly.
  - Two tests now check only `settings["units"]`.
- **Two decision records were written, 0008 and 0009,** where at least one
  was required.

## Unresolved / possible follow-ups (none were requested)

- **No way to show only the logging default.** One option is
  `units --log` or a second line in `units`. The second line would change
  output that `test_R11_*` tests check exactly.
- **A one-off `--unit` changes the default.** A lbs lifter who logs one kg
  dumbbell then logs everything after it in kg until they notice the notice
  line. A `--once` flag, or a rule that `--unit` only sticks when it matches
  the last N entries, would address this. Neither was asked for.
- **No undo for `delete`, and no history of edits.** The entry is gone
  once the user confirms.
- **The highest deleted ID can be reused.** Deleting #7 (the highest) and
  then adding gives a new #7. Persisting a `next_id` would prevent this.
- **`edit` and `delete` are single-entry only.** There is no bulk delete
  (e.g. by date) and no "delete last".
- **`view --group` shows IDs, but there is no way to look up one entry**
  (e.g. `show 7`).
- **`load()` still ignores the file's `version`.** A Round 4 copy of the
  program reading a version 3 file works, because it ignores `id` and
  `log_unit`. A Round 3 copy would misread kg entries as lbs.
- Left over from Rounds 2-4:
  - There is no "as logged" display mode.
  - There is no "new all-time PRs this week" view.
  - There is no multi-week history.
  - `summary` has no `--group` filter.
  - There is no alias support for exercise names.
  - R9 ignores progress in reps alone.
  - `improved` has no `--top N` option.
  - The shared test helpers are still not in `tests/conftest.py`.

## Warnings for the next session

- **Tests that run `delete` without `--yes` must pass stdin.** `run()` in
  `tests/test_lift.py` passes no stdin, so the child process inherits the
  terminal and can hang. Use `ask(data_file, answer, *args)` from
  `tests/test_round5.py`. Pass `""` for end of input.
- **R12 is stateful across adds in one data file.** Any new test that logs
  kg and then calls `add()` or `log()` without `unit=` gets kg. Four Round 4
  tests had to be fixed for this.
- **`format_entry()` adds `  #N` only when the entry has an `id`.** Entries
  built directly with `make_entry()` in unit tests have no ID. That is
  intended, but it means a mutation removing IDs only shows up in CLI tests.
- **`add_entry()` now returns a new dict that includes `id`.** Use the
  return value, not the dict you passed in.
- **`describe()` always shows the weight as entered.** Don't use it for
  output that should follow the R11 display mode. Use `format_entry(e, mode)`
  for that.
- **Line endings are unchanged from Round 4:**
  - `lift.py` and `README.md` are CRLF.
  - The other files are LF. That includes `tests/test_round5.py` and
    decisions 0008-0009, which the Write tool created as LF.
  - Edits to `lift.py` and `README.md` were made with byte-level scripts in
    the scratchpad. Each script normalised to LF, applied exact replacements
    that were checked to match once, and wrote CRLF back.
- **Mutation check, Round 5:** 36 mutants, all caught (7 R12, 29 R13).
  - The script swapped one snippet in `lift.py`, ran `test_round5.py` and
    `test_round4.py` with `-x`, and restored the original bytes. It then
    checked the md5.
  - The script was in the session scratchpad and is probably gone.
  - One equivalent mutant was skipped: `parse_id` accepting 0. It still
    fails with exit 2, because no entry has ID 0.
- **Any new code that saves must call `save(path, entries, settings)`.**
  `test_R12_both_settings_survive_every_save` covers `units`, `add`, `edit`
  and `delete`. Extend it for any new command that saves.
- **`test_R10_defaults_to_current_week` uses the real clock.** It can fail
  if it runs across midnight from Sunday to Monday.
- **Commit `9f088fc` (Round 2) still has R9 tests that fail at that
  commit.** This matters for `git bisect`.
