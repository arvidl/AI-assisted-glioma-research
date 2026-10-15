import re

import matplotlib

matplotlib.use("Agg")

from glioma_ai.paper_assets import (  # noqa: E402
    cantab_cohort_assets,
    cohort_assets,
    connectome_assets,
    lumiere_assets,
    network_assets,
)

MACRO = re.compile(r"\\newcommand\{\\([A-Za-z]+)\}\{([^}]*)\}")


def macros(path):
    return dict(MACRO.findall(path.read_text()))


def test_network_and_connectome_assets_write_figures_and_numeric_macros(tmp_path):
    paper = tmp_path / "paper"
    paper.mkdir()
    assert network_assets(tmp_path / "network", paper)["status"] == "built"
    assert connectome_assets(tmp_path / "connectome", paper)["status"] == "built"
    for name in ("network_lesion", "network_resection", "pat16_connectome", "pat16_resection"):
        assert (paper / f"{name}.pdf").stat().st_size > 0
    assert (paper / "pat16_scenario.pdf").stat().st_size > 0
    for name in ("network_numbers.tex", "connectome_numbers.tex"):
        values = macros(paper / name)
        assert values and all(re.fullmatch(r"-?\d+(\.\d+)?", v) for v in values.values())
    pat = macros(paper / "connectome_numbers.tex")
    assert float(pat["PatProxyRecall"]) <= 100 and float(pat["PatProxyPrecision"]) <= 100


def test_inputs_that_need_fetching_are_skipped_not_substituted(tmp_path, monkeypatch):
    for variable in ("HPGS_REPO", "LUMIERE_P048_ROOT", "LUMIERE_P048_SLICE_BUNDLE"):
        monkeypatch.delenv(variable, raising=False)
    paper = tmp_path / "paper"
    paper.mkdir()
    assert cantab_cohort_assets(tmp_path / "btc", paper)["status"] == "skipped"
    assert cohort_assets(tmp_path, tmp_path / "cohort", paper, {})["status"] == "skipped"
    assert lumiere_assets(tmp_path, tmp_path / "lumiere", paper)["status"] == "skipped"
    assert list(paper.iterdir()) == []
