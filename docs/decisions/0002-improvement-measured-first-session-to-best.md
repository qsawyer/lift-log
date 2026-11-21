# 0002 — Measure improvement as best weight minus first-session weight, in lbs

**Status:** accepted · 2026-11-21

In the context of **R9 (show the exercises with the most improvement), using
only the data each entry already has (weight, reps, sets, date)**,
facing **several reasonable measures: first vs. best weight in lbs, the same as
a percentage, first vs. latest weight, or the gain in estimated 1-rep max
(Epley: weight × (1 + reps/30))**,
we decided for **improvement = heaviest weight ever − heaviest weight on the
exercise's earliest date, in pounds, counting only gains above zero and
ranking the top 5**,
and neglected **percent change (it fairly compares light and heavy lifts, but
can't be computed from a 0 lb start, e.g. bodyweight dips, and inflates small
numbers: 5→10 lbs is +100%), first vs. latest (one off day or deload would wipe
out real progress and can produce negative "improvement"), and estimated 1RM
(it credits rep gains, but the formula is unreliable at high reps and is a
number the user never actually lifted)**,
to achieve **a number the user can check by eye against their log and that
matches their PR (R8), so the two features never contradict each other**,
accepting that **heavy compound lifts will usually outrank small isolation lifts,
that rep-only progress at the same weight is not counted, and that the "first
session" uses that day's heaviest set rather than an average**.
The user chose this measure and the top-5 limit when asked during
clarification.
