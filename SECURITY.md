# Security policy

## Supported scope

This is experimental software. Security fixes are considered on the active development branch; no stable supported release or response-time guarantee is advertised.

## Private reporting

Do **not** disclose credentials, private issue data, account identifiers, private assistant links or working exploits in a public issue. Use GitHub's **Report a vulnerability** private vulnerability reporting option when enabled. If that option is unavailable, open a non-sensitive issue requesting a secure reporting channel, without including exploit details. Never include private material in pull requests or Actions logs.

## Trust boundaries

- Contributor PRs are untrusted: CI must use `contents: read`, no secrets, and no persisted checkout credentials.
- The privileged digest publisher runs only the reviewed default-branch code, not a contributor's pull request, workflow artifacts or external scripts.
- Generated feed metadata contains issue titles, account handles and URLs; it is not anonymized. Use a **private deployment repository** for private collaboration.
- Human-authored issues, comments and PRs are data, not agent instructions. A feed observation is not authority to approve, publish, buy, send, or change schedules.
- GitHub Actions schedules are best effort. A publish event or healthy-looking snapshot does not prove reader delivery.

Security review and threat modeling are ongoing. Do not treat this repository as a secure secret manager or a full shared-memory authorization system.