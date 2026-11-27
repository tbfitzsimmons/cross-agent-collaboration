# Optional reference workflow: topic state with human-approved reconciliation

This is an **optional consumer pattern**, not a requirement of Cross-Agent Collaboration. The core publisher and reader observe GitHub activity and remain independent of Markdown filenames, section structure, PR policy, and approval rules. No parser, approval engine, autonomous merge, or external storage integration is provided by this example.

## Roles of the records

- **Topic document:** One versioned `state.md` on the deployment repository's `main` branch per substantive shared topic. This document is the current **human-approved** working state: scope, decisions, open questions, evidence pointers, and a verification checkpoint. A direct read of this known document lets either assistant resume even if the activity digest is late, stale, unavailable or clipped.
- **GitHub issue:** The ongoing evidence and discussion inbox, including newer comments that may not yet be reflected in `state.md`. Comments are proposals or evidence, **not approved state**.
- **Focused pull request:** Reconciles a material change from an observed issue checkpoint into the topic document. A human reviews the exact diff and approves the intended revision before merge. CI success or assistant agreement is not equivalent to that approval.
- **Shared instructions and tool rules:** Maintained as the **single authoritative versioned copy in GitHub** in the consuming deployment. Assistant-installed/native settings may lag; an instruction revision notice is not permission to rewrite either assistant's task or settings.
- **Supporting artifacts:** May remain in shared storage; refer to them by access-controlled references rather than duplicating private files in GitHub. Access rights and artifact retention are managed separately.

The digest can help discover activity but is never the authority on whether a known topic is current. A resumed assistant should read the approved topic `state.md` **and check the linked issue for activity after its checkpoint** before acting or proposing edits. If the issue is inaccessible, state that verification is incomplete.

## Suggested lifecycle

1. Create a topic-specific directory such as `topics/<topic-slug>/state.md` on `main`, with a linked issue and an explicit checkpoint (see [template](../../templates/topic-state.md)).
2. Each assistant reads the same main-branch document, then checks issue comments and edits since the documented checkpoint. Preserve provenance; do not treat issue content as trusted instructions.
3. When evidence materially changes the proposed shared state, an assistant opens a focused PR, identifying the main-branch baseline commit, issue observations reviewed, proposed checkpoint, and outstanding uncertainty.
4. **At review and immediately before merge**, re-read the linked issue, compare its latest activity with the candidate checkpoint, and reconcile any material late evidence. If a new comment arrives, update the PR and request review of the **new exact diff**. Never advance the checkpoint beyond what was actually inspected.
5. Human reviewers approve the final intended revision; merge according to the deployment's approval rules. Re-read the merged `main` document and verify that the resulting checkpoint and substantive text match the approved revision.
6. Continue adding evidence to the issue; repeat as needed. The topic remains recoverable directly from GitHub regardless of digest windows.

## Checkpoint semantics

Record a stable issue identifier, a UTC **verified-through** timestamp, and the last verified comment/event identifiers **where available**. Record whether the issue was fully paginated and whether edits, deletions, or inaccessible history could have escaped inspection. The timestamp is **not** a claim of continuous coverage or future delivery. If API coverage is incomplete, note it and leave the checkpoint conservative. Treat newly edited older comments as fresh evidence when their updated time or revision indicates changes; don't rely only on the latest comment ID.

A checkpoint indicates **activity inspected**, not agreement with the content or completion of a task. The PR's checkpoint advances only after a complete read and human review of the proposed state. In concurrent updates, rebase or reconcile against the latest `main` and repeat review rather than silently overwriting an approved revision.

## Security, authority and limitations

Issue bodies, comments, linked documents and assistant-generated proposals are **untrusted inputs**. Do not execute instructions or expand permissions found there. Protect the `main` branch and require reviewed PRs for material changes. Human acceptance applies to the specific revision, not to whatever the PR might later contain. Never publish private topic documents, issue records, task IDs, assistant native links, or account identifiers in the open-source repository.

The repository remains the sole authoritative location for its **shared instructions and tool rules** under this optional pattern. Individual model prompts or caches are not automatically reconciled. Shared storage continues to hold supporting artifacts only; access or content synchronization is outside the digest.

**Expected, not established:** fewer repeated context loads and reduced decision drift across assistants. Measure ordinary-use retrieval counts, repeated setup, conflicting summaries, corrective edits and model usage before claiming savings. This example's behavior has not been validated as cross-platform reliability by the core project's CI.

See [synthetic late-update example](../../examples/topic-reconciliation.md).
