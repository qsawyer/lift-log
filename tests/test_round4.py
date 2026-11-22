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
    """R6: files are written as version 2 or later, since entries now carry
    a unit. (Changed in round 5: R13 made it version 3.)"""
    log(data_file)
    assert lift.FILE_VERSION >= 2
    assert file_json(data_file)["version"] == lift.FILE_VERSION


def test_R6_version1_file_is_read_as_lbs_and_kept(data_file):
    """R6: an old file (no unit fields) reads as lbs; adding to it keeps the
    old entries as they were. (Changed in round 5: each also gains an R13
    "id", and nothing else changes.)"""
    old = {"exercise": "Bench Press", "group": "chest", "sets": 3, "reps": 5,
           "weight": 200, "difficulty": 7, "date": "2026-11-01"}
    data_file.write_text(json.dumps({"version": 1, "entries": [old]}),
                         encoding="utf-8")
    assert "@ 200 lbs" in run(data_file, "view").stdout
    assert "Bench Press: 200 lbs x 5 reps" in run(data_file, "prs").stdout
    log(data_file, exercise="Bench Press", weight="100", unit="kg",
        group="chest")
    data = file_json(data_file)
    assert data["version"] == lift.FILE_VERSION
    assert data["entries"][0] == {"id": 1, **old}


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
    """R6/R9: the first session's heaviest set is chosen by mass, too.
    (Round 5: lbs is now passed explicitly, since R12 keeps the last unit.)"""
    log(data_file, weight="60", unit="kg", date="2026-11-01")   # 132.28 lbs
    log(data_file, weight="100", unit="lbs", date="2026-11-01")
    log(data_file, weight="150", unit="lbs", date="2026-11-08")
    assert "+17.72 lbs (132.28 lbs on 2026-11-01" in \
        run(data_file, "improved").stdout


def test_R6_same_mass_in_other_unit_is_not_improvement(data_file):
    """R6/R9: 68.0388555 kg then 150 lbs is the same mass, so no gain.

    Without rounding, float conversion gives 149.99999999999997 lbs, which
    would wrongly count as a tiny improvement. (Round 5: lbs is now passed
    explicitly, since R12 keeps the last unit.)
    """
    log(data_file, weight="68.0388555", unit="kg", date="2026-11-01")
    log(data_file, weight="150", unit="lbs", date="2026-11-08")
    assert run(data_file, "improved").stdout.strip() == \
        "No improvement recorded yet."


def test_R6_weekly_pr_compares_by_mass(data_file):
    """R6/R10: the week's best lift is chosen by mass across units."""
    log(data_file, weight="225", date="2026-11-17")
    log(data_file, weight="105", unit="kg", date="2026-11-18")  # 231.49 lbs
    out = run(data_file, "summary", "--week", "2026-11-18").stdout
    assert "Squat: 231.49 lbs x 5 reps (5 sets) on 2026-11-18" in out


# ---------- R11: display weights in lbs, kg or both, and switch quickly ----------

def mixed_log(data_file):
    """One lbs entry and one kg entry, both legs, same week."""
    log(data_file, exercise="Deadlift", weight="225", date="2026-11-17")
    log(data_file, exercise="Squat", weight="100", unit="kg", date="2026-11-18")


def test_R11_default_display_is_lbs(data_file):
    """R11: with nothing chosen, weights show in lbs and `units` says so."""
    mixed_log(data_file)
    out = run(data_file, "view").stdout
    assert "Deadlift: 5 sets x 5 reps @ 225 lbs  (difficulty 8/10)" in out
    assert "Squat: 5 sets x 5 reps @ 220.46 lbs  (difficulty 8/10)" in out
    assert run(data_file, "units").stdout.strip() == "Weights are shown in: lbs"


def test_R11_units_kg_is_saved_and_used(data_file):
    """R11: `units kg` is remembered; later commands show kg. (Round 5: the
    settings may also hold the R12 log_unit, so only "units" is checked.)"""
    mixed_log(data_file)
    r = run(data_file, "units", "kg")
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "Weights will now be shown in: kg"
    assert file_json(data_file)["settings"]["units"] == "kg"
    out = run(data_file, "view").stdout
    assert "Deadlift: 5 sets x 5 reps @ 102.06 kg  (difficulty 8/10)" in out
    assert "Squat: 5 sets x 5 reps @ 100 kg  (difficulty 8/10)" in out
    assert run(data_file, "units").stdout.strip() == "Weights are shown in: kg"


def test_R11_units_both_shows_lbs_then_kg(data_file):
    """R11: `both` shows every weight as 'X lbs / Y kg'."""
    mixed_log(data_file)
    run(data_file, "units", "both")
    out = run(data_file, "view").stdout
    assert "@ 225 lbs / 102.06 kg  (difficulty 8/10)" in out
    assert "@ 220.46 lbs / 100 kg  (difficulty 8/10)" in out


def test_R11_switching_back_to_lbs(data_file):
    """R11: the user can switch again at any time. (Round 5: only "units"
    is checked, as settings may also hold the R12 log_unit.)"""
    mixed_log(data_file)
    run(data_file, "units", "kg")
    run(data_file, "units", "lbs")
    assert "@ 220.46 lbs  (" in run(data_file, "view").stdout
    assert file_json(data_file)["settings"]["units"] == "lbs"


def test_R11_units_mode_is_case_insensitive(data_file):
    """R11: `units BOTH` works like `units both`."""
    assert run(data_file, "units", "BOTH").returncode == 0
    assert file_json(data_file)["settings"]["units"] == "both"


@pytest.mark.parametrize("mode", ["stone", "pounds", ""])
def test_R11_invalid_units_mode_rejected(data_file, mode):
    """R11: an unknown mode is a usage error and nothing is saved."""
    r = run(data_file, "units", mode)
    assert r.returncode == 2
    assert "invalid choice" in r.stderr
    assert not data_file.exists()


