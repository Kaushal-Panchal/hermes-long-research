---
name: long-research
description: Run a time-boxed autonomous research sprint. Trigger when the user wants to research a topic over time — "research <topic> for <duration>", "do a long research on <X>", "start a 2h research run", or just "start" after a goal has been prepared — and when a cron tick invokes this skill in TICK MODE. The skill scaffolds the project folder itself and refuses to launch until goal.md is actually filled in. Externalizes the clock via a recurring cron job so the sprint stops on real wall-clock time instead of the model guessing when it is done.
version: 1.0.0
metadata:
  hermes:
    tags: [research, cron, automation]
    category: research
---

# Long Research

A research sprint runs as many short cron ticks, not one long live session. Each tick
checks the real system clock, does ONE focused increment, checkpoints to disk, and exits.
The sprint ends when wall-clock time passes the recorded `stop_time`. This is what makes
time enforcement reliable — the model never has to "feel" how long two hours is.

The workspace lives under `$HOME/LongResearches/` (the cloned repo directory). Each research is
one folder (usually under `active/`) holding five files.

> **Resolve the root to an absolute path first.** Cron `workdir` and file tools need a real
> absolute path, not the literal string `$HOME`. At the start of LAUNCH/TICK, run `echo $HOME`
> (or `realpath ~/LongResearches`) once and use that absolute path (e.g. `/home/you/LongResearches`)
> everywhere below. The docs write `$HOME/LongResearches` for portability; you must expand it.

Each research folder holds five files:

- `goal.md` — what to research. The user writes this; you never invent it.
- `plan.md` — the research plan: a ranked checklist of concrete questions with per-question
  status (`[ ] open` / `[x] done` / `[v] verified` / `[!] unsupported`). The agent builds and
  grows this; it drives what each tick works on and prevents overlap. The user does not edit it.
- `report.md` — the living deliverable you grow and finally polish.
- `sources.md` — append-only citation log.
- `log.md` — has a `control` block (HTML comment) at the top + tick checkpoints below.

The `control` block is the source of truth:

```
<!-- control
status: idle | active | done | blocked
started_at: <ISO 8601 UTC>
stop_time: <ISO 8601 UTC>
last_tick_at: <ISO 8601 UTC>
tick_interval_minutes: 15
-->
```

Reference notes for recurring edge cases live in `references/tick-mode-fallbacks.md`.
Additional concrete examples: `references/mislanded-terminal-workspace.md` documents the recovery path when a tick lands outside the workspace, all initial relative core-file reads fail, and the best candidate workspace is already terminal/non-active. `references/ambiguous-cross-project-match.md` covers the variant where a distinctive goal phrase matches multiple related workspaces and the safest fast disambiguator is freshest `last_tick_at` / `log.md` recency. `references/split-brain-relative-reads-vs-terminal-cwd.md` covers the nastier split-brain case where relative `read_file` calls surface the intended workspace contents while `terminal` / `readlink -f` still resolve inside a different active research folder. `references/sibling-workspace-mislanding.md` covers the variant where the tick actually lands inside a sibling research workspace, all initial relative core-file reads fail, and the fastest safe recovery is to inspect candidate `log.md` headers first, re-anchor to one absolute workspace, then let the status gate win.

## When to Use

- **LAUNCH MODE** — the user wants to start a research run. This covers both:
  - first contact: "research <topic> for 2h", "do a long research on <X>" — no folder yet.
  - resuming after filling the goal: "start", "go", "run it".
  You are in an interactive chat session.
- **TICK MODE** — a cron job invokes this skill with a prompt that says "TICK MODE". You are
  in a fresh isolated session whose working directory is already the research folder.

Decide which mode you are in from the prompt. If it says TICK MODE (or you were started by
cron), it is TICK. Otherwise it is LAUNCH.

Do NOT interview the user. You never write the goal for them — the user authors `goal.md`.
Your job in LAUNCH mode is only: scaffold the folder, gate on whether the goal is filled,
and (once it is) schedule the run.

---

## LAUNCH MODE Procedure

1. **Resolve the project folder.**
   - If the user named a folder/path, use it (expand `active/my-topic` →
     `$HOME/LongResearches/active/my-topic`).
   - Otherwise derive a kebab-case slug from the topic (e.g. "EU AI Act impact" →
     `eu-ai-act-impact`) and use `active/<slug>`. Briefly confirm the slug with the user.

