"""Lift Log: a command-line workout tracker.

Usage:
    python lift.py add --exercise NAME --group GROUP --sets N --reps N \
                       --weight W [--unit lbs|kg] --difficulty 1-10 \
                       [--date YYYY-MM-DD]
    python lift.py view [--group GROUP]
    python lift.py groups
    python lift.py prs
    python lift.py improved
    python lift.py summary [--week YYYY-MM-DD]

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
FILE_VERSION = 2  # 2: entries may have "unit"; optional "settings" (Round 4)

UNITS = ("lbs", "kg")
KG_PER_LB = 0.45359237  # exact, by definition


class InputError(ValueError):
    """Raised when user input is invalid."""


# ---------- storage (R5, R7) ----------

def data_path(cli_value=None):
    if cli_value:
        return Path(cli_value)
    env = os.environ.get("LIFT_LOG_FILE")
    return Path(env) if env else DEFAULT_FILE


def load_file(path):
    """Read the whole data file as {"entries": [...], "settings": {...}}.

    A missing file means no entries and no settings. Version 1 files have no
    settings and no "unit" on entries; both are read as-is.
    """
    path = Path(path)
    if not path.exists():
        return {"entries": [], "settings": {}}
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return {"entries": list(data.get("entries", [])),
            "settings": dict(data.get("settings") or {})}


def load(path):
    """Read all entries from the data file. Missing file means no entries."""
    return load_file(path)["entries"]


def save(path, entries, settings=None):
    """Write all entries (and settings, if any) atomically: temp file in the
    same dir, then replace."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"version": FILE_VERSION}
    if settings:
        payload["settings"] = settings
    payload["entries"] = entries
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


def make_entry(exercise, group, sets, reps, weight, difficulty, date=None,
               unit="lbs"):
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
        raise InputError(f"weight must be a number, got {weight!r}")
    if weight != weight or weight in (float("inf"), float("-inf")):
        raise InputError("weight must be a finite number")
    if weight < 0:
        raise InputError(f"weight cannot be negative, got {weight}")
    if weight == int(weight):
        weight = int(weight)

    unit = (unit or "").strip().lower()
    if unit not in UNITS:
        raise InputError(f"unit must be lbs or kg, got {unit!r}")

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
        "unit": unit,
        "difficulty": difficulty,
        "date": date,
    }


# ---------- operations ----------

def add_entry(path, entry):
    """Append one entry and save immediately (R5), keeping saved settings."""
    data = load_file(path)
    data["entries"].append(entry)
    save(path, data["entries"], data["settings"])
    return entry


def sort_by_group(entries):
    """Return {group: [entries]} with groups alphabetical, entries by date (R2).

    Python's sort is stable, so same-date entries keep insertion order.
    """
    grouped = {}
    for e in sorted(entries, key=lambda e: (e["group"], e["date"])):
        grouped.setdefault(e["group"], []).append(e)
    return grouped


# ---------- units (R6) ----------

def entry_unit(e):
    """The unit an entry was logged in. Older entries have none: lbs."""
    return e.get("unit", "lbs")


def weight_in(e, unit):
    """An entry's weight in `unit`. Its own unit is returned unchanged;
    conversions are rounded to 6 places so equal masses compare equal."""
    w = e["weight"]
    if entry_unit(e) == unit:
        return w
    return round(w * KG_PER_LB if unit == "kg" else w / KG_PER_LB, 6)


def weight_lbs(e):
    """Weight in lbs, used whenever entries are compared (R8, R9, R10)."""
    return weight_in(e, "lbs")


def fmt_num(x):
    """185 -> '185', 132.5 -> '132.5', 2.2000000000000002 -> '2.2'."""
    return f"{x:.2f}".rstrip("0").rstrip(".")


def fmt_weight(e, unit="lbs"):
    return f"{fmt_num(weight_in(e, unit))} {unit}"


def format_entry(e, unit="lbs"):
    return (f"  {e['date']}  {e['exercise']}: {e['sets']} sets x {e['reps']} reps"
            f" @ {fmt_weight(e, unit)}  (difficulty {e['difficulty']}/10)")


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
        prs.append((name, best_entry(items)))
    prs.sort(key=lambda p: (p[0].casefold(), p[0]))
    return prs


def format_prs(entries):
    if not entries:
        return "No workouts logged yet."
    lines = ["Personal records:"]
    for name, e in personal_records(entries):
        lines.append(f"  {name}: {fmt_weight(e)} x {e['reps']} reps"
                     f" ({e['sets']} sets) on {e['date']}")
    return "\n".join(lines)


# ---------- most improved (R9) ----------

TOP_IMPROVED = 5


