# Private pilot acceptance checklist

**Release status:** local RC. No private repository was created or modified in this preparation. Do not publish without explicit approval of the files and license.

1. Create a **new private** GitHub repository named `cross-agent-collaboration` (or a temporary private pilot name). Push the clean-history release candidate. Never push the source repository or its Git history.
2. Set `config.json` `repository` to the actual `owner/repo`; verify `main` default branch and GitHub Actions permissions. Keep the example inputs fictional.
3. Run the workflow through **Actions > Publish assistant activity digest > Run workflow**. Record UTC time, run URL, exit status and state-branch commit. Read `digest-state:state/inbox.json`; validate schema 2, repository, timestamps and window slots. The first run is a quiet baseline.
4. Create a synthetic issue with a configured label, publish again; verify a single `issue` event and relevant reporting slot. Dispatch a third time unchanged; assert no increment in sequence. Edit, reassign, comment, close and exercise a synthetic PR review; verify observed changes and SHA metadata.
5. Observe a **real scheduled publisher run** at the configured local time and compare intended and actual start times. GitHub schedules can be delayed or dropped; never infer this from workflow configuration.
6. From each supported assistant, read the same **private** feed using its own read-only connector. Test two **separate scheduled sessions** with no prior chat checkpoint; capture actual window selection, output location, quiet behavior, repeat observations, and late/stale/partial cases. A successful manual connector read does not establish native scheduler support.
7. If a provider fails the scheduled test, use `docs/assistant-prompt.md` schema-2-compatible manual fallback; do not roll back to a schema-1-only prompt.
8. Before public publication, rerun the privacy scan on the exact intended release commit, review all files and history manually, confirm attribution and license, and get explicit owner approval.

## Evidence ledger (fill only after observation)

| Platform or component | Version/date | Actual evidence link or artifact | Result |
| --- | --- | --- | --- |
| GitHub Actions manual first publish | Pending | Pending | Unverified |
| GitHub Actions scheduled publish | Pending | Pending | Unverified |
| Read-only assistant connector 1 | Pending | Pending | Unverified |
| Separate scheduled runs connector 1 | Pending | Pending | Unverified |
| Read-only assistant connector 2 | Pending | Pending | Unverified |
| Separate scheduled runs connector 2 | Pending | Pending | Unverified |
| Final sanitization and license sign-off | Pending | Pending | Unverified |