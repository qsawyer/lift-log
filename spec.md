# Lift Log — Specification

A command-line workout tracker. Run as `python lift.py <command> [args]`.
Data is stored in a JSON file (default `workouts.json` next to `lift.py`;
override with the `LIFT_LOG_FILE` environment variable or the `--file` option).

## Data model

Each logged entry is a JSON object:

| field        | type   | rule                                   |
|--------------|--------|----------------------------------------|
| `exercise`   | string | non-empty, surrounding spaces stripped |
| `group`      | string | non-empty, stored lowercase            |
| `sets`       | int    | >= 1                                   |
| `reps`       | int    | >= 1                                   |
| `weight`     | number | >= 0, in `unit`, as entered            |
| `unit`       | string | `lbs` or `kg` (Round 4; missing = `lbs`) |
| `difficulty` | int    | 1–10 inclusive                         |
| `date`       | string | ISO date (`YYYY-MM-DD`), defaults to today |

The file holds `{"version": 2, "settings": {...}, "entries": [ ... ]}`
(see Round 4). Version 1 files (`{"version": 1, "entries": [...]}`, no
`unit` fields, no `settings`) are still read; their weights are lbs.

## Commands

- `add --exercise NAME --group GROUP --sets N --reps N --weight W [--unit lbs|kg] --difficulty 1-10 [--date YYYY-MM-DD]`
- `view [--group GROUP] [--units lbs|kg|both]`
- `groups` — list muscle groups that have entries
- `prs [--units lbs|kg|both]` — show the personal record for every exercise (R8)
- `improved [--units lbs|kg|both]` — show the 5 most-improved exercises (R9)
- `summary [--week YYYY-MM-DD] [--units lbs|kg|both]` — weekly summary: workouts and PRs for one Mon-Sun week (R10)
- `units [lbs|kg|both]` — show or save how weights are displayed (R11)

Invalid input prints an error to stderr, exits with status 2, and does not change the file.

## How each requirement is met

- **R1 – rep and set numbers.** `add` requires `--sets` and `--reps`, both
  positive integers. They are stored per entry and shown by `view`.
- **R2 – sorts by muscle group.** Every entry requires `--group`. `view` prints
  entries grouped under a heading for each muscle group, groups in alphabetical
  order (case-insensitive, since groups are stored lowercase). Within a group,
  entries are ordered by date then insertion order. `view --group G` shows only
  that group; `groups` lists the groups.
- **R3 – name of exercise.** `add` requires `--exercise`; it is stored and shown.
- **R4 – difficulty 1–10.** `add` requires `--difficulty`; values outside 1–10
  or non-integers are rejected.
- **R5 – automatic save after every input.** Every successful `add` writes the
  whole data file immediately (write to a temp file, then atomically replace),
  so no separate "save" step exists and a crash mid-write cannot corrupt the
  existing file. Every run reads the file fresh.
- **R6 – weight in lbs or kg.** `add` requires `--weight` (non-negative,
  decimals allowed, e.g. 2.5 plates). Changed in Round 4: see below.
- **R7 – view saved data.** `view` reads the file and prints all entries; with
  no data it prints `No workouts logged yet.`

## Round 2

### Exercise identity (used by R8 and R9)

Two entries are the same exercise when their names match after removing
extra spaces and ignoring case: `"bench  press"` and `"Bench Press"` are one
exercise. The muscle group does not matter. Output shows the spelling from the
most recently logged entry (latest date; on the same date, the one added last).
Stored entries are not changed.

Weights in R8/R9 output are printed with at most two decimal places and no
trailing zeros (`185`, `132.5`, `2.25`).

- **R8 – display all personal records.** `prs` prints one line per exercise,
  sorted alphabetically by name (ignoring case):

  ```
  Personal records:
    Bench Press: 225 lbs x 5 reps (3 sets) on 2026-11-10
  ```

  The PR is the entry with the heaviest weight. Ties go to more reps, then the
  earlier date (the first time the record was set). With no data it prints
  `No workouts logged yet.`

- **R9 – display most-improved exercises.** `improved` ranks exercises by
  improvement and prints the top 5:

  ```
  Most improved exercises:
    1. Squat: +50 lbs (185 lbs on 2026-11-01 -> 235 lbs on 2026-11-15)
  ```

  - *Starting weight* = the heaviest weight logged on the exercise's earliest
    date (its first session).
  - *Best weight* = the heaviest weight ever logged (the R8 PR). The date shown
    is the earliest date that weight was reached.
  - *Improvement* = best weight − starting weight, in lbs.
  - Only exercises with an improvement greater than 0 are listed. An exercise
    logged on just one date, or never heavier than its first session, has not
    improved.
  - Order: largest improvement first. Ties are broken by exercise name, A–Z,
    ignoring case. At most 5 are shown.
  - If no exercise qualifies, it prints `No improvement recorded yet.` (or
    `No workouts logged yet.` when the file is empty).

