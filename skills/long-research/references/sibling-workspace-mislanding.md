# Sibling-workspace mislanding

Use this when a cron tick lands inside the wrong research folder under `active/`.

## Symptom pattern
- Relative reads for `goal.md`, `report.md`, `sources.md`, and `log.md` all fail with file-not-found.
- `pwd` / `terminal` resolves to a **different** research folder under `$HOME/LongResearches/active/`.
- Multiple candidate workspaces exist, often all already terminal (`done` / `idle` / `blocked`).

## Fast recovery
1. Do **not** keep retrying relative reads.
2. Enumerate candidate `goal.md` and `log.md` files under `$HOME/LongResearches/active/`.
3. Read the top of each `log.md` first and compare `status` plus `last_tick_at` / recent activity.
4. Pick the best candidate using the freshest `last_tick_at` / log recency heuristic, then confirm with the matching `goal.md`.
5. Re-anchor every subsequent read/write to **absolute paths** in that workspace.
6. Verify that `goal.md`, `report.md`, `sources.md`, and `log.md` all resolve inside the same absolute directory before doing anything else.
7. If the verified workspace is non-active (`done`, `idle`, `blocked`), stop immediately with `[SILENT]` rather than exploring sibling workspaces further.

## Why this matters
A mislanded tick can start in a sibling active workspace even though the invoked sprint is elsewhere. The safe pattern is: inspect candidate `log.md` headers first, verify one authoritative absolute workspace, then let the status gate decide whether to proceed.
