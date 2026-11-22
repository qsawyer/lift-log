"""Round 6 tests: R14 (export entries to a CSV file for a spreadsheet).

Every test uses a temporary data file (tmp_path) and runs `export` with
explicit stdin, because it can ask before overwriting a file.
"""

import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import lift  # noqa: E402
from test_lift import add, data_file, run  # noqa: E402,F401
from test_round5 import ask  # noqa: E402

HEADER = ["id", "date", "exercise", "group", "sets", "reps", "weight", "unit",
          "weight_lbs", "weight_kg", "difficulty"]


def export(data_file, *args, answer=""):
    """Run `export` with `answer` as stdin ("" means end of input)."""
    return ask(data_file, answer, "export", *args)


def read_csv(path):
    """Rows of a CSV file as lists of strings, the way a spreadsheet sees it."""
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.reader(f))


# ---------- columns and values ----------

def test_R14_header_and_one_row_per_entry(data_file):
    """R14: the CSV has a header row, then one row per entry with every field."""
    add(data_file, exercise="Bench Press", group="chest", sets="3", reps="8",
        weight="185", difficulty="7", date="2026-11-18")
    r = export(data_file)
    assert r.returncode == 0, r.stderr
    rows = read_csv(data_file.parent / "workouts.csv")
    assert rows == [HEADER,
                    ["1", "2026-11-18", "Bench Press", "chest", "3", "8",
                     "185", "lbs", "185", "83.91", "7"]]


def test_R14_kg_entry_exported_as_logged_plus_lbs(data_file):
    """R14: a kg entry keeps its weight and unit; weight_lbs is converted."""
    add(data_file, exercise="Squat", group="legs", weight="100", unit="kg",
        date="2026-11-20")
    export(data_file, "out.csv")
    row = read_csv(data_file.parent / "out.csv")[1]
    assert row[HEADER.index("weight")] == "100"
    assert row[HEADER.index("unit")] == "kg"
    assert row[HEADER.index("weight_lbs")] == "220.46"
    assert row[HEADER.index("weight_kg")] == "100"


def test_R14_decimal_weight_kept_as_stored(data_file):
    """R14: a decimal weight is written as stored in its own unit."""
    add(data_file, weight="132.5", unit="lbs")
    export(data_file)
    row = read_csv(data_file.parent / "workouts.csv")[1]
    assert row[HEADER.index("weight")] == "132.5"
    assert row[HEADER.index("weight_lbs")] == "132.5"
    assert row[HEADER.index("weight_kg")] == "60.1"


def test_R14_version1_entry_without_unit_is_lbs(data_file):
    """R14: entries from a version 1 file (no unit) export as lbs."""
    data_file.write_text(json.dumps({"version": 1, "entries": [
        {"exercise": "Row", "group": "back", "sets": 3, "reps": 10,
         "weight": 95, "difficulty": 6, "date": "2026-10-01"}]}),
        encoding="utf-8")
    r = export(data_file)
    assert r.returncode == 0, r.stderr
    row = read_csv(data_file.parent / "workouts.csv")[1]
    assert row == ["1", "2026-10-01", "Row", "back", "3", "10", "95", "lbs",
                   "95", "43.09", "6"]


def test_R14_display_mode_does_not_change_file(data_file):
    """R14: the saved R11 display mode does not affect the exported values."""
    add(data_file, weight="185")
    export(data_file, "before.csv")
    assert run(data_file, "units", "kg").returncode == 0
    export(data_file, "after.csv")
    assert (read_csv(data_file.parent / "before.csv")
            == read_csv(data_file.parent / "after.csv"))


def test_R14_names_written_as_stored(data_file):
    """R14: differently spelled names of one exercise are not merged."""
    add(data_file, exercise="bench  press", date="2026-11-01")
    add(data_file, exercise="Bench Press", date="2026-11-02")
    export(data_file)
    rows = read_csv(data_file.parent / "workouts.csv")
    assert [r[2] for r in rows[1:]] == ["bench  press", "Bench Press"]


def test_R14_commas_quotes_and_non_ascii_round_trip(data_file):
    """R14: names with commas, quotes or accents survive the CSV unchanged."""
    name = 'Press, "close grip" é'
    add(data_file, exercise=name)
    r = export(data_file)
    assert r.returncode == 0, r.stderr
    assert read_csv(data_file.parent / "workouts.csv")[1][2] == name


