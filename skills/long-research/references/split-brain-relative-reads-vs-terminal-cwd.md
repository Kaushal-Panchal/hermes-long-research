# Split-brain: relative `read_file` content vs terminal cwd

Use this when a TICK MODE session shows a contradictory mix such as:

- relative `read_file('goal.md')` / `report.md` / `sources.md` / `log.md` returning the *intended* project contents;
- but `terminal` reports `pwd` inside a different active research folder;
- and `readlink -f goal.md` / `report.md` resolves to that other folder.

This means **tool context is ambiguous**. Do not treat either signal as sufficient on its own.

## Fast recovery

1. Keep the earlier relative-file contents as *clues*, not proof.
2. Search `$HOME/LongResearches/active/` for a distinctive phrase from the intended `goal.md` (company codename, product name, central question).
3. If multiple folders match, inspect the freshest `log.md` / `last_tick_at` first.
4. Re-anchor to the winning folder with **absolute paths** for all subsequent reads/writes.
5. Absolute-path re-reads may return Hermes dedup responses like `unchanged`; that is acceptable once the path itself is verified.
6. After the re-anchor, apply the normal status gate. If the workspace is already `done` / `idle` / `blocked`, return `[SILENT]` and stop.

## Why this matters

A shell-relative path is anchored to the terminal's cwd, while Hermes file tools may still surface the intended workspace from earlier tool context. In that split-brain state, blindly trusting `pwd` or blindly trusting the first plausible relative read can send later edits to the wrong research folder.

## Session pattern that prompted this note

- `read_file(goal.md)` surfaced the intended sprint's contents.
- `terminal` showed `pwd` in a different active research folder, e.g. `$HOME/LongResearches/active/another-topic`.
- `search_files` over `goal.md` markers found multiple related workspaces.
- The correct workspace was selected by matching the distinctive goal phrase and fresher `last_tick_at`.
- Absolute-path re-reads returned `unchanged`, confirming there was nothing new to fetch before the status gate.
