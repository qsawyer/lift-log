# Handoff — end of Round 4

Written for a fresh session starting Round 5. Read `CLAUDE.md` first (standing
rules; several were added or corrected this round), then `problem.md`
(requirements), `spec.md` (exact behavior; see its "Round 4" section), and
`docs/decisions/` (why things are the way they are). `handoff-round-3.md` and
`handoff-round-2.md` still have useful background on R8-R10.

## Current state

- Requirements R1-R11 are all implemented and tested. Round 4 changed R6
  (weight could only be lbs; now lbs or kg) and added R11 (show weights in
  lbs, kg or both, and switch quickly).
- **113 tests, all passing** (Python 3.13.7 on Windows 11), in about 30-45 s
  because most tests run the CLI as a subprocess.
- Last commit is `ff23fcb`. Nothing has been pushed. This handoff file and
  this round's CLAUDE.md edits are not committed (the user will review them).
- Files:
  - `lift.py` (about 490 lines): the whole program, in sections: storage,
    validation, operations, units (R6, R11), view, personal records (R8),
    most improved (R9), weekly summary (R10), CLI.
  - `tests/test_lift.py`: R1-R7 (its three R6 tests were updated this round).
    `tests/test_round2.py`: R8-R9. `tests/test_round3.py`: R10.
    `tests/test_round4.py`: R6 (changed) and R11, 37 tests.
  - `spec.md`: "Round 2", "Round 3" and "Round 4" sections with exact rules
    and output formats, including file format version 2.
  - `docs/decisions/0001-0007`: Y-statement decision records.
  - `README.md`: user-facing usage, including the units section.

## How to run

```
python lift.py add -e "Bench Press" -g chest -s 3 -r 8 -w 185 -d 7 [--date YYYY-MM-DD]
python lift.py add -e Squat -g legs -s 5 -r 5 -w 100 --unit kg -d 8   # R6
python lift.py view [--group legs] [--units lbs|kg|both]
python lift.py groups
python lift.py prs [--units ...]                          # R8
python lift.py improved [--units ...]                     # R9
python lift.py summary [--week YYYY-MM-DD] [--units ...]  # R10
python lift.py units                 # R11: show the saved display mode
python lift.py units kg|lbs|both     # R11: save a display mode
python lift.py --file other.json view   # or set LIFT_LOG_FILE
python -m pytest
```

`--units` also has the short form `-u`. Units and modes ignore case. Data
defaults to `workouts.json` next to `lift.py`. That file is gitignored and holds
the user's real data, so don't touch it.

## Round 4 commits

- `f40b829`: spec for R6/R11, written before any code.
- `1114645`: R6. Adds `--unit`, the `unit` field, `FILE_VERSION` 2, and
  comparison by mass, plus R6 tests.
- `7ae7d47`: R11. Adds the `units` command, the `--units` override and the
  formatters, plus R11 tests.
- `b264cad`: README and the spec note about `-u`.
- `e274667`: decisions 0006 and 0007.
- `ff23fcb`: the Round 1 R6 tests were updated for lbs-or-kg (docstrings say
  "R6 (changed in round 4)"), and `add()` gained `unit=`. Decision 0006 gained
  a "Requirement change" section that says R6 went from lbs-only to
  lbs-or-kg, why, and what happens to existing data.

Every commit passed the full suite when it was made.

## Decisions made in Round 4, and why

The user chose these during clarification:
- **The unit is picked with `add --unit lbs|kg`, and lbs is the default.** All
  Round 1-3 commands and tests keep working unchanged.
- **Display switching uses both a saved setting and a one-off flag.**
  `units MODE` is remembered, and `--units MODE` on a command applies once.
- **The default display is lbs**, so output for existing data is identical to
  Round 3 until the user picks kg or both.

Made by Claude without being asked, and reported to the user:
- **Weights are stored exactly as typed, with a `unit` field.** They are not
  converted to lbs on save, and both values are not stored. The file is now
  version 2. Old entries are never migrated, and a missing `unit` means lbs.
  See decision 0006.
- **Weights are compared by real mass.** `weight_lbs()` converts using
  1 lb = 0.45359237 kg and rounds to 6 decimal places, so equal masses tie
  (68.0388555 kg vs 150 lbs) instead of producing a "+0 lbs" improvement.
  `best_entry()` and `most_improved()` use it.
- **The display mode is saved in the data file** as
  `"settings": {"units": ...}`, not in a separate file or an env var. It is
  written only after the user runs `units`, and every later save keeps it.
  See decision 0007.
