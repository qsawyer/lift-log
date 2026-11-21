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
| `weight`     | number | >= 0, pounds                           |
| `difficulty` | int    | 1–10 inclusive                         |
| `date`       | string | ISO date (`YYYY-MM-DD`), defaults to today |

The file holds `{"version": 1, "entries": [ ... ]}`.

## Commands

- `add --exercise NAME --group GROUP --sets N --reps N --weight LBS --difficulty 1-10 [--date YYYY-MM-DD]`
- `view [--group GROUP]`
- `groups` — list muscle groups that have entries
- `prs` — show the personal record for every exercise (R8)
- `improved` — show the 5 most-improved exercises (R9)

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
- **R6 – weight in lbs.** `add` requires `--weight` (pounds, non-negative,
  decimals allowed, e.g. 2.5 plates). `view` shows it with a `lbs` suffix.
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
