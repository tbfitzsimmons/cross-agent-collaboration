# Cross-Agent Collaboration (release candidate)

A provider-neutral starting point for collaboration between independent AI assistants. This release candidate implements the GitHub activity-feed layer—not shared agent memory, conflict-resolution, or autonomous cross-agent execution. A small, assistant-neutral GitHub activity feed. A GitHub Actions publisher reconciles issues, comments, PRs, review comments and formal reviews into a bounded JSON snapshot on a separate state branch. Any assistant with **read access** to that repository can check the same window without relying on prior chat memory.

**Status:** local release candidate; not published or deployed. Python 3.11+, GitHub CLI (`gh`) on Actions, and GitHub read/write permissions for the publisher. No extra Python dependencies.

## Quick start

1. Create a *new* repository (private while testing) using these files; its default branch must be `main` for the example workflow. Do not copy a private source repo's `.git` history.
2. Set `repository` in `config.json` to `your-org/your-repo`. Customize the label map, reader times, `timezone`, overlap, budget and `state_branch`. Do not enter personal information in the example files.
3. Match the workflow's scheduled cron with the desired publisher times: by default **08:37 and 14:37** in `America/Denver`, ahead of readers at **09:00 and 15:00**. Changing `config.json` alone does not change GitHub Actions cron. Verify actual runs and times on your account.
4. Enable GitHub Actions and permit `GITHUB_TOKEN` to write repository contents. Keep the repository private unless all issue titles, user handles, labels and links are intentionally public. Grant assistants **read-only** access.
5. Run the test suite: `PYTHONPATH=src python3 -P -m unittest discover -s tests -v`. Dispatch **Publish assistant activity digest** once. Confirm branch `digest-state` contains `state/inbox.json` and `state/cursor.json`, then dispatch it again.
6. Give the assistant `docs/assistant-prompt.md`. Confirm it can read `state/inbox.json` and that its scheduled executions identify the correct slot. Test two independent scheduled sessions on each platform before relying on notifications.

## Snapshot contract

The feed uses **schema 2**: `repository`, `checked_at`, global `sequence`, `coverage_started_at`, `oldest_sequence`, `dropped_through_at`, `updates[]`, and two `windows[]` (latest elapsed and next scheduled slot). Each window has its local-schedule slot expressed as a UTC instant, `from`, `through`, `fresh`, `limits`, and inclusive sequence bounds. A new repository starts with a **quiet baseline**, not a replay of every historical issue.

An update is an *observed difference between complete API snapshots*, not proof that an event happened at its source timestamp or that an assistant delivered it. No body text is included; body changes affect fingerprints. Source links and author handles are included, so this is **not an anonymizer**. Public repositories make published metadata public.

## Limitations and choice of tradeoffs

- **Stateless windows vs per-assistant cursor:** windows can work in fresh sessions, but overlapping periods can repeat entries. The same slot retried can report the same update. Do not claim “unread” or “new to you.” If stronger once-only notifications are essential, add a *verified persistent per-reader receipt* outside this publisher.
- **Overlap:** an update near the previous boundary appears in both windows by design; `sequence` makes it identifiable. Changing overlap adjusts recovery and repetition together.
- **Staleness:** an on-time-looking feed is not enough. The reader matches the exact scheduled slot and checks `fresh`, checked time, expected repository and schema. A published snapshot is not proof the scheduler delivered a reader task.
- **Partial coverage:** the initial baseline and feed-size trimming are marked as `baseline` or `retention`. Show available entries with a partial warning; never silently equate an empty limited window with no activity. A missed whole reader session may be unrecoverable from the two retained windows.
- **Sampling, not event sourcing:** edits superseded between scans, deleted records, inaccessible resources, and transient API events cannot necessarily be reconstructed. PR review/commit changes may not trigger immediate publishing; scheduled reconciliation is the recovery mechanism.
- **Failures:** API errors abort before updating files; GitHub Actions publishes cursor and inbox together in one state-branch Git commit. Scheduled jobs may be delayed or dropped. A GitHub push failure leaves the previous remote snapshot unchanged. Re-run the publisher and investigate rather than declaring quiet.

See [setup and security notes](docs/setup.md) and [verification matrix](docs/verification.md).

## License

**Pending owner approval.** Proposed: MIT (see `LICENSE-PROPOSED.txt`). No public release or final licensing is authorized by this release candidate.

## Private pilot gate

The source package has been tested locally, but **a private GitHub deployment is still required**. Do not publicize the code or mark multi-agent collaboration as verified solely because the GitHub Actions publisher succeeds. See `docs/private-pilot.md` for the two-run acceptance checklist and the evidence log.