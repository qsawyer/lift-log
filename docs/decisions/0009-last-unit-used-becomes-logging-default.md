# 0009 — The last `--unit` passed to `add` becomes the logging default

**Status:** accepted · 2026-11-22

In the context of **R12 (once a unit is set it is saved as the default and the
user is not asked about units again unless they ask), after Round 4 left a kg
lifter typing `--unit kg` on every `add`**,
facing **three ways to set the default: the unit given on the last `add` sticks,
a separate setting command (e.g. `units --log kg`), or one shared setting with
the R11 display mode (`units kg` sets both)**,
we decided for **sticky `--unit`: `add --unit X` saves X as
`"settings": {"log_unit": X}` (next to the R11 `units` key, see 0007), later
adds without `--unit` use it and ask nothing, lbs is used until a unit is first
given, and `add` prints `Default unit for new entries is now: X` when it changes**,
and neglected **a separate command (explicit, but adds a step the requirement
says should not be needed, and an `add --unit kg` that is forgotten next time
would quietly log lbs) and sharing the display setting (one command, but
`both` has no single logging unit, and someone who logs kg while reading lbs, or
the reverse, could not do so)**,
to achieve **the fewest keystrokes for someone who lifts in one unit (set it
once, as part of a normal add) while keeping how weights are logged and how
they are shown independent**,
accepting that **a one-off `--unit` for a single lift (e.g. a kg dumbbell for a
lbs lifter) also changes the default, which is why `add` announces every change,
and that there is no command that only shows the logging default (the `Saved:`
line shows the unit of each entry)**.
The user chose "last `--unit` sticks" and "lbs, never ask, until a unit is
set" during clarification; keeping it separate from the display mode, the
notice line and `edit --unit` not changing the default were Claude's choices.
