# Research Goal

## Topic
Self-hosting open-source LLMs for a small team: is it worth it vs. paying per-token APIs?

## Primary objective
Decide whether a 10-person startup should self-host an open-weight model on its own GPUs or
keep using a hosted API, on a 12-month total-cost and operational-burden basis.

## Background / facts to hold in view
- ~10 engineers, moderate daily LLM usage (coding + internal tools).
- Currently on a hosted API, spend ~$1.5k/month and rising.
- One engineer has light MLOps experience; no dedicated infra team.
- Cloud GPU and owned-hardware both on the table.

## Specific questions to answer
1. Break-even point: at what monthly token volume does self-hosting beat API pricing?
2. Realistic total cost of self-hosting (GPUs, power, ops time, model updates), not just sticker price.
3. Quality gap between current open-weight models and the hosted API for this team's tasks.
4. Operational risks: uptime, on-call burden, security, model/version maintenance.
5. Hybrid options (self-host cheap/bulk, API for hard tasks) — viable?

## Working method
- Real pricing and benchmark numbers with dates and sources, not vibes.
- Separate hard costs from soft costs (engineer time).
- Prefer primary sources (provider pricing pages, model cards, vendor docs).
- Say plainly where evidence is thin.

## Deliverables expected
A decision-useful report: a cost model, the break-even analysis, a quality assessment, a risk
list, and a clear recommendation with the conditions under which it flips.

## Final report structure
1. Executive summary + recommendation
2. Cost model (self-host vs API, 12-month)
3. Break-even analysis
4. Quality comparison
5. Operational risk assessment
6. Hybrid options
7. Open questions / next steps