2. **Scaffold if missing.** If the folder does not exist, create it by copying the template:
   `cp -r $HOME/LongResearches/template $HOME/LongResearches/active/<slug>`.
   This gives a fresh `goal.md` (still the unfilled template), `report.md`, `sources.md`, `log.md`.
   If the folder already exists, do not overwrite it — reuse it.

3. **Readiness gate on `goal.md`.** Read `active/<slug>/goal.md`. It is **NOT READY** if any of:
   - it contains the literal token `UNFILLED`, or
   - its content is under ~400 characters, or
   - it still contains template placeholder tokens like `<one-line title`, `<the central question`,
     or `<section>`.

   If NOT READY: do **not** start. Tell the user the exact path to `goal.md`, that the folder is
   created and waiting, and to fill it in then say "start". STOP here. Do not research, do not
   schedule cron, do not write the goal yourself.

   If READY: continue to step 4.

4. **Confirm duration.** Use the duration already established in the current chat for this sprint.
   If the user first said something like "research <topic> for 30 minutes" and later only says
   "start", carry forward that previously specified duration instead of re-asking. Ask only if the
   conversation truly never established a duration for this launch. This single number is the only
   thing you must not guess; everything else proceeds without questions.

5. **Get the real clock.** Run `date -u +%Y-%m-%dT%H:%M:%SZ` in the terminal. This is `started_at`.

6. **Compute `stop_time`.** Add the requested duration to `started_at`
   (e.g. `date -u -d '+2 hours' +%Y-%m-%dT%H:%M:%SZ`). Never compute time in your head.

7. **Write the control block** at the top of `log.md`:
   - `status: active`
   - `started_at`, `stop_time` as computed
   - `last_tick_at:` (leave blank)
   - `tick_interval_minutes: 15`
   Append a "Sprint started" checkpoint under `## Checkpoints` (start time, stop time, duration).

8. **Prune stale jobs.** Call `cronjob(action="list")`. If a `longresearch-<slug>` job already
   exists for THIS folder, reuse/edit it instead of creating a duplicate. Remove any
   `longresearch-*` job whose project `log.md` shows `status: done` (cleanup of finished runs).
   (Cron management only works here in LAUNCH mode — cron ticks cannot manage cron.)

9. **Create the recurring job:**
   ```python
   cronjob(
       action="create",
       name="longresearch-<slug>",
       schedule="every 15m",
       workdir="$HOME/LongResearches/active/<slug>",
       skills=["long-research"],
       deliver="local",
       prompt="TICK MODE. Run the long-research skill's TICK MODE procedure exactly. "
              "The current working directory is the research folder. Read its goal.md, "
              "report.md, sources.md, log.md, then continue or finalize based on the control block."
   )
   ```

10. **Start the loop immediately after scheduling.** After creating or updating the recurring job,
    run one tick right away with `cronjob(action="run", job_id=...)` so the workspace starts making
    progress now rather than waiting for the first scheduled interval.

11. **Verify launch from durable state, not just the run call.** The immediate `cronjob(action="run")`
    response may arrive before `last_run_at` / `last_status` are populated. Do a quick verification
    pass instead of over-reading that synchronous metadata:
    - confirm `log.md` shows the intended active control block (`status: active`, correct `started_at`,
      correct future `stop_time`)
    - confirm the cron job exists and points at the intended workspace
    - if needed, wait briefly and check whether workspace artifacts begin changing, rather than
      treating blank `last_run_at` as a failed launch
    - do **not** keep calling `cronjob(action="run")` again just because `last_run_at` is still null
      or `plan.md` still looks like the template a few seconds later; the first immediate run can be
      accepted before either metadata or workspace artifacts visibly update

    Then tell the user the sprint is live: folder, stop time, cadence, job name. Remind them the
    **Hermes gateway must be running** in WSL or no scheduled tick fires (`hermes gateway status`).

Reference: `references/launch-verification-after-immediate-run.md`.

---

## TICK MODE Procedure

You are in a fresh session. Working directory is the research folder.

