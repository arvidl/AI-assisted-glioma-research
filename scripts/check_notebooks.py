"""Validate notebook source and execute teaching notebooks in this uv Python."""

import ast
import json
import sys
import tempfile
from pathlib import Path

import nbformat
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpecManager
from nbclient import NotebookClient

from glioma_ai.lumiere_dynamics import configured_case_inputs
from glioma_ai.lumiere_slice import lumiere_p048_root

ISOLATED_KERNEL_LAUNCHER = """\
import sys

del sys.path[0]

from IPython.core import application

application.SYSTEM_CONFIG_DIRS.clear()
application.ENV_CONFIG_DIRS.clear()

from ipykernel import kernelapp

kernelapp.launch_new_instance()
"""


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


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    output = root / "outputs/notebooks"
    output.mkdir(parents=True, exist_ok=True)
    summary = []
    with tempfile.TemporaryDirectory(prefix="glioma-kernel-") as directory:
        spec_root = Path(directory)
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
                    "argv": [sys.executable, str(launcher), "-f", "{connection_file}"],
                    "env": {
                        "IPYTHONDIR": str(spec_root / "ipython"),
                        "JUPYTER_CONFIG_DIR": str(spec_root / "jupyter"),
                    },
                    "display_name": "Glioma AI (validation)",
                    "language": "python",
                }
            )
        )
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
            manager = KernelManager(
                kernel_name="glioma-ai",
                kernel_spec_manager=KernelSpecManager(kernel_dirs=[str(spec_root)]),
            )
            client = NotebookClient(
                notebook,
                km=manager,
                timeout=300,
                resources={"metadata": {"path": str(root)}},
            )
            try:
                client.execute()
            finally:
                if manager.has_kernel:
                    manager.shutdown_kernel(now=True)
                if client.kc is not None:
                    client.kc.stop_channels()
                manager.cleanup_resources()
            nbformat.write(notebook, output / path.name)
            print(f"Executed {path.name}", flush=True)
            summary.append({"notebook": path.name, "execution": "passed"})
    (output / "execution.json").write_text(json.dumps(summary, indent=2) + "\n")


if __name__ == "__main__":
    main()
