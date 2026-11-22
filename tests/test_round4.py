"""Round 4 tests: weight in lbs or kg (R6, changed) and display units (R11).

Every test names its requirement. All tests use a temporary data file.
"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import lift  # noqa: E402
from test_lift import add, data_file, run  # noqa: E402,F401


def log(data_file, exercise="Squat", weight="100", unit=None, reps="5",
        date="2026-11-18", group="legs"):
    """Add one entry, passing --unit only when given."""
    args = ["add", "-e", exercise, "-g", group, "-s", "5", "-r", reps,
            "-w", weight, "-d", "8", "--date", date]
    if unit is not None:
        args += ["--unit", unit]
    r = run(data_file, *args)
    assert r.returncode == 0, r.stderr
    return r


def file_json(data_file):
    return json.loads(data_file.read_text(encoding="utf-8"))


def lines(out):
    return [l.strip() for l in out.strip().splitlines()]


# ---------- R6 (changed): log weight in lbs or kg ----------

def test_R6_kg_weight_saved_as_entered(data_file):
    """R6: --unit kg stores the number typed and the unit, unconverted."""
    log(data_file, weight="102.5", unit="kg")
    e = file_json(data_file)["entries"][0]
    assert (e["weight"], e["unit"]) == (102.5, "kg")


def test_R6_unit_defaults_to_lbs(data_file):
    """R6: leaving out --unit logs lbs, as in earlier rounds."""
    log(data_file, weight="225")
    e = file_json(data_file)["entries"][0]
    assert (e["weight"], e["unit"]) == (225, "lbs")


def test_R6_unit_is_case_insensitive(data_file):
    """R6: --unit KG is accepted and stored as kg."""
    log(data_file, unit="KG")
    assert file_json(data_file)["entries"][0]["unit"] == "kg"


@pytest.mark.parametrize("unit", ["stone", "lb", ""])
def test_R6_invalid_unit_rejected(data_file, unit):
    """R6: only lbs and kg are accepted; nothing is saved otherwise."""
    r = run(data_file, "add", "-e", "Squat", "-g", "legs", "-s", "5", "-r", "5",
            "-w", "100", "-d", "8", "--unit", unit)
    assert r.returncode == 2
    assert "unit" in r.stderr
    assert not data_file.exists()


def test_R6_make_entry_rejects_bad_unit():
    """R6: make_entry validates the unit for any caller, not just the CLI."""
    with pytest.raises(lift.InputError):
        lift.make_entry("Squat", "legs", 5, 5, 100, 8, "2026-11-18", unit="g")


def test_R6_saved_message_shows_weight_as_entered(data_file):
    """R6: the add confirmation echoes the weight in the unit typed."""
    r = log(data_file, weight="100", unit="kg")
    assert "@ 100 kg" in r.stdout
    assert "lbs" not in r.stdout


def test_R6_kg_entry_shown_in_lbs_by_default(data_file):
    """R6/R11: with no display setting, a kg entry is converted to lbs."""
    log(data_file, weight="100", unit="kg")
    assert "@ 220.46 lbs" in run(data_file, "view").stdout


def test_R6_file_version_is_bumped(data_file):
    """R6: files are written as version 2, since entries now carry a unit."""
    log(data_file)
    assert lift.FILE_VERSION == 2
    assert file_json(data_file)["version"] == 2


def test_R6_version1_file_is_read_as_lbs_and_kept(data_file):
    """R6: an old file (no unit fields) reads as lbs; adding to it keeps the
    old entries exactly as they were."""
    old = {"exercise": "Bench Press", "group": "chest", "sets": 3, "reps": 5,
           "weight": 200, "difficulty": 7, "date": "2026-11-01"}
    data_file.write_text(json.dumps({"version": 1, "entries": [old]}),
                         encoding="utf-8")
    assert "@ 200 lbs" in run(data_file, "view").stdout
    assert "Bench Press: 200 lbs x 5 reps" in run(data_file, "prs").stdout
    log(data_file, exercise="Bench Press", weight="100", unit="kg",
        group="chest")
    data = file_json(data_file)
    assert data["version"] == 2
    assert data["entries"][0] == old


def test_R6_pr_compares_lbs_and_kg_by_mass(data_file):
    """R6/R8: 100 kg (220.46 lbs) beats 220 lbs even though 100 < 220."""
    log(data_file, weight="220", date="2026-11-01")
    log(data_file, weight="100", unit="kg", date="2026-11-02")
    log(data_file, weight="99", unit="kg", date="2026-11-03")
    assert "Squat: 220.46 lbs x 5 reps (5 sets) on 2026-11-02" in \
        run(data_file, "prs").stdout


def test_R6_best_entry_uses_mass_not_raw_number():
    """R6: best_entry picks the heavier mass across units."""
    lbs = lift.make_entry("Squat", "legs", 5, 5, 150, 8, "2026-11-01")
    kg = lift.make_entry("Squat", "legs", 5, 5, 70, 8, "2026-11-02", unit="kg")
    assert lift.best_entry([lbs, kg]) is kg  # 70 kg = 154.32 lbs


def test_R6_improvement_across_units(data_file):
    """R6/R9: 100 lbs then 50 kg (110.23 lbs) is a +10.23 lbs improvement."""
    log(data_file, weight="100", date="2026-11-01")
    log(data_file, weight="50", unit="kg", date="2026-11-08")
    assert lines(run(data_file, "improved").stdout)[1] == (
        "1. Squat: +10.23 lbs (100 lbs on 2026-11-01 -> "
        "110.23 lbs on 2026-11-08)")


def test_R6_first_session_start_uses_mass(data_file):
    """R6/R9: the first session's heaviest set is chosen by mass, too."""
    log(data_file, weight="60", unit="kg", date="2026-11-01")   # 132.28 lbs
    log(data_file, weight="100", date="2026-11-01")
    log(data_file, weight="150", date="2026-11-08")
    assert "+17.72 lbs (132.28 lbs on 2026-11-01" in \
        run(data_file, "improved").stdout


def test_R6_same_mass_in_other_unit_is_not_improvement(data_file):
    """R6/R9: 68.0388555 kg then 150 lbs is the same mass, so no gain.

    Without rounding, float conversion gives 149.99999999999997 lbs, which
    would wrongly count as a tiny improvement.
    """
    log(data_file, weight="68.0388555", unit="kg", date="2026-11-01")
    log(data_file, weight="150", date="2026-11-08")
    assert run(data_file, "improved").stdout.strip() == \
        "No improvement recorded yet."


def test_R6_weekly_pr_compares_by_mass(data_file):
    """R6/R10: the week's best lift is chosen by mass across units."""
    log(data_file, weight="225", date="2026-11-17")
    log(data_file, weight="105", unit="kg", date="2026-11-18")  # 231.49 lbs
    out = run(data_file, "summary", "--week", "2026-11-18").stdout
    assert "Squat: 231.49 lbs x 5 reps (5 sets) on 2026-11-18" in out
