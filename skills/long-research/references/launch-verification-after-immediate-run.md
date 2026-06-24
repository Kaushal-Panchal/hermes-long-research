# Launch verification after immediate cron run

Use this when LAUNCH MODE creates or updates a long-research cron job and then calls `cronjob(action="run", job_id=...)` to start the first tick immediately.

## Observed behavior

The immediate `run` call can succeed while job metadata still looks stale for a short window:
- `last_run_at` may still be null immediately after the call.
- `last_status` may still be null immediately after the call.
- `next_run_at` may not yet be a useful proof that the first tick actually touched the workspace.

This is not, by itself, a launch failure.

## Preferred verification pattern

After scheduling and triggering the immediate run:
1. Verify the workspace `log.md` control block is `status: active` with the intended `started_at` and `stop_time`.
2. Verify the cron job exists and points at the intended workspace.
3. If you need evidence that the first tick has begun, check durable workspace artifacts after a short delay rather than over-interpreting synchronous `run` metadata.
4. Tell the user the sprint is live based on the durable launch state even if `last_run_at` has not populated yet.

## Reporting rule

Do not emit a generic failure/refusal just because the immediate run response lacks populated `last_run_at` / `last_status`. Base the user-facing status on durable evidence in the workspace and cron registry.