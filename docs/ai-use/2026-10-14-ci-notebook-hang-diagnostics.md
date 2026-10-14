# Diagnostics for the intermittent CI notebook hang

- Date: 14 October 2026.
- Tool: Cursor agent; exact backend snapshot and settings not captured.
- Request: after the notebook 09 publication, the Ubuntu/Python 3.12 job of the public CI hung twice in a row in the notebook step; the investigator asked why and chose to add diagnostics and a step timeout, and to publish them after checks.
- Observations: the step normally takes 45–55 s; earlier hangs stopped before notebooks 04 and 05, so no single notebook is implicated; each cell has a 300 s timeout that did not fire, so the wait is probably outside cell execution (kernel start-up, messaging or shutdown). The cause is not known.
- Contribution: `scripts/check_notebooks.py` prints "Executing <notebook>" before each run and, through the standard `faulthandler` module, dumps the stacks of all threads of the runner and of the kernel every 240 s while a notebook is still running. The notebook step in both workflows (`.github/` and `public/.github/`) has `timeout-minutes: 15`, so a hang fails with its log instead of running until cancelled. No notebook, test or result changed.
- Verification: recorded in `docs/validation.md`.
- Decision: the investigator chose this option; the push to public `main` is made with the investigator's approval.

This is a retrospective development summary, not a captured verbatim dialogue.

## Follow-up: cause located and runner change

- The first CI run with the diagnostics (run 38563332722 on public `0bfa6d6`) hung in both Python 3.12 jobs right after "Executing 04_ai_assistance_record.ipynb"; the step timeout ended them at 15 minutes and the logs contained the stack dumps. The runner waited for the first cell's messages (`nbclient` `_async_poll_output_msg`); in the kernel the main and shell threads were idle and the thread that forwards OS-level stdout/stderr (`ipykernel.iostream._watch_pipe_fd`) was blocked inside a write (Ubuntu: creating its event-pipe socket; macOS: `parent_header`). The underlying ipykernel 7.3.0 race was not investigated further.
- Contribution, chosen by the investigator over an ipykernel upgrade: the validation kernel starts with `--IPKernelApp.capture_fd_output=False`, which removes that thread; Python-level output still reaches the notebooks and OS-level output goes to the runner's stderr. `uv.lock` is unchanged; Colab and interactive Jupyter are not affected.
