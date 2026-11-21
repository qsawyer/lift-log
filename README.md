# Lift Log

A small command-line workout tracker for people who lift. Notebooks get lost and
phone notes don't always save. Lift Log records each exercise (name, muscle group,
sets, reps, weight in lbs, and difficulty 1–10) and **saves to disk right after
every entry**. You can view your history grouped by muscle group.

Requires Python 3 and nothing else (pytest is only needed to run the tests).

## Usage

```
python lift.py <command> [args]
```

### Log an exercise

```
python lift.py add --exercise "Bench Press" --group chest --sets 3 --reps 8 --weight 185 --difficulty 7
python lift.py add -e Squat -g legs -s 5 -r 5 -w 225.5 -d 9 --date 2026-11-01
```

`--date` is optional and defaults to today. Short flags: `-e -g -s -r -w -d`.

### View saved workouts

```
python lift.py view                 # everything, grouped by muscle group
python lift.py view --group legs    # only one muscle group
python lift.py groups               # list muscle groups you've logged
```

Example output:

```
== chest ==
  2026-11-21  Bench Press: 3 sets x 8 reps @ 185 lbs  (difficulty 7/10)
== legs ==
  2026-11-01  Squat: 5 sets x 5 reps @ 225.5 lbs  (difficulty 9/10)
```

### Personal records and progress

```
python lift.py prs         # heaviest weight ever logged for each exercise
python lift.py improved    # the 5 exercises with the biggest gain in lbs
```

Example output:

```
Personal records:
  Bench Press: 225 lbs x 5 reps (3 sets) on 2026-11-10
  Squat: 235 lbs x 5 reps (5 sets) on 2026-11-15
Most improved exercises:
  1. Squat: +50 lbs (185 lbs on 2026-11-01 -> 235 lbs on 2026-11-15)
```

Improvement is your best weight minus the heaviest weight from your first
session of that exercise. Exercise names are matched ignoring capitalization,
so "bench press" and "Bench Press" count as the same lift.

### Where data is stored

By default data goes to `workouts.json` next to `lift.py`. That file is not
tracked by git. To use a different file, pass `--file PATH` before the command
(`python lift.py --file my.json view`) or set the `LIFT_LOG_FILE` environment variable.

## Running the tests

```
python -m pytest
```
