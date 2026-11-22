"""Round 5 tests: saved default logging unit (R12) and edit/delete (R13).

Every test names its requirement. All tests use a temporary data file.
Commands that might ask a question are run with explicit stdin (`ask`), so
a test can never hang waiting on the terminal.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import lift  # noqa: E402
from test_lift import LIFT, add, data_file, run  # noqa: E402,F401


def ask(data_file, answer, *args):
    """Run the CLI with `answer` as its whole stdin ("" means end of input)."""
    env = dict(os.environ, LIFT_LOG_FILE=str(data_file))
    return subprocess.run([sys.executable, LIFT, *args], input=answer,
                          capture_output=True, text=True, env=env,
                          cwd=str(data_file.parent))


def log(data_file, exercise="Squat", weight="100", unit=None, reps="5",
        date="2026-11-18", group="legs", answer=""):
    """Add one entry with empty stdin, passing --unit only when given."""
    args = ["add", "-e", exercise, "-g", group, "-s", "5", "-r", reps,
            "-w", weight, "-d", "8", "--date", date]
    if unit is not None:
        args += ["--unit", unit]
    r = ask(data_file, answer, *args)
    assert r.returncode == 0, r.stderr
    return r


def file_json(data_file):
    return json.loads(data_file.read_text(encoding="utf-8"))


def entries(data_file):
    return file_json(data_file)["entries"]


def write_file(data_file, payload):
    data_file.write_text(json.dumps(payload), encoding="utf-8")


def lines(out):
    return [l.strip() for l in out.strip().splitlines()]


# ---------- R12: saved default logging unit ----------

def test_R12_unit_given_becomes_default(data_file):
    """R12: after `add --unit kg`, later adds without --unit log kg."""
    log(data_file, unit="kg")
    log(data_file, weight="105")
    assert [e["unit"] for e in entries(data_file)] == ["kg", "kg"]
    assert file_json(data_file)["settings"] == {"log_unit": "kg"}
    assert "@ 105 kg" in run(data_file, "view", "-u", "kg").stdout


def test_R12_default_is_used_without_asking(data_file):
    """R12: with a saved default, add asks no question, even with no input."""
    log(data_file, unit="kg")
    r = log(data_file, answer="")
    assert "?" not in r.stdout + r.stderr
    assert "@ 100 kg" in r.stdout


def test_R12_no_default_logs_lbs_without_asking(data_file):
    """R12: before any unit is saved, add logs lbs and asks nothing."""
    r = log(data_file, answer="")
    assert "?" not in r.stdout + r.stderr
    assert entries(data_file)[0]["unit"] == "lbs"
    assert "settings" not in file_json(data_file)


def test_R12_user_can_change_default(data_file):
    """R12: passing --unit again overrides and becomes the new default."""
    log(data_file, unit="kg")
    log(data_file, unit="lbs")
    log(data_file)
    assert [e["unit"] for e in entries(data_file)] == ["kg", "lbs", "lbs"]
    assert file_json(data_file)["settings"]["log_unit"] == "lbs"


def test_R12_unit_is_case_insensitive_when_saved(data_file):
    """R12: `--unit KG` saves the default as kg."""
    log(data_file, unit="KG")
    assert file_json(data_file)["settings"]["log_unit"] == "kg"


def test_R12_message_only_when_default_changes(data_file):
    """R12: add says when the default changes, and only then."""
    msg = "Default unit for new entries is now: "
    assert msg + "kg" in log(data_file, unit="kg").stdout
    assert msg not in log(data_file, unit="kg").stdout
    assert msg not in log(data_file).stdout
    assert msg + "lbs" in log(data_file, unit="lbs").stdout


def test_R12_explicit_lbs_with_no_default_has_no_message(data_file):
    """R12: --unit lbs when lbs is already the default changes nothing visible."""
    r = log(data_file, unit="lbs")
    assert "Default unit" not in r.stdout
    assert file_json(data_file)["settings"] == {"log_unit": "lbs"}


def test_R12_invalid_unit_keeps_default_and_saves_nothing(data_file):
    """R12: a bad --unit is rejected and the saved default is unchanged."""
    log(data_file, unit="kg")
    before = data_file.read_bytes()
    r = add(data_file, unit="stone")
    assert r.returncode == 2
    assert data_file.read_bytes() == before


def test_R12_logging_default_is_separate_from_display(data_file):
    """R12/R11: `units kg` does not change the logging unit, and
    `add --unit kg` does not change the display mode."""
    run(data_file, "units", "kg")
    log(data_file)
    assert entries(data_file)[0]["unit"] == "lbs"
    run(data_file, "units", "lbs")
    log(data_file, unit="kg")
    assert run(data_file, "units").stdout.strip() == "Weights are shown in: lbs"


def test_R12_both_settings_survive_every_save(data_file):
    """R12/R11: units, add, edit and delete each keep both settings."""
    run(data_file, "units", "both")
    log(data_file, unit="kg")
    expected = {"units": "both", "log_unit": "kg"}
    assert file_json(data_file)["settings"] == expected
    log(data_file)
    assert file_json(data_file)["settings"] == expected
    assert run(data_file, "edit", "1", "--reps", "3").returncode == 0
    assert file_json(data_file)["settings"] == expected
    assert run(data_file, "delete", "2", "--yes").returncode == 0
    assert file_json(data_file)["settings"] == expected
    run(data_file, "units", "kg")
    assert file_json(data_file)["settings"] == {"units": "kg", "log_unit": "kg"}


def test_R12_unknown_saved_default_falls_back_to_lbs(data_file):
    """R12: a hand-edited, unknown log_unit is read as lbs."""
    write_file(data_file, {"version": 3, "settings": {"log_unit": "stone"},
                           "entries": []})
    log(data_file)
    assert entries(data_file)[0]["unit"] == "lbs"


def test_R12_edit_unit_does_not_change_default(data_file):
    """R12/R13: relabelling one entry with edit --unit leaves the default."""
    log(data_file, unit="kg")
    assert run(data_file, "edit", "1", "--unit", "lbs").returncode == 0
    assert file_json(data_file)["settings"]["log_unit"] == "kg"
    log(data_file)
    assert entries(data_file)[1]["unit"] == "kg"


def test_R12_default_unit_used_in_mixed_comparisons(data_file):
    """R12/R6: entries logged via the saved default compare by mass."""
    log(data_file, weight="220", unit="lbs", date="2026-11-17")
    log(data_file, weight="100", unit="kg", date="2026-11-18")
    log(data_file, weight="99", date="2026-11-19")  # kg, from the default
    assert "Squat: 220.46 lbs x 5 reps (5 sets) on 2026-11-18" in \
        run(data_file, "prs").stdout


# ---------- R13: entry IDs ----------

def test_R13_new_entries_get_increasing_ids(data_file):
    """R13: each new entry gets the next ID."""
    for _ in range(3):
        log(data_file)
    assert [e["id"] for e in entries(data_file)] == [1, 2, 3]


def test_R13_view_and_saved_line_show_id(data_file):
    """R13: the ID is shown on the Saved line and in view."""
    assert "Saved: #1  2026-11-18  Squat:" in log(data_file).stdout
    assert "  #1  2026-11-18  Squat: 5 sets x 5 reps @ 100 lbs  (difficulty 8/10)" \
        in run(data_file, "view").stdout.splitlines()


def test_R13_old_file_entries_get_ids_in_file_order(data_file):
    """R13: entries from a version 2 file are numbered in file order, and
    the numbers are saved without changing anything else."""
    old = [{"exercise": "Squat", "group": "legs", "sets": 5, "reps": 5,
            "weight": 200, "unit": "lbs", "difficulty": 8, "date": "2026-11-02"},
           {"exercise": "Bench", "group": "chest", "sets": 3, "reps": 5,
            "weight": 150, "difficulty": 7, "date": "2026-11-01"}]
    write_file(data_file, {"version": 2, "entries": old})
    out = run(data_file, "view").stdout
    assert "#1  2026-11-02  Squat" in out and "#2  2026-11-01  Bench" in out
    log(data_file)
    saved = entries(data_file)
    assert [e["id"] for e in saved] == [1, 2, 3]
    assert [{k: v for k, v in e.items() if k != "id"} for e in saved[:2]] == old


def test_R13_bad_or_duplicate_ids_are_renumbered(data_file):
    """R13: a missing, non-integer or duplicate id gets a fresh number after
    the highest valid one; valid ids are kept."""
    base = {"exercise": "Curl", "group": "arms", "sets": 3, "reps": 10,
            "weight": 30, "difficulty": 6, "date": "2026-11-01"}
    write_file(data_file, {"version": 3, "entries": [
        dict(base, id=5), dict(base, id=5), dict(base, id="x"),
        dict(base, id=True), dict(base, id=0), dict(base)]})
    log(data_file)
    assert [e["id"] for e in entries(data_file)] == [5, 6, 7, 8, 9, 10, 11]


def test_R13_file_version_is_3(data_file):
    """R13: files are written as version 3, since entries now carry an id."""
    log(data_file)
    assert lift.FILE_VERSION == 3
    assert file_json(data_file)["version"] == 3


# ---------- R13: delete ----------

def test_R13_delete_with_yes(data_file):
    """R13: delete --yes removes the entry without asking."""
    log(data_file, exercise="Keep")
    log(data_file, exercise="Drop")
    r = ask(data_file, "", "delete", "2", "--yes")
    assert r.returncode == 0, r.stderr
    assert "Delete this entry?" not in r.stdout
    assert "Deleted #2." in r.stdout
    assert [e["exercise"] for e in entries(data_file)] == ["Keep"]


def test_R13_delete_short_yes_flag(data_file):
    """R13: -y is the short form of --yes."""
    log(data_file)
    assert ask(data_file, "", "delete", "1", "-y").returncode == 0
    assert entries(data_file) == []


@pytest.mark.parametrize("answer", ["y\n", "Y\n", "yes\n", "  YES  \n"])
def test_R13_delete_after_confirming(data_file, answer):
    """R13: delete asks first, and y/yes (any case) confirms."""
    log(data_file, weight="100", unit="kg")
    r = ask(data_file, answer, "delete", "1")
    assert r.returncode == 0, r.stderr
    assert ("#1  2026-11-18  Squat: 5 sets x 5 reps @ 100 kg  "
            "(difficulty 8/10)  [legs]") in r.stdout
    assert "Delete this entry? [y/N]" in r.stdout
    assert "Deleted #1." in r.stdout
    assert entries(data_file) == []


@pytest.mark.parametrize("answer", ["n\n", "\n", "", "yep\n", "no\n"])
def test_R13_delete_declined_changes_nothing(data_file, answer):
    """R13: any answer but y/yes, or no input, cancels the delete."""
    log(data_file)
    before = data_file.read_bytes()
    r = ask(data_file, answer, "delete", "1")
    assert r.returncode == 1
    assert "Not deleted." in r.stdout
    assert "Deleted" not in r.stdout
    assert data_file.read_bytes() == before


def test_R13_delete_does_not_renumber(data_file):
    """R13: deleting one entry leaves the other IDs as they were."""
    for name in ("A", "B", "C"):
        log(data_file, exercise=name)
    ask(data_file, "", "delete", "2", "--yes")
    out = run(data_file, "view").stdout
    assert "#1  2026-11-18  A" in out and "#3  2026-11-18  C" in out
    assert "#2" not in out
    log(data_file, exercise="D")
    assert [e["id"] for e in entries(data_file)] == [1, 3, 4]


def test_R13_hash_prefix_accepted(data_file):
    """R13: an ID may be written as #N, as view shows it."""
    log(data_file)
    assert ask(data_file, "", "delete", "#1", "--yes").returncode == 0
    assert entries(data_file) == []


