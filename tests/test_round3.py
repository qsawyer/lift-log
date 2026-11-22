"""Round 3 tests: weekly summary (R10).

Every test names its requirement. All tests use a temporary data file.
"""

import datetime
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import lift  # noqa: E402
from test_lift import add, data_file, run  # noqa: E402,F401


def lines(out):
    return [l.strip() for l in out.strip().splitlines()]


def entry(exercise="Bench Press", weight=185, reps=8, sets=3, date="2026-11-18",
          group="chest"):
    return lift.make_entry(exercise, group, sets, reps, weight, 7, date)


# ---------- R10: which week ----------

def test_R10_week_runs_monday_to_sunday():
    """R10: any day of a week maps to that week's Monday..Sunday."""
    for day in ["2026-11-16", "2026-11-19", "2026-11-22"]:
        start, end = lift.week_bounds(datetime.date.fromisoformat(day))
        assert (start.isoformat(), end.isoformat()) == ("2026-11-16", "2026-11-22")
    start, _ = lift.week_bounds(datetime.date(2026, 11, 23))
    assert start.isoformat() == "2026-11-23"


def test_R10_only_entries_in_the_week_count():
    """R10: entries the Sunday before and the Monday after are excluded."""
    entries = [entry(date="2026-11-15", weight=300),   # Sunday before
               entry(date="2026-11-16", weight=185),   # Monday
               entry(date="2026-11-22", weight=190),   # Sunday
               entry(date="2026-11-23", weight=400)]   # Monday after
    s = lift.weekly_summary(entries, datetime.date(2026, 11, 18))
    assert s["workouts"] == 2
    assert [(n, e["weight"]) for n, e in s["prs"]] == [("Bench Press", 190)]


def test_R10_week_option_selects_week(data_file):
    """R10: --week DATE summarizes the Mon-Sun week containing DATE."""
    add(data_file, date="2026-11-10", weight="100")
    add(data_file, date="2026-11-18", weight="200")
    r = run(data_file, "summary", "--week", "2026-11-12")
    assert r.returncode == 0, r.stderr
    out = lines(r.stdout)
    assert out[0] == "Week of 2026-11-09 to 2026-11-15"
    assert "Bench Press: 100 lbs x 8 reps (3 sets) on 2026-11-10" in out
    assert not any("200 lbs" in l for l in out)


def test_R10_defaults_to_current_week(data_file):
    """R10: with no --week, the week containing today is summarized."""
    add(data_file, date=None, weight="155")  # date defaults to today
    start, end = lift.week_bounds(datetime.date.today())
    r = run(data_file, "summary")
    assert r.returncode == 0, r.stderr
    out = lines(r.stdout)
    assert out[0] == f"Week of {start} to {end}"
    assert "Workouts: 1" in out
    assert any("155 lbs" in l for l in out)


def test_R10_invalid_week_date_is_rejected(data_file):
    """R10: a bad --week value is an input error (exit 2)."""
    r = run(data_file, "summary", "--week", "2026-13-01")
    assert r.returncode == 2
    assert "error" in r.stderr


# ---------- R10: workout count ----------

def test_R10_workouts_count_distinct_days():
    """R10: several exercises on one day are one workout."""
    entries = [entry("Bench Press", date="2026-11-16"),
               entry("Squat", date="2026-11-16", group="legs"),
               entry("Row", date="2026-11-16", group="back"),
               entry("Bench Press", date="2026-11-18")]
    assert lift.weekly_summary(entries, datetime.date(2026, 11, 16))["workouts"] == 2


def test_R10_workout_count_is_printed(data_file):
    """R10: the CLI prints the number of workouts that week."""
    add(data_file, exercise="Bench Press", date="2026-11-16")
    add(data_file, exercise="Squat", group="legs", date="2026-11-16")
    add(data_file, exercise="Squat", group="legs", date="2026-11-20")
    out = lines(run(data_file, "summary", "--week", "2026-11-16").stdout)
    assert out[1] == "Workouts: 2"


# ---------- R10: PRs for the week ----------

def test_R10_week_pr_is_best_lift_that_week():
    """R10: each exercise's best in the week uses the R8 rule
    (heaviest, then more reps, then earlier date)."""
    entries = [entry(weight=200, reps=5, date="2026-11-16"),
               entry(weight=210, reps=3, date="2026-11-17"),
               entry(weight=210, reps=5, date="2026-11-20"),   # added first
               entry(weight=210, reps=5, date="2026-11-19")]
    (name, best), = lift.weekly_summary(entries, datetime.date(2026, 11, 16))["prs"]
    assert (best["weight"], best["reps"], best["date"]) == (210, 5, "2026-11-19")


def test_R10_week_pr_listed_even_if_not_all_time_record(data_file):
    """R10: a lighter week still lists its best lift (not only all-time PRs)."""
    add(data_file, date="2026-11-09", weight="250")
    add(data_file, date="2026-11-17", weight="205")
    out = lines(run(data_file, "summary", "--week", "2026-11-17").stdout)
    assert "Bench Press: 205 lbs x 8 reps (3 sets) on 2026-11-17" in out


def test_R10_full_output_format(data_file):
    """R10: exact output, exercises alphabetical ignoring case, names matched
    ignoring case and spacing."""
    add(data_file, exercise="squat", group="legs", weight="225", reps="5",
        sets="5", date="2026-11-16")
    add(data_file, exercise="Bench Press", weight="185", date="2026-11-18")
    add(data_file, exercise="SQUAT", group="legs", weight="235", reps="5",
        sets="5", date="2026-11-20")
    add(data_file, exercise="arnold press", group="shoulders", weight="40.5",
        reps="10", date="2026-11-20")
    r = run(data_file, "summary", "--week", "2026-11-22")
    assert r.returncode == 0, r.stderr
    assert r.stdout.splitlines() == [
        "Week of 2026-11-16 to 2026-11-22",
        "Workouts: 3",
        "PRs this week (best lift per exercise):",
        "  arnold press: 40.5 lbs x 10 reps (3 sets) on 2026-11-20",
        "  Bench Press: 185 lbs x 8 reps (3 sets) on 2026-11-18",
        "  SQUAT: 235 lbs x 5 reps (5 sets) on 2026-11-20",
    ]


def test_R10_name_shown_matches_prs_spelling(data_file):
    """R10: the name shown is the latest spelling overall, same as `prs`."""
    add(data_file, exercise="bench press", date="2026-11-17")
    add(data_file, exercise="Bench Press", date="2026-11-25")
    out = lines(run(data_file, "summary", "--week", "2026-11-17").stdout)
    assert any(l.startswith("Bench Press: 185 lbs") for l in out)


# ---------- R10: empty week ----------

def test_R10_empty_week(data_file):
    """R10: a week with nothing logged shows zero workouts."""
    add(data_file, date="2026-11-01")
    r = run(data_file, "summary", "--week", "2026-11-18")
    assert r.returncode == 0, r.stderr
    assert r.stdout.splitlines() == ["Week of 2026-11-16 to 2026-11-22",
                                     "Workouts: 0",
                                     "No lifts logged this week."]


def test_R10_empty_log(data_file):
    """R10: summary works with no data file at all."""
    r = run(data_file, "summary", "--week", "2026-11-18")
    assert r.returncode == 0, r.stderr
    assert lines(r.stdout)[1:] == ["Workouts: 0", "No lifts logged this week."]
    assert not data_file.exists()
