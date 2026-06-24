# Tick-mode fallbacks and guardrails

Concise notes from real cron-tick runs.

## Missing local brief referenced by `goal.md`

If `goal.md` says to read an additional workspace file first (for example `brief-original.md`), try to read it immediately after the core four files.

If the file is missing:
- do not block the tick
- do not invent what it might have said
- log the absence in `log.md`
- continue the increment using the available workspace state

Reason: the sprint state still lives in `goal.md`, `report.md`, `sources.md`, and `log.md`; a missing optional/local brief should degrade gracefully.

## Search-only extraction backend fallback

When `web_extract` is unavailable because the backend is search-only:
1. use `web_search` to find the source
2. before scraping raw HTML, probe for cleaner plain-text docs endpoints such as `llms.txt`, `llms-full.txt`, or a page-level `.md` variant
3. open the source directly in the browser or fetch it by HTTP
4. capture the specific evidence you actually relied on
5. append the source to `sources.md` immediately
6. only then synthesize into `report.md`

### Plain-text docs endpoint shortcut

When a vendor docs site exposes LLM-oriented plaintext or markdown views, prefer those over raw HTML cleanup:
- `llms-full.txt` is often richer than `llms.txt` and may already bundle the surrounding context you need
- some docs stacks support appending `.md` to a normal docs URL for a clean markdown view
- cite the exact resolved plaintext/markdown endpoint you actually read, not just the search-result landing page

Why this matters: these endpoints are cheap to fetch, work well inside cron-bounded ticks, and often avoid the need for browser rendering or manual HTML stripping entirely.

### Dependency-light terminal fetch pattern

If browser extraction is awkward and you only need quoted evidence from a docs page, prefer a terminal HTTP fetch that does **not** assume extra parsing libraries are installed:
- fetch the page with a basic HTTP client
- strip `<script>` / `<style>` blocks
- strip HTML tags and unescape entities
- normalize whitespace
- scan the resulting text for the target heading/keywords

Why this matters: cron ticks are time-boxed, and a simple text extraction pass is often enough to recover the exact line you need without spending the whole tick fighting rendering or missing packages.

## JS-heavy docs / FAQ pages

When the answer is buried in a long docs or FAQ page:
- jump to the relevant anchor/section if possible
- then extract a bounded snippet around that heading from the section node or `document.body.innerText`
- avoid wasting a full tick fighting whole-page extraction if one quoted passage answers the question

### Browser-console text extraction recipe

If `web_extract` is unavailable and the page renders in-browser, prefer these low-friction probes before fighting the whole DOM:
- `document.querySelector('main article, article, main')?.innerText`
- if that is too sparse, fall back to `document.body.innerText`
- if the site redirects to a canonical URL, log the **resolved** page URL you actually read rather than the pre-redirect search hit

Why this matters: some docs/blog stacks render the content cleanly in the browser even when extraction backends cannot read it. Capturing the canonical resolved URL also avoids noisy source logs where the cited URL does not match the page text you actually used.

## All four core relative reads fail at tick start

If `goal.md`, `report.md`, `sources.md`, and `log.md` all fail immediately with file-not-found errors:
1. do **not** keep retrying the same relative reads
2. treat the cwd as suspect or unrelated
3. enumerate candidate workspaces under `$HOME/LongResearches/active/`
4. inspect `log.md` control blocks and mtimes first to narrow candidates quickly
5. prioritize the folders with the freshest `log.md` mtime or `last_tick_at`
6. confirm the best candidate by reading its `goal.md`
7. once confirmed, switch all subsequent reads/writes to absolute paths in that workspace

Why this matters: repeating the same four relative reads tends to burn the bounded tick and can trigger tool-loop warnings, while `log.md` freshness plus the control block usually identifies the active sprint quickly.

## Path discipline for workspace writes

After identifying the research folder, use absolute paths for writes to `report.md`, `sources.md`, and `log.md`.

Why: cron/tick work is sensitive to cross-folder mistakes, and absolute paths reduce the chance of mis-targeted edits if a tool resolves relative paths from an unexpected working directory.
