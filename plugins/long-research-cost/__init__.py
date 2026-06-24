"""long-research-cost — log per-tick token usage into each run's log.md.

Registers a `post_llm_call` hook (fires once per turn, after the tool loop).
When a turn runs inside a LongResearches workspace, it appends one usage line
to that workspace's log.md. The long-research skill's FINALIZE role later sums
those lines into a "Run cost" block in report.md.

Design notes:
- No database, no network. Pure local file append.
- Best-effort: any failure is swallowed so the agent loop is never broken.
- Defensive extraction: Hermes/provider may expose usage under different keys
  (input_tokens/output_tokens vs prompt_tokens/completion_tokens) and may or may
  not include a computed cost. We log whatever we can find.
- Workspace resolution: workdir cron jobs export TERMINAL_CWD; we fall back to
  the process cwd. We only write when the path is a LongResearches/active run,
  so normal chats are never touched.
"""

import os
import datetime


def _resolve_workspace():
    for path in (os.environ.get("TERMINAL_CWD"), os.getcwd()):
        if path and "LongResearches" in path and "active" in path:
            return path
    return None


def _extract_usage(conversation_history, kwargs):
    usage = kwargs.get("usage")
    if not usage and conversation_history:
        for msg in reversed(conversation_history):
            if isinstance(msg, dict):
                cand = msg.get("usage") or msg.get("token_usage")
                if cand:
                    usage = cand
                    break
    if not isinstance(usage, dict):
        return None

    def pick(*keys):
        for k in keys:
            v = usage.get(k)
            if v is not None:
                return v
        return None

    inp = pick("input_tokens", "prompt_tokens") or 0
    out = pick("output_tokens", "completion_tokens") or 0
    tot = pick("total_tokens") or (inp + out)
    cost = pick("cost", "total_cost", "cost_usd")
    return inp, out, tot, cost


def _on_post_llm_call(session_id=None, assistant_response=None,
                      conversation_history=None, model=None, platform=None, **kwargs):
    try:
        ws = _resolve_workspace()
        if not ws:
            return
        log_path = os.path.join(ws, "log.md")
        if not os.path.isfile(log_path):
            return
        parsed = _extract_usage(conversation_history, kwargs)
        if not parsed:
            return
        inp, out, tot, cost = parsed
        ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        cost_str = ("$%.4f" % cost) if isinstance(cost, (int, float)) else "n/a"
        line = ("- tick usage: in %s out %s total %s | cost %s | model %s | %s\n"
                % (inp, out, tot, cost_str, model or "?", ts))
        with open(log_path, "a", encoding="utf-8") as fh:
            fh.write(line)
    except Exception:
        pass  # never break the agent loop


def register(ctx):
    ctx.register_hook("post_llm_call", _on_post_llm_call)