@pytest.mark.parametrize("ident", ["9", "abc", "0", "-1", "1.5", "#"])
def test_R13_delete_unknown_or_bad_id(data_file, ident):
    """R13: an ID that no entry has is an input error; nothing changes."""
    log(data_file)
    before = data_file.read_bytes()
    r = ask(data_file, "y\n", "delete", ident, "--yes")
    assert r.returncode == 2
    assert "error:" in r.stderr
    assert data_file.read_bytes() == before


def test_R13_delete_on_missing_file(data_file):
    """R13: delete with no data file is an error and creates no file."""
    r = ask(data_file, "y\n", "delete", "1")
    assert r.returncode == 2
    assert not data_file.exists()


def test_R13_deleted_entry_leaves_prs(data_file):
    """R13/R8: deleting the PR entry makes the next best the PR."""
    log(data_file, weight="200", date="2026-11-17")
    log(data_file, weight="250", date="2026-11-18")
    ask(data_file, "", "delete", "2", "--yes")
    assert "Squat: 200 lbs x 5 reps" in run(data_file, "prs").stdout


# ---------- R13: edit ----------

def test_R13_edit_changes_only_given_fields(data_file):
    """R13: edit changes the fields given and keeps all others."""
    log(data_file, unit="kg")
    before = entries(data_file)[0]
    r = run(data_file, "edit", "1", "--reps", "6", "-d", "9")
    assert r.returncode == 0, r.stderr
    after = entries(data_file)[0]
    assert after == dict(before, reps=6, difficulty=9)


