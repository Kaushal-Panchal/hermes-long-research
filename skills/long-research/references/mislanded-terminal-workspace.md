# Mislanded tick with all local workspace files missing, but only terminal candidates exist

Use this when a cron tick claims the current working directory is the research folder, but the initial sequential `read_file` calls for `goal.md`, `report.md`, `sources.md`, and `log.md` all fail with file-not-found errors.

## Real pattern this note captures
- Relative reads failed from a non-workspace cwd (the Hermes repo).
- Enumerating `$HOME/LongResearches/active/*/{goal,log}.md` found several candidate workspaces.
- The freshest candidate by `last_tick_at` / `log.md` mtime was already `status: done`.
- Re-anchoring to that absolute folder, verifying the four core files all shared the same parent directory, and checking any goal-requested local brief file was enough to confirm identity.
- Because the control block was terminal, the correct tick output was exactly `[SILENT]` with no research and no writes.

## Practical heuristic
1. If all four relative core-file reads fail, stop retrying relative paths.
2. Inspect candidate active research folders by freshest `last_tick_at` first, then `log.md` mtime.
3. If every plausible candidate is already `done`, `idle`, or `blocked`, pick the best candidate, verify the absolute paths for the four core files, and apply the normal status gate.
4. Do not burn the tick trying to prove a more specific topic match once every candidate is terminal/non-active.
5. If `goal.md` references an extra local file (for example `brief-original.md`), read it after the re-anchor when present, but do not treat its absence as permission to invent content.

## Why this matters
The failure mode is not "research blocked"; it is usually just cwd drift. The correct recovery is to re-anchor quickly, verify one absolute workspace, and then let the control block decide whether the tick should no-op.