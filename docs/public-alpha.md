# Experimental public alpha: scope and publication gates

This repository is a **source project**, not a live multi-tenant service. A user deploys a copy in a repository they control; private deployments should use private repositories and read-only assistant integrations.

## Release gate

- Approve the complete public Git history, all reachable branches, issues, review comments, GitHub Actions logs and artifacts; changing visibility exposes more than current `main`.
- Remove the pilot-only `digest-state` branch **and verify remaining history/log exposure**. Deleting a branch is not proof that Git objects or workflow logs have been erased. Document remaining public artifacts and obtain explicit acceptance of any non-sensitive identifiers.
- Keep the original private implementation independent; do not import its logs, workflow artifacts, account details or history.
- Confirm the final MIT license/copyright, contributor and security instructions, branch rules, PR CI isolation and the source-only publisher-disabled default.
- Run tests on the exact release commit. Audit tracked content and history for secrets, private URLs, household details, account IDs and non-synthetic sample data.
- Mark v0.1.0-alpha as a **pre-release** only after repository visibility is changed and source review is complete. Do not imply scheduler reliability or autonomous decision authority.

## Verified versus pending

Synthetic unit tests and hosted PR CI have previously passed in the private project. The first GitHub state publisher was observed. GitHub best-effort scheduled recovery, real independent ChatGPT/Claude scheduler delivery, notification placement, and other providers remain **unverified**. The actual release commit must be re-tested before any new claims.

## Privacy

Published activity includes issue titles, actors, SHA metadata, URLs and timestamps, not message bodies. The publisher hashes bodies to detect changes, but this is **not** an anonymization tool. The state branch can reveal metadata about private collaboration if its repository becomes public. Never publish a private deployment solely for community review.