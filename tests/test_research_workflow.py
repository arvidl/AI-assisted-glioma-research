"""Notebook 13's workflow stages, examples, synthetic masks and reference check."""

import io
import json
import re
from pathlib import Path
from urllib.parse import unquote

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from glioma_ai import research_workflow as rw

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks/13_research_workflow_examples.ipynb"


def test_nine_stages_in_slide_order_with_existing_examples():
    assert [stage.title for stage in rw.STAGES] == [
        "Idea",
        "Literature review",
        "Research questions",
        "Study design",
        "Applications",
        "Implementation",
        "Data analysis",
        "Reporting",
        "Further studies",
    ]
    assert rw.missing_examples(ROOT) == []
    assert rw.STAGES[5].label == "Implementa-\ntion"


def test_overlap_and_volume_disagree():
    shifted, larger = rw.overlap_volume_example()
    assert shifted["volume_error"] == 0 and shifted["dice"] < 0.6
    assert larger["dice"] > 0.85 and larger["volume_error"] > 0.3


def test_figure_draws_every_stage_and_highlight():
    for highlight in (None, 4):
        figure = plt.figure(figsize=(12, 6.8))
        rw.draw_workflow(figure, highlight=highlight)
        texts = [text.get_text() for text in figure.axes[0].texts]
        assert all(any(stage.label in text for text in texts) for stage in rw.STAGES)
        plt.close(figure)


class Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_doi_metadata_reads_csl_json_and_reports_disagreements():
    record = {
        "title": "A title",
        "author": [{"family": "Collins", "given": "Gary S"}],
        "issued": {"date-parts": [[2024, 4, 16]]},
        "published-online": {"date-parts": [[2024, 4, 16]]},
    }
    seen = {}

    def opener(request, timeout):
        seen["url"], seen["accept"] = request.full_url, request.get_header("Accept")
        return Response(json.dumps(record).encode())

    metadata = rw.doi_metadata("10.1136/bmj-2023-078378", opener=opener)
    assert seen["url"] == "https://doi.org/10.1136/bmj-2023-078378"
    assert "csl+json" in seen["accept"]
    assert metadata["years"] == [2024] and metadata["first_author"] == "Collins"
    assert rw.check_reference("Collins", 2024, metadata) == []
    assert len(rw.check_reference("Moons", 2023, metadata)) == 2


def test_notebook_dois_are_the_checked_list():
    text = "".join(
        "".join(cell["source"])
        for cell in json.loads(NOTEBOOK.read_text())["cells"]
        if cell["cell_type"] == "markdown"
    )
    cited = {unquote(doi) for doi in re.findall(r"https://doi\.org/(10\.[^)\s]+)\)", text)}
    assert cited == {doi for doi, _, _ in rw.NOTEBOOK_DOIS}
