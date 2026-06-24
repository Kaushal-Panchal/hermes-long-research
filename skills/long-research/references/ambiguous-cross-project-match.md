# Ambiguous cross-project goal-match during TICK MODE

Use this when a mislanded cron tick reads plausible workspace files for one research sprint, but `pwd` / `readlink -f` resolve to a different active research folder and a distinctive phrase search matches **multiple** related workspaces.

## Symptom pattern
- Relative `read_file(goal.md)` / `report.md` / `sources.md` / `log.md` surface the intended research contents.
- Terminal `pwd` / `readlink -f` points at a different active research folder.
- Searching `$HOME/LongResearches/active/*/goal.md` for a distinctive phrase returns multiple siblings (for example, two folders for closely related topics).
- The tick prompt itself does not contain enough topic detail to prove which sibling was invoked.

## Fast recovery
1. Stop trusting relative-path reads; switch to absolute candidate paths only.
2. For each matching candidate, inspect `log.md` control-block recency first (`last_tick_at`, then `log.md` mtime if needed).
3. Read the freshest candidate's `log.md` control block before spending time comparing full reports.
4. If that freshest candidate is already terminal / non-active (`done`, `idle`, or `blocked`), verify the four core files all resolve inside that same absolute directory and then apply the normal status gate.
5. Return `[SILENT]` once the verified absolute workspace is non-active. Do **not** burn the tick trying to prove which older sibling was intended when there is nothing left to advance anyway.

## Why this matters
When several related sprints reuse the same company/product phrases, phrase search alone may not uniquely identify the workspace. Ranking by freshest control-block activity is the quickest safe disambiguator, especially for no-op ticks after finalization.
