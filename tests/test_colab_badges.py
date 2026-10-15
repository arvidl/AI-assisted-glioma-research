"""Published notebooks open in Colab from their own file in the public repository."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BADGE = re.compile(
    r"\[!\[Open In Colab\]\(https://colab\.research\.google\.com/assets/colab-badge\.svg\)\]"
    r"\(https://colab\.research\.google\.com/github/arvidl/AI-assisted-glioma-research"
    r"/blob/main/notebooks/([^)]+)\)"
)


def published() -> list[Path]:
    return sorted((ROOT / "notebooks").glob("[0-9][0-9]_*.ipynb"))


def badges(path: Path) -> list[str]:
    cells = json.loads(path.read_text())["cells"]
    return BADGE.findall("".join(cells[0]["source"])) if cells[0]["cell_type"] == "markdown" else []


def test_published_notebooks_have_a_badge_to_their_own_file():
    paths = published()
    assert paths
    for path in paths:
        assert badges(path) == [path.name], path


def test_badges_name_their_own_file_everywhere():
    for path in sorted((ROOT / "notebooks").rglob("*.ipynb")):
        assert set(badges(path)) <= {path.name}, path
