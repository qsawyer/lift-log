"""Tests for lift.py. Every test names the requirement it checks (R1-R7).

All tests use a temporary data file via pytest's tmp_path; none touch the
real workouts.json.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import lift  # noqa: E402

LIFT = str(ROOT / "lift.py")


@pytest.fixture
def data_file(tmp_path):
    return tmp_path / "workouts.json"


def run(data_file, *args):
    """Run the CLI as a separate process, the way a user would."""
    env = dict(os.environ, LIFT_LOG_FILE=str(data_file))
    return subprocess.run([sys.executable, LIFT, *args], capture_output=True,
                          text=True, env=env, cwd=str(data_file.parent))


def add(data_file, exercise="Bench Press", group="chest", sets="3", reps="8",
        weight="185", difficulty="7", date="2026-11-01", unit=None):
    args = ["add", "--exercise", exercise, "--group", group, "--sets", sets,
            "--reps", reps, "--weight", weight, "--difficulty", difficulty]
    if date is not None:
        args += ["--date", date]
    if unit is not None:  # R6 (changed in round 4): omit to log lbs
        args += ["--unit", unit]
    return run(data_file, *args)


def saved(data_file):
    return json.loads(data_file.read_text(encoding="utf-8"))["entries"]


# ---------- R1: sets and reps ----------

def test_R1_sets_and_reps_are_saved_and_shown(data_file):
    """R1: sets and reps entered are stored and displayed."""
    r = add(data_file, sets="4", reps="12")
    assert r.returncode == 0, r.stderr
    e = saved(data_file)[0]
    assert e["sets"] == 4 and e["reps"] == 12
    assert "4 sets x 12 reps" in run(data_file, "view").stdout


@pytest.mark.parametrize("field,value", [("sets", "0"), ("reps", "0"),
                                         ("sets", "-1"), ("reps", "abc"),
                                         ("sets", "2.5")])
def test_R1_rejects_invalid_sets_or_reps(data_file, field, value):
    """R1: sets/reps must be positive whole numbers; bad input saves nothing."""
    r = add(data_file, **{field: value})
    assert r.returncode == 2
    assert field in r.stderr
    assert not data_file.exists()


def test_R1_sets_and_reps_are_required(data_file):
    """R1: add without --sets or --reps fails."""
    r = run(data_file, "add", "-e", "Curl", "-g", "arms", "-r", "10",
            "-w", "30", "-d", "5")
    assert r.returncode != 0
    assert not data_file.exists()


# ---------- R2: sort by muscle group ----------

def test_R2_view_groups_entries_alphabetically_by_muscle_group(data_file):
    """R2: view lists groups alphabetically with each entry under its group."""
    add(data_file, exercise="Squat", group="legs")
    add(data_file, exercise="Row", group="back")
    add(data_file, exercise="Bench", group="chest")
    add(data_file, exercise="Deadlift", group="back")
    out = run(data_file, "view").stdout
    i_back, i_chest, i_legs = (out.index("== back =="), out.index("== chest =="),
                               out.index("== legs =="))
    assert i_back < i_chest < i_legs
    # both back exercises appear between the back and chest headings
    back_section = out[i_back:i_chest]
    assert "Row" in back_section and "Deadlift" in back_section
    assert "Squat" in out[i_legs:]


def test_R2_group_is_case_insensitive(data_file):
    """R2: 'Chest' and 'chest' are the same muscle group."""
    add(data_file, exercise="Bench", group="Chest")
    add(data_file, exercise="Fly", group="chest")
    out = run(data_file, "view").stdout
    assert out.count("== chest ==") == 1
    assert run(data_file, "groups").stdout.split() == ["chest"]


def test_R2_view_filter_by_group(data_file):
    """R2: view --group shows only that muscle group."""
    add(data_file, exercise="Squat", group="legs")
    add(data_file, exercise="Bench", group="chest")
    out = run(data_file, "view", "--group", "LEGS").stdout
    assert "Squat" in out and "Bench" not in out


def test_R2_within_group_sorted_by_date(data_file):
    """R2: inside a group, entries are ordered oldest date first."""
    add(data_file, exercise="Later", group="legs", date="2026-11-10")
    add(data_file, exercise="Earlier", group="legs", date="2026-11-02")
    out = run(data_file, "view").stdout
    assert out.index("Earlier") < out.index("Later")


def test_R2_sort_by_group_function():
    """R2: sort_by_group returns groups in alphabetical order."""
    entries = [lift.make_entry(n, g, 1, 1, 1, 1, "2026-01-01")
               for n, g in [("a", "shoulders"), ("b", "arms"), ("c", "core")]]
    assert list(lift.sort_by_group(entries)) == ["arms", "core", "shoulders"]


def test_R2_group_is_required(data_file):
    """R2: every entry needs a muscle group."""
    r = add(data_file, group="   ")
    assert r.returncode == 2
    assert not data_file.exists()


# ---------- R3: exercise name ----------

def test_R3_exercise_name_is_saved_and_shown(data_file):
    """R3: the exercise name is stored and displayed."""
    add(data_file, exercise="  Romanian Deadlift  ")
    assert saved(data_file)[0]["exercise"] == "Romanian Deadlift"
    assert "Romanian Deadlift" in run(data_file, "view").stdout


def test_R3_blank_exercise_name_rejected(data_file):
    """R3: an empty exercise name is rejected."""
    r = add(data_file, exercise="  ")
    assert r.returncode == 2
    assert "exercise" in r.stderr
    assert not data_file.exists()


# ---------- R4: difficulty 1-10 ----------

@pytest.mark.parametrize("value", ["1", "10"])
def test_R4_difficulty_boundaries_accepted(data_file, value):
    """R4: difficulty 1 and 10 are valid and saved."""
    r = add(data_file, difficulty=value)
    assert r.returncode == 0, r.stderr
    assert saved(data_file)[0]["difficulty"] == int(value)
    assert f"difficulty {value}/10" in run(data_file, "view").stdout


@pytest.mark.parametrize("value", ["0", "11", "-3", "hard", "7.5"])
def test_R4_difficulty_out_of_range_rejected(data_file, value):
    """R4: difficulty outside 1-10 or non-integer is rejected and not saved."""
    r = add(data_file, difficulty=value)
    assert r.returncode == 2
    assert "difficulty" in r.stderr
    assert not data_file.exists()


# ---------- R5: automatic save ----------

def test_R5_each_add_is_saved_immediately(data_file):
    """R5: after each add the file already contains that entry."""
    add(data_file, exercise="One")
    assert [e["exercise"] for e in saved(data_file)] == ["One"]
    add(data_file, exercise="Two")
    assert [e["exercise"] for e in saved(data_file)] == ["One", "Two"]


def test_R5_data_persists_across_separate_runs(data_file):
    """R5: data written by one process is read by a later one."""
    add(data_file, exercise="Persisted Lift")
    out = run(data_file, "view").stdout
    assert "Persisted Lift" in out


def test_R5_invalid_add_leaves_existing_data_untouched(data_file):
    """R5: a rejected add does not change already-saved data."""
    add(data_file, exercise="Keep Me")
    before = data_file.read_bytes()
    add(data_file, difficulty="99")
    assert data_file.read_bytes() == before


def test_R5_failed_write_does_not_corrupt_file(data_file, monkeypatch):
    """R5: if writing fails midway, the previous file is intact (atomic save)."""
    lift.save(data_file, [lift.make_entry("Old", "legs", 1, 1, 1, 1, "2026-01-01")])
    before = data_file.read_bytes()

    def boom(*a, **k):
        raise OSError("disk full")
    monkeypatch.setattr(lift.json, "dump", boom)
    with pytest.raises(OSError):
        lift.add_entry(data_file, lift.make_entry("New", "legs", 1, 1, 1, 1))
    assert data_file.read_bytes() == before
    assert list(data_file.parent.glob(".lift-*.tmp")) == []


def test_R5_file_location_override(tmp_path):
    """R5: --file saves to the given path (so tests never use real data)."""
    target = tmp_path / "sub" / "mine.json"
    r = subprocess.run([sys.executable, LIFT, "--file", str(target), "add",
                        "-e", "Dip", "-g", "triceps", "-s", "3", "-r", "10",
                        "-w", "0", "-d", "6"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert saved(target)[0]["exercise"] == "Dip"


# ---------- R6: weight in lbs or kg (changed in round 4) ----------

def test_R6_weight_saved_in_lbs(data_file):
    """R6 (changed in round 4): weight was lbs-only; now lbs is the default
    unit. Without --unit, the weight is stored as a number with unit "lbs"
    and shown with 'lbs'. Logging in kg is covered here and in
    tests/test_round4.py."""
    add(data_file, weight="225")
    e = saved(data_file)[0]
    assert (e["weight"], e["unit"]) == (225, "lbs")
    assert "@ 225 lbs" in run(data_file, "view").stdout


@pytest.mark.parametrize("unit,weight,shown", [(None, "132.5", "@ 132.5 lbs"),
                                               ("kg", "62.5", "@ 62.5 kg")])
def test_R6_fractional_weight_allowed(data_file, unit, weight, shown):
    """R6 (changed in round 4): fractional weights (e.g. 2.5 lb or 1.25 kg
    plates) are kept exactly, in whichever unit was logged."""
    add(data_file, weight=weight, unit=unit)
    assert saved(data_file)[0]["weight"] == float(weight)
    shown_unit = unit or "lbs"
    assert shown in run(data_file, "view", "--units", shown_unit).stdout


@pytest.mark.parametrize("unit", [None, "kg"])
@pytest.mark.parametrize("value", ["-5", "heavy", "nan", "inf"])
def test_R6_invalid_weight_rejected(data_file, value, unit):
    """R6 (changed in round 4): negative or non-numeric weight is rejected
    and not saved, whether it is logged in lbs or kg."""
    r = add(data_file, weight=value, unit=unit)
    assert r.returncode == 2
    assert "weight" in r.stderr
    assert not data_file.exists()


# ---------- R7: view saved data ----------

def test_R7_view_with_no_data(data_file):
    """R7: viewing before anything is saved gives a clear message."""
    r = run(data_file, "view")
    assert r.returncode == 0
    assert r.stdout.strip() == "No workouts logged yet."


def test_R7_view_shows_every_field_of_saved_entry(data_file):
    """R7: view shows date, exercise, sets, reps, weight and difficulty."""
    add(data_file, exercise="Overhead Press", group="shoulders", sets="5",
        reps="5", weight="95", difficulty="8", date="2026-10-31")
    out = run(data_file, "view").stdout
    assert "== shoulders ==" in out
    assert ("2026-10-31  Overhead Press: 5 sets x 5 reps @ 95 lbs  "
            "(difficulty 8/10)") in out


def test_R7_view_reads_file_written_externally(data_file):
    """R7: view reads whatever is in the file on each run, not cached state."""
    data_file.write_text(json.dumps({"version": 1, "entries": [
        {"exercise": "Hand Added", "group": "core", "sets": 2, "reps": 20,
         "weight": 0, "difficulty": 3, "date": "2026-11-05"}]}), encoding="utf-8")
    assert "Hand Added" in run(data_file, "view").stdout


def test_R7_view_shows_all_entries(data_file):
    """R7: every saved entry is shown, not just the latest."""
    for i in range(5):
        add(data_file, exercise=f"Lift{i}")
    out = run(data_file, "view").stdout
    for i in range(5):
        assert f"Lift{i}" in out


def test_R7_corrupt_file_reports_error(data_file):
    """R7: a corrupt data file gives a clear error rather than a traceback."""
    data_file.write_text("{not json", encoding="utf-8")
    r = run(data_file, "view")
    assert r.returncode == 1
    assert "not valid JSON" in r.stderr
    assert "Traceback" not in r.stderr


def test_add_defaults_date_to_today(data_file):
    """R5/R7: an add without --date records today's date."""
    import datetime
    add(data_file, date=None)
    assert saved(data_file)[0]["date"] == datetime.date.today().isoformat()
