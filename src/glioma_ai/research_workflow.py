"""The nine stages of a research workflow and where this repository illustrates them.

Teaching content for notebook 13. Stage names and bullets follow the
investigator's slide "The Research Workflow (from idea to reporting)"; the
notebooks and files listed for each stage are curated examples in this
repository, checked to exist by the tests. Nothing here calls a language model.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np
from matplotlib.patches import FancyBboxPatch, Polygon

from glioma_ai.metrics import dice_score, relative_volume_error, volume_ml

DARK_GREEN, TEAL, BLUE, LIGHT_GREEN, YELLOW = "#548235", "#00957f", "#1a9ad6", "#8cc63f", "#ffe93b"
NAVY = "#1f3864"


@dataclass(frozen=True)
class Stage:
    title: str
    slide: tuple[str, ...]
    colour: str
    notebooks: tuple[str, ...]
    examples: tuple[str, ...]

    @property
    def label(self) -> str:
        """Title broken to fit a narrow box, hyphenating one long word as on the slide."""
        if " " in self.title or len(self.title) <= 12:
            return self.title.replace(" ", "\n")
        return f"{self.title[:10]}-\n{self.title[10:]}"

    @property
    def text_colour(self) -> str:
        return NAVY if self.colour in (LIGHT_GREEN, YELLOW) else "white"


STAGES = (
    Stage(
        "Idea",
        ("Initial concept or question",),
        DARK_GREEN,
        ("05", "06", "11"),
        ("notebooks/11_network_disconnection.ipynb",),
    ),
    Stage(
        "Literature review",
        ("Existing research, knowledge gaps",),
        TEAL,
        ("09", "11", "12"),
        ("docs/bibliography-check.md", "docs/ai-use/2026-10-15-notebook-12-tracks.md"),
    ),
    Stage(
        "Research questions",
        ("Precisely testable hypothesis or question",),
        BLUE,
        ("03", "05", "12"),
        ("notebooks/README.md",),
    ),
    Stage(
        "Study design",
        ("Methodology, participants, variables",),
        LIGHT_GREEN,
        ("04", "06", "10"),
        ("docs/cognition-prediction-study.md", "docs/ai-benefit-evaluation.md"),
    ),
    Stage(
        "Applications",
        ("Ethics approval", "Financing"),
        YELLOW,
        ("03", "10"),
        ("docs/data.md",),
    ),
    Stage(
        "Implementation",
        ("Execution, collection of data",),
        DARK_GREEN,
        ("00", "01", "03"),
        ("src/glioma_ai/references/lumiere_bundle_p048.json", "docs/reproducibility.md"),
    ),
    Stage(
        "Data analysis",
        ("Processing, analysis, statistics, interpretation",),
        TEAL,
        ("01", "02", "03", "10", "12"),
        ("docs/ai-use/2026-10-15-notebook-runner-stall.md",),
    ),
    Stage(
        "Reporting",
        ("Publishing, peer reviews", "Dissemination"),
        BLUE,
        ("04", "10"),
        ("docs/ai-records/template.json", "docs/ai-workflow.md", "paper/main.tex"),
    ),
    Stage(
        "Further studies",
        ("New studies and collaboration", "Research-based teaching"),
        LIGHT_GREEN,
        ("00", "10", "12"),
        ("docs/cognition-prediction-study.md", "notebooks/README.md"),
    ),
)

AI_MODES = (
    ("AI support", "answers a bounded request; the researcher does everything else"),
    ("AI collaborator", "drafts, critiques and revises in a dialogue; the researcher decides"),
    ("AI agent", "plans and carries out several steps with tools; the researcher sets limits"),
)


def missing_examples(root: Path) -> list[str]:
    """Example paths and notebook numbers of STAGES that do not exist under root."""
    notebooks = {path.name[:2] for path in (root / "notebooks").glob("[0-9][0-9]_*.ipynb")}
    missing = [path for stage in STAGES for path in stage.examples if not (root / path).exists()]
    missing += [f"notebook {n}" for stage in STAGES for n in stage.notebooks if n not in notebooks]
    return sorted(set(missing))


def _box(axis, x, y, width, height, colour, alpha=1.0):
    axis.add_patch(
        FancyBboxPatch(
            (x, y),
            width,
            height,
            boxstyle="round,pad=0,rounding_size=0.12",
            facecolor=colour,
            edgecolor="none",
            alpha=alpha,
        )
    )


def draw_workflow(figure, highlight: int | None = None, show_notebooks: bool = True) -> None:
    """The nine stages on a grey arrow, with lines from the three AI modes to every stage.

    highlight is a 0-based stage index; other stages are faded. Notebook numbers
    under each title are this repository's examples of the stage.
    """
    axis = figure.add_axes((0, 0, 1, 1))
    axis.set_xlim(0, 10.2)
    axis.set_ylim(0, 5.8)
    axis.axis("off")
    axis.add_patch(
        Polygon(
            [(0.8, 2.4), (7.3, 2.4), (7.3, 1.2), (9.9, 3.5), (7.3, 5.8), (7.3, 4.6), (0.8, 4.6)],
            facecolor="#d5ddd2",
            edgecolor="none",
        )
    )
    axis.text(4.1, 5.35, "The research workflow", ha="center", fontsize=17)
    axis.text(4.1, 4.95, "(from idea to reporting)", ha="center", fontsize=12)
    width, gap, top = 0.97, 0.15, 4.2
    hub = (4.6, 0.75)
    for index, stage in enumerate(STAGES):
        x = 0.05 + index * (width + gap)
        faded = highlight is not None and index != highlight
        alpha = 0.25 if faded else 1.0
        _box(axis, x, 2.55, width, top - 2.55, stage.colour, alpha)
        colour = stage.text_colour if not faded else "#888888"
        axis.text(
            x + 0.07,
            top - 0.1,
            stage.label,
            color=colour,
            fontsize=9,
            fontweight="bold",
            va="top",
        )
        bullets = "\n".join("• " + "\n  ".join(_wrap(b, 14)) for b in stage.slide)
        axis.text(x + 0.07, top - 0.62, bullets, color=colour, fontsize=7, va="top")
        if show_notebooks:
            axis.text(
                x + width / 2,
                2.65,
                "NB " + ", ".join(stage.notebooks),
                color=colour,
                fontsize=6.4,
                ha="center",
                va="bottom",
                style="italic",
            )
        line_alpha = 0.2 if faded else 0.9
        axis.annotate(
            "",
            xy=(x + width / 2, 2.53),
            xytext=hub,
            arrowprops={"arrowstyle": "->", "color": "#34495e", "lw": 0.8, "alpha": line_alpha},
        )
    axis.text(
        hub[0],
        hub[1] - 0.15,
        "  /  ".join(name for name, _ in AI_MODES),
        ha="center",
        va="top",
        fontsize=13,
    )


def _wrap(text: str, width: int) -> list[str]:
    lines, line = [], ""
    for word in text.split():
        if line and len(line) + 1 + len(word) > width:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    return [*lines, line]


def _sphere(shape: int, centre_mm, radius_mm: float) -> np.ndarray:
    grid = np.indices((shape, shape, shape), dtype=float) + 0.5
    distance = np.sqrt(sum((grid[i] - centre_mm[i]) ** 2 for i in range(3)))
    return (distance <= radius_mm).astype(np.uint8)


def overlap_volume_example(shape: int = 48, radius_mm: float = 10.0) -> list[dict]:
    """Synthetic 1 mm isotropic spheres: Dice and volume error disagree.

    The reference is a sphere of radius_mm. One candidate has the same radius,
    shifted by 6 mm; the other is concentric with a radius 1 mm larger.
    """
    affine = np.eye(4)
    centre = np.array([shape / 2] * 3)
    reference = _sphere(shape, centre, radius_mm)
    candidates = {
        "same size, shifted 6 mm": _sphere(shape, centre + [6.0, 0, 0], radius_mm),
        "same centre, radius +1 mm": _sphere(shape, centre, radius_mm + 1.0),
    }
    reference_ml = volume_ml(reference, affine)
    rows = []
    for name, mask in candidates.items():
        candidate_ml = volume_ml(mask, affine)
        rows.append(
            {
                "candidate": name,
                "reference_ml": reference_ml,
                "candidate_ml": candidate_ml,
                "volume_error": relative_volume_error(candidate_ml, reference_ml),
                "dice": dice_score(mask, reference),
            }
        )
    return rows


NOTEBOOK_DOIS = (
    ("10.1038/s41586-019-1563-y", "Venkatesh", 2019),
    ("10.1038/nature26000", "Capper", 2018),
    ("10.1038/s41586-023-06221-2", "Wang", 2023),
    ("10.1038/s41598-023-41032-5", "Walters", 2023),
    ("10.1038/s41586-024-07146-0", "Messeri", 2024),
    ("10.1093/neuonc/noab106", "Louis", 2021),
    ("10.1200/JCO.23.01059", "Wen", 2023),
    ("10.1136/bmj-2023-078378", "Collins", 2024),
    ("10.1148/ryai.240300", "Tejani", 2024),
    ("10.1038/sdata.2016.18", "Wilkinson", 2016),
    ("10.1038/sdata.2016.44", "Gorgolewski", 2016),
    ("10.1038/s41597-022-01881-7", "Suter", 2022),
    ("10.1148/ryai.220058", "Calabrese", 2022),
    ("10.1038/s41597-022-01806-4", "Aerts", 2022),
    ("10.1038/s41592-020-01008-z", "Isensee", 2021),
    ("10.1016/S1470-2045(19)30098-1", "Kickingereder", 2019),
    ("10.1038/s41591-019-0715-9", "Hollon", 2020),
    ("10.1080/03091902.2026.2713703", "Lundervold", 2026),
    ("10.1016/j.patter.2023.100804", "Kapoor", 2023),
    ("10.1038/s41746-023-00819-6", "Gao", 2023),
    ("10.1056/AIoa2400196", "Liang", 2024),
    ("10.1126/science.adg7879", "Thorp", 2023),
    ("10.48550/arXiv.2408.06292", "Lu", 2024),
    ("10.48550/arXiv.2502.18864", "Gottweis", 2025),
)


def doi_metadata(doi: str, timeout: float = 20.0, opener=urlopen) -> dict:
    """First author, years and title of a DOI from doi.org (Crossref or DataCite).

    This is an explicit network request; nothing in the package calls it implicitly.
    """
    request = Request(
        f"https://doi.org/{doi}", headers={"Accept": "application/vnd.citationstyles.csl+json"}
    )
    with opener(request, timeout=timeout) as response:
        record = json.loads(response.read())
    years = {
        int(record[key]["date-parts"][0][0])
        for key in ("issued", "published-print", "published-online")
        if record.get(key, {}).get("date-parts", [[None]])[0][0]
    }
    authors = record.get("author") or [{}]
    title = record.get("title")
    return {
        "doi": doi,
        "first_author": authors[0].get("family", ""),
        "years": sorted(years),
        "title": title[0] if isinstance(title, list) else title or "",
    }


def check_reference(expected_author: str, expected_year: int, metadata: dict) -> list[str]:
    """Disagreements between a cited first author and year and the registry record."""
    problems = []
    if metadata["first_author"].casefold() != expected_author.casefold():
        problems.append(f"first author {metadata['first_author']!r}, cited {expected_author!r}")
    if expected_year not in metadata["years"]:
        problems.append(f"years {metadata['years']}, cited {expected_year}")
    return problems