def test_R11_setting_units_does_not_change_entries(data_file):
    """R11: switching display mode never rewrites logged weights."""
    mixed_log(data_file)
    before = file_json(data_file)["entries"]
    run(data_file, "units", "kg")
    assert file_json(data_file)["entries"] == before


def test_R11_add_keeps_saved_units(data_file):
    """R11/R5: logging after choosing a mode keeps the mode."""
    run(data_file, "units", "kg")
    log(data_file)
    assert file_json(data_file)["settings"] == {"units": "kg"}
    assert "@ 100 lbs" in log(data_file).stdout  # Saved: shows as entered
    assert "@ 45.36 kg" in run(data_file, "view").stdout


def test_R11_settings_not_written_until_chosen(data_file):
    """R11: a file with no chosen mode has no settings block."""
    log(data_file)
    assert "settings" not in file_json(data_file)


def test_R11_one_off_override_does_not_change_setting(data_file):
    """R11: --units changes one command's output only."""
    mixed_log(data_file)
    run(data_file, "units", "kg")
    before = data_file.read_bytes()
    assert "@ 225 lbs / 102.06 kg" in run(data_file, "view", "--units", "both").stdout
    assert "@ 225 lbs  (" in run(data_file, "view", "-u", "LBS").stdout
    assert data_file.read_bytes() == before
    assert "@ 102.06 kg  (" in run(data_file, "view").stdout


def test_R11_invalid_override_rejected(data_file):
    """R11: --units with an unknown mode is a usage error."""
    mixed_log(data_file)
    r = run(data_file, "view", "--units", "stone")
    assert r.returncode == 2
    assert "invalid choice" in r.stderr


def test_R11_prs_in_each_mode(data_file):
    """R11/R8: prs follows the display mode."""
    mixed_log(data_file)
    def pr_line(*opt):
        return [l for l in lines(run(data_file, "prs", *opt).stdout)
                if l.startswith("Squat")][0]
    assert pr_line() == "Squat: 220.46 lbs x 5 reps (5 sets) on 2026-11-18"
    assert pr_line("--units", "kg") == "Squat: 100 kg x 5 reps (5 sets) on 2026-11-18"
    assert pr_line("--units", "both") == \
        "Squat: 220.46 lbs / 100 kg x 5 reps (5 sets) on 2026-11-18"


def test_R11_improved_in_each_mode(data_file):
    """R11/R9: the gain is shown in each unit, computed in that unit."""
    log(data_file, weight="90", unit="kg", date="2026-11-01")
    log(data_file, weight="100", unit="kg", date="2026-11-21")
    out = lambda *o: lines(run(data_file, "improved", *o).stdout)[1]
    assert out() == ("1. Squat: +22.05 lbs (198.42 lbs on 2026-11-01 -> "
                     "220.46 lbs on 2026-11-21)")
    assert out("--units", "kg") == ("1. Squat: +10 kg (90 kg on 2026-11-01 -> "
                                    "100 kg on 2026-11-21)")
    assert out("--units", "both") == (
        "1. Squat: +22.05 lbs / +10 kg (198.42 lbs / 90 kg on 2026-11-01 -> "
        "220.46 lbs / 100 kg on 2026-11-21)")


def test_R11_improved_kg_gain_from_lbs_entries(data_file):
    """R11/R9: lbs entries shown in kg: 100 -> 150 lbs is +22.68 kg."""
    log(data_file, weight="100", date="2026-11-01")
    log(data_file, weight="150", date="2026-11-08")
    assert lines(run(data_file, "improved", "--units", "kg").stdout)[1] == (
        "1. Squat: +22.68 kg (45.36 kg on 2026-11-01 -> 68.04 kg on 2026-11-08)")


def test_R11_summary_uses_saved_mode(data_file):
    """R11/R10: the weekly summary follows the saved mode and the override."""
    mixed_log(data_file)
    run(data_file, "units", "kg")
    out = lines(run(data_file, "summary", "--week", "2026-11-18").stdout)
    assert "Deadlift: 102.06 kg x 5 reps (5 sets) on 2026-11-17" in out
    assert "Squat: 100 kg x 5 reps (5 sets) on 2026-11-18" in out
    out = lines(run(data_file, "summary", "--week", "2026-11-18",
                    "--units", "both").stdout)
    assert "Squat: 220.46 lbs / 100 kg x 5 reps (5 sets) on 2026-11-18" in out


def test_R11_unknown_saved_mode_falls_back_to_lbs(data_file):
    """R11: a hand-edited, unknown mode is treated as lbs, not a crash."""
    data_file.write_text(json.dumps({"version": 2, "settings": {"units": "stone"},
        "entries": [{"exercise": "Row", "group": "back", "sets": 3, "reps": 8,
                     "weight": 50, "unit": "kg", "difficulty": 6,
                     "date": "2026-11-18"}]}), encoding="utf-8")
    assert "@ 110.23 lbs" in run(data_file, "view").stdout
    assert run(data_file, "units").stdout.strip() == "Weights are shown in: lbs"


def test_R11_save_display_units_validates(data_file):
    """R11: save_display_units refuses an unknown mode for any caller."""
    with pytest.raises(lift.InputError):
        lift.save_display_units(data_file, "stone")
    assert not data_file.exists()


def test_R11_output_is_ascii(data_file):
    """R11: every display mode prints plain ASCII (Windows cp1252 safety)."""
    mixed_log(data_file)
    for mode in ("lbs", "kg", "both"):
        for cmd in (["view"], ["prs"], ["improved"],
                    ["summary", "--week", "2026-11-18"]):
            run(data_file, *cmd, "--units", mode).stdout.encode("ascii")
