"""Figures and number macros for paper/main.tex, one group per notebook.

Synthetic constructions (notebooks 01, 02, 05-08, 11) and the tracked sub-PAT16
matrices (notebook 12) are always built. Inputs that must be fetched or
configured first are used only when present: the OpenNeuro participant tables
(notebook 10, make btc-fetch), the UCSF-PDGM cohort release (notebook 01's
cohort figure, make hpgs-bundle-fetch), the prepared LUMIERE case (notebook 03,
make lumiere-bundle-fetch) and the published figures (notebook 09, make
published-figures-fetch). Nothing is downloaded or substituted here; a missing
input is reported in assets.json and the paper shows a notice in its place.
"""

import json
import shutil
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from glioma_ai.btc_cantab import btc_reference, load_cohort  # noqa: E402
from glioma_ai.btc_cantab_figures import draw_cohort  # noqa: E402
from glioma_ai.connectome import homotopic_summary, load_case  # noqa: E402
from glioma_ai.connectome_figures import write_connectome_experiment  # noqa: E402
from glioma_ai.connectome_interactive import (  # noqa: E402
    TUMOUR_CENTRE,
    draw_scenario,
    proxy_calibration,
    resection_scenario,
)
from glioma_ai.demo import run_demo  # noqa: E402
from glioma_ai.hpgs_cohort import (  # noqa: E402
    cohort_table,
    companion_checkout,
    write_cohort_figure,
)
from glioma_ai.lumiere_dynamics import (  # noqa: E402
    load_configured_case,
    run_case_experiment,
    write_case_paper_assets,
    write_observation_figures,
)
from glioma_ai.network_figures import write_network_experiment  # noqa: E402
from glioma_ai.published import prepared_published_figures  # noqa: E402

SCENARIO_RADIUS_MM = 20.0


def _macros(path: Path, comment: str, values: dict[str, str]) -> None:
    path.write_text(
        f"% {comment}\n"
        + "".join("\\newcommand{\\" + key + "}{" + value + "}\n" for key, value in values.items())
    )


def network_assets(output: Path, paper_dir: Path) -> dict:
    """Notebook 11: constructed network, tumour disconnection and resection."""
    record = write_network_experiment(output)
    for name in ("network_lesion", "network_resection"):
        shutil.copy2(output / f"{name}.pdf", paper_dir / f"{name}.pdf")
    at = record["scenarios_at_day"]
    names = list(at)
    _macros(
        paper_dir / "network_numbers.tex",
        "Generated from the synthetic network of notebook 11; no patient data.",
        {
            "NetDay": f"{record['day']:.0f}",
            "NetHealthyInterFC": f"{record['healthy_mean_interhemispheric_fc']:.3f}",
            "NetGuidedInterWeight": f"{at[names[-2]]['interhemispheric_weight_percent']:.1f}",
            "NetGuidedEfficiency": f"{at[names[-2]]['global_efficiency_percent']:.1f}",
            "NetGuidedInterFC": f"{at[names[-2]]['mean_interhemispheric_fc']:.3f}",
            "NetSparedInterWeight": f"{at[names[-1]]['interhemispheric_weight_percent']:.1f}",
            "NetResectionDay": f"{record['resection']['day']:.0f}",
            "NetCavityArea": f"{record['resection']['cavity_area_mm2']:.0f}",
        },
    )
    return {"notebook": "11", "status": "built", "scenarios": names}


