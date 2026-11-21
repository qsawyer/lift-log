"""Round 2 tests: personal records (R8) and most-improved exercises (R9).

Every test names its requirement. All tests use a temporary data file.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import lift  # noqa: E402
from test_lift import add, data_file, run  # noqa: E402,F401


def lines(out):
    return [l.strip() for l in out.strip().splitlines()]


# ---------- R8: personal records ----------

def test_R8_prs_with_no_data(data_file):
    """R8: prs on an empty log says nothing is logged."""
    r = run(data_file, "prs")
    assert r.returncode == 0
    assert r.stdout.strip() == "No workouts logged yet."


def test_R8_pr_is_heaviest_weight(data_file):
    """R8: the PR is the heaviest weight logged, whatever the order of entry."""
    add(data_file, exercise="Bench Press", weight="185", reps="8", date="2026-11-01")
    add(data_file, exercise="Bench Press", weight="225", reps="3", date="2026-11-05")
    add(data_file, exercise="Bench Press", weight="205", reps="5", date="2026-11-09")
    r = run(data_file, "prs")
    assert r.returncode == 0, r.stderr
    assert lines(r.stdout) == [
        "Personal records:",
        "Bench Press: 225 lbs x 3 reps (3 sets) on 2026-11-05",
    ]


def test_R8_every_exercise_listed_alphabetically(data_file):
    """R8: all exercises have a PR line, sorted A-Z ignoring case."""
    add(data_file, exercise="squat", group="legs", weight="315")
    add(data_file, exercise="Bench Press", group="chest", weight="225")
    add(data_file, exercise="Deadlift", group="back", weight="405")
    out = lines(run(data_file, "prs").stdout)
    names = [l.split(":")[0] for l in out[1:]]
    assert names == ["Bench Press", "Deadlift", "squat"]


def test_R8_tie_on_weight_goes_to_more_reps(data_file):
    """R8: with equal weight, the entry with more reps is the PR."""
    add(data_file, exercise="Row", weight="135", reps="6", date="2026-11-01")
    add(data_file, exercise="Row", weight="135", reps="10", date="2026-11-03")
    add(data_file, exercise="Row", weight="135", reps="8", date="2026-11-05")
    assert "Row: 135 lbs x 10 reps (3 sets) on 2026-11-03" in run(data_file, "prs").stdout


def test_R8_full_tie_goes_to_earliest_date(data_file):
    """R8: same weight and reps -> the first time it was achieved is the PR."""
    add(data_file, exercise="Row", weight="135", reps="8", date="2026-11-07")
    add(data_file, exercise="Row", weight="135", reps="8", date="2026-11-02")
    assert "on 2026-11-02" in run(data_file, "prs").stdout


def test_R8_names_match_ignoring_case_and_spaces(data_file):
    """R8: 'bench  press' and 'Bench Press' are one exercise; latest spelling shown."""
    add(data_file, exercise="bench  press", weight="245", date="2026-11-01")
    add(data_file, exercise="Bench Press", weight="200", date="2026-11-10")
    out = lines(run(data_file, "prs").stdout)
    assert out == ["Personal records:",
                   "Bench Press: 245 lbs x 8 reps (3 sets) on 2026-11-01"]


def test_R8_same_date_spelling_uses_last_added(data_file):
    """R8: on the same date, the spelling added last is the one shown."""
    add(data_file, exercise="ohp", weight="95", date="2026-11-01")
    add(data_file, exercise="OHP", weight="90", date="2026-11-01")
    assert lines(run(data_file, "prs").stdout)[1].startswith("OHP: 95 lbs")


def test_R8_fractional_weight_shown(data_file):
    """R8: fractional pound PRs are shown exactly."""
    add(data_file, exercise="Curl", weight="32.5")
    assert "Curl: 32.5 lbs" in run(data_file, "prs").stdout


def test_R8_personal_records_function():
    """R8: personal_records returns one heaviest entry per exercise."""
    es = [lift.make_entry("Dip", "triceps", 3, 10, 0, 5, "2026-11-01"),
          lift.make_entry("Dip", "triceps", 3, 8, 25, 7, "2026-11-04"),
          lift.make_entry("Curl", "arms", 3, 10, 30, 5, "2026-11-01")]
    prs = lift.personal_records(es)
    assert [(name, e["weight"]) for name, e in prs] == [("Curl", 30), ("Dip", 25)]


# ---------- R9: most-improved exercises ----------

def test_R9_improved_with_no_data(data_file):
    """R9: improved on an empty log says nothing is logged."""
    r = run(data_file, "improved")
    assert r.returncode == 0
    assert r.stdout.strip() == "No workouts logged yet."


def test_R9_improvement_is_best_minus_first_session(data_file):
    """R9: improvement = heaviest ever - heaviest on the first date, in lbs."""
    add(data_file, exercise="Squat", weight="185", date="2026-11-01")
    add(data_file, exercise="Squat", weight="175", date="2026-11-01")
    add(data_file, exercise="Squat", weight="235", date="2026-11-15")
    add(data_file, exercise="Squat", weight="215", date="2026-11-20")
    r = run(data_file, "improved")
    assert r.returncode == 0, r.stderr
    assert lines(r.stdout) == [
        "Most improved exercises:",
        "1. Squat: +50 lbs (185 lbs on 2026-11-01 -> 235 lbs on 2026-11-15)",
    ]


def test_R9_first_session_is_earliest_date_not_first_entered(data_file):
    """R9: the starting weight comes from the earliest date, even if logged later."""
    add(data_file, exercise="Press", weight="135", date="2026-11-10")
    add(data_file, exercise="Press", weight="95", date="2026-11-01")
    assert "+40 lbs (95 lbs on 2026-11-01 -> 135 lbs on 2026-11-10)" in \
        run(data_file, "improved").stdout


def test_R9_ranked_most_improved_first(data_file):
    """R9: exercises are ordered by improvement, largest first."""
    for name, start, end in [("Curl", 30, 40), ("Deadlift", 315, 405),
                             ("Bench", 185, 225)]:
        add(data_file, exercise=name, weight=str(start), date="2026-11-01")
        add(data_file, exercise=name, weight=str(end), date="2026-11-08")
    out = lines(run(data_file, "improved").stdout)
    assert [l.split(":")[0] for l in out[1:]] == ["1. Deadlift", "2. Bench", "3. Curl"]


def test_R9_shows_only_top_five(data_file):
    """R9: at most 5 exercises are shown, the 5 most improved."""
    for i in range(7):  # Lift0 improves by 10, Lift6 by 70
        add(data_file, exercise=f"Lift{i}", weight="100", date="2026-11-01")
        add(data_file, exercise=f"Lift{i}", weight=str(100 + 10 * (i + 1)),
            date="2026-11-08")
    out = lines(run(data_file, "improved").stdout)
    assert len(out) == 6
    assert [l.split(":")[0] for l in out[1:]] == [
        "1. Lift6", "2. Lift5", "3. Lift4", "4. Lift3", "5. Lift2"]


def test_R9_ties_broken_alphabetically(data_file):
    """R9: equal improvement is ordered by exercise name A-Z."""
    for name in ["Zercher", "apple pick", "Mid"]:
        add(data_file, exercise=name, weight="100", date="2026-11-01")
        add(data_file, exercise=name, weight="120", date="2026-11-02")
    out = lines(run(data_file, "improved").stdout)
    assert [l.split(":")[0] for l in out[1:]] == ["1. apple pick", "2. Mid", "3. Zercher"]


def test_R9_excludes_no_improvement(data_file):
    """R9: single-date and never-heavier exercises are not listed."""
    add(data_file, exercise="Once", weight="100", date="2026-11-01")
    add(data_file, exercise="Flat", weight="100", date="2026-11-01")
    add(data_file, exercise="Flat", weight="90", date="2026-11-05")
    r = run(data_file, "improved")
    assert r.stdout.strip() == "No improvement recorded yet."
    add(data_file, exercise="Better", weight="50", date="2026-11-01")
    add(data_file, exercise="Better", weight="55", date="2026-11-05")
    out = lines(run(data_file, "improved").stdout)
    assert out[1:] == ["1. Better: +5 lbs (50 lbs on 2026-11-01 -> 55 lbs on 2026-11-05)"]


def test_R9_names_match_ignoring_case(data_file):
    """R9: different capitalisations count as one exercise."""
    add(data_file, exercise="lat pulldown", weight="100", date="2026-11-01")
    add(data_file, exercise="Lat Pulldown", weight="130", date="2026-11-09")
    out = lines(run(data_file, "improved").stdout)
    assert out[1:] == ["1. Lat Pulldown: +30 lbs (100 lbs on 2026-11-01 -> "
                       "130 lbs on 2026-11-09)"]


def test_R9_fractional_improvement_formatted(data_file):
    """R9: fractional gains print cleanly, without float noise."""
    add(data_file, exercise="Raise", weight="10.1", date="2026-11-01")
    add(data_file, exercise="Raise", weight="12.3", date="2026-11-02")
    assert "+2.2 lbs (10.1 lbs" in run(data_file, "improved").stdout


def test_R9_most_improved_function():
    """R9: most_improved returns (name, gain, start, best) for the top 5."""
    es = [lift.make_entry("A", "x", 1, 1, 10, 1, "2026-01-01"),
          lift.make_entry("A", "x", 1, 1, 25, 1, "2026-01-02"),
          lift.make_entry("B", "x", 1, 1, 10, 1, "2026-01-01")]
    result = lift.most_improved(es)
    assert len(result) == 1
    name, gain, start, best = result[0]
    assert (name, gain, start["weight"], best["weight"]) == ("A", 15, 10, 25)