def test_R13_edit_every_field(data_file):
    """R13: every field add takes can be edited."""
    log(data_file)
    r = run(data_file, "edit", "1", "-e", "Front Squat", "-g", "quads",
            "-s", "4", "-r", "3", "-w", "80.5", "--unit", "kg", "-d", "7",
            "--date", "2026-11-20")
    assert r.returncode == 0, r.stderr
    assert entries(data_file) == [{
        "id": 1, "exercise": "Front Squat", "group": "quads", "sets": 4,
        "reps": 3, "weight": 80.5, "unit": "kg", "difficulty": 7,
        "date": "2026-11-20"}]


def test_R13_edit_prints_was_and_now(data_file):
    """R13: edit shows the entry before and after, weight as entered."""
    log(data_file, unit="kg")
    r = run(data_file, "edit", "#1", "--reps", "6")
    assert lines(r.stdout) == [
        "Was: #1  2026-11-18  Squat: 5 sets x 5 reps @ 100 kg  (difficulty 8/10)  [legs]",
        "Now: #1  2026-11-18  Squat: 5 sets x 6 reps @ 100 kg  (difficulty 8/10)  [legs]",
    ]


def test_R13_edit_needs_a_field(data_file):
    """R13: edit with nothing to change is an input error."""
    log(data_file)
    before = data_file.read_bytes()
    r = run(data_file, "edit", "1")
    assert r.returncode == 2
    assert "error:" in r.stderr
    assert data_file.read_bytes() == before