- **Output format:** `both` always shows lbs first, joined by ` / `
  (`220.46 lbs / 100 kg`). Weights show at most 2 decimals with no trailing
  zeros. `view` now uses the same formatter, so a weight typed with 3 or
  more decimals shows rounded (before Round 4, `view` printed the raw number).
- **In R9, each unit's gain is computed in that unit** (90 -> 100 kg shows
  `+10 kg`). Which exercises qualify, and their order, are still decided in lbs.
- **The `Saved:` line after `add` shows the weight as typed**, whatever the
  display mode.
- **An unknown saved mode (from a hand edit) is read as lbs**, not treated as
  an error. A bad mode on the command line is an argparse usage error (exit 2).
- **Messages and naming:** the messages are `Weights are shown in: X` and
  `Weights will now be shown in: X`. There is a `-u` short flag. `fmt_lbs()`
  was renamed to `fmt_num()`, and `load()` is now a wrapper around
  `load_file()`.
- **Decision 0006 was updated in a later commit**, rather than writing a
  new record, when the user asked for the R6 change to be stated explicitly.

## Unresolved / possible follow-ups (none were requested)

- **A kg lifter must type `--unit kg` on every `add`.** There is no saved
  default *logging* unit. The R11 `units` setting controls display only. This
  is the most likely next request, and it would fit as a second key in
  `settings` (decision 0007).
- **There is no "as logged" display mode**, where each weight is shown in the
  unit it was entered in. It was offered during clarification and not chosen.
- **`load()` ignores the file's `version`.** A future version 3 file, or a
  version 2 file read by a Round 3 copy of the program, is read without any
  warning. kg entries would be misread as lbs by an older program.
- **`units` rewrites the whole data file** to change one setting. It is
  atomic (decision 0001), but it is a write the user might not expect.
- **Settings are per data file**, so `--file other.json` has its own mode.
  This is intended, but it is worth knowing.
- Left over from Rounds 2-3:
  - There is no "new all-time PRs this week" view.
  - There is no multi-week history or "last week" shortcut.
  - `summary` has no `--group` filter.
  - There is no alias support (e.g. "OHP" vs "Overhead Press").
  - R9 ignores rep-only progress.
  - `improved` has no `--top N` option.
  - Bodyweight lifts at 0 never show improvement.
  - The shared test helpers are still not in `tests/conftest.py`.

## Warnings for the next session

- **The working copy has mixed line endings, which differs from what the
  Round 3 handoff said.** `lift.py` and `README.md` are CRLF; `spec.md`,
  `CLAUDE.md`, `problem.md`, all tests and all decision records are LF. Check
  a file's bytes first (`python -c "b=open(f,'rb').read(); print(b.count(b'\r\n'))"`).
  This round, edits to `lift.py` went through a byte-level script that
  normalises to LF, applies exact, checked single-match replacements, and
  writes CRLF back.
- **Python heredocs in the Bash tool can break.** A long `python - <<'EOF'`
  containing many quotes failed with "unexpected EOF while looking for
  matching `"'". Writing the script to a file with the Write tool (in the
  scratchpad) and then running it worked reliably.
- **Mutation checks were done with throwaway scripts in the session
  scratchpad, which are not in the repo and are probably gone.** The approach:
  for each (old, new) snippet, swap it in `lift.py`, run one test file with
  `-x`, restore from the original bytes, and check the md5 at the end. Round 4
  ran 43 mutations (14 for R6, 25 for R11, and 4 for the updated Round 1 R6
  tests). All were killed after one test was strengthened: the
  equal-mass-across-units test uses 68.0388555 kg vs 150 lbs, because
  45.359237 kg converts to exactly 100.0 and didn't exercise the rounding.
- **Any new code path that calls `save()` must pass the settings**, or it
  silently resets the user's display mode to lbs.
  `test_R11_add_keeps_saved_units` only covers `add` and `units`.
- **Any new code that compares or prints weights must go through
  `weight_lbs()` / `best_entry()` and `fmt_weight()`.** Using raw
  `e["weight"]` gives wrong answers as soon as kg entries exist, and most of
  the Round 1-3 tests use lbs only, so they would not catch it. Add a
  mixed-unit test for any new weight feature.
- **Changing `best_entry()` or `weight_lbs()` affects R8, R9, R10 and R6
  tests.** Run the full suite.
- **`test_R10_defaults_to_current_week` uses the real clock.** It could fail
  if it runs exactly across midnight from Sunday to Monday.
- **Commit `9f088fc` (Round 2) still has R9 tests that fail at that commit**,
  which matters for `git bisect`.