def connectome_assets(output: Path, paper_dir: Path) -> dict:
    """Notebook 12: sub-PAT16 structure-function, virtual resection and a sphere scenario."""
    case = load_case()
    record = write_connectome_experiment(output, case=case)
    for name in ("pat16_connectome", "pat16_resection"):
        shutil.copy2(output / f"{name}.pdf", paper_dir / f"{name}.pdf")
    scenario = resection_scenario(case, TUMOUR_CENTRE, SCENARIO_RADIUS_MM)
    figure = plt.figure(figsize=(19, 4.8), constrained_layout=True)
    draw_scenario(figure, case, scenario)
    figure.savefig(paper_dir / "pat16_scenario.pdf")
    plt.close(figure)
    homotopic = homotopic_summary(case)
    proxy = proxy_calibration(case)
    agreement = record["fc_change_agreement"]
    _macros(
        paper_dir / "connectome_numbers.tex",
        "Generated from the tracked CC0 sub-PAT16 matrices; upstream QC not reviewed.",
        {
            "PatPreR": f"{record['structure_function']['preop']['r_at_g']:.3f}",
            "PatPostR": f"{record['structure_function']['postop']['r_at_g']:.3f}",
            "PatNullHigh": f"{record['preop_shuffled_region_null_at_g']['percentile_97_5']:.3f}",
            "PatMaskML": f"{record['tumour']['mask_volume_ml']:.1f}",
            "PatTumourWeight": f"{record['tumour']['preop_weight_through_tumour_percent']:.1f}",
            "PatVirtualR": f"{agreement['r_virtual_resection']:.3f}",
            "PatPlacementMedian": f"{agreement['placement_null']['median']:.3f}",
            "PatMeasuredScR": f"{agreement['r_measured_postop_sc']:.3f}",
            "PatHomotopicFC": f"{homotopic['preop']['homotopic']['mean_fc']:.2f}",
            "PatOtherInterFC": f"{homotopic['preop']['other_interhemispheric']['mean_fc']:.2f}",
            "PatHomotopicModelFC": f"{homotopic['preop']['homotopic']['mean_model_fc']:.2f}",
            "PatInterSharePre": f"{homotopic['preop']['interhemispheric_weight_percent']:.1f}",
            "PatInterSharePost": f"{homotopic['postop']['interhemispheric_weight_percent']:.1f}",
            "PatProxyRadius": f"{proxy['radius_mm']:.1f}",
            "PatProxyRemoved": f"{proxy['proxy_weight_removed_percent']:.1f}",
            "PatMeasuredThrough": f"{proxy['measured_weight_through_mask_percent']:.1f}",
            "PatProxyRecall": f"{proxy['recall_percent']:.0f}",
            "PatProxyPrecision": f"{proxy['precision_percent']:.0f}",
            "PatScenarioRadius": f"{SCENARIO_RADIUS_MM:.0f}",
            "PatScenarioRemoved": f"{scenario['weight_removed_percent']:.1f}",
        },
    )
    return {"notebook": "12", "status": "built", "upstream_qc": record["upstream_qc"]}


def cohort_assets(repo_root: Path, output: Path, paper_dir: Path, synthetic: dict) -> dict:
    """Notebook 01 cohort figure from the UCSF-PDGM release, when configured."""
    checkout = companion_checkout(repo_root)
    if checkout is None:
        return {"notebook": "01", "status": "skipped", "needs": "make hpgs-bundle-fetch"}
    write_cohort_figure(checkout, cohort_table(checkout), synthetic, output)
    shutil.copy2(output / "hpgs_cohort.png", paper_dir / "hpgs_cohort.png")
    return {"notebook": "01", "status": "built"}


def cantab_cohort_assets(btc_dir: Path, paper_dir: Path) -> dict:
    """Notebook 10 group summaries with the sub-PAT16 case, from the pinned CC0 tables."""
    if not all((Path(btc_dir) / name).is_file() for name in btc_reference()["files"]):
        return {"notebook": "10", "status": "skipped", "needs": "make btc-fetch"}
    figure = plt.figure(figsize=(13, 8))
    draw_cohort(figure, load_cohort(btc_dir))
    figure.savefig(paper_dir / "btc_cohort.pdf", bbox_inches="tight")
    plt.close(figure)
    return {"notebook": "10", "status": "built"}


def lumiere_assets(repo_root: Path, output: Path, paper_dir: Path) -> dict:
    """Notebook 03 panels and numbers from the prepared LUMIERE case, when configured."""
    case = load_configured_case(repo_root)
    if case is None:
        return {"notebook": "03", "status": "skipped", "needs": "make lumiere-bundle-fetch"}
    write_observation_figures(case, output)
    result = run_case_experiment(case, output, selected_labels=(1, 4))
    write_case_paper_assets(result, output, paper_dir)
    return {"notebook": "03", "status": "built"}


def write_paper_assets(repo_root: Path, output: Path, paper_dir: Path, btc_dir: Path) -> dict:
    repo_root, output, paper_dir = Path(repo_root), Path(output), Path(paper_dir)
    paper_dir.mkdir(parents=True, exist_ok=True)
    demo = run_demo(output / "demo", paper_dir)
    published = prepared_published_figures(paper_dir)
    assets = {
        "synthetic": {"notebooks": ["01", "02", "05", "06", "07", "08"], "status": "built"},
        "cohort": cohort_assets(repo_root, output / "cohort", paper_dir, demo["imaging"]),
        "lumiere": lumiere_assets(repo_root, output / "lumiere", paper_dir),
        "published_figures": {
            "notebook": "09",
            "status": "present" if all(f["ready"] for f in published) else "skipped",
            "needs": "make published-figures-fetch",
        },
        "cantab": cantab_cohort_assets(btc_dir, paper_dir),
        "network": network_assets(output / "network", paper_dir),
        "connectome": connectome_assets(output / "connectome", paper_dir),
    }
    (paper_dir / "assets.json").write_text(json.dumps(assets, indent=2) + "\n")
    return assets