@pytest.mark.parametrize("opt", [["-d", "11"], ["-s", "0"], ["-w", "-5"],
                                 ["--unit", "stone"], ["--date", "2026-13-01"],
                                 ["-e", "  "], ["-g", ""], ["-r", "x"]])
def test_R13_edit_invalid_value_saves_nothing(data_file, opt):
    """R13: edit uses add's validation; a bad value changes nothing."""
    log(data_file)
    before = data_file.read_bytes()
    r = run(data_file, "edit", "1", *opt)
    assert r.returncode == 2
    assert data_file.read_bytes() == before


def test_R13_edit_unknown_id(data_file):
    """R13: editing an ID that no entry has is an input error."""
    log(data_file)
    before = data_file.read_bytes()
    r = run(data_file, "edit", "2", "--reps", "3")
    assert r.returncode == 2
    assert data_file.read_bytes() == before


def test_R13_edit_weight_keeps_unit(data_file):
    """R13/R6: a new weight without --unit stays in the entry's unit, not
    the saved default."""
    log(data_file, unit="kg")
    log(data_file, unit="lbs")  # default is now lbs
    run(data_file, "edit", "1", "-w", "110")
    e = entries(data_file)[0]
    assert (e["weight"], e["unit"]) == (110, "kg")


def test_R13_edit_unit_relabels_without_converting(data_file):
    """R13/R6: --unit alone changes the label; the number is kept."""
    log(data_file, weight="100")
    run(data_file, "edit", "1", "--unit", "kg")
    e = entries(data_file)[0]
    assert (e["weight"], e["unit"]) == (100, "kg")


def test_R13_edit_normalizes_like_add(data_file):
    """R13: edited values are cleaned the same way as on add."""
    log(data_file)
    run(data_file, "edit", "1", "-e", "  Box Squat ", "-g", " LEGS ",
        "-w", "2.50")
    e = entries(data_file)[0]
    assert (e["exercise"], e["group"], e["weight"]) == ("Box Squat", "legs", 2.5)


def test_R13_edit_keeps_id_and_position(data_file):
    """R13: the edited entry keeps its ID and its place in the file."""
    for name in ("A", "B", "C"):
        log(data_file, exercise=name)
    run(data_file, "edit", "2", "-e", "Bee", "--date", "2026-11-01")
    assert [(e["id"], e["exercise"]) for e in entries(data_file)] == [
        (1, "A"), (2, "Bee"), (3, "C")]


def test_R13_edit_old_entry_without_unit(data_file):
    """R13/R6: editing a version 1 entry (no unit) keeps it lbs."""
    write_file(data_file, {"version": 1, "entries": [
        {"exercise": "Row", "group": "back", "sets": 3, "reps": 8,
         "weight": 135, "difficulty": 6, "date": "2026-11-01"}]})
    assert run(data_file, "edit", "1", "-r", "10").returncode == 0
    e = entries(data_file)[0]
    assert (e["id"], e["weight"], e["unit"], e["reps"]) == (1, 135, "lbs", 10)


def test_R13_edit_updates_prs_by_mass(data_file):
    """R13/R8/R6: after an edit, prs compares the new value by mass."""
    log(data_file, weight="220", date="2026-11-17")
    log(data_file, weight="200", date="2026-11-18")
    run(data_file, "edit", "2", "-w", "100", "--unit", "kg")
    assert "Squat: 220.46 lbs x 5 reps (5 sets) on 2026-11-18" in \
        run(data_file, "prs").stdout


def test_R13_output_is_ascii(data_file):
    """R13: edit and delete output is plain ASCII (Windows cp1252 pipes)."""
    log(data_file)
    log(data_file)
    outs = [run(data_file, "edit", "1", "-r", "3"),
            ask(data_file, "n\n", "delete", "1"),
            ask(data_file, "y\n", "delete", "2"),
            run(data_file, "view")]
    for r in outs:
        (r.stdout + r.stderr).encode("ascii")
