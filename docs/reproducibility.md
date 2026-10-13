# Environments and reproduction

## Local environment

Python 3.12 is selected by `.python-version`; 3.11–3.13 are supported. The core
uses NumPy, NiBabel and Matplotlib on CPU; no GPU, model weights or API key are
needed.

~~~sh
uv sync --locked --group notebooks
make doctor
make check
make notebooks
make demo
~~~

The lock is committed. Do not regenerate it incidentally. See
[uv locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/).

## CPU, Apple MPS, and CUDA

The torch extra is optional and unnecessary for the notebooks:

~~~sh
uv sync --locked --group notebooks --extra torch
uv run --locked --extra torch glioma-ai doctor --device mps
~~~

On macOS PyTorch provides MPS when supported. The command compares a tensor
operation with CPU. A smoke test does not validate all segmentation operators.
Unavailable requested devices fail. See [PyTorch MPS](https://docs.pytorch.org/docs/stable/notes/mps.html).
The separate cuda extra selects Linux CUDA 12.8 wheels. The torch and cuda
extras are mutually exclusive.

## Editors and notebook kernels

`uv sync --locked --group notebooks` creates `.venv` with `ipykernel`. In
Cursor, VS Code or JupyterLab, select `.venv/bin/python` as the notebook kernel.
Rebuilding the notebooks never contacts an assistant or a model endpoint. The
automated checker (`make notebooks`) uses a temporary kernel specification bound
to its own uv interpreter, independent of system kernel registrations, and writes
executed copies to ignored `outputs/notebooks/`.

## Google Colab

Each published notebook has an "Open in Colab" badge under its title, and the
[README](../README.md#notebooks) links them. Notebooks 01–03 detect Colab in
their first code cell, clone this repository into
`/content/AI-assisted-glioma-research`, install NiBabel if it is missing and put
the package source on the path; they use Colab's own NumPy, Matplotlib and
ipywidgets rather than `uv.lock`. Notebook 03 has a Colab-only cell that fetches
the released LUMIERE Patient-048 inputs and checks them against the pinned
SHA-256. Notebook 00 instead installs the locked environment with uv and runs
the notebook checker on all published notebooks.

No GitHub token is needed. Resources and lifetime vary; see
[the official Colab FAQ](https://research.google.com/colaboratory/faq.html).
Hosted runs are recorded in [the validation record](validation.md) when they
have been observed.
