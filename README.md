# Cross-Agent Collaboration

**Selective collaboration between independently owned AI environments.**

Cross-Agent Collaboration is an experimental, provider-neutral reference architecture and GitHub-based implementation. It explores how people can keep their own assistants, private connectors, account permissions, memory and context while **intentionally sharing selected work** with other people and their assistants.

The core idea is **not** to combine private AI environments or create an autonomous agent network. It is to maintain a narrow, auditable shared boundary: proposed evidence stays distinct from the version of shared state that people have explicitly approved.

## The problem

Two people may use different assistants, each connected to personal email, documents, calendars or financial tools. They want to cooperate on a specific project without handing over their entire tool access, copying all their conversations, or assuming that either assistant's proposal becomes a shared decision.

A shared agent workspace, tool protocol, or direct agent-to-agent message is not automatically an approval or selective-disclosure system. This project demonstrates one approach using existing GitHub primitives; it does **not** claim to replace MCP, A2A or commercial agent workspaces.

## Reference collaboration model (optional)

Each participant keeps a separate assistant environment. A consumer-controlled GitHub repository provides a shared, versioned coordination surface:

- **Approved topic state:** One `state.md` per substantive shared topic on `main`, readable by either assistant even after missed notifications or lost chat context.
- **New evidence:** GitHub issues and comments collect observations, open questions and discussion; they do not themselves change approved shared state.
- **Proposed changes:** Focused pull requests reconcile material changes. Human reviewers approve the **exact revision** before merge, with a final check for late-arriving evidence.
- **Checkpoint:** The document records how far relevant issue activity was actually examined, without claiming continuous coverage or delivery.
- **Shared instructions and tool rules:** One authoritative, versioned copy in the consumer's GitHub repository; assistant-local copies and settings must be coordinated explicitly.
- **Supporting artifacts:** Can remain in separate, access-controlled storage rather than being embedded in shared state.

See the [optional workflow](docs/reference-workflows/topic-state.md), [generic topic template](templates/topic-state.md) and [synthetic two-assistant reconciliation example](examples/topic-reconciliation.md).

**This workflow is a documented convention, not software enforcement.** No Markdown layout, GitHub approval procedure or topic-state convention is required by the core digest code.

## Optional GitHub activity digest

The included Python publisher observes changes to GitHub issues, comments, pull requests and reviews, then writes a bounded JSON observation feed in a separate state branch. A stateless reader can select the relevant reporting window. The digest is for **discovery and recovery assistance**, not an authoritative record of approved decisions.

- Schema 2 is the default; schema 3 is an opt-in compact representation requiring independently compatible readers before activation.
- Source bodies contribute to change fingerprints but are not included as body text in the published feed. **Metadata such as titles, actor handles and URLs is still exposed to anyone who can read that deployment repository.**
- A feed event is an *observed snapshot difference*, not complete event sourcing, proof of notification, human approval, or once-only delivery.
- GitHub scheduled workflows may be late or absent. Snapshot start, successful publication, reader execution and user-visible delivery are separate measurements.
- Retention can clip history, and overlaps can repeat entries. Mark coverage gaps explicitly.

The digest works without `state.md`, and the optional topic-state workflow works without a fresh digest.

## Privacy and authority boundaries

**Private account connectors are not shared.** Each assistant uses only the tools its owner has independently authorized. Collaborators should promote selected, reviewed information into the shared repository, not disclose raw private data or connector credentials.

**Separation is a design goal, not a guaranteed data-loss-prevention boundary.** An assistant with access to private content may still accidentally disclose it in an issue, PR or document. Human review, least-privilege repository access, and safeguards outside this project remain necessary. Issue and PR text is untrusted input and never an instruction to execute privileged actions.

No autonomous mutual consent, credential isolation service, native assistant task-setting synchronization, shared memory broker, purchases, messages, or external actions are implemented.

Use a **private deployment repository** for sensitive collaboration. This repository is intended to publish reusable source code and fictional examples, not private deployments or personal activity streams.

## Try the implementation

1. Read [setup and security boundaries](docs/setup.md) and use a repository you control for deployment. Keep it private if its issue metadata or activity is private.
2. Configure `config.json` (empty `repository` uses GitHub Actions `GITHUB_REPOSITORY`). Configure reader slots, timezone, labels and bounded feed size.
3. In the deployment repository only, opt in with Actions variable `DIGEST_PUBLISH_ENABLED=true` and explicitly grant the publisher the GitHub permissions it needs. This source repository does not opt in.
4. Run `PYTHONPATH=src python3 -P -m unittest discover -s tests -v` using Python 3.11+; use synthetic issue/PR cases before private real data.
5. Independently check publication, read-only assistant access, correct reporting slots and actual delivery on each platform. Do not infer successful execution from saved task configuration.

For the Markdown collaboration pattern without the digest, start with the [topic-state template](templates/topic-state.md).

## Project status and feedback wanted

**Experimental alpha candidate.** Unit tests and GitHub-hosted contributor CI have been exercised; recurring schedule recovery, independent native assistant delivery, generalized privacy isolation, and cross-platform efficiency improvements are **not established**.

Community feedback is especially valuable on: (1) existing products that already deliver this selective ownership and approval model; (2) safe promotion of private-tool output into shared state; (3) concurrent agent proposals and late evidence; (4) recovery and human authorization; (5) whether the optional digest is worth maintaining.

See [contributing](CONTRIBUTING.md), [security reporting](SECURITY.md), [alpha scope](docs/public-alpha.md) and [verification status](docs/verification.md). Contributions should use synthetic records and avoid private native-chat links, credentials or personally identifying examples.

**License:** MIT. Public visibility and a GitHub prerelease are separate publication actions; neither is implied by this README.