1. **Read everything first:** `goal.md`, `report.md`, `sources.md`, `log.md`. Parse the `control` block.
   - Read these workspace files **sequentially in the same agent context** before doing anything else.
   - Do **not** use parallel wrappers / sibling subagents for the initial file reads or for later workspace-file edits. In practice this can cross-contaminate research folders or create sibling-write races, which is especially dangerous because `report.md`, `sources.md`, and `log.md` are the sprint state.
   - **Immediately resolve and verify the workspace root before any research or writes.** After the first sequential reads, confirm that the four files you read all belong to the same directory (for example by resolving their absolute paths) and then switch to **absolute paths for every subsequent edit**. If any signal suggests path drift — e.g. tool-reported cwd disagrees with the file contents you just read, a sibling-write warning mentions a different folder, **or the initial relative reads for `goal.md` / `report.md` / `sources.md` / `log.md` fail entirely** — stop using relative paths, re-read the core files from the intended absolute workspace path, and only continue once the workspace identity is consistent. **Do not treat plausible relative-path reads as proof that the workspace is correct**: in at least one real tick, relative `read_file` calls surfaced the intended research contents while `pwd`/`readlink -f` resolved to a different active research folder. When that split-brain symptom appears, treat the workspace as ambiguous, locate the intended folder from unique `goal.md` markers if needed, then re-anchor every subsequent read/write to that absolute directory. **Concrete fallbacks:**
     - if the tick lands in an unrelated cwd (for example the Hermes repo) while the relative file reads look plausible, search `$HOME/LongResearches/active/` for a distinctive `goal.md` phrase (company codename, product name, central question), pick the matching folder, and continue only from that absolute workspace; this same recovery applies when `terminal` claims you are already inside a *different* active research folder, because shell-resolved relative paths may still point at the wrong project even when `read_file` looked right.
     - if the initial relative core-file reads all fail with file-not-found errors, **do not keep retrying the same relative reads**; immediately enumerate `$HOME/LongResearches/active/*/{goal,log}.md`, inspect candidate `log.md` control blocks / mtimes, and re-anchor to the folder whose contents best match the invoked sprint before doing any writes. In practice, the fastest first heuristic is usually: inspect the folders with the freshest `log.md` mtime / `last_tick_at` first, then confirm by reading the matching `goal.md`.
     - if the tick prompt gives no unique topic clue and **all candidate workspaces you can find are already terminal/non-active** (`done`, `idle`, or `blocked`), you do **not** need to spend the tick trying to prove which inactive workspace was intended before gating. Re-anchor to the best candidate using the freshest `last_tick_at` / `log.md` mtime heuristic, verify the four core files belong to that same absolute directory, then apply the normal status gate and return `[SILENT]`. This handles mislanded cron ticks where cwd is wrong but there is nothing left to advance anyway. In this branch, once the freshest candidate passes the consistency check and the status gate fires, **stop** — do not fan out into full reads of every other inactive workspace just to get perfect attribution.
   After the absolute re-anchor succeeds, do not waste the tick repeatedly re-reading unchanged core files just to satisfy the earlier ambiguity; treat the verified absolute-path reads as authoritative unless one of the files was edited. If absolute-path re-reads return a tool-level dedup/"unchanged" response, that is fine — the important verification is the resolved absolute path, and all subsequent edits must stay anchored to that absolute workspace. In Hermes tool practice, repeated `read_file` calls on the same unchanged path can escalate from dedup/"unchanged" into a hard BLOCKED response for that file/region. That is not new evidence of corruption; it is a cue to stop re-reading and continue from the earlier verified content.
   - If `goal.md` explicitly tells you to read an additional local brief/input file, try to read it immediately after the core four files. If that extra file is missing, do **not** stall or invent its contents: note the absence in the tick checkpoint/log and continue with the available workspace.

2. **Gate on status.** If `status` is `idle`, `done`, or `blocked`, do NOT research. Output exactly
   `[SILENT]` and stop. (This makes the job a cheap no-op when no sprint is active — the job keeps
   existing but burns almost nothing.) After any workspace re-anchor/disambiguation, this status gate wins immediately: once one authoritative absolute workspace is verified as non-active, stop there instead of spending the tick comparing sibling workspaces, re-reading other reports, or trying to perfect attribution.

3. **Get the real clock:** `date -u +%Y-%m-%dT%H:%M:%SZ`. Compare to `stop_time`.

