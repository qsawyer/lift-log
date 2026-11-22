# 0006 — Store each weight as entered, with its unit, and compare by mass

**Status:** accepted · 2026-11-22

## Requirement change

**R6 changed in Round 4 from lbs-only to lbs-or-kg.** Rounds 1-3 read "R6:
tracks the weight lifted in lbs", and every weight was saved and shown as
pounds. Round 4 of `problem.md` changes it to "gives the user the option to
track either in lbs or kg". The reason is that a lifter whose gym, plates or
program uses kilograms otherwise had to convert every lift to pounds by hand
before logging it, which is slow and invites mistakes.

**What happens to existing data:**
- Nothing is migrated or rewritten. Version 1 files (Rounds 1-3) are read
  as they are; an entry without a `unit` field means lbs.
- The first save after upgrading (an `add` or `units`) writes the file as
  version 2. The old entries are kept exactly as they were, with no `unit`
  field added. New entries always carry `"unit"`.
- Output for old data does not change: the default display (R11) is lbs,
  so `view`, `prs`, `improved` and `summary` print the same lines as in
  Round 3 until the user chooses kg or both.
- Going back is the only risk: a Round 3 copy of the program reading a
  version 2 file would treat kg entries as lbs.

## Decision

In the context of **R6 (changed): the user can now log weight in lbs or kg,
while R8, R9 and R10 must still pick the heaviest lift correctly, and the data
file already holds lbs-only entries from earlier rounds**,
facing **three ways to store a kg lift: convert it to lbs when saving (one
unit in the file, no format change), store the number as typed plus a `unit`
field, or store both the lbs and kg values on every entry**,
we decided for **storing the weight exactly as entered with a `unit` field
(`"lbs"` or `"kg"`; a missing field means lbs), bumping `FILE_VERSION` to 2,
and converting to lbs (1 lb = 0.45359237 kg, rounded to 6 places) only when
comparing or displaying**,
and neglected **converting on save (no version bump, but 100 kg would be saved
as 220.462262... lbs, so the user's own number is lost and shows back as
"100 kg" only by luck of rounding; it also makes it impossible to show a lift
"as logged" later) and storing both values (easy display, but the two numbers
can disagree after a hand edit, and the file holds redundant data)**,
to achieve **a file that keeps exactly what the user typed, reads Round 1-3
files without migration, and lets `prs`, `improved` and `summary` compare a kg
lift and a lbs lift fairly (100 kg beats 220 lbs)**,
accepting that **every comparison goes through a conversion, that float
conversion needs rounding so equal masses (68.0388555 kg and 150 lbs) tie
instead of showing a +0 lbs "improvement", and that a version 2 file written
with kg entries would be misread as lbs by a Round 3 copy of the program**.
The user chose `--unit` with lbs as the default during clarification; the
storage format was Claude's choice.