def most_improved(entries, top=TOP_IMPROVED):
    """Return up to `top` of [(name, gain_lbs, start_entry, best_entry)].

    start = heaviest entry on the exercise's earliest date (first session);
    best = heaviest entry ever, earliest date on ties; gain = best - start,
    in lbs (entries logged in kg are converted before comparing).
    Only exercises with gain > 0 are included. Largest gain first, then name.
    """
    results = []
    for name, items in by_exercise(entries).values():
        first_date = min(e["date"] for e in items)
        start = max((e for e in items if e["date"] == first_date),
                    key=weight_lbs)
        best = min(items, key=lambda e: (-weight_lbs(e), e["date"]))
        gain = weight_lbs(best) - weight_lbs(start)
        if gain > 0:
            results.append((name, gain, start, best))
    results.sort(key=lambda r: (-r[1], r[0].casefold(), r[0]))
    return results[:top]


def format_improved(entries):
    if not entries:
        return "No workouts logged yet."
    ranked = most_improved(entries)
    if not ranked:
        return "No improvement recorded yet."
    lines = ["Most improved exercises:"]
    for i, (name, gain, start, best) in enumerate(ranked, 1):
        lines.append(f"  {i}. {name}: +{fmt_num(gain)} lbs"
                     f" ({fmt_weight(start)} on {start['date']}"
                     f" -> {fmt_weight(best)} on {best['date']})")
    return "\n".join(lines)


# ---------- weekly summary (R10) ----------

def week_bounds(day):
    """Return (Monday, Sunday) of the calendar week containing `day`."""
    start = day - datetime.timedelta(days=day.weekday())
    return start, start + datetime.timedelta(days=6)


def best_entry(items):
    """The R8 rule: heaviest weight, then more reps, then the earlier date.

    Weights are compared in lbs, so lbs and kg entries compare by mass (R6).
    """
    return min(items, key=lambda e: (-weight_lbs(e), -e["reps"], e["date"]))


def weekly_summary(entries, day):
    """Summarize the Mon-Sun week containing `day`.

    Returns {"start", "end", "workouts", "prs"}: workouts is the number of
    distinct dates with entries; prs is [(name, best_entry)] for each exercise
    logged that week, sorted by name ignoring case. Names use the latest
    spelling across the whole log, so they match `prs`.
    """
    start, end = week_bounds(day)
    lo, hi = start.isoformat(), end.isoformat()
    week = [e for e in entries if lo <= e["date"] <= hi]
    names = {key: name for key, (name, _) in by_exercise(entries).items()}
    prs = [(names[key], best_entry(items))
           for key, (_, items) in by_exercise(week).items()]
    prs.sort(key=lambda p: (p[0].casefold(), p[0]))
    return {"start": start, "end": end,
            "workouts": len({e["date"] for e in week}), "prs": prs}


def format_summary(entries, day):
    s = weekly_summary(entries, day)
    lines = [f"Week of {s['start']} to {s['end']}", f"Workouts: {s['workouts']}"]
    if not s["prs"]:
        lines.append("No lifts logged this week.")
        return "\n".join(lines)
    lines.append("PRs this week (best lift per exercise):")
    for name, e in s["prs"]:
        lines.append(f"  {name}: {fmt_weight(e)} x {e['reps']} reps"
                     f" ({e['sets']} sets) on {e['date']}")
    return "\n".join(lines)


def parse_date(value):
    try:
        return datetime.date.fromisoformat(value)
    except (TypeError, ValueError):
        raise InputError(f"date must be YYYY-MM-DD, got {value!r}")


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
    a.add_argument("--weight", "-w", required=True, help="weight lifted")
    a.add_argument("--unit", default="lbs",
                   help="unit of --weight: lbs or kg (default: lbs)")
    a.add_argument("--difficulty", "-d", required=True, help="difficulty 1-10")
    a.add_argument("--date", help="YYYY-MM-DD (default: today)")

    v = sub.add_parser("view", help="show saved workouts grouped by muscle group")
    v.add_argument("--group", "-g", help="only show this muscle group")

    sub.add_parser("groups", help="list muscle groups with entries")
    sub.add_parser("prs", help="show the personal record for every exercise")
    sub.add_parser("improved", help="show the 5 most-improved exercises")

    w = sub.add_parser("summary", help="weekly summary: workouts and PRs (Mon-Sun)")
    w.add_argument("--week", help="any date in the week, YYYY-MM-DD (default: this week)")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    path = data_path(args.file)
    try:
        if args.command == "add":
            entry = make_entry(args.exercise, args.group, args.sets, args.reps,
                               args.weight, args.difficulty, args.date,
                               args.unit)
            add_entry(path, entry)
            # Confirm the weight exactly as it was entered, in its own unit.
            print("Saved:" + format_entry(entry, entry_unit(entry))[1:]
                  + f"  [{entry['group']}]")
        elif args.command == "view":
            print(format_view(load(path), args.group))
        elif args.command == "groups":
            groups = sorted({e["group"] for e in load(path)})
            print("\n".join(groups) if groups else "No workouts logged yet.")
        elif args.command == "prs":
            print(format_prs(load(path)))
        elif args.command == "improved":
            print(format_improved(load(path)))
        elif args.command == "summary":
            day = parse_date(args.week) if args.week else datetime.date.today()
            print(format_summary(load(path), day))
    except InputError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"error: data file {path} is not valid JSON: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
