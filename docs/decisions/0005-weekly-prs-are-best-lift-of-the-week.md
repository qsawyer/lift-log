# 0005 — "PRs for the week" means each exercise's best lift that week

**Status:** accepted · 2026-11-21

In the context of **R10's weekly summary, which must show "what their PRs for
the week" were, alongside R8's all-time personal records**,
facing **three readings: only new all-time records set during the week (the
week's best beat everything before it), the same but not counting an
exercise's first-ever session, or the best lift of each exercise trained that
week regardless of earlier weeks**,
we decided for **the best entry per exercise within the week, chosen with the
R8 rule (heaviest weight, then more reps, then the earlier date) through one
shared `best_entry()` function, and the workout count as the number of distinct
days trained**,
and neglected **new all-time PRs only (it highlights real milestones, but most
weeks would show an empty list, which says little about what was lifted) and
the variant that excludes first sessions (it adds a rule the user then has to
learn)**,
to achieve **a summary that always reports what was actually lifted that week
and uses the same tie-break rule as `prs`, so the two commands never disagree
about which set was best**,
accepting that **a line under "PRs this week" may be lighter than the all-time
PR shown by `prs`, so the README spells out the difference, and that a lifter
who wants to see only new records cannot do so yet**.
The user chose "best lift per exercise that week" and "distinct days trained"
during clarification.
