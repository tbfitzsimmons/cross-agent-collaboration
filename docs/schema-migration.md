# Reader-first schema migration and operating evidence

Schema 3 is **opt-in** via `feed_schema: 3` in `config.json`; default remains 2. A merge of compaction code must not activate a new reader contract. The canonical operational prompt lives in `docs/reader-operational.md`; its Git blob revision is included as `revisions.reader_prompt`, independently of README or setup notes. A revision notice is not permission to edit another account's task.

## Coordinated gate

1. Agree on the exact target versions, rollback and schedule. Record one rollout decision, not separate copies per area.
2. Install an approved **schema-2-and-3-compatible** reader on every participating account. Test schema 2 live and schema 3 with a fictional fixture. Verify saved task configuration separately from actual scheduled execution, link behavior, delivery location and phone notification.
3. Record both parties' readiness and explicit publisher-activation approval. Only then change `feed_schema` from 2 to 3. PR review/CI alone does not constitute such approval.
4. Verify schema 3 publication, retained exact links, windows, warnings and at least two independent scheduled reads on each platform. A scheduled timer is never established by a push or manual dispatch.
5. If a reader fails, it may restore its own **last active-schema-compatible** prompt only under existing authorization. Never restore a schema-2-only prompt against schema 3; preserve private routing and record old/restored revision, date, reason, actual result and what remains unverified.

## Boundaries and risk

- The state cursor retains complete event versions separately from the compact feed. Cursor retention is separately bounded (`cursor_max_events`) and a dropped-history watermark is exposed. No historical event reconstruction is promised after trimming, and no distinct historical versions are silently coalesced.
- A feed near its byte budget is informational. Flag **partial coverage** if truncation affects an active reporting window, with explicit retained observations; do not increase routine model input as the first response.
- `checked_at` is the **start of capture**, not proof of Git push completion or consumer delivery. Actual publisher job time/commit and consumer receipts require external evidence; inaccessible or trimmed measurements are **unmeasured**, not success.
- Timer recovery is unresolved until two recovery periods show true `event=schedule` executions AND successful remote state publication. Event-driven, `workflow_run`, manual and push-trigger successes do not substitute. GitHub may delay or drop schedules; no external paid scheduler is introduced.
- A separate production installation reported a 105-minute freshness allowance for a 103-minute earliest recovery candidate. This export retains its own 23-minute allowance and original cadence. Any recovery redesign must change candidate schedules and freshness rules **together**, with explicit tests and hosted evidence, not copy a number.
- Continuous improvement is a **proposed governance process**, not a background optimizer. After seven days' ordinary use, a human-authorized active infrastructure session may review operational evidence and official assistant/GitHub release notes at most weekly, with one coordinator, cross-review, an audit ledger, specific scope and agreed rollback. No new recurring task or autonomous self-mutation is authorized here.

## Evidence ledger — do not fill from unrelated deployments

| Gate | Status |
| --- | --- |
| Local synthetic unit suite | See relevant PR's test log; independent of hosted validation |
| Hosted proposed-code PR CI | Pending until actual checks are observed |
| Trusted main publisher bridge | Pending until merged and workflow event observed |
| Real timer-triggered publisher across two recovery periods | Unverified |
| Configured reader prompts | Unverified on each AI account |
| Actual independent scheduled sessions | Unverified per platform |
| Link destination, phone delivery and model/token usage | Unverified |
| Public code license and final privacy review | Separate owner gate |