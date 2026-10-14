# Diagnostics for the intermittent CI notebook hang

- Date: 14 October 2026.
- Tool: Cursor agent; exact backend snapshot and settings not captured.
- Request: after the notebook 09 publication, the Ubuntu/Python 3.12 job of the public CI hung twice in a row in the notebook step; the investigator asked why and chose to add diagnostics and a step timeout, and to publish them after checks.
- Observations: the step normally takes 45–55 s; earlier hangs stopped before notebooks 04 and 05, so no single notebook is implicated; each cell has a 300 s timeout that did not fire, so the wait is probably outside cell execution (kernel start-up, messaging or shutdown). The cause is not known.
- Contribution: `scripts/check_notebooks.py` prints "Executing <notebook>" before each run and, through the standard `faulthandler` module, dumps the stacks of all threads of the runner and of the kernel every 240 s while a notebook is still running. The notebook step in both workflows (`.github/` and `public/.github/`) has `timeout-minutes: 15`, so a hang fails with its log instead of running until cancelled. No notebook, test or result changed.
- Verification: recorded in `docs/validation.md`.
- Decision: the investigator chose this option; the push to public `main` is made with the investigator's approval.

This is a retrospective development summary, not a captured verbatim dialogue.
