# Contributing

Thanks for helping improve the provider-neutral GitHub collaboration feed. This is an experimental project, not a verified multi-agent orchestration framework.

1. Search existing issues before opening a proposal. Describe the problem, expected observable outcome, and privacy implications.
2. Fork the repository and create a focused branch. Use fictional issues, names, URLs and timestamps in tests and examples. Never submit actual chats, private native links, access tokens, exported account data or personal details.
3. Run `PYTHONPATH=src python3 -P -m unittest discover -s tests -v` (Python 3.11+). Add regression tests for changes to window boundaries, event sequencing, fingerprint compatibility, compaction or workflow permissions.
4. Open a pull request using the template. Contributor CI runs with read-only repository permission. Maintainers review before merging; an automatic CI pass is not approval.
5. For public API or feed-schema changes, provide migration and rollback instructions. Schema 3 requires compatible consumers before activation; do not alter another user’s assistant settings.

Please keep changes small and avoid adding runtime secrets or real account identifiers. This project does not require assignment of copyright or a contributor license agreement. By contributing, you agree to distribute your contribution under the project MIT license.

## Design priorities

Correctness before apparent freshness; preserve exact URLs, provenance, explicit coverage gaps and the distinction between publication and actual delivery. No autonomous write actions, task alterations or cross-account permission expansion without explicit human authorization.