4. **Pick this tick's ROLE, then do that ONE job.** Decide in this exact order — the first match wins.
   Every role is one bounded increment: do it, append a checkpoint to `log.md`, update
   `last_tick_at`, then exit. Research is always **sequential** (no parallel research subagents —
   they fail with broken-pipe errors here).

   **(a) `plan.md` missing, empty, or still template → PLAN.**
   - Decompose `goal.md` into a ranked checklist of concrete, answerable research questions
     (see the `plan.md` format below). Order by importance to `goal.md`'s primary objective.
   - Write `plan.md`. Do minimal/no web research this tick — just frame the questions.
   - Output `[SILENT]`.

   **(b) `now >= stop_time` → FINALIZE.** (the ONLY condition that ends a sprint — a fully-covered
   plan never ends it early; see EXPAND.)
   - Polish `report.md` into the full structure declared in `goal.md` (exec summary first, all
     sections, open questions). Integrate everything gathered. Do **not** add new external research.
   - Append a **self-grade** block to the end of `report.md`:
     ```
     ## Quality self-grade
     factual_accuracy: 0.0–1.0 | citation_accuracy: 0.0–1.0 | coverage: 0.0–1.0 | source_quality: 0.0–1.0
     verdict: PASS | FAIL
     weakest / unverified claims: ...
     still-thin questions: ...
     ```
   - **Run cost.** Read every `- tick usage:` line in `log.md` (written automatically by the
     `long-research-cost` plugin). Sum `in` / `out` / `total` tokens, and `cost` where present
     (skip `n/a`). Append a block to the end of `report.md`:
     ```
     ## Run cost
     ticks logged: <count> | input: <sum> | output: <sum> | total: <sum> tokens | cost: $<sum or n/a>
     (note: this FINALIZE tick's own usage is logged after this sum, so it isn't included)
     ```
     If there are zero `- tick usage:` lines, write `## Run cost: not logged (plugin not enabled)`
     instead of inventing numbers.
   - Append an end-of-sprint checkpoint to `log.md`; set `status: done` and `last_tick_at: <now>`.
   - Output a short plain summary (NOT silent). Do not try to delete the cron job — you cannot from a
     tick; it no-ops on future ticks because status is now `done`.

   **(c) `plan.md` has `[ ] open` questions → RESEARCH (one question).**
   - Take the top `[ ] open` question. Search **broad → narrow**: short broad query, see what
     exists, then narrow. After each result, briefly judge quality + spot gaps before the next query.
   - **Source quality:** prefer primary / official / authoritative sources over SEO content farms
     and low-quality secondary pages.
   - Append every source to `sources.md` immediately (URL + one-line note + date). **Ground every
     claim** you write in `report.md` to a source that's in `sources.md` — no unsourced claims.
   - Integrate findings into the correct `report.md` section. Mark the question `[x] done` in `plan.md`.
   - Checkpoint should note: what you added, the single strongest signal, next open question.
   - Output `[SILENT]`.

   **(d) all questions `[x] done` but load-bearing claims not yet verified → VERIFY.**
   - Take the strongest / most decision-critical claims in `report.md`. Decompose each into atomic
     statements. Re-check each against its cited source **in isolation** (chain-of-verification).
   - Mark verified claims' questions `[v] verified` in `plan.md`; for any claim that fails, flag it
     `[!] unsupported` and fix or qualify it in `report.md`.
   - Output `[SILENT]`.

   **(e) all questions `[x] done` + `[v] verified`, and `now < stop_time` → EXPAND.**
   - Grow `plan.md` with the next layer of `[ ] open` questions: deeper sub-questions, adjacent
     angles, edge cases, and explicitly **disconfirming evidence** for the current conclusions.
   - Stay inside `goal.md`'s scope. Favor gaps and counter-evidence over restating known findings.
   - Do no research this tick beyond framing — the next tick resumes RESEARCH on the new questions.
   - Output `[SILENT]`.

   This loop (RESEARCH → VERIFY → EXPAND → RESEARCH …) keeps every tick busy with new ground until
   `stop_time`. Time is the budget; fill it with widening, verified coverage.

### `plan.md` format

```markdown
# Research Plan

> Agent-owned. Drives each tick. The user does not edit this.

## Source rule
Prefer primary / official / authoritative sources over SEO content farms and weak secondary pages.

## Questions
- [ ] open      | Q1: <concrete answerable question tied to the goal's objective>
- [x] done      | Q2: <question> — covered in report.md §<section>
- [v] verified  | Q3: <question> — claims checked against sources
- [!] unsupported | Q4: <question> — flagged, claim could not be grounded
```

Status legend: `[ ] open` not yet researched · `[x] done` researched + written · `[v] verified`
claims re-checked against sources · `[!] unsupported` a claim failed verification (fix or qualify).

## Rules (both modes)

- **Never finalize early** because the synthesis already feels complete, or because `plan.md` is
  fully covered. Elapsed wall-clock (`now >= stop_time`) is the ONLY thing that ends a sprint. If the
  plan is exhausted and time remains, EXPAND it (deeper/adjacent/disconfirming questions) and keep going.
