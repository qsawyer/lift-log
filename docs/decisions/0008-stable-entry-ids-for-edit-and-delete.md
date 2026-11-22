# 0008 — Identify entries by a stable ID stored in the file

**Status:** accepted · 2026-11-22

In the context of **R13 (the user can edit or delete an entry), where the
command line needs some way to say which entry is meant, on top of a data
file whose entries have no identity beyond their position**,
facing **three ways to refer to an entry: its position in the `view` listing
(numbered 1..N as printed), a stable number stored on each entry, or a
match on its fields (e.g. `delete --exercise Squat --date 2026-11-18`)**,
we decided for **a positive integer `id` stored on every entry, given out as
one more than the highest ID in the file, shown as `#N` by `view` and accepted
as `N` or `#N`; files from Rounds 1-4 are numbered in file order when read and
the numbers are written on the next save, so `FILE_VERSION` becomes 3**,
and neglected **view positions (no format change, but `view` sorts by group
and date, so numbers shift after every delete, after `view --group`, and after
adding a back-dated entry, and a second `delete 3` right after the first one
would remove a different entry) and matching on fields (needs no numbers, but
two sets of the same lift on one day are identical in every field the user
can type, so it cannot pick one of them)**,
to achieve **a number that means the same entry every time the user sees it,
so `edit`/`delete` can never hit the wrong row because something else changed
in between**,
accepting that **the file format changes again (older files are still read,
see 0001 and 0006), that old entries gain an `id` field on their next save,
that IDs have gaps after deletes, and that deleting the highest-numbered entry
lets its number be given out again (keeping a separate "next id" counter
would prevent that, at the cost of more state to keep in step)**.
The user chose stable IDs over view positions during clarification; the
numbering rule for old files and duplicates was Claude's choice.
