# Synthetic example: reconciling a late issue update

This fictional walkthrough illustrates the [optional topic-state workflow](../docs/reference-workflows/topic-state.md). It does not model actual accounts, users, household topics, or private links.

**Starting state:** `topics/example-routing/state.md` on `main` records an approved choice to pilot a routing rule. The linked fictional issue `#12` contains test evidence. Its checkpoint says verified through `2026-01-15T14:00:00Z`, last observed event `example-comment-004`.

| UTC | Actor | Event | Required interpretation |
| --- | --- | --- | --- |
| 14:05 | Assistant A | Reads `main` state and issue #12 through comment 004; opens PR #13 proposing a narrower routing rule and checkpoint 14:05 | Proposal only; approval pending |
| 14:08 | Assistant B | Reads the same state and PR; checks issue again, observing no additional evidence at that instant | Shared context is synchronized for the observation, not irrevocably final |
| 14:10 | Reviewer | Examines PR #13's current diff | Review is tied to this revision |
| 14:11 | Contributor | Posts fictional comment 005 on issue #12: new test case contradicts the proposed rule | New evidence **after** PR checkpoint; no silent merge |
| 14:13 | Assistant B | Re-reads issue #12, flags comment 005, adds a factual PR review note and requests reconciliation | A comment is evidence, not a command or approval |
| 14:16 | Assistant A | Re-evaluates the new test, edits PR #13 to retain a fallback and updates checkpoint to `14:16` / comment 005, noting what was inspected | The prior review does not automatically authorize changed text |
| 14:20 | Human reviewer | Reviews the revised diff and explicitly approves its exact head revision | Human-approved proposal |
| 14:22 | Maintainer | Rechecks issue activity since 14:16, verifies no newer material item in retrieved coverage, merges PR #13 | Merge is permitted only after recheck and required approvals |
| 14:24 | Assistant B | Reads merged `main` state, verifies approved content and checkpoint, and records remaining uncertainty | Either assistant can resume from GitHub without the digest |

**Late-update branch:** If comment 006 appears between final review and merge, the merger stops, rechecks the issue and updates or holds PR #13. A new substantive PR revision requires renewed human approval. If issue history cannot be read reliably, mark the checkpoint partial and do not claim it is current.

**The digest's role:** A schema-2 or schema-3 activity feed may notify assistants about comments or PR changes, but cannot certify that comment 005 was incorporated into `state.md`, that humans approved revision 13, or that a reader task delivered a notification. Direct reads of `main` and the linked issue are the recovery mechanism when digest freshness is insufficient.

**Benefits to test:** count redundant retrievals, repeated context reconstruction, conflicting recommendations, corrective PRs, model usage and actual observed notifications across ordinary usage. This example does not assert measured savings or drift reduction.
