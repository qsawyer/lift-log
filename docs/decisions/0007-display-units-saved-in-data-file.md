# 0007 — Save the display-units choice in the data file

**Status:** accepted · 2026-11-22

In the context of **R11: the user can show weights in lbs, kg or both and
switch quickly; the user chose a saved setting (`units kg|lbs|both`) plus a
one-off `--units` override, with lbs as the default**,
facing **where to keep the saved setting: in the data file next to the
entries, in a separate settings file (e.g. `lift-settings.json` beside the
data file, or in the user's home directory), or in an environment variable
such as `LIFT_UNITS`**,
we decided for **an optional `"settings": {"units": ...}` object in the data
file (part of file version 2, see 0006), written only once the user picks a
mode, kept by every later `add`, with an unknown value read as lbs**,
and neglected **a separate settings file (keeps workout data and preferences
apart, but adds a second file to locate, back up and keep in step with
`--file`/`LIFT_LOG_FILE`, and tests would have to redirect it too) and an
environment variable (no file writes at all, but it is not "quick and easy"
to switch on Windows and does not persist across terminals unless the user
edits their profile)**,
to achieve **one file that holds everything, so `--file other.json` and the
test `tmp_path` files automatically carry their own setting, and switching is
a single command**,
accepting that **changing the display mode rewrites the data file (atomically,
as in 0001, with entries unchanged), that two logs (e.g. two people) each have
their own setting, and that every save must remember to carry the settings
forward, which a test (`test_R11_add_keeps_saved_units`) guards**.
