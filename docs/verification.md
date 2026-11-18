# Verification and evidence matrix (release candidate)

| Property | Evidence status |
| --- | --- |
| API snapshot modeling, dedup quiet repeat, comment edit and closure | Local synthetic unit tests pass |
| Reassignment included in issue fingerprint | Local regression test passes |
| PR approval metadata ties to reviewed commit SHA | Local synthetic unit test passes |
| Stateless windows, lead cutoff and DST | Local synthetic unit tests pass |
| Retention clipping and partial coverage flags | Local synthetic unit tests pass |
| Failed API read preserves existing files | Local synthetic unit test passes |
| New Git history independent of source | Local `git init` and audit; no source `.git` copied |
| Live `gh` permissions, pagination on a target repo, Actions state branch and push | **Not yet verified** in a new repository |
| GitHub local-time scheduled run actually fires at intended time | **Not yet verified** in a new repository |
| Read-only connector sees fresh schema-2 snapshot on each AI platform | **Not yet verified** |
| Scheduler fresh-session delivery, links, quiet notifications, missed runs and repeat behavior | **Not yet verified per platform** |

The motivating private implementation previously exercised synthetic comment/review/edit scenarios and a quiet state-branch baseline. That evidence does not certify this independent export or other vendors' schedulers. All acceptance on this project must be repeated in the new repository.

A scheduled occurrence is not proof of job execution; a GitHub run is not proof of a successful reader notification. The recipient must observe actual task output and its destination before claiming end-to-end delivery.

## Current neutral-name RC

Local tests re-executed after renaming: 9 passed. The private-pilot checklist is in `docs/private-pilot.md`; no live independent repository was created or exercised by this local build.