def test_R14_file_has_bom_and_crlf_lines(data_file):
    """R14: UTF-8 byte-order mark (for Excel) and CRLF line ends."""
    add(data_file)
    export(data_file)
    raw = (data_file.parent / "workouts.csv").read_bytes()
    assert raw.startswith(b"\xef\xbb\xbfid,date,")
    assert raw.count(b"\r\n") == 2
    assert raw.count(b"\n") == 2


# ---------- which entries, in what order ----------

def test_R14_rows_ordered_by_date_then_file_order(data_file):
    """R14: oldest date first; same-date entries keep their file order."""
    add(data_file, exercise="C", date="2026-11-03")
    add(data_file, exercise="A", date="2026-11-01")
    add(data_file, exercise="B2", date="2026-11-02")
    add(data_file, exercise="B1", date="2026-11-02")
    export(data_file)
    rows = read_csv(data_file.parent / "workouts.csv")
    assert [r[2] for r in rows[1:]] == ["A", "B2", "B1", "C"]
    assert [r[0] for r in rows[1:]] == ["2", "3", "4", "1"]


def test_R14_group_filter(data_file):
    """R14: --group exports only that group, ignoring case and spaces."""
    add(data_file, exercise="Bench", group="chest")
    add(data_file, exercise="Squat", group="legs")
    add(data_file, exercise="Fly", group="chest")
    r = export(data_file, "--group", "  CHEST ")
    assert r.returncode == 0, r.stderr
    assert "Exported 2 entries" in r.stdout
    rows = read_csv(data_file.parent / "workouts.csv")
    assert [r[2] for r in rows[1:]] == ["Bench", "Fly"]


def test_R14_group_filter_short_flag_no_match(data_file):
    """R14: -g with no matching entries writes only the header."""
    add(data_file, group="chest")
    r = export(data_file, "-g", "legs")
    assert r.returncode == 0, r.stderr
    assert "Exported 0 entries" in r.stdout
    assert read_csv(data_file.parent / "workouts.csv") == [HEADER]


def test_R14_empty_log_writes_header_only(data_file):
    """R14: with no data file, export writes the header and creates no data file."""
    r = export(data_file)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "Exported 0 entries to workouts.csv"
    assert read_csv(data_file.parent / "workouts.csv") == [HEADER]
    assert not data_file.exists()


def test_R14_message_counts_entries(data_file):
    """R14: the message names the count and the path ('1 entry', 'N entries')."""
    add(data_file)
    r = export(data_file, "one.csv")
    assert r.stdout.strip() == "Exported 1 entry to one.csv"
    add(data_file)
    r = export(data_file, "two.csv")
    assert r.stdout.strip() == "Exported 2 entries to two.csv"


def test_R14_export_does_not_change_data_file(data_file):
    """R14: export only reads the data file."""
    add(data_file)
    add(data_file, unit="kg")
    before = data_file.read_bytes()
    assert export(data_file).returncode == 0
    assert data_file.read_bytes() == before


def test_R14_export_does_not_ask_when_file_is_new(data_file):
    """R14: no question when the target does not exist yet."""
    add(data_file)
    r = export(data_file, "new.csv")
    assert "Overwrite" not in r.stdout


# ---------- existing files ----------

@pytest.fixture
def existing(data_file):
    add(data_file)
    target = data_file.parent / "workouts.csv"
    target.write_bytes(b"old contents\r\n")
    return target


@pytest.mark.parametrize("answer", ["y\n", "yes\n", "  YES \n"])
def test_R14_overwrite_when_confirmed(data_file, existing, answer):
    """R14: an existing file is replaced only after y/yes."""
    r = export(data_file, answer=answer)
    assert r.returncode == 0, r.stderr
    assert "File workouts.csv already exists." in r.stdout
    assert "Overwrite it? [y/N]" in r.stdout
    assert read_csv(existing)[0] == HEADER


@pytest.mark.parametrize("answer", ["n\n", "\n", "sure\n", ""])
def test_R14_not_overwritten_without_yes(data_file, existing, answer):
    """R14: any other answer, or end of input, leaves the file and exits 1."""
    r = export(data_file, answer=answer)
    assert r.returncode == 1
    assert "Not exported." in r.stdout
    assert existing.read_bytes() == b"old contents\r\n"


