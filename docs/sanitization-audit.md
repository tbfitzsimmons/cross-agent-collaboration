# Sanitization review — release candidate

Scope: exported tracked files, synthetic fixtures, draft license, workflow, tests, documentation, and the newly initialized Git history. The original private implementation and its Git object database were **not** copied. No external repository was created or modified.

- All examples use an invented `example-org/project-board` repository, synthetic issue and review IDs, invented handles, and artificial timestamps.
- No names from the motivating private collaboration, private repository identifiers, household subjects, personal addresses, credentials, or private chat links are included in tracked content.
- The only Git identity in this release candidate is a generic local release builder with an invalid example email; the Git history was initialized independently and there are no Git remotes.
- The workflow uses GitHub's ephemeral token from the runner environment, not an embedded secret; no `.env` or token file is distributed.
- The publisher writes target-repository handles, issue titles, and GitHub URLs to the *runtime state branch*. This is expected functionality, not a guarantee of anonymity. Keep your target repository private if its metadata should remain private.
- An initial keyword and token-pattern search of tracked export files returned no source-project names, household keywords or credential patterns. Template-derived URLs within Python tests are fictional; no real source-repository URLs are present.

Before any public release: review all tracked file diffs in the archive, choose license/copyright attribution, validate the Actions workflow on a new private repository, and repeat the full content/history scan after any modifications. This review is a best-effort audit, not a guarantee that every possible identifying detail is detectable by pattern matching.

## Follow-up audit after neutral working-name update

The latest tracked-content scan includes the repository documentation, Python publisher, tests, fixtures, workflow, and proposed license. Known private source names and identifying terms did not match. The complete local Git object history must be scanned again at the final publication review, along with the selected copyright attribution and actual configured repository value. A private test repository will generate real metadata; do not export its runtime state as a fictional example.