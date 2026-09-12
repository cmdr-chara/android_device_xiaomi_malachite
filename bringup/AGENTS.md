# Bring-up evidence contracts

- Preserve historical source locks and candidate reports as immutable evidence. Add a new candidate record for changed inputs instead of relabeling an old result as current.
- Record exact repository/manifest revisions, dirty state, tool versions, commands, artifact hashes, and the scope of each observation. A partial owned-project lock is not a full resolved Android manifest.
- Distinguish source identity, static checks, configuration, compilation, populated artifacts, ABI/packaging, and actual hardware behavior. Do not promote evidence from one level into another.
- Keep FAIL, GAP, stale results, missing fixtures, and runtime limitations visible. No pass counts inferred from skipped tests or previous commits.
- Retain only bounded, sanitized evidence. Never include credentials, device keys, private calibration dumps, personal data, or unrelated workspace contents.

Use [SAFETY.md](SAFETY.md) for device boundaries and [VERIFICATION.md](VERIFICATION.md) for candidate acceptance. Reports and successful CI runs do not grant permission to touch a phone. These instructions apply to this evidence subtree, not automatically to separate synced Git projects.
