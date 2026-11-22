# 0011 — Write the export CSV as UTF-8 with a byte-order mark

**Status:** accepted · 2026-11-22

In the context of **R14 export to CSV for Excel or Google Sheets, where
exercise names are free text the user typed (and may contain characters
such as `é`), and the user is on Windows, where Excel guesses a CSV's
encoding when it is double-clicked**,
facing **four encodings: plain UTF-8, UTF-8 with a byte-order mark
(`utf-8-sig`), the Windows code page (cp1252), or ASCII with other characters
replaced**,
we decided for **UTF-8 with a byte-order mark, with the `csv` module's
standard quoting and CRLF line ends**,
and neglected **plain UTF-8 (Google Sheets reads it, but Excel on Windows
opens a BOM-less CSV in the local code page and shows `é` as `Ã©`), cp1252
(Excel reads it, but it cannot hold every name and Google Sheets and other
tools expect UTF-8) and ASCII-only (always safe, but changes the names the
user typed, which the project never does to stored names)**,
to achieve **a file that shows every exercise name correctly when it is
double-clicked in Excel and when it is uploaded to Google Sheets, with no
import settings**,
accepting that **a few tools that do not expect a BOM may show three stray
bytes before the `id` header (Python readers need `encoding="utf-8-sig"`, as
the tests use), and that this differs from `workouts.json`, which is UTF-8
without a BOM**.
This was Claude's choice; the user was not asked.
