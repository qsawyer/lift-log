# 0004 — Weekly summary covers one Monday-Sunday calendar week, chosen by date

**Status:** accepted · 2026-11-21

In the context of **R10 (the user can request a weekly summary of how many
workouts they did and their PRs for the week)**,
facing **several meanings of "a week": the Monday-Sunday calendar week, the
Sunday-Saturday (US) week, the last 7 days counting back from today, or one
summary for every week in the log**,
we decided for **the Monday-Sunday (ISO) calendar week containing today, with
`summary --week YYYY-MM-DD` choosing the week that contains any given date**,
and neglected **a rolling last-7-days window (its boundaries move every day,
so the same "week" gives different numbers depending on when it is asked, and
past weeks cannot be looked up), Sunday-Saturday weeks (equally valid, but
Python's `date.weekday()` and the ISO standard start on Monday, and the weekend
stays together in one week), and printing every week (long output that grows
without bound, when the request is for "the week")**,
to achieve **stable weeks that always contain the same days, so a summary can
be checked against `view` and repeated later with the same result**,
accepting that **on a Monday the current week holds at most one day of data,
so the user must pass `--week` to see the week that just ended, and that users
who think of Sunday as the first day may find the boundary surprising**.
The user chose the Monday-Sunday week with a `--week` option during
clarification.