@pytest.mark.parametrize("flag", ["--yes", "-y"])
def test_R14_yes_flag_overwrites_without_asking(data_file, existing, flag):
    """R14: --yes/-y replaces an existing file without the question."""
    r = export(data_file, flag)
    assert r.returncode == 0, r.stderr
    assert "Overwrite" not in r.stdout
    assert read_csv(existing)[0] == HEADER


def test_R14_refuses_to_overwrite_data_file(data_file):
    """R14: exporting onto the data file is an input error, even with --yes."""
    add(data_file)
    before = data_file.read_bytes()
    r = export(data_file, str(data_file), "--yes")
    assert r.returncode == 2
    assert "data file" in r.stderr
    assert data_file.read_bytes() == before


def test_R14_refuses_data_file_by_relative_path(data_file):
    """R14: the data file is recognised however its path is written."""
    add(data_file)
    before = data_file.read_bytes()
    r = export(data_file, "./" + data_file.name, "-y")
    assert r.returncode == 2
    assert data_file.read_bytes() == before


def test_R14_refuses_folder(data_file):
    """R14: a folder as PATH is an input error and nothing is written."""
    (data_file.parent / "sheets").mkdir()
    r = export(data_file, "sheets", "--yes")
    assert r.returncode == 2
    assert "folder" in r.stderr
    assert list((data_file.parent / "sheets").iterdir()) == []


def test_R14_write_failure_exits_1(data_file):
    """R14: a path that cannot be written is an error (exit 1), no traceback."""
    add(data_file)
    r = export(data_file, "missing-folder/out.csv")
    assert r.returncode == 1
    assert r.stderr.startswith("error: could not write")
    assert "Traceback" not in r.stderr
    assert not (data_file.parent / "missing-folder").exists()


def test_R14_no_temp_files_left_behind(data_file):
    """R14: the CSV is written via a temp file that is moved into place."""
    add(data_file)
    export(data_file, "out.csv")
    names = sorted(p.name for p in data_file.parent.iterdir())
    assert names == ["out.csv", "workouts.json"]


# ---------- unit level ----------

def test_R14_export_rows_function():
    """R14: export_rows() gives the header and string rows, sorted by date."""
    e1 = {"id": 5, **lift.make_entry("Squat", "Legs", 5, 5, 100, 8,
                                     "2026-11-20", "kg")}
    e2 = {"id": 9, **lift.make_entry("Curl", "arms", 3, 12, 30, 5,
                                     "2026-11-02")}
    rows = lift.export_rows([e1, e2])
    assert rows[0] == HEADER
    assert rows[1] == ["9", "2026-11-02", "Curl", "arms", "3", "12", "30",
                       "lbs", "30", "13.61", "5"]
    assert rows[2][0] == "5"
    assert lift.export_rows([e1, e2], group="ARMS")[1:] == [rows[1]]


def test_R14_weight_with_many_decimals_not_rounded(data_file):
    """R14: the as-logged weight is the stored number, never rounded."""
    add(data_file, weight="1.125", unit="kg")
    export(data_file)
    row = read_csv(data_file.parent / "workouts.csv")[1]
    assert row[HEADER.index("weight")] == "1.125"
    assert row[HEADER.index("weight_kg")] == "1.125"
    assert row[HEADER.index("weight_lbs")] == "2.48"


def test_R14_same_date_uses_file_order_not_id(data_file):
    """R14: same-date rows follow the data file's order, even if IDs don't."""
    entry = {"group": "legs", "sets": 5, "reps": 5, "weight": 100,
             "unit": "lbs", "difficulty": 8, "date": "2026-11-18"}
    data_file.write_text(json.dumps({"version": 3, "entries": [
        {"id": 7, "exercise": "First", **entry},
        {"id": 2, "exercise": "Second", **entry}]}), encoding="utf-8")
    export(data_file)
    rows = read_csv(data_file.parent / "workouts.csv")
    assert [(r[0], r[2]) for r in rows[1:]] == [("7", "First"), ("2", "Second")]


def test_R14_temp_file_removed_when_move_fails(tmp_path, monkeypatch):
    """R14: if the finished CSV can't be moved into place, no temp file is left."""
    def fail(src, dst):
        raise PermissionError("file is open in another program")
    monkeypatch.setattr(lift.os, "replace", fail)
    with pytest.raises(PermissionError):
        lift.write_csv(tmp_path / "out.csv", [["id"], ["1"]])
    assert list(tmp_path.iterdir()) == []
