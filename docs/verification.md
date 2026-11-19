# Verification matrix (this export only)

| Property | Status and evidence boundary |
| --- | --- |
| Publisher, reader, fingerprint migration, topic compaction, exact links, UTF-8 budget and synthetic regression fixtures | Local automated tests; see reviewed PR suite |
| Repository and initial schema-2 state branch | GitHub connector read verified in prior deployment; not proof of recurring schedule |
| CI on untrusted PR code | Hosted CI passed for proposal PRs; re-test on release commit |
| Trusted-main publisher following PR CI | Pending merge and actual workflow-run observation |
| Initial state bootstrap failure handling | Local static workflow test; failure-mode hosted observation pending |
| Feed fullness/retention pressure | Tested synthetically; another installation's 98–99% result is not evidence about this export |
| Timer: actual `event=schedule`, remote state commit across two recovery periods | Unverified |
| Native AI task saved configuration | Unverified per account |
| Independent scheduled reader sessions, exact links, quiet/partial/stale output | Unverified per platform |
| Native destination, phone delivery, measured token usage | Unverified |
| Privacy audit and public release | Needs final audit, license and visibility decision |

No cross-account task change or repository visibility change is authorized by these draft PRs. Source deployment results, if cited, remain explicitly labeled as **external evidence**. See [schema migration and operational limits](schema-migration.md).