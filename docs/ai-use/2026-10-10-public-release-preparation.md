# Executed-notebook export and public release checklist

- Date: 10 October 2026.
- Tool: Cursor agent; exact backend snapshot and settings not captured.
- Request: the investigator asked whether learners should see notebook outputs on GitHub, and stated the plan to publish a polished snapshot as `AI-assisted-glioma-research` without the development history. The assistant recommended building an export now without committing executed notebooks, and writing a release checklist; the investigator agreed.
- Inputs: `scripts/check_notebooks.py`, the Makefile, `.gitignore`, the notebook map, `docs/data.md`, and searches of the tracked tree for the repository name, private-repository wording and tracked binaries.
- Contribution: `scripts/export_executed_notebooks.py` and the `make executed-notebooks` target; `tests/test_export_notebooks.py`; `docs/public-release.md`; links from `README.md` and `notebooks/README.md`.
- Found during the work: 15 generated files from notebooks 08 and 09 were tracked under `notebooks/outputs/` since commit `14879bf`, because those notebooks wrote to a path relative to the working directory and `.gitignore` only covered the root `outputs/`. The assistant anchored both notebooks to the repository root, added `/notebooks/outputs/` to `.gitignore` and removed the files from the index. The local folder was then removed by the stash used for validation; the files were unmodified generated outputs, recoverable from the previous commit and regenerated under `outputs/notebooks/`. The files are still in the development history, which the public snapshot does not carry.
- Investigator choices: no executed notebooks are committed in the development repository; publication of executed copies is deferred to the public snapshot. The allowlist (01–04, 07–11) and the exclusion of 00, 05, 06, 12 and 13 are assistant proposals awaiting review.
- Verification: recorded in `docs/validation.md`.
- Evidence status: tooling and documentation; no scientific results changed.
- Decision: pending investigator review.

This is a retrospective development summary, not a captured verbatim dialogue.

## Follow-up: tracked executed notebook 02

- Request: have notebook 02 display its figures on GitHub now.
- Investigator choice: from options the assistant offered, track an executed copy of notebook 02 only, as an exception to the executed-notebook rule.
- Contribution: the `AGENTS.md` exception, the second export line in `make executed-notebooks`, a freshness test, and notes in `notebooks/README.md` and `docs/public-release.md`.
- Verification: recorded in `docs/validation.md`.
