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
