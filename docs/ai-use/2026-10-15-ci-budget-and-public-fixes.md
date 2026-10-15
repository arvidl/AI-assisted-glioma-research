# Actions budget, notebook cleanup and public-page fixes

- Date: 15 October 2026.
- Tool: Cursor agent (Claude Opus 5.5, medium); exact backend snapshot and settings not captured.
- Request: after a GitHub warning that 90% of the included Actions minutes were used, the investigator asked for a plan for the rest of the project that is sound scientifically and budget-wise, and then for its implementation.
- Investigator decisions (answers to the assistant's questions): the private repository's CI runs on manual dispatch only, on Ubuntu, with the manuscript job kept; after the talk the private repository stays the home of the held-back material (paper, talk, `AGENTS.md`, the perspective plan, the release checklist, the sub-PAT16 derivation script) with manual CI.
- Contribution:
  - `.github/workflows/checks.yml`: `workflow_dispatch` only, `ubuntu-latest` only, a concurrency group that cancels a superseded run. The public workflow (`public/.github/workflows/checks.yml`) is unchanged, because Actions on standard runners are free for public repositories.
  - Notebooks 00–11 in the working copy carried IDE execution outputs, empty trailing cells and the local "Glioma AI (uv)" kernelspec. A comparison against `HEAD` found no change to any cell source; the files were restored to the committed, output-free versions (a copy was kept outside the repository).
  - Public "About" description: "(provisional; private until release)" and the unpublished talk and perspective were removed.
  - Public README layout: `data/` no longer claims the sub-PAT16 matrices, which are held back with notebook 12.
- Not done by the assistant, because they need the investigator: a $0 Actions budget and the Cursor on-demand cap (billing pages); the notebook 12 QC review; clinical and citation review of the talk; timed rehearsals; collaborator agreements.
- Verification: recorded in `docs/validation.md`.

This is a retrospective development summary, not a captured verbatim dialogue.
