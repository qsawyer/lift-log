# Lift Log

A small command-line workout tracker for people who lift. Notebooks get lost and
phone notes don't always save. Lift Log records each exercise (name, muscle group,
sets, reps, weight in lbs or kg, and difficulty 1–10) and **saves to disk right after
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
python lift.py add -e Deadlift -g back -s 3 -r 5 -w 140 --unit kg -d 8
```

`--date` is optional and defaults to today. `--unit` is `lbs` or `kg`; the
weight is saved exactly as you typed it. Short flags: `-e -g -s -r -w -d`.

The unit you pick is remembered: after one `add ... --unit kg`, later adds
without `--unit` are logged in kg, with no question asked, until you pass
`--unit lbs`. `add` tells you when the default changes
(`Default unit for new entries is now: kg`). Until you first pass `--unit`,
entries are logged in lbs. This is separate from the display setting below.

### View saved workouts

```
python lift.py view                 # everything, grouped by muscle group
python lift.py view --group legs    # only one muscle group
python lift.py groups               # list muscle groups you've logged
```

Example output:

```
== chest ==
  #1  2026-11-21  Bench Press: 3 sets x 8 reps @ 185 lbs  (difficulty 7/10)
== legs ==
  #2  2026-11-01  Squat: 5 sets x 5 reps @ 225.5 lbs  (difficulty 9/10)
```

`#1`, `#2` are entry IDs, used by `edit` and `delete`. An entry's ID never
changes, even when other entries are deleted.

### Fix or remove an entry

```
python lift.py edit 2 --reps 6            # change only the reps of entry #2
python lift.py edit 2 -w 230 -d 8         # any of add's options can be changed
python lift.py delete 2                   # shows the entry and asks [y/N]
python lift.py delete 2 --yes             # delete without asking
```

`edit` prints the entry before and after (`Was:` / `Now:`). Changing
`--weight` keeps the entry's unit; changing `--unit` alone only relabels the
number (100 lbs becomes 100 kg), it does not convert it. `delete` only deletes
if you answer `y` or `yes`; anything else leaves the entry alone.

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

### Weekly summary

```
python lift.py summary                     # this week (Monday to Sunday)
python lift.py summary --week 2026-11-12   # the week containing that date
```

Example output:

```
Week of 2026-11-16 to 2026-11-22
Workouts: 2
PRs this week (best lift per exercise):
  Bench Press: 225 lbs x 5 reps (3 sets) on 2026-11-18
  Squat: 235 lbs x 5 reps (5 sets) on 2026-11-20
```

"Workouts" counts the days you trained, so a day with three exercises is one
workout. "PRs this week" is your heaviest set of each exercise you did that
week, even if you lifted more in an earlier week (use `prs` for all-time records).

### Showing weights in lbs, kg, or both

```
python lift.py units          # see the current setting (lbs until you change it)
python lift.py units kg       # from now on, show every weight in kg
python lift.py units both     # show "225 lbs / 102.06 kg"
python lift.py units lbs      # back to lbs
python lift.py prs --units kg # just this once, without changing the setting
```

`--units` (or `-u`) works on `view`, `prs`, `improved` and `summary`. The
setting is saved in your data file and never changes the weights you logged.
Converted weights are rounded to two decimals (1 lb = 0.45359237 kg).

You can mix units: a lift logged in kg and one logged in lbs are compared by
their real weight, so 100 kg (220.46 lbs) counts as heavier than 220 lbs for
`prs`, `improved` and `summary`.

### Export to a spreadsheet

```
python lift.py export                     # writes workouts.csv in this folder
python lift.py export lifts-nov.csv       # or any file name you like
python lift.py export --group legs        # only one muscle group
python lift.py export --yes               # replace an existing file without asking
```

This writes a CSV file you can open in Excel (double-click it) or bring into
Google Sheets (File > Import > Upload). There is one row per entry, oldest
first:

```
id,date,exercise,group,sets,reps,weight,unit,weight_lbs,weight_kg,difficulty
1,2026-11-18,Bench Press,chest,3,8,185,lbs,185,83.91,7
2,2026-11-20,Squat,legs,5,5,100,kg,220.46,100,8
```

`weight` and `unit` are exactly what you logged. `weight_lbs` and `weight_kg`
give every entry in both units, so you can sort or chart lifts logged in
different units together. If the file already exists, `export` asks before
replacing it. It never changes your data file. Close the CSV in Excel
before exporting again, or the export can't write it.

### Where data is stored

By default data goes to `workouts.json` next to `lift.py`. That file is not
tracked by git. To use a different file, pass `--file PATH` before the command
(`python lift.py --file my.json view`) or set the `LIFT_LOG_FILE` environment variable.

## Running the tests

```
python -m pytest
```