- **Source quality:** prefer primary / official / authoritative sources over SEO content farms and
  low-quality secondary pages.
- **Grounding:** every claim in `report.md` must trace to a source logged in `sources.md`. No
  unsourced assertions. If you cannot source it, mark it as an assumption/open question, not a fact.
- **Sequential research only.** No research subagents.
- **Only touch files inside this workspace folder.** No unrelated edits.
- Once the workspace folder is known, prefer **absolute paths for writes/patches** to `report.md`,
  `sources.md`, and `log.md`. Relative-path edits are easier to mis-target if tool context or cwd
  drifts across research folders.
- **Always compute time with `date`**, never by estimation.
- Follow `goal.md`'s own instructions about what is ground truth vs what to stress-test.
- If web/browser collection is flaky, fall back to plain search + reading the source directly +
  logging it immediately. Partial progress logged beats perfect progress lost.
- If `web_extract` is unavailable because the configured backend is search-only (for example,
  a DDGS-only extractor setup), do not stall the tick. Read the source directly with another
  available tool (browser or terminal HTTP fetch), capture the specific quoted evidence you used,
  and append the source to `sources.md` before moving on. Before scraping raw HTML, check whether
  the docs site exposes a plain-text endpoint such as `llms.txt`, `llms-full.txt`, or a `.md`
  version of the page — these are often faster and cleaner than browser rendering during a bounded
  tick. For terminal HTTP fallbacks, prefer a **dependency-light fetch** that does not assume
  BeautifulSoup/markdown-conversion packages are installed: fetch the page, strip `<script>` /
  `<style>` blocks and HTML tags, normalize text, then scan for the relevant headings/keywords.
  See `references/tick-mode-fallbacks.md`.
- When `report.md` is large, prefer **targeted section patches** during active ticks instead of
  whole-file rewrites. If you only read a paginated slice of the file (`offset`/`limit`), re-read
  the full file before any broad overwrite; otherwise patch the specific section you are updating.
- For JS-heavy docs sites, try low-friction source-reading fallbacks before spending the whole tick
  fighting the renderer: check for `llms.txt`, `.md` alternates, or `<link rel="alternate"
  type="text/markdown">`; if the page renders in-browser but extraction is awkward, read the main
  article text via browser console (`document.querySelector('main article, article, main')?.innerText`).
  If that is too sparse, fall back to `document.body.innerText`. When browser navigation redirects to
  a canonical docs/blog URL, cite the **resolved URL you actually read**, not just the pre-redirect
  search result. For long FAQ/docs pages, it is often faster to jump to the relevant anchor/section
  first and then extract a bounded snippet around that heading from `document.body.innerText` or the
  section node. Log the source immediately once you have the key evidence. See
  `references/tick-mode-fallbacks.md`.

## Pitfalls

- A duplicate cron job per folder → always list and reuse in LAUNCH mode.
- Editing the control block by hand mid-sprint changes behavior on the next tick (intended: set
  `status: done` to abort early, or change `stop_time` to extend/shorten).
- Parallel file reads/writes in TICK MODE (including multi-tool parallel wrappers that run sibling workers) can mix up workspace context or race on `report.md` / `sources.md` / `log.md` → keep workspace-state reads and edits in one sequential context.
- Split-brain workspace verification hazard: `read_file` may show the intended project while `terminal` / `pwd` / `readlink -f` still resolve a different active research folder. Treat that as ambiguity, not confirmation; locate the intended workspace from `goal.md` markers plus freshest `last_tick_at` / `log.md` recency, then re-anchor all later reads/writes to absolute paths there.
- Large-file partial-read hazard: if `report.md` was only read via paginated slices, broad rewrites are easy to mis-target and toolchains may warn that you only saw part of the file. During active ticks, prefer section-level patches or re-read the whole file before a full rewrite.
- Gateway not running → ticks silently never fire. Check `hermes gateway status`.

## Verification

- After LAUNCH: `cronjob(action="list")` shows the `longresearch-<topic>` job; `log.md` control
  block shows `status: active` with a future `stop_time`.
- First tick: `plan.md` is populated with a ranked question checklist (no longer the template).
- During a run: `plan.md` questions flip `[ ] open` → `[x] done` → `[v] verified`; new checkpoints
  appear in `log.md`; `sources.md` grows; `report.md` grows. When the plan is fully covered before
  `stop_time`, `plan.md` gains new EXPAND questions instead of the run stopping.
- At stop_time: `log.md` shows `status: done`, `report.md` is finalized and ends with a
  `## Quality self-grade` block.
