"""Copy executed notebooks from the checked run for publication.

Reads the copies that `make notebooks` wrote to outputs/notebooks/, removes
volatile execution metadata, adjusts markdown links that leave notebooks/ to
the deeper folder, and refuses outputs that contain local paths.
Every numbered notebook present is exported (01-13 here, fewer in a staged
public snapshot); 00 (Colab bootstrap) never is. Notebooks 03, 09, 10 and 12
show openly licensed real or published data with their licence notes; a run in
which their local inputs were absent is refused, so tracked figures are never
replaced by missing-input notices.
"""

import argparse
import json
import re
import sys
from pathlib import Path

import nbformat

NOTEBOOKS = Path(__file__).resolve().parents[1] / "notebooks"
EXPORTABLE = tuple(
    sorted(
        path.name
        for path in NOTEBOOKS.glob("[0-9][0-9]_*.ipynb")
        if not path.name.startswith("00_")
    )
)
MISSING_INPUT_NOTICES = (
    "Empirical inputs absent",
    "Case not run:",
    "Illustration not imported locally",
    "CANTAB not shown:",
)
LOCAL_PATH = re.compile(r"/Users/[^/\s\"']+|/home/[^/\s\"']+|/var/folders/|[A-Za-z]:\\\\Users\\\\")
KERNELSPEC = {"display_name": "Python 3 (ipykernel)", "language": "python", "name": "python3"}
PARENT_LINK = re.compile(r"(\]\(|(?:src|href)=\")\.\./")


def relink(markdown: str) -> str:
    """Links that leave notebooks/ go up one folder more from notebooks/executed/."""
    return PARENT_LINK.sub(r"\1../../", markdown)


def check_exportable(name: str) -> None:
    if name not in EXPORTABLE:
        raise ValueError(f"{name} is not an exportable notebook.")


WIDGET_STATE = "application/vnd.jupyter.widget-state+json"
RANDOM_ID = re.compile(r"(?<![0-9a-f])[0-9a-f]{12}4[0-9a-f]{3}[89ab][0-9a-f]{15}(?![0-9a-f])")


def strip_volatile(notebook):
    """Drop per-run timestamps and renumber random identifiers.

    Widget model IDs and Matplotlib animation element IDs are random UUID4 hex
    strings regenerated on every run; they are replaced in order of first
    appearance, so regenerated copies differ only when content does. Longer hex
    strings such as SHA-256 hashes are left untouched. Returns the cleaned notebook.
    """
    for cell in notebook.cells:
        cell.metadata.pop("execution", None)
    notebook.metadata.pop("papermill", None)
    order = list(dict.fromkeys(RANDOM_ID.findall(json.dumps(notebook.cells, sort_keys=True))))
    state = notebook.metadata.get("widgets", {}).get(WIDGET_STATE, {}).get("state", {})
    queue = [key for key in order if key in state]
    while queue:
        for key in RANDOM_ID.findall(json.dumps(state[queue.pop(0)], sort_keys=True)):
            if key not in order:
                order.append(key)
                if key in state:
                    queue.append(key)
    masked = {
        key: RANDOM_ID.sub("", json.dumps(value, sort_keys=True)) for key, value in state.items()
    }
    order += sorted((key for key in state if key not in order), key=masked.get)
    text = json.dumps(notebook, sort_keys=True)
    order += [key for key in dict.fromkeys(RANDOM_ID.findall(text)) if key not in order]
    for number, key in enumerate(order):
        text = text.replace(key, f"id{number:04d}")
    return nbformat.from_dict(json.loads(text))


def local_paths(notebook) -> list[str]:
    """Local filesystem paths found anywhere in the outputs or metadata."""
    text = json.dumps([cell.get("outputs", []) for cell in notebook.cells]) + json.dumps(
        notebook.metadata
    )
    return sorted(set(LOCAL_PATH.findall(text)))


def missing_inputs(notebook) -> list[str]:
    """Missing-input notices printed by notebooks whose local inputs were absent."""
    text = json.dumps([cell.get("outputs", []) for cell in notebook.cells])
    return [notice for notice in MISSING_INPUT_NOTICES if notice in text]


def export(source: Path, destination: Path, names: tuple[str, ...] = EXPORTABLE) -> list[str]:
    summary = json.loads((source / "execution.json").read_text())
    passed = {row["notebook"] for row in summary if row["execution"] == "passed"}
    destination.mkdir(parents=True, exist_ok=True)
    written = []
    for name in names:
        check_exportable(name)
        if name not in passed:
            raise ValueError(f"{name} did not pass in the checked run; rerun make notebooks.")
        notebook = nbformat.read(source / name, as_version=4)
        notebook = strip_volatile(notebook)
        notebook.metadata["kernelspec"] = dict(KERNELSPEC)
        for cell in notebook.cells:
            if cell.cell_type == "markdown":
                cell.source = relink(cell.source)
        found = local_paths(notebook)
        if found:
            raise ValueError(f"{name} outputs contain local paths: {found}")
        notices = missing_inputs(notebook)
        if notices:
            raise ValueError(f"{name} ran without its local inputs: {notices}")
        nbformat.validate(notebook)
        nbformat.write(notebook, destination / name)
        written.append(name)
    return written


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=root / "outputs/notebooks")
    parser.add_argument("--destination", type=Path, default=root / "notebooks/executed")
    parser.add_argument("names", nargs="*", help="subset of notebooks (default: all)")
    arguments = parser.parse_args()
    try:
        written = export(
            arguments.source, arguments.destination, tuple(arguments.names) or EXPORTABLE
        )
    except ValueError as error:
        sys.exit(str(error))
    for name in written:
        print(f"Exported {name} -> {arguments.destination / name}")


if __name__ == "__main__":
    main()
