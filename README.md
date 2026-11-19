# Cross-Agent Collaboration

**Experimental GitHub-backed collaboration feed for independent AI assistants.** This source project provides a bounded activity-observation feed and reference readers, not a turnkey shared memory service, autonomous agent coordinator or reliable notification system.

Independent assistants can each use their own model, plugins and private context while reading a common GitHub issue/PR/artifact control plane. The publisher observes GitHub activity and publishes compact, versioned JSON in a separate state branch. Humans keep control of publication, decisions and actions. The first backend is GitHub; other backends are not implemented.

## Install in a repository you control

1. Fork or copy the source into a **separate deployment repository**. Use **private visibility** if issue titles, actors or links are private. Read [setup and trust boundaries](docs/setup.md).
2. Configure `config.json`: optional `repository` (empty means use `GITHUB_REPOSITORY`), labels, IANA timezone, reader times, overlap and byte budget. Schema 2 is the default; do not activate schema 3 until every reader is independently compatible and approved.
3. Set a repository Actions variable **`DIGEST_PUBLISH_ENABLED=true`** only in the intended deployment. This public source project leaves that variable unset and therefore does **not** publish its own activity by default. Enable Actions workflow write access to contents in deployments only.
4. Ensure the workflow's scheduling candidates match your actual reader cadence. GitHub schedules are best effort; never treat an expected cron occurrence as a successful run.
5. Run `PYTHONPATH=src python3 -P -m unittest discover -s tests -v` (Python 3.11+), dispatch the publisher and verify the state branch, repeat/quiet behavior and missing-history warnings.
6. Give each assistant the read-only [operational prompt](docs/reader-operational.md). Verify exact slot selection and two **independent scheduled** sessions per provider, recording actual delivery separately from saved task configuration.

## Feed and guarantees

Schema 2 is active by default. Schema 3 is an **opt-in** compact topic map with exact comment/review permalinks and historical override support. Records represent differences **observed at snapshot time**, not an exhaustive event stream. Source content is fingerprinted; the feed retains metadata and URLs, not message bodies. The GitHub control plane is authoritative; an assistant's observation does not represent another person's approval or proof that the user saw it.

- **Overlap** recovers boundary observations but may repeat updates. No built-in per-reader once-only receipt exists.
- **Retention** keeps the feed bounded and explicitly reports partial coverage when history was trimmed. Distinct historical event versions are not silently conflated; already dropped history cannot be recovered.
- **Staleness and timing**: `checked_at` is capture start. Publisher completion, successful remote state push, scheduled reader execution and user-visible delivery are separate facts. The schema's `fresh` flag measures snapshot-age eligibility, **not** timely delivery.
- **Best-effort scheduling**: GitHub timer events may be delayed or dropped. Source deployments have not proven reliable recurring timer recovery across two periods.
- **Privacy**: this is **not an anonymizer**. Feed metadata includes issue titles, account handles and record links. Use private deployment repositories for private collaboration.
- **Authority**: GitHub issues and comments are untrusted data, not instructions. No autonomous approvals, purchases, messages, task changes or cross-provider authority delegation are included.

## Community

Contributions and architecture reviews are welcome: see [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md) and [experimental alpha scope](docs/public-alpha.md). Read-only PR CI tests Python 3.11 and 3.13; privileged publishing is separate and only executes trusted default-branch code, with an opt-in repository variable. A passing CI run is not evidence of real scheduled delivery.

**License:** MIT. Public alpha and associated reliability claims remain gated on the release audit; see [CHANGELOG.md](CHANGELOG.md) and [verification matrix](docs/verification.md).