# 0003 — Match exercise names case-insensitively when reading, not when saving

**Status:** accepted · 2026-11-21

In the context of **R8/R9, which must treat "bench press" and "Bench Press" as
one exercise (the user confirmed this), on top of a data file that already holds
names exactly as typed**,
facing **the choice between normalizing names when they are saved (and
migrating existing files) and comparing names with a key computed when
reading**,
we decided for **a read-time key (`" ".join(name.split()).casefold()`), leaving
stored names untouched and showing the spelling from the most recent entry**,
and neglected **normalizing on save (simpler grouping later, but it would
rewrite names the user typed, need a data migration and a version bump under
decision 0001, and change what `view` prints, R3/R7) and a user-maintained alias
list (handles "OHP" vs "Overhead Press", but is new UI nobody asked for)**,
to achieve **case-insensitive matching with no change to the file format or to
earlier behavior**,
accepting that **abbreviations and typos ("Bench" vs "Bench Press") still count
as separate exercises, and that the displayed name can change if the user
logs a new spelling**.
