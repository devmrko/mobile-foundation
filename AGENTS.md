# Repository development rules


## Reuse and quality checks

- Read docs/design/quality-contract.md before changing reusable behavior; preserve the existing public/security contracts.
- Run `bash scripts/check-quality.sh`; add a failing regression for recurring defects and update the shared implementation.
- Distinguish automated checks, independent consumer execution, actual UI observation and untested environments.
- Global quality procedure lookup: knowledge `c7085828-a0ad-4b6c-becd-9c65598947ef`; read its current exact revision through vector-knowledge.
- Public contract changes require docs/design first. Do not commit secrets or generated environments/builds.
- Keep mf tokens, macros and frames compatible; run installed-wheel verification after packaging changes.
