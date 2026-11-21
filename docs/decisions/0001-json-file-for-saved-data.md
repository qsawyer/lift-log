# 0001 — Store workout data in a single JSON file, rewritten atomically

**Status:** accepted · 2026-11-21

In the context of **a standard-library-only Python CLI that must save after
every input (R5) and let the user view saved data (R7)**,
facing **the choice of on-disk format: CSV, JSON Lines (append-only), a single
JSON document, or SQLite (`sqlite3`)**,
we decided for **one JSON document (`{"version": 1, "entries": [...]}`) that is
rewritten in full after every add, via a temp file plus `os.replace`**,
and neglected **CSV (no types, awkward to extend with new fields and quoting
issues in exercise names), JSON Lines (cheap appends, but a crash mid-append
leaves a half-written last line and there is no place for a format version), and
SQLite (robust, but opaque to a user who wants to open or fix their data by
hand, and more schema machinery than seven fields need)**,
to achieve **a human-readable file that is never left half-written, with a version
field so later rounds can change the format safely**,
accepting that **each save rewrites the whole file (O(n) per add, which is
negligible for a personal log of thousands of entries) and that two processes
writing at the same moment could lose one write (last writer wins)**.
