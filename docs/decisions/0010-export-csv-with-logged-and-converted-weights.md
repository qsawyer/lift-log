# 0010 — Export as CSV with the logged weight plus lbs and kg columns

**Status:** accepted · 2026-11-22

In the context of **R14 (the user can export their data into a file that can
be used in a spreadsheet such as Google Sheets or Excel), with the rule that
the program uses only the Python standard library and with entries that may
be logged in lbs or kg (R6)**,
facing **three file formats (CSV, a real `.xlsx` workbook, or both chosen by a
flag) and three ways to write weights (exactly as logged, converted to the
R11 display mode, or as logged plus a column for each unit)**,
we decided for **one CSV file (`export [PATH]`, default `workouts.csv`), one
row per entry with the columns
`id,date,exercise,group,sets,reps,weight,unit,weight_lbs,weight_kg,difficulty`,
where `weight`/`unit` are as stored and `weight_lbs`/`weight_kg` are the same
mass in each unit (stored number in its own unit, otherwise converted and
rounded to two decimals as elsewhere)**,
and neglected **`.xlsx` (native to Excel and could hold several sheets, but
without a third-party package it means hand-writing zipped Office XML, a lot
of code that is easy to get subtly wrong and hard to test without Excel),
weights as logged only (faithful, but a sheet sorting or charting a mixed
lbs/kg log would compare 100 kg as lighter than 185 lbs), and the display
mode (matches the screen, but the file would lose what was actually logged
and would change depending on a setting at export time)**,
to achieve **a file that both Excel and Google Sheets open without any
import settings, that never loses the entry as typed, and that can be sorted
or charted by real weight straight away**,
accepting that **CSV has one sheet and no types or formatting (dates and
numbers are guessed by the spreadsheet, which works for ISO dates and plain
numbers), that the two converted columns repeat information, and that
`export` ignores `--units` and the saved display mode even though it deals
with weights**.
The user chose CSV, the as-logged-plus-both-units columns, a path argument
with an overwrite question, and the optional `--group` during clarification;
the exact column names and order, sorting by date, and rounding were
Claude's choices.
