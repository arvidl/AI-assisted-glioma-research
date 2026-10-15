"""Validate notebook source and execute teaching notebooks in this uv Python."""

import ast
import faulthandler
import json
import os
import signal
import sys
import tempfile
from pathlib import Path

import nbformat
from jupyter_client import AsyncKernelManager
from jupyter_client.kernelspec import KernelSpecManager
from nbclient import NotebookClient
from nbclient.exceptions import CellTimeoutError

from glioma_ai.lumiere_dynamics import configured_case_inputs
from glioma_ai.lumiere_slice import lumiere_p048_root

# Notebook cells finish in seconds; a cell that has not replied after CELL_TIMEOUT
# seconds, or whose output has not ended IOPUB_TIMEOUT seconds after its reply, is
# treated as a kernel stall. A stalled notebook is run once more in a fresh kernel
# and the retry is printed and recorded in execution.json; a second stall fails.
CELL_TIMEOUT = 120
IOPUB_TIMEOUT = 30
ATTEMPTS = 2
STALL_SECONDS = 240

ISOLATED_KERNEL_LAUNCHER = """\
import faulthandler
import signal
import sys

del sys.path[0]
# The runner sends SIGUSR1 before shutting down a stalled kernel: dump its threads.
faulthandler.register(signal.SIGUSR1, all_threads=True)

from IPython.core import application

application.SYSTEM_CONFIG_DIRS.clear()
application.ENV_CONFIG_DIRS.clear()

from ipykernel import kernelapp

kernelapp.launch_new_instance()
"""


def dump_kernel_stacks(manager: AsyncKernelManager) -> None:
    """Ask a stalled kernel to print every thread's stack to the runner's stderr."""
    pid = getattr(manager.provisioner, "pid", None) if manager.has_kernel else None
    if pid is not None and hasattr(signal, "SIGUSR1"):
        try:
            os.kill(pid, signal.SIGUSR1)
        except ProcessLookupError:
            pass


def execute(path: Path, spec_root: Path, root: Path) -> tuple[nbformat.NotebookNode, list[str]]:
    """Execute a notebook, once more in a fresh kernel after a stall.

    Returns the executed notebook and a description of each stalled attempt.
    """
    stalls: list[str] = []
    for attempt in range(1, ATTEMPTS + 1):
        notebook = nbformat.read(path, as_version=4)
        # nbclient needs an asynchronous kernel manager: with a synchronous one its
        # IOPub wait blocks the event loop without a timeout, so the cell timeout and
        # the dead-kernel check never run and a lost kernel message hangs the run.
        manager = AsyncKernelManager(
            kernel_name="glioma-ai",
            kernel_spec_manager=KernelSpecManager(kernel_dirs=[str(spec_root)]),
        )
        client = NotebookClient(
            notebook,
            km=manager,
            timeout=CELL_TIMEOUT,
            iopub_timeout=IOPUB_TIMEOUT,
            raise_on_iopub_timeout=True,
            shutdown_kernel="immediate",
            resources={"metadata": {"path": str(root)}},
        )
        # A run that hangs outside cell execution (kernel start or shutdown) has no
        # nbclient timeout; dump every runner thread's stack while it waits.
        faulthandler.dump_traceback_later(STALL_SECONDS, repeat=True)
        try:
            client.execute(cleanup_kc=False)
            return notebook, stalls
        except CellTimeoutError as error:
            summary = str(error).strip().splitlines()[0]
            stalls.append(f"attempt {attempt}: {summary}")
            print(f"Kernel stall in {path.name} (attempt {attempt}): {summary}", flush=True)
            dump_kernel_stacks(manager)
            if attempt == ATTEMPTS:
                raise RuntimeError(
                    f"{path.name} stalled in {ATTEMPTS} fresh kernels: {'; '.join(stalls)}"
                ) from error
        finally:
            faulthandler.cancel_dump_traceback_later()
            # Stop the channels, shut the kernel down and remove its connection file
            # (the cleanup nbclient runs itself when it owns the kernel manager).
            client._cleanup_kernel()
    raise AssertionError("unreachable")


def skip_reason(name: str, repo_root: Path | None = None) -> str | None:
    repo_root = repo_root or Path(__file__).resolve().parents[1]
    if name.startswith("00_"):
        return "hosted Colab execution is a separate check"
    if (
        name.startswith("03_")
        and lumiere_p048_root() is None
        and not configured_case_inputs(repo_root)
    ):
        return "explicit prepared LUMIERE root or fixed-plane bundle is absent"
    return None


def write_kernel_spec(spec_root: Path) -> None:
    """Write the isolated validation kernel spec "glioma-ai" under spec_root."""
    spec = spec_root / "glioma-ai"
    spec.mkdir()
    # Hosts such as Colab put kernel classes and extensions that this environment
    # lacks in /etc/ipython, which IPython always reads; the launcher drops those
    # directories so the kernels use no host IPython configuration.
    launcher = spec_root / "isolated_kernel.py"
    launcher.write_text(ISOLATED_KERNEL_LAUNCHER)
    (spec / "kernel.json").write_text(
        json.dumps(
            {
                # ipykernel 7.3's thread that forwards OS-level stdout/stderr can
                # deadlock and leave a finished cell unreported; Python-level output
                # is unaffected, and OS-level output goes to this process's stderr.
                "argv": [
                    sys.executable,
                    str(launcher),
                    "-f",
                    "{connection_file}",
                    "--IPKernelApp.capture_fd_output=False",
                ],
                "env": {
                    "IPYTHONDIR": str(spec_root / "ipython"),
                    "JUPYTER_CONFIG_DIR": str(spec_root / "jupyter"),
                },
                "display_name": "Glioma AI (validation)",
                "language": "python",
            }
        )
    )


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    output = root / "outputs/notebooks"
    output.mkdir(parents=True, exist_ok=True)
    summary = []
    with tempfile.TemporaryDirectory(prefix="glioma-kernel-") as directory:
        spec_root = Path(directory)
        write_kernel_spec(spec_root)
        for path in sorted((root / "notebooks").glob("*.ipynb")):
            notebook = nbformat.read(path, as_version=4)
            nbformat.validate(notebook)
            for cell in notebook.cells:
                if cell.cell_type == "code":
                    ast.parse(cell.source)
                    if cell.outputs or cell.execution_count is not None:
                        raise ValueError(
                            f"Commit an output-free notebook: {path.name}; run make clear-notebooks"
                        )
            reason = skip_reason(path.name, root)
            if reason:
                print(f"Validated {path.name}; skipped: {reason}.", flush=True)
                summary.append({"notebook": path.name, "execution": "skipped", "reason": reason})
                continue
            print(f"Executing {path.name}", flush=True)
            executed, stalls = execute(path, spec_root, root)
            nbformat.write(executed, output / path.name)
            entry = {"notebook": path.name, "execution": "passed"}
            if stalls:
                entry["retried_after_kernel_stall"] = stalls
                print(f"Executed {path.name} after {len(stalls)} kernel stall(s)", flush=True)
            else:
                print(f"Executed {path.name}", flush=True)
            summary.append(entry)
    (output / "execution.json").write_text(json.dumps(summary, indent=2) + "\n")


if __name__ == "__main__":
    main()
