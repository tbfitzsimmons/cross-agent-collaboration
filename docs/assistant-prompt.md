# Assistant connector setup (example)

Use the **canonical reader prompt** in [`reader-operational.md`](reader-operational.md) with the approved target repository, state branch, time zone and reader schedule. The maintained prompt accepts schema 2 and schema 3; do not install schema-3-only behavior until both participating assistants have independently demonstrated old-schema reads and new-schema fixtures.

Reference implementation: `src/reader.py` validates slot selection, status and topic resolution. This is a pure function, **not** a deployed scheduler or connector. Test it with fictional fixtures before saving tasks. Verify saved configuration, manual reads, independent actual scheduled runs, native location and phone notification separately. Do not store private account destinations in the shared repository.

## Fallback

For manual recovery use the same compatible read-only prompt and the explicitly requested slot or a manual most-recent-elapsed slot. If a task fails, only its own account may restore its **last verified compatible prompt** under applicable authorization; do not silently change the publisher, prompts on other accounts, or private routing. Record the old/restored revision, why, and what remains unverified.