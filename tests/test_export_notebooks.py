"""Only checked numbered notebooks with their inputs and without local paths are exported."""

import importlib.util
import json
import re
import sys
from pathlib import Path

import nbformat
import pytest
from nbformat.v4 import new_code_cell, new_notebook, new_output

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "export_executed_notebooks.py"
spec = importlib.util.spec_from_file_location("export_executed_notebooks", SCRIPT)
assert spec is not None and spec.loader is not None
exporter = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = exporter
spec.loader.exec_module(exporter)

NOTEBOOKS = Path(__file__).resolve().parents[1] / "notebooks"


def write_run(directory: Path, name: str, text: str, status: str = "passed") -> None:
    cell = new_code_cell("print(1)", outputs=[new_output("stream", name="stdout", text=text)])
    cell.metadata["execution"] = {"iopub.execute_input": "2026-10-10T12:00:00Z"}
    nbformat.write(new_notebook(cells=[cell]), directory / name)
    (directory / "execution.json").write_text(json.dumps([{"notebook": name, "execution": status}]))


def test_colab_bootstrap_is_never_exported():
    with pytest.raises(ValueError):
        exporter.check_exportable("00_colab_quickstart.ipynb")


def test_every_repository_notebook_is_classified():
    present = {path.name for path in NOTEBOOKS.glob("*.ipynb")}
    assert present == set(exporter.EXPORTABLE) | {"00_colab_quickstart.ipynb"}
    assert "01_imaging_measurements.ipynb" in exporter.EXPORTABLE


def test_export_strips_timestamps_and_keeps_outputs(tmp_path):
    source, destination = tmp_path / "run", tmp_path / "out"
    source.mkdir()
    name = "02_tumor_dynamics.ipynb"
    write_run(source, name, "M = 96.85 mm²\n")
    assert exporter.export(source, destination, (name,)) == [name]
    exported = nbformat.read(destination / name, as_version=4)
    assert "execution" not in exported.cells[0].metadata
    assert exported.cells[0].outputs[0].text == "M = 96.85 mm²\n"


def sources(notebook, relinked: bool = False) -> list[str]:
    """Cell sources without trailing empty cells, which editors add and the export drops."""
    texts = [
        exporter.relink(cell.source) if relinked and cell.cell_type == "markdown" else cell.source
        for cell in notebook.cells
    ]
    while texts and not texts[-1].strip():
        texts.pop()
    return texts


def test_tracked_executed_copies_are_authorized_clean_and_current():
    tracked = sorted((NOTEBOOKS / "executed").glob("*.ipynb"))
    assert [path.name for path in tracked] == list(exporter.EXPORTABLE)
    for path in tracked:
        executed = nbformat.read(path, as_version=4)
        source = nbformat.read(NOTEBOOKS / path.name, as_version=4)
        assert sources(executed) == sources(source, relinked=True)
        assert executed.metadata.kernelspec == source.metadata.kernelspec == exporter.KERNELSPEC
        assert not exporter.local_paths(executed)
        assert all("execution" not in cell.metadata for cell in executed.cells)
        assert any(cell.get("outputs") for cell in executed.cells)
        assert not exporter.missing_inputs(executed), path.name


def test_links_leaving_notebooks_are_deepened_and_others_kept():
    text = '[a](../docs/x.md) [b](02_tumor_dynamics.ipynb) <img src="../f.png"> [c](https://x/../y)'
    assert exporter.relink(text) == (
        '[a](../../docs/x.md) [b](02_tumor_dynamics.ipynb) <img src="../../f.png"> '
        "[c](https://x/../y)"
    )


def test_tracked_executed_links_resolve():
    for path in sorted((NOTEBOOKS / "executed").glob("*.ipynb")):
        for cell in nbformat.read(path, as_version=4).cells:
            if cell.cell_type != "markdown":
                continue
            for link in re.findall(r"\]\((\.\.[^)\s#]*)", cell.source):
                assert (path.parent / link).resolve().exists(), (path.name, link)


def test_random_ids_are_renumbered_consistently_and_hashes_kept():
    cell = new_code_cell("w")
    cell.outputs = [
        new_output(
            "display_data",
            data={
                "application/vnd.jupyter.widget-view+json": {
                    "model_id": "b" * 12 + "4bbb8" + "b" * 15
                }
            },
        )
    ]
    notebook = new_notebook(cells=[cell])
    first, second = "b" * 12 + "4" + "b" * 3 + "8" + "b" * 15, "a" * 12 + "4aaa9" + "a" * 15
    digest = "c" * 64
    cell.outputs[0].data["text/plain"] = f"anim{second} sha256 {digest}"
    state = {first: {"state": {"children": ["IPY_MODEL_" + second]}}, second: {"state": {}}}
    notebook.metadata["widgets"] = {exporter.WIDGET_STATE: {"state": state}}
    cleaned = exporter.strip_volatile(notebook)
    view = cleaned.cells[0].outputs[0].data["application/vnd.jupyter.widget-view+json"]
    renamed = cleaned.metadata["widgets"][exporter.WIDGET_STATE]["state"]
    first_id = view["model_id"]
    assert first_id.startswith("id") and set(renamed) == {
        first_id,
        *(child[len("IPY_MODEL_") :] for child in renamed[first_id]["state"]["children"]),
    }
    text = cleaned.cells[0].outputs[0].data["text/plain"]
    assert "c" * 64 in text and "a" * 12 not in text


def test_outputs_with_local_paths_or_failed_runs_are_refused(tmp_path):
    name = "02_tumor_dynamics.ipynb"
    for text, status in (("saved to /Users/someone/x.png\n", "passed"), ("ok\n", "failed")):
        source = tmp_path / status
        source.mkdir()
        write_run(source, name, text, status)
        with pytest.raises(ValueError):
            exporter.export(source, tmp_path / "out", (name,))


def test_runs_without_local_inputs_are_refused(tmp_path):
    name = "03_lumiere_prepared_slice.ipynb"
    source = tmp_path / "run"
    source.mkdir()
    write_run(source, name, "Empirical inputs absent. Run make cantab-fetch.\n")
    with pytest.raises(ValueError, match="without its local inputs"):
        exporter.export(source, tmp_path / "out", (name,))
