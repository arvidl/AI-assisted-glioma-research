# Notebook runner stall: cause, runner fix and ipykernel 7.4.0

- Date: 15 October 2026.
- Tool: Antigravity agent (model selection reported as Claude Opus 5.5, high); exact backend
  snapshot and settings not captured.
- Request: the investigator asked for the intermittent notebook-runner stall to be investigated
  and fixed (two local `make notebooks` runs stalled at notebook 12 on 14–15 October; CI jobs
  stalled at notebook 04 in runs 38691739414 and 38714864343).
- Investigator decisions:
  - Review of the paper, front matter and the sub-PAT16 QC stay open until after the talk
    (21–25 October 2026); only the stall was in scope.
  - After the assistant's recommendation, the investigator approved upgrading ipykernel from
    7.3.0 to 7.4.0 in `uv.lock` (`uv lock --upgrade-package ipykernel`; no other package changed),
    as a separate commit from the runner fix.
- Contribution:
  - Diagnosis. The CI stack dumps showed the runner waiting in nbclient's
    `_async_poll_output_msg` and the kernel idle. Reading the installed nbclient 0.11.0 showed
    that with the synchronous `jupyter_client.KernelManager` the runner passed, nbclient's IOPub
    wait (`get_msg(timeout=None)`) blocks its event loop, so the cell timeout and the dead-kernel
    check never run. A direct test confirmed it: with a 3 s cell timeout, a 20 s cell completed
    after 20.8 s under the synchronous manager and raised `CellTimeoutError` after 4.2 s under
    `AsyncKernelManager`.
  - Reproduction (scratch harness, not committed). Repeated execution under heavy local load
    reproduced the stall with the previous runner and ipykernel 7.3.0: 3 stalls in about 1,390
    notebook executions (notebooks 04, 08, 04). In every case the stalled cell was the code cell
    after an ipywidgets explorer, and the kernel published no `busy` status for it, i.e. it never
    dispatched the request.
  - Upstream cause. ipykernel PR #1529 (merged 13 August 2026, released in 7.4.0) describes the
    same symptom on ipykernel 7 (kernel idle, no `execute_reply`, the hanging cell varying between
    runs) and its cause: a reply sent raw on the shell ROUTER socket can consume the socket's
    edge-triggered read event, stranding a concurrently arriving request. The PR was read through
    the GitHub API; its analysis was not re-derived here. On a notebook that alternates an explorer
    with a plain cell (20 pairs), ipykernel 7.3.0 stalled in 2 of 40 runs and 7.4.0 (scratch
    environment) in 0 of 40, run side by side on the same machine. This is consistent with the
    upstream fix but is a small sample.
  - Runner fix (`scripts/check_notebooks.py`): `AsyncKernelManager`; cell timeout 120 s;
    `raise_on_iopub_timeout` with 30 s; a stalled notebook is run once more in a fresh kernel, the
    retry printed and recorded in `outputs/notebooks/execution.json` under
    `retried_after_kernel_stall`; a second stall fails the run. A stalled kernel is sent SIGUSR1
    and prints its thread stacks before shutdown. Kernel shutdown stays immediate, as before.
  - Tests (`tests/test_notebook_stall.py`): a cell that hangs in the first kernel only is retried
    and recorded; a cell that always hangs fails within the timeouts.
- Verification: recorded in `docs/validation.md`.
- Not done: a CI rerun count large enough to estimate the remaining stall rate; hosted Colab
  (which uses Colab's own kernel, not the locked one).

This is a retrospective development summary, not a captured verbatim dialogue.
