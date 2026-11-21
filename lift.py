"""Lift Log: a command-line workout tracker.

Usage:
    python lift.py add --exercise NAME --group GROUP --sets N --reps N \
                       --weight LBS --difficulty 1-10 [--date YYYY-MM-DD]
    python lift.py view [--group GROUP]
    python lift.py groups
    python lift.py prs

Data is saved to workouts.json next to this file after every add, unless
--file or the LIFT_LOG_FILE environment variable points elsewhere.
"""

import argparse
import datetime
import json
import os
import sys
import tempfile
from pathlib import Path

DEFAULT_FILE = Path(__file__).resolve().parent / "workouts.json"
FILE_VERSION = 1


class InputError(ValueError):
    """Raised when user input is invalid."""


# ---------- storage (R5, R7) ----------

def data_path(cli_value=None):
    if cli_value:
        return Path(cli_value)
    env = os.environ.get("LIFT_LOG_FILE")
    return Path(env) if env else DEFAULT_FILE


def load(path):
    """Read all entries from the data file. Missing file means no entries."""
    path = Path(path)
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return list(data.get("entries", []))


def save(path, entries):
    """Write all entries atomically: temp file in same dir, then replace."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"version": FILE_VERSION, "entries": entries}
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".lift-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


# ---------- validation (R1, R3, R4, R6) ----------

def _positive_int(value, field):
    try:
        n = int(value)
    except (TypeError, ValueError):
        raise InputError(f"{field} must be a whole number, got {value!r}")
    if isinstance(value, float) and value != n:
        raise InputError(f"{field} must be a whole number, got {value!r}")
    if n < 1:
        raise InputError(f"{field} must be at least 1, got {n}")
    return n


def make_entry(exercise, group, sets, reps, weight, difficulty, date=None):
    exercise = (exercise or "").strip()
    if not exercise:
        raise InputError("exercise name is required")
    group = (group or "").strip().lower()
    if not group:
        raise InputError("muscle group is required")

    sets = _positive_int(sets, "sets")
    reps = _positive_int(reps, "reps")

    try:
        weight = float(weight)
    except (TypeError, ValueError):
        raise InputError(f"weight must be a number of lbs, got {weight!r}")
    if weight != weight or weight in (float("inf"), float("-inf")):
        raise InputError("weight must be a finite number")
    if weight < 0:
        raise InputError(f"weight cannot be negative, got {weight}")
    if weight == int(weight):
        weight = int(weight)

    try:
        difficulty = int(difficulty)
    except (TypeError, ValueError):
        raise InputError(f"difficulty must be a whole number 1-10, got {difficulty!r}")
    if not 1 <= difficulty <= 10:
        raise InputError(f"difficulty must be between 1 and 10, got {difficulty}")

    if date is None:
        date = datetime.date.today().isoformat()
    else:
        try:
            date = datetime.date.fromisoformat(date).isoformat()
        except (TypeError, ValueError):
            raise InputError(f"date must be YYYY-MM-DD, got {date!r}")

    return {
        "exercise": exercise,
        "group": group,
        "sets": sets,
        "reps": reps,
        "weight": weight,
        "difficulty": difficulty,
        "date": date,
    }


# ---------- operations ----------

def add_entry(path, entry):
    """Append one entry and save immediately (R5)."""
    entries = load(path)
    entries.append(entry)
    save(path, entries)
    return entry


def sort_by_group(entries):
    """Return {group: [entries]} with groups alphabetical, entries by date (R2).

    Python's sort is stable, so same-date entries keep insertion order.
    """
    grouped = {}
    for e in sorted(entries, key=lambda e: (e["group"], e["date"])):
        grouped.setdefault(e["group"], []).append(e)
    return grouped


def format_entry(e):
    return (f"  {e['date']}  {e['exercise']}: {e['sets']} sets x {e['reps']} reps"
            f" @ {e['weight']} lbs  (difficulty {e['difficulty']}/10)")


def format_view(entries, group=None):
    if group is not None:
        group = group.strip().lower()
        entries = [e for e in entries if e["group"] == group]
        if not entries:
            return f"No workouts logged for {group}."
    if not entries:
        return "No workouts logged yet."
    lines = []
    for g, items in sort_by_group(entries).items():
        lines.append(f"== {g} ==")
        lines.extend(format_entry(e) for e in items)
    return "\n".join(lines)


# ---------- personal records (R8) ----------

def exercise_key(name):
    """Names that differ only in case or spacing are the same exercise."""
    return " ".join(name.split()).casefold()


def by_exercise(entries):
    """Return {key: (display name, [entries])}.

    The display name is the spelling of the most recently logged entry (latest
    date; on the same date, the one added last).
    """
    grouped = {}
    for e in entries:
        grouped.setdefault(exercise_key(e["exercise"]), []).append(e)
    result = {}
    for key, items in grouped.items():
        # max() returns the first maximum, so iterate newest-added first.
        latest = max(reversed(items), key=lambda e: e["date"])
        result[key] = (latest["exercise"], items)
    return result


def personal_records(entries):
    """Return [(name, pr_entry)] sorted by name, ignoring case.

    The PR is the heaviest weight; ties go to more reps, then the earlier date.
    """
    prs = []
    for name, items in by_exercise(entries).values():
        best = min(items, key=lambda e: (-e["weight"], -e["reps"], e["date"]))
        prs.append((name, best))
    prs.sort(key=lambda p: (p[0].casefold(), p[0]))
    return prs


def fmt_lbs(weight):
    """185 -> '185', 132.5 -> '132.5', 2.2000000000000002 -> '2.2'."""
    return f"{weight:.2f}".rstrip("0").rstrip(".")


def format_prs(entries):
    if not entries:
        return "No workouts logged yet."
    lines = ["Personal records:"]
    for name, e in personal_records(entries):
        lines.append(f"  {name}: {fmt_lbs(e['weight'])} lbs x {e['reps']} reps"
                     f" ({e['sets']} sets) on {e['date']}")
    return "\n".join(lines)


# ---------- CLI ----------

def build_parser():
    p = argparse.ArgumentParser(prog="lift.py", description="Track your lifts.")
    p.add_argument("--file", help="data file (default: workouts.json or $LIFT_LOG_FILE)")
    sub = p.add_subparsers(dest="command", required=True)

    a = sub.add_parser("add", help="log an exercise")
    a.add_argument("--exercise", "-e", required=True, help="exercise name")
    a.add_argument("--group", "-g", required=True, help="muscle group, e.g. chest")
    a.add_argument("--sets", "-s", required=True, help="number of sets")
    a.add_argument("--reps", "-r", required=True, help="reps per set")
    a.add_argument("--weight", "-w", required=True, help="weight in lbs")
    a.add_argument("--difficulty", "-d", required=True, help="difficulty 1-10")
    a.add_argument("--date", help="YYYY-MM-DD (default: today)")

    v = sub.add_parser("view", help="show saved workouts grouped by muscle group")
    v.add_argument("--group", "-g", help="only show this muscle group")

    sub.add_parser("groups", help="list muscle groups with entries")
    sub.add_parser("prs", help="show the personal record for every exercise")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    path = data_path(args.file)
    try:
        if args.command == "add":
            entry = make_entry(args.exercise, args.group, args.sets, args.reps,
                               args.weight, args.difficulty, args.date)
            add_entry(path, entry)
            print("Saved:" + format_entry(entry)[1:] + f"  [{entry['group']}]")
        elif args.command == "view":
            print(format_view(load(path), args.group))
        elif args.command == "groups":
            groups = sorted({e["group"] for e in load(path)})
            print("\n".join(groups) if groups else "No workouts logged yet.")
        elif args.command == "prs":
            print(format_prs(load(path)))
    except InputError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"error: data file {path} is not valid JSON: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
