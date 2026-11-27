# Public alpha: positioning, scope and publication gates

## One-sentence description

**Selective, human-governed collaboration between independently owned AI environments using GitHub as a shared versioned boundary.**

This is a reference architecture and an experimental optional GitHub activity digest. It does not merge personal assistant accounts, private connectors or memories. It does not implement A2A or replace MCP, agent workspaces or native AI subscriptions.

## What is included

- A provider-neutral example of topic state on `main`, issue evidence, checkpoints, focused PRs and approval of the exact revision. This is optional documented practice, not enforced by the digest.
- A Python GitHub metadata-snapshot publisher, bounded stateless observation windows and example readers (schema 2 default, schema 3 opt-in).
- Synthetic fixtures, tests, contributor CI, and instructions for private consumer-owned deployments.

## What must not be claimed

- That the system prevents an assistant from accidentally disclosing private connector data.
- That a pass on CI or a configured cron proves scheduled notification delivery or reliable timer recovery.
- That native Claude, ChatGPT or other vendors' assistants autonomously coordinate, authorize changes or share tasks through this software.
- That cross-platform usage, token savings, reduced context drift, or operational time savings are measured.
- That the optional GitHub topic-state layout is required by the digest.

## Release hygiene

Before changing **this existing repository** to public, audit current files, all branches (including past `digest-state` content), reachable Git history, issue/PR comments, and GitHub Actions logs/artifacts. Deleting a branch does not erase historical objects or logs by itself. Stop the public change if private material or credentials remain exposed.

Confirm MIT attribution, contributor/security docs, read-only PR CI, source-only publisher-disabled default, main-branch protections, and the exact commit's tests. Mark the first public tag as a **prerelease**, with a factual verified/unverified matrix. Do not publish private companion implementations or personal records.

An alpha can seek feedback before end-to-end scheduler reliability is proven, but must state that limitation unambiguously.