## Round 3

- **R10 – weekly summary.** `summary [--week YYYY-MM-DD]` prints how many
  workouts the user did in one week and their PRs for that week:

  ```
  Week of 2026-11-16 to 2026-11-22
  Workouts: 2
  PRs this week (best lift per exercise):
    Bench Press: 225 lbs x 5 reps (3 sets) on 2026-11-18
    Squat: 235 lbs x 5 reps (5 sets) on 2026-11-20
  ```

  - *Week* = a calendar week, Monday through Sunday. By default it is the
    week containing today. `--week DATE` selects the week containing DATE
    (any day of that week). An invalid date is an input error (exit 2).
  - *Workouts* = the number of distinct dates in the week with at least one
    logged entry. Several exercises on one day are one workout.
  - *PRs this week* = for every exercise logged that week, its best entry
    within the week, using the R8 rule (heaviest weight; ties go to more reps,
    then the earlier date). Earlier weeks are not considered, so a lift can be
    listed even if it is not an all-time record. Exercises are matched with the
    Round 2 exercise identity and listed alphabetically, ignoring case. The name
    shown is the same spelling `prs` shows (the most recently logged one).
  - A week with no entries (including an empty log) prints the heading, then
    `Workouts: 0` and `No lifts logged this week.`

## Round 4

### R6 (changed) – track weight in lbs or kg

- `add` takes `--unit lbs` or `--unit kg` (case-insensitive). Leaving it out
  means `lbs`, so every Round 1-3 command works unchanged. Any other unit is
  an input error (exit 2) and nothing is saved.
- The weight is stored exactly as entered, with its unit:
  `{"weight": 100, "unit": "kg", ...}`. It is never converted when saved.
  Entries without a `unit` field (from older files) are lbs.
- The `Saved:` confirmation after `add` shows the weight as entered
  (`@ 100 kg`), whatever the display setting is.
- Comparisons use the real mass, so lbs and kg entries of one exercise are
  compared fairly: for R8 (`prs`), R9 (`improved`) and R10 (`summary`), each
  weight is converted to lbs (1 lb = 0.45359237 kg exactly, rounded to 6
  decimal places) before choosing the heaviest. The tie-break rules are
  unchanged. 100 kg (220.46 lbs) beats 220 lbs.

### R11 – display weights in lbs, kg, or both

- There are three display modes: `lbs`, `kg`, `both`. The default is `lbs`,
  so output looks the same as in Round 3 until the user picks something else.
- `units` prints the current mode: `Weights are shown in: lbs`.
- `units kg` (or `lbs`, `both`; case-insensitive) saves the mode in the data
  file and prints `Weights will now be shown in: kg`. Every later `view`,
  `prs`, `improved` and `summary` uses it. Workout entries are not changed.
- `--units MODE` on `view`, `prs`, `improved` or `summary` uses MODE for that
  one command and does not change the saved mode.
- An invalid mode is rejected with a usage error (exit 2) and nothing is saved.
  An unknown mode found in a hand-edited file is treated as `lbs`.
- Formatting: a weight in its own unit is shown as stored; a converted weight
  is computed from the stored value. Both are printed with at most two decimal
  places and no trailing zeros (`100 kg`, `220.46 lbs`). `both` always shows
  lbs first, joined by ` / `:

  ```
  view:      2026-11-21  Squat: 5 sets x 5 reps @ 220.46 lbs / 100 kg  (difficulty 8/10)
  prs:       Squat: 220.46 lbs / 100 kg x 5 reps (5 sets) on 2026-11-21
  improved:  1. Squat: +22.05 lbs / +10 kg (198.42 lbs / 90 kg on 2026-11-01 -> 220.46 lbs / 100 kg on 2026-11-21)
  summary:   Squat: 220.46 lbs / 100 kg x 5 reps (5 sets) on 2026-11-21
  ```

  The R9 gain shown in a unit is (best − start) computed in that unit.
  Which exercises qualify and their order are decided in lbs, as before.

### Data file, version 2

```
{"version": 2, "settings": {"units": "kg"}, "entries": [ ... ]}
```

`settings` is written only once a mode has been saved with `units`. Every
save writes `"version": 2` and keeps the saved settings. Entries from a
version 1 file are kept exactly as they are (no `unit` field is added).
