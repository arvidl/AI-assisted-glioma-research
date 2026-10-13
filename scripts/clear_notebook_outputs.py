"""Remove code-cell outputs and execution counts from tracked notebook sources."""

from pathlib import Path

import nbformat


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    for path in sorted((root / "notebooks").glob("*.ipynb")):
        notebook = nbformat.read(path, as_version=4)
        changed = False
        for cell in notebook.cells:
            if cell.cell_type == "code" and (cell.outputs or cell.execution_count is not None):
                cell.outputs = []
                cell.execution_count = None
                changed = True
        if changed:
            nbformat.write(notebook, path)
            print(f"Cleared outputs: {path.name}")


if __name__ == "__main__":
    main